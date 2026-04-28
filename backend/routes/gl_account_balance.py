# -*- coding: utf-8 -*-
"""科目余额：查询、导出、从凭证重算"""
import importlib
from datetime import datetime
from io import BytesIO
from typing import Any

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import and_, or_

from Auth.auth import token_required
from Model import Account, AccountBookFiscalYear, GLAccountBalance, db
from services.gl_account_balance_recalc_from_vouchers import (
    recalculate_gl_account_balance_from_vouchers,
)

gl_account_balance_bp = Blueprint("gl_account_balance", __name__)

EXPORT_MAX_ROWS = 100_000


def _ensure_fiscal_year(account_book_code: str, fiscal_year: int):
    row = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
    ).first()
    if not row:
        return None, (
            jsonify(
                {
                    "success": False,
                    "message": f"未找到账套年度: {account_book_code}/{fiscal_year}",
                }
            ),
            404,
        )
    return row, None


def _normalize_page_gl() -> tuple[int, int]:
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50
    if page_size > 200:
        page_size = 200
    if page_size not in (10, 20, 50, 100, 200):
        page_size = 50
    return page, page_size


def _gl_balance_base_query(
    account_book_code: str,
    fiscal_year: int,
) -> Any:
    """
    与科目、期间、币种、科目名称等筛选条件一起使用的查询（
    返回 session.query(GLAccountBalance, Account.account_name) 对象）。
    """
    q = (
        db.session.query(GLAccountBalance, Account.account_name)
        .outerjoin(
            Account,
            and_(
                Account.account_book_code == GLAccountBalance.account_book_code,
                Account.fiscal_year == GLAccountBalance.fiscal_year,
                Account.account_code == GLAccountBalance.account_code,
            ),
        )
        .filter(
            GLAccountBalance.account_book_code == account_book_code,
            GLAccountBalance.fiscal_year == fiscal_year,
        )
    )

    period_num = request.args.get("period_number", type=int)
    period_start = request.args.get("period_start", type=int)
    period_end = request.args.get("period_end", type=int)
    if period_num is not None:
        q = q.filter(GLAccountBalance.period_number == period_num)
    else:
        if period_start is not None:
            q = q.filter(GLAccountBalance.period_number >= period_start)
        if period_end is not None:
            q = q.filter(GLAccountBalance.period_number <= period_end)

    code_q = request.args.get("account_code", "").strip()
    if code_q:
        q = q.filter(GLAccountBalance.account_code.like(f"%{code_q}%"))

    name_q = request.args.get("account_name", "").strip()
    if name_q:
        q = q.filter(Account.account_name.like(f"%{name_q}%"))

    summary_only = request.args.get("summary_only", "false").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if summary_only:
        q = q.filter(GLAccountBalance.currency_code.is_(None))

    lazy = request.args.get("lazy_tree", "").strip().lower() in ("1", "true", "yes")
    if lazy:
        pk = request.args.get("parent_key", "").strip()
        if not pk or pk == "__root__":
            q = q.filter(
                or_(
                    GLAccountBalance.parent_code.is_(None),
                    GLAccountBalance.parent_code == "",
                )
            )
        else:
            q = q.filter(GLAccountBalance.parent_code == pk)

    return q


def _codes_with_children_for_period(
    account_book_code: str, fiscal_year: int, period_number: int
) -> set[str]:
    """该期间下作为父级出现的科目编码（用于懒加载树是否可展开）。"""
    rows = (
        db.session.query(GLAccountBalance.parent_code)
        .filter(
            GLAccountBalance.account_book_code == account_book_code,
            GLAccountBalance.fiscal_year == fiscal_year,
            GLAccountBalance.period_number == period_number,
            GLAccountBalance.parent_code.isnot(None),
            GLAccountBalance.parent_code != "",
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows if r and r[0]}


def _row_to_item_gl_balance(row: GLAccountBalance, account_name: str | None) -> dict:
    d = row.to_dict()
    d["account_name"] = account_name
    return d


@gl_account_balance_bp.route(
    "/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/gl_account_balance",
    methods=["GET"],
)
@token_required
def list_gl_account_balance(current_user, account_book_code, fiscal_year):
    """
    分页查询科目余额表。

    查询参数（均可选，除账套/年度在路径中）:
    - period_number: 精确会计期间
    - period_start / period_end: 期间起止（含），与 period_number 互斥，若传 period_number 则仅按单期
    - account_code: 科目编号模糊
    - account_name: 科目名称模糊
    - summary_only: true/1 时只返回 currency_code 为空的行（本币/无币种）
    - lazy_tree: true/1 时启用树懒加载（与 period_number 联用，无分页）
    - parent_key: 懒加载时父级科目编号；省略或 __root__ 表示仅顶级（parent_code 为空）
    - page: 页码，默认 1（非 lazy_tree 时有效）
    - page_size: 每页条数，仅允许 10/20/50/100/200，默认 50（非 lazy_tree 时有效）
    """
    account_book_code = (account_book_code or "").strip()
    if not account_book_code:
        return jsonify({"success": False, "message": "账套编码不能为空"}), 400

    err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if err[1]:
        return err[1]

    try:
        lazy = request.args.get("lazy_tree", "").strip().lower() in ("1", "true", "yes")
        if lazy:
            pn = request.args.get("period_number", type=int)
            if pn is None:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "lazy_tree=1 时必须指定 period_number（会计期间 1–12）",
                        }
                    ),
                    400,
                )
            q = _gl_balance_base_query(account_book_code, fiscal_year)
            q = q.order_by(
                GLAccountBalance.account_code.asc(),
                GLAccountBalance.id.asc(),
            )
            rows = q.all()
            items = [
                _row_to_item_gl_balance(glab, aname) for glab, aname in rows
            ]
            with_children = _codes_with_children_for_period(
                account_book_code, fiscal_year, pn
            )
            for it in items:
                it["has_children"] = it.get("account_code") in with_children
            return jsonify(
                {
                    "success": True,
                    "items": items,
                    "lazy_tree": True,
                    "period_number": pn,
                }
            )

        page, page_size = _normalize_page_gl()
        q = _gl_balance_base_query(account_book_code, fiscal_year)
        q = q.order_by(
            GLAccountBalance.account_code.asc(),
            GLAccountBalance.period_number.asc(),
            GLAccountBalance.id.asc(),
        )
        pagination = q.paginate(page=page, per_page=page_size, error_out=False)
        items = [
            _row_to_item_gl_balance(glab, aname) for glab, aname in pagination.items
        ]
        return jsonify(
            {
                "success": True,
                "items": items,
                "total": pagination.total,
                "page": page,
                "page_size": page_size,
                "total_pages": pagination.pages,
            }
        )
    except Exception as e:  # noqa: BLE001
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"查询科目余额失败: {str(e)}",
                }
            ),
            500,
        )


