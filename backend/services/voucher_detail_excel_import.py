# -*- coding: utf-8 -*-
"""
凭证明细 Excel 导入：财政「凭证导入临时表」样式 → gl_voucher / gl_voucher_entry / gl_voucher_entry_auxiliary。
复用 services.gl_import_service 的 import_vouchers、import_voucher_entries、import_voucher_entry_auxiliaries。
"""
from __future__ import annotations

import calendar
import io
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from Model import AccountAuxiliary, GLVoucherType, db
from services.gl_import_service import (
    _ensure_fiscal_year,
    _extract_and_create_accounts_from_references,
    _str_or_empty,
    import_voucher_entries,
    import_voucher_entry_auxiliaries,
    import_vouchers,
)

# 与 gl_import 一致：无类型列时 0 期 → 期初，1–12、13 → 记帐
VOUCHER_TYPE_OPENING = ("QC", "期初凭证")
VOUCHER_TYPE_NORMAL = ("JZ", "记账凭证")

_HEADER_SCAN_MAX_ROW = 35

# account_auxiliary.auxiliary_item_name → 临时表「编码」列名（与计划表头一致）
AUX_NAME_TO_CODE_COL: dict[str, str] = {
    "项目": "项目编码",
    "部门": "部门编码",
    "单位往来": "单位往来",
    "功能科目": "功能性分类编码",
    "功能分类": "功能性分类编码",
    "部门经济科目": "部门经济科目编码",
    "资金性质": "资金来源编码",
    "预算来源": "预算来源编码",
    "预算项目": "预算项目编码",
    "经营性项目": "经营性项目编码",
    "业务活动项目": "业务活动项目编码",
    "业务活动类型": "业务活动类型编码",
    "银行资金类型": "银行资金类型编码",
}

_ALIAS_INTERVAL = ("会计区间", "会计期间", "期间")
_ALIAS_VOUCHER_NO = ("凭证编码", "凭证号", "记账凭证编号", "凭证编号")
_ALIAS_VOUCHER_DATE = ("凭证日期", "日期")
_ALIAS_ACCOUNT = ("会计科目编码", "科目编号", "科目编码")
_ALIAS_ACCOUNT_NAME = ("会计科目名称", "科目名称")
_ALIAS_ENTRY_SUMMARY = ("分录行摘要", "摘要", "分录摘要")
_ALIAS_DEBIT = ("借方金额", "借方")
_ALIAS_CREDIT = ("贷方金额", "贷方")

# 「项目」辅助项：优先取项目编码，为空则用预算项目编码（与财政临时表习惯一致）
_COL_PROJECT_CODE = "项目编码"
_COL_BUDGET_PROJECT_CODE = "预算项目编码"


def _cell_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
    return str(v).strip()


def _decimal_cell(v: Any) -> Decimal | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float, Decimal)):
        try:
            return Decimal(str(v))
        except Exception:
            return None
    s = str(v).strip().replace(",", "").replace("，", "")
    if not s or s in ("-", "—"):
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def _parse_voucher_date(v: Any) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y%m%d")
    if isinstance(v, date):
        return v.strftime("%Y%m%d")
    s = re.sub(r"[\s\-/\.年月]", "", str(v))
    if len(s) == 6 and s.isdigit():
        return s + "01"
    if len(s) == 7 and s.isdigit():
        return s + "0"
    if len(s) >= 8 and s[:8].isdigit():
        return s[:8]
    return None


def _synthetic_voucher_date(fiscal_year: int, period_number: int) -> str:
    if period_number == 0 or period_number is None:
        return f"{fiscal_year}0101"
    if 1 <= period_number <= 12:
        _y, m_len = calendar.monthrange(fiscal_year, period_number)
        return f"{fiscal_year}{period_number:02d}{m_len:02d}"
    if period_number == 13:
        return f"{fiscal_year}1231"
    return f"{fiscal_year}0101"


def _int_period(v: Any) -> int | None:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)) and v == int(v):
        p = int(v)
    else:
        s = str(v).strip()
        m = re.match(r"^(\d+)", s)
        p = int(m.group(1)) if m else None
    if p is None:
        return None
    if 0 <= p <= 13:
        return p
    return None


def _ordered_auxiliaries(
    account_book_code: str,
    fiscal_year: int,
    account_code: str,
) -> list[AccountAuxiliary]:
    rows = (
        AccountAuxiliary.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=account_code,
        )
        .all()
    )
    if not rows:
        return []

    def _k(a: AccountAuxiliary) -> tuple[int, str]:
        c = str(a.auxiliary_item_code or "")
        if c.isdigit():
            return (int(c), c)
        return (999, c)

    return sorted(rows, key=_k)


def _excel_code_col(aa: AccountAuxiliary) -> str | None:
    name = (aa.auxiliary_item_name or "").strip()
    if name in AUX_NAME_TO_CODE_COL:
        return AUX_NAME_TO_CODE_COL[name]
    return None


def _value_for_project_auxiliary(row: dict[str, Any]) -> str:
    """科目辅助项为「项目」时：有项目编码用项目编码，否则用预算项目编码。"""
    v = _str_or_empty(row.get(_COL_PROJECT_CODE))
    if v:
        return v
    return _str_or_empty(row.get(_COL_BUDGET_PROJECT_CODE))


def validate_auxiliaries_for_row(
    account_book_code: str,
    fiscal_year: int,
    row: dict[str, Any],
    excel_row_no: int,
) -> str | None:
    """若科目在 account_auxiliary 中有定义，则对应 Excel 编码列须非空；无列映射则报错。"""
    acct = _str_or_empty(
        row.get("会计科目编码")
        or row.get("科目编号")
    )
    if not acct:
        return None
    for aa in _ordered_auxiliaries(account_book_code, fiscal_year, acct):
        aux_name = (aa.auxiliary_item_name or "").strip()
        if aux_name == "项目":
            if not _value_for_project_auxiliary(row):
                return (
                    f"第{excel_row_no}行：科目 {acct} 需填「项目」辅助："
                    f"请先填「{_COL_PROJECT_CODE}」；若为空，可仅填「{_COL_BUDGET_PROJECT_CODE}」"
                )
            continue
        col = _excel_code_col(aa)
        if not col:
            return (
                f"第{excel_row_no}行：科目 {acct} 的辅助项「{aa.auxiliary_item_name}」无对应临时表列映射，"
                f"请维护 services/voucher_detail_excel_import.AUX_NAME_TO_CODE_COL"
            )
        v = row.get(col)
        if v is None or str(v).strip() == "":
            return f"第{excel_row_no}行：科目 {acct} 需填辅助项「{aa.auxiliary_item_name}」（列「{col}」）"
    return None


def parse_voucher_detail_excel(
    file_bytes: bytes,
) -> tuple[list[dict[str, Any]], int, int, list[str]]:
    """
    解析第一张工作表。
    返回 (行字典列表(表头为键), 表头行号, 空行跳过数, warnings)
    """
    try:
        openpyxl_mod = __import__("openpyxl", fromlist=["load_workbook"])
        load_workbook = openpyxl_mod.load_workbook
    except Exception as e:
        raise RuntimeError("缺少 openpyxl 依赖，请先安装：pip install openpyxl") from e

    warnings: list[str] = []
    wb = load_workbook(filename=io.BytesIO(file_bytes), data_only=True, read_only=True)
    try:
        ws = wb.worksheets[0]
        header_row_no: int | None = None
        header_display: list[str] = []
        for row_no, row in enumerate(
            ws.iter_rows(min_row=1, max_row=_HEADER_SCAN_MAX_ROW, values_only=True),
            start=1,
        ):
            row_list = [row[i] if i < len(row) else None for i in range(len(row))]
            headers = [_cell_str(x) for x in row_list]
            if not any(headers):
                continue
            h_interval = -1
            for alias in _ALIAS_INTERVAL:
                for i, h in enumerate(headers):
                    if h == alias:
                        h_interval = i
                        break
                if h_interval >= 0:
                    break
            h_voucher = -1
            for alias in _ALIAS_VOUCHER_NO:
                for i, h in enumerate(headers):
                    if h == alias:
                        h_voucher = i
                        break
                if h_voucher >= 0:
                    break
            h_acct = -1
            for alias in _ALIAS_ACCOUNT:
                for i, h in enumerate(headers):
                    if h == alias:
                        h_acct = i
                        break
                if h_acct >= 0:
                    break
            if h_interval >= 0 and h_voucher >= 0 and h_acct >= 0:
                header_row_no = row_no
                header_display = headers
                break

        if header_row_no is None:
            raise ValueError(
                f"前 {_HEADER_SCAN_MAX_ROW} 行内未找到表头"
                f"（需同时包含：会计区间类、凭证编码类、会计科目编码类列）"
            )

        out: list[dict[str, Any]] = []
        skipped = 0
        for row in ws.iter_rows(min_row=header_row_no + 1, values_only=True):
            raw = [row[i] if i < len(row) else None for i in range(len(header_display))]
            if not any((x is not None and str(x).strip() != "") for x in raw):
                skipped += 1
                continue
            row_dict: dict[str, Any] = {}
            for j, h in enumerate(header_display):
                if h:
                    row_dict[h] = raw[j] if j < len(raw) else None
            out.append(row_dict)
        return out, header_row_no, skipped, warnings
    finally:
        wb.close()