@gl_account_balance_bp.route(
    "/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/gl_account_balance/export",
    methods=["GET"],
)
@token_required
def export_gl_account_balance(current_user, account_book_code, fiscal_year):
    """
    按与列表相同的查询条件导出为 Excel（.xlsx），无分页、返回文件下载。

    行数超过 {EXPORT_MAX_ROWS} 时返回 400。需安装 openpyxl。
    """
    account_book_code = (account_book_code or "").strip()
    if not account_book_code:
        return jsonify({"success": False, "message": "账套编码不能为空"}), 400

    err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if err[1]:
        return err[1]

    try:
        importlib.import_module("openpyxl")
    except ImportError:  # pragma: no cover
        return (
            jsonify(
                {
                    "success": False,
                    "message": "缺少 openpyxl 依赖，请先安装：pip install openpyxl",
                }
            ),
            500,
        )

    from openpyxl import Workbook

    try:
        q = _gl_balance_base_query(account_book_code, fiscal_year)
        q = q.order_by(
            GLAccountBalance.account_code.asc(),
            GLAccountBalance.period_number.asc(),
            GLAccountBalance.id.asc(),
        )
        total = q.count()
        if total > EXPORT_MAX_ROWS:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"导出行数 {total} 超过上限 {EXPORT_MAX_ROWS}，请缩小查询条件。",
                    }
                ),
                400,
            )

        rows = q.all()
        wb = Workbook()
        ws = wb.active
        ws.title = "科目余额"
        headers = [
            "账套编码",
            "会计年度",
            "会计期间",
            "科目编号",
            "科目名称",
            "父级科目",
            "期初余额",
            "期初方向",
            "本期借方",
            "本期贷方",
            "期末余额",
            "期末方向",
            "币种",
        ]
        ws.append(headers)
        for glab, aname in rows:
            d = glab
            ws.append(
                [
                    d.account_book_code,
                    d.fiscal_year,
                    d.period_number,
                    d.account_code,
                    (aname or "") if aname else "",
                    d.parent_code,
                    float(d.opening_balance) if d.opening_balance is not None else None,
                    d.opening_balance_direction,
                    float(d.current_period_debit_amount)
                    if d.current_period_debit_amount is not None
                    else None,
                    float(d.current_period_credit_amount)
                    if d.current_period_credit_amount is not None
                    else None,
                    float(d.closing_balance) if d.closing_balance is not None else None,
                    d.closing_balance_direction,
                    d.currency_code,
                ]
            )

        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        fn = f"科目余额表_{account_book_code}_{fiscal_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(
            bio,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=fn,
        )
    except Exception as e:  # noqa: BLE001
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"导出失败: {str(e)}",
                }
            ),
            500,
        )


@gl_account_balance_bp.route(
    "/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/gl_account_balance/recalculate_from_vouchers",
    methods=["POST"],
)
@token_required
def post_recalculate_from_vouchers(current_user, account_book_code, fiscal_year):
    """
    按账套、年度用凭证分录重算总账级科目余额（详见服务说明）。

    可选 JSON 体：{"level_pattern": "422"} — 每位表示一级编码长度增量（1–9），
    累计为各级科目编码总长度；将凭证明细按此前缀规则汇总到各级。不传或空串则仅保留明细科目行。
    """
    try:
        level_pattern = None
        if request.is_json and request.get_json(silent=True):
            body = request.get_json(silent=True) or {}
            lp = body.get("level_pattern")
            if lp is not None:
                level_pattern = str(lp).strip() or None
        result = recalculate_gl_account_balance_from_vouchers(
            account_book_code, fiscal_year, level_pattern=level_pattern
        )
        db.session.commit()
        return jsonify({"success": True, **result})
    except ValueError as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        return jsonify(
            {
                "success": False,
                "message": str(e) or "重算科目余额失败",
            }
        ), 500