def _normalize_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    """统一为样例表头键名，便于验证与建 gl_data。"""
    m: dict[str, Any] = {}
    for k, v in row.items():
        key = (k or "").strip()
        if not key:
            continue
        m[key] = v
    for alias in _ALIAS_INTERVAL:
        if alias in m and "会计区间" not in m:
            m["会计区间"] = m[alias]
            break
    for alias in _ALIAS_VOUCHER_NO:
        if alias in m and "凭证编码" not in m:
            m["凭证编码"] = m[alias]
            break
    for alias in _ALIAS_VOUCHER_DATE:
        if alias in m and "凭证日期" not in m:
            m["凭证日期"] = m[alias]
            break
    for alias in _ALIAS_ACCOUNT:
        if alias in m and "会计科目编码" not in m:
            m["会计科目编码"] = m[alias]
            break
    for alias in _ALIAS_ACCOUNT_NAME:
        if alias in m and "会计科目名称" not in m:
            m["会计科目名称"] = m[alias]
            break
    for alias in _ALIAS_ENTRY_SUMMARY:
        if alias in m and "分录行摘要" not in m:
            m["分录行摘要"] = m[alias]
            break
    for alias in _ALIAS_DEBIT:
        if alias in m and "借方金额" not in m:
            m["借方金额"] = m[alias]
            break
    for alias in _ALIAS_CREDIT:
        if alias in m and "贷方金额" not in m:
            m["贷方金额"] = m[alias]
            break
    return m


def _fill_auxiliaries_in_entry(
    d: dict[str, Any],
    r: dict[str, Any],
    account_book_code: str,
    fiscal_year: int,
) -> None:
    acct = d.get("科目编号") or ""
    for aa in _ordered_auxiliaries(account_book_code, fiscal_year, _str_or_empty(acct)):
        sc = str(aa.auxiliary_item_code or "")
        if not sc.isdigit():
            continue
        i = int(sc)
        if i < 1 or i > 30:
            continue
        aux_name = (aa.auxiliary_item_name or "").strip()
        if aux_name == "项目":
            val = _value_for_project_auxiliary(r)
        else:
            col = _excel_code_col(aa)
            if not col:
                continue
            val = _str_or_empty(r.get(col))
        if val:
            d[f"辅助项{i}编号"] = val


def _voucher_type_for_period(p: int) -> tuple[str, str]:
    if p == 0:
        return VOUCHER_TYPE_OPENING
    return VOUCHER_TYPE_NORMAL


def ensure_voucher_types_for_periods(
    account_book_code: str,
    fiscal_year: int,
    periods: set[int],
) -> int:
    """为出现的期间确保 gl_voucher_type 存在：0→QC/期初，1–12/13→JZ/记帐。"""
    n = 0
    for p in sorted(periods):
        code, name = _voucher_type_for_period(p)
        rec = GLVoucherType.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            voucher_type_code=code,
        ).first()
        if not rec:
            db.session.add(
                GLVoucherType(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    voucher_type_code=code,
                    voucher_type_name=name,
                    voucher_type_abbreviation=None,
                )
            )
            n += 1
    return n


def run_voucher_detail_excel_import(
    file_bytes: bytes,
    account_book_code: str,
    fiscal_year: int,
) -> dict[str, Any]:
    from Model import AccountBookFiscalYear

    ab = (account_book_code or "").strip()
    if not ab:
        return {"success": False, "message": "账套编码不能为空"}
    if not AccountBookFiscalYear.query.filter_by(
        account_book_code=ab, fiscal_year=fiscal_year
    ).first():
        return {
            "success": False,
            "message": f"未找到账套年度 {ab}/{fiscal_year}，请先在账套中维护该会计年度",
        }

    try:
        raw_rows, header_row, rows_skipped, parse_warnings = parse_voucher_detail_excel(
            file_bytes
        )
    except (RuntimeError, ValueError) as e:
        return {"success": False, "message": str(e)}

    warnings = list(parse_warnings)
    # 归一、分行号、构建 gl
    groups: dict[tuple[str, int | None], int] = {}
    entry_lines: list[tuple[dict[str, Any], int, int]] = []  # (norm_row, line_no, excel_row_no)
    for idx, r0 in enumerate(raw_rows):
        r = _normalize_row_keys(r0)
        excel_no = header_row + 1 + idx
        p = _int_period(r.get("会计区间"))
        vno = _str_or_empty(r.get("凭证编码"))
        acct = _str_or_empty(r.get("会计科目编码"))
        if p is None:
            return {"success": False, "message": f"第{excel_no}行：「会计区间」无效（须为 0–13）"}
        if not vno:
            return {"success": False, "message": f"第{excel_no}行：「凭证编码」不能为空"}
        if not acct:
            return {"success": False, "message": f"第{excel_no}行：「会计科目编码」不能为空"}
        dep = (vno, p)
        groups[dep] = groups.get(dep, 0) + 1
        line = groups[dep]
        deb = _decimal_cell(r.get("借方金额"))
        cr = _decimal_cell(r.get("贷方金额"))
        if deb is None and cr is None:
            return {
                "success": False,
                "message": f"第{excel_no}行：借方金额、贷方金额不能同时为空",
            }
        err = validate_auxiliaries_for_row(ab, fiscal_year, r, excel_no)
        if err:
            return {"success": False, "message": err}
        entry_lines.append((r, line, excel_no))

    # 凭证头（每个凭证键一条，取该凭证首行作摘要/日期等）
    list_voucher: list[dict[str, Any]] = []
    seen_h: set[tuple[str, int]] = set()
    periods_set: set[int] = set()
    for r, _line, en in entry_lines:
        r = _normalize_row_keys(r)
        p = _int_period(r.get("会计区间"))
        p = p if p is not None else 0
        vno = _str_or_empty(r.get("凭证编码"))
        periods_set.add(p)
        key = (vno, p)
        if key in seen_h:
            continue
        seen_h.add(key)
        vtype, _tname = _voucher_type_for_period(p)
        vdt = _parse_voucher_date(r.get("凭证日期"))
        if not vdt:
            vdt = _synthetic_voucher_date(fiscal_year, p)
            warnings.append(
                f"凭证 {vno} 期间{p} 未提供或无法解析「凭证日期」，已按年度与期间合成为 {vdt}（行约 {en}）"
            )
        list_voucher.append(
            {
                "凭证编号": vno,
                "会计期间号": p,
                "会计年度": fiscal_year,
                "凭证日期": vdt,
                "记账凭证类型编号": vtype,
                "附单据数": None,
                "制单人": None,
                "审核人": None,
                "记账人": None,
                "凭证状态": "未记账",
                "摘要": _str_or_empty(r.get("分录行摘要")) or None,
            }
        )

    list_entry: list[dict[str, Any]] = []
    for r, line, _en in entry_lines:
        r = _normalize_row_keys(r)
        p = _int_period(r.get("会计区间"))
        p = p if p is not None else 0
        d = {
            "凭证编号": _str_or_empty(r.get("凭证编码")),
            "会计年度": fiscal_year,
            "会计期间号": p,
            "分录行号": line,
            "科目编号": _str_or_empty(r.get("会计科目编码")),
            "科目名称": _str_or_empty(r.get("会计科目名称")) or None,
            "摘要": _str_or_empty(r.get("分录行摘要")) or None,
        }
        deb = _decimal_cell(r.get("借方金额"))
        crd = _decimal_cell(r.get("贷方金额"))
        if deb is not None:
            d["借方金额"] = float(deb)
        if crd is not None:
            d["贷方金额"] = float(crd)
        _fill_auxiliaries_in_entry(d, r, ab, fiscal_year)
        list_entry.append(d)

    gl_data: dict[str, list[dict[str, Any]]] = {
        "记账凭证": list_voucher,
        "记账凭证分录行": list_entry,
    }

    stats = {
        "记账凭证": 0,
        "记账凭证分录行": 0,
        "凭证分录辅助项": 0,
        "自动创建会计科目": 0,
        "补全凭证类型": 0,
    }

    try:
        _ensure_fiscal_year(ab, fiscal_year)
        stats["补全凭证类型"] = ensure_voucher_types_for_periods(
            ab, fiscal_year, periods_set
        )
        stats["自动创建会计科目"] = _extract_and_create_accounts_from_references(
            gl_data, ab, fiscal_year
        )
        stats["记账凭证"] = import_vouchers(gl_data, ab, fiscal_year)
        stats["记账凭证分录行"] = import_voucher_entries(gl_data, ab, fiscal_year)
        stats["凭证分录辅助项"] = import_voucher_entry_auxiliaries(
            gl_data, ab, fiscal_year
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": str(e),
            "stats": stats,
        }

    return {
        "success": True,
        "message": "凭证明细导入完成",
        "account_book_code": ab,
        "fiscal_year": fiscal_year,
        "stats": stats,
        "rows_skipped_empty": rows_skipped,
        "row_count": len(entry_lines),
        "warnings": warnings,
    }
