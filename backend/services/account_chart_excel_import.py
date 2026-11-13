# -*- coding: utf-8 -*-
"""会计科目 Excel 导入：解析工作簿并写入 account / account_auxiliary。"""
from __future__ import annotations

import io
import re
from typing import Any

from sqlalchemy.exc import IntegrityError

from Model import Account, AccountAuxiliary, AccountBookFiscalYear, CustomArchiveItem, db
from services.share_import_service import _int_or_none, _str_or_empty

_HEADER_SCAN_MAX_ROW = 15

_CODE_ALIASES = ('编码', '科目编号', '科目编码', '科目代码')
_NAME_ALIASES = ('名称', '科目名称')
_LEVEL_ALIASES = ('科目级次',)
# 科目类型：兼容财政模板「会计要素」「科目类别」与 SHARE「科目类型」列
_TYPE_ELEMENT_ALIASES = ('会计要素',)
_TYPE_CATEGORY_ALIASES = ('科目类别',)
_TYPE_LEGACY_ALIASES = ('科目类型',)
_BALANCE_ALIASES = ('余额方向',)
_IS_LEAF_ALIASES = ('是否末级',)
_IS_ENABLED_ALIASES = ('是否启用',)
_PARENT_ALIASES = ('上级科目编号', '上级科目', '父科目编号', '父级编码', '父级科目', '父级科目编码')
_AUX_ALIASES = ('辅助核算项', '辅助核算', '辅助项')
# 单元格里是档案/辅助项编码（如 3），不是名称。须与上面的名称列分开识别。
_AUX_CODE_ALIASES = ('辅助项编码', '辅助核算项编码', '辅助项编号')

_AUX_SPLIT_RE = re.compile(r'[,，、;；]+')


def _cell_str(v: Any) -> str:
    if v is None:
        return ''
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    return str(v).strip()


def _split_auxiliary_names(cell_val: Any) -> list[str]:
    s = _cell_str(cell_val)
    if not s:
        return []
    parts = [p.strip() for p in _AUX_SPLIT_RE.split(s) if p.strip()]
    return parts


def _resolve_col_index(headers: list[str], aliases: tuple[str, ...]) -> int:
    for a in aliases:
        if a in headers:
            return headers.index(a)
    return -1


def parse_account_chart_excel(file_bytes: bytes) -> tuple[list[dict[str, Any]], int]:
    """
    解析第一张工作表，返回 (行字典列表, 跳过的空行数)。
    支持财政模板表头：编码、名称、科目类别、会计要素、余额方向、辅助核算项、是否启用；
    亦兼容 SHARE 模板（科目编号、科目名称、科目级次、科目类型 等）。
    行字典内含标准化键（科目编号、科目名称、会计要素、科目类别…）及 _auxiliary_names。
    """
    try:
        openpyxl_module = __import__('openpyxl', fromlist=['load_workbook'])
        load_workbook = openpyxl_module.load_workbook
    except Exception as e:
        raise RuntimeError('缺少 openpyxl 依赖，请先安装：pip install openpyxl') from e

    wb = load_workbook(filename=io.BytesIO(file_bytes), data_only=True, read_only=True)
    try:
        ws = wb.worksheets[0]
        header_row_no: int | None = None
        idx: dict[str, int] = {}

        for row_no, row in enumerate(
            ws.iter_rows(min_row=1, max_row=_HEADER_SCAN_MAX_ROW, values_only=True),
            start=1,
        ):
            headers = [_cell_str(v) for v in row]
            code_i = _resolve_col_index(headers, _CODE_ALIASES)
            name_i = _resolve_col_index(headers, _NAME_ALIASES)
            bal_i = _resolve_col_index(headers, _BALANCE_ALIASES)
            type_el_i = _resolve_col_index(headers, _TYPE_ELEMENT_ALIASES)
            type_cat_i = _resolve_col_index(headers, _TYPE_CATEGORY_ALIASES)
            type_leg_i = _resolve_col_index(headers, _TYPE_LEGACY_ALIASES)
            # 必填：编码类、名称类、余额方向；类型列至少其一（会计要素/科目类别/科目类型），否则该行不算有效表头
            if code_i < 0 or name_i < 0 or bal_i < 0:
                continue
            if type_el_i < 0 and type_cat_i < 0 and type_leg_i < 0:
                continue
            header_row_no = row_no
            idx = {
                'code': code_i,
                'name': name_i,
                'level': _resolve_col_index(headers, _LEVEL_ALIASES),
                'type_element': type_el_i,
                'type_category': type_cat_i,
                'type_legacy': type_leg_i,
                'balance': bal_i,
                'is_leaf': _resolve_col_index(headers, _IS_LEAF_ALIASES),
                'is_enabled': _resolve_col_index(headers, _IS_ENABLED_ALIASES),
                'parent': _resolve_col_index(headers, _PARENT_ALIASES),
                'aux': _resolve_col_index(headers, _AUX_ALIASES),
                'aux_code': _resolve_col_index(headers, _AUX_CODE_ALIASES),
            }
            break

        if header_row_no is None:
            raise ValueError(
                '未找到有效表头行（前 %s 行内需同时包含：编码/科目编号、名称/科目名称、余额方向，'
                '以及会计要素/科目类别/科目类型至少一列）' % _HEADER_SCAN_MAX_ROW
            )

        rows_out: list[dict[str, Any]] = []
        skipped = 0
        seen_codes: set[str] = set()

        for row in ws.iter_rows(min_row=header_row_no + 1, values_only=True):
            row = list(row)
            def get_ci(key: str) -> Any:
                i = idx[key]
                if i < 0 or i >= len(row):
                    return None
                return row[i]

            code = _cell_str(get_ci('code'))
            name = _cell_str(get_ci('name'))
            level_raw = get_ci('level') if idx['level'] >= 0 else None
            el_raw = get_ci('type_element') if idx['type_element'] >= 0 else None
            cat_raw = get_ci('type_category') if idx['type_category'] >= 0 else None
            leg_raw = get_ci('type_legacy') if idx['type_legacy'] >= 0 else None
            bal_raw = get_ci('balance')

            if (
                not code
                and not name
                and level_raw in (None, '')
                and el_raw in (None, '')
                and cat_raw in (None, '')
                and leg_raw in (None, '')
                and bal_raw in (None, '')
            ):
                skipped += 1
                continue

            if not code:
                raise ValueError('存在科目编号为空的行（科目名称=%s）' % (name or ''))
            if not name:
                raise ValueError('存在科目名称为空的行（科目编号=%s）' % code)
            el_s = _cell_str(el_raw) if el_raw is not None else ''
            cat_s = _cell_str(cat_raw) if cat_raw is not None else ''
            leg_s = _cell_str(leg_raw) if leg_raw is not None else ''
            if not el_s and not cat_s and not leg_s:
                raise ValueError(
                    '存在会计要素、科目类别、科目类型均为空的行（编码=%s）' % code
                )
            if code in seen_codes:
                raise ValueError('Excel 中存在重复的科目编号：%s' % code)
            seen_codes.add(code)

            is_leaf_cell = get_ci('is_leaf') if idx['is_leaf'] >= 0 else None
            is_en_cell = get_ci('is_enabled') if idx['is_enabled'] >= 0 else None
            parent_cell = get_ci('parent') if idx['parent'] >= 0 else None
            aux_cell = get_ci('aux') if idx['aux'] >= 0 else None
            aux_code_cell = get_ci('aux_code') if idx['aux_code'] >= 0 else None

            aux_codes = _split_auxiliary_names(aux_code_cell)
            aux_names = [] if aux_codes else _split_auxiliary_names(aux_cell)

            rows_out.append({
                '科目编号': code,
                '科目名称': name,
                '科目级次': level_raw,
                '会计要素': el_raw,
                '科目类别': cat_raw,
                '科目类型': leg_raw,
                '余额方向': bal_raw,
                '是否末级': is_leaf_cell,
                '是否启用': is_en_cell,
                '上级科目编号': _cell_str(parent_cell) or None,
                '_auxiliary_names': aux_names,
                '_auxiliary_codes': aux_codes,
            })

        if not rows_out:
            raise ValueError('未读取到有效数据行')

        _fill_missing_levels(rows_out)
        if idx['is_leaf'] < 0:
            parent_codes = {
                _str_or_empty(r.get('上级科目编号'))
                for r in rows_out
                if _str_or_empty(r.get('上级科目编号'))
            }
            for r in rows_out:
                r['是否末级'] = '0' if r['科目编号'] in parent_codes else '1'

        return rows_out, skipped
    finally:
        wb.close()


def _fill_missing_levels(rows: list[dict[str, Any]]) -> None:
    """没有科目级次时，按上级科目链计算级次。"""
    by_code = {_str_or_empty(r.get('科目编号')): r for r in rows}
    memo: dict[str, int] = {}

    def depth(code: str, stack: set[str]) -> int:
        if code in memo:
            return memo[code]
        row = by_code.get(code)
        explicit = _int_or_none(row.get('科目级次')) if row else None
        if explicit:
            memo[code] = explicit
            return explicit
        if row is None or code in stack:
            memo[code] = 1
            return 1
        parent = _str_or_empty(row.get('上级科目编号'))
        if not parent:
            level = 1
        elif parent not in by_code:
            level = 2
        else:
            level = depth(parent, stack | {code}) + 1
        memo[code] = level
        return level

    for row in rows:
        if _int_or_none(row.get('科目级次')) is None:
            row['科目级次'] = depth(_str_or_empty(row.get('科目编号')), set())


def _row_to_account_fields(row: dict[str, Any]) -> dict[str, Any]:
    code = _str_or_empty(row.get('科目编号'))
    name = _str_or_empty(row.get('科目名称')) or code
    level = _int_or_none(row.get('科目级次'))
    if level is None:
        level = 1
    el = _str_or_empty(row.get('会计要素'))
    cat = _str_or_empty(row.get('科目类别'))
    leg = _str_or_empty(row.get('科目类型'))
    # 优先会计要素（与资产类/负债类等要素一致），其次科目类别，再次 SHARE「科目类型」列
    account_type = el or cat or leg or '资产类'
    remark = cat if (el and cat and account_type == el) else None
    balance_direction = _str_or_empty(row.get('余额方向')) or '借'
    is_leaf = 1 if _str_or_empty(row.get('是否末级')) in ('1', '是', 'true', 'True', 'Y', 'y') else 0
    is_enabled = 1 if _str_or_empty(row.get('是否启用')) not in ('0', '否', 'false', 'False', 'N', 'n') else 0
    parent_code = _str_or_empty(row.get('上级科目编号')) or None
    return {
        'account_code': code,
        'account_name': name,
        'account_level': level,
        'account_type': account_type,
        'balance_direction': balance_direction,
        'is_leaf': is_leaf,
        'is_enabled': is_enabled,
        'parent_account_code': parent_code,
        'remark': remark,
    }


def run_account_chart_excel_import(
    account_book_code: str,
    fiscal_year: int,
    parsed_rows: list[dict[str, Any]],
    *,
    mode: str = 'upsert',
    rows_skipped: int = 0,
) -> dict[str, Any]:
    """
    mode: upsert（默认）— 更新或新增科目，并重建该科目辅助核算；
          append — 仅新增，已存在科目则失败（整单不提交）。
    """
    mode = (mode or 'upsert').strip().lower()
    if mode not in ('upsert', 'append'):
        return {'success': False, 'message': 'mode 仅支持 upsert 或 append'}

    fy = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
    ).first()
    if not fy:
        return {
            'success': False,
            'message': '未找到账套年度: %s/%s' % (account_book_code, fiscal_year),
        }

    sorted_rows = sorted(
        parsed_rows,
        key=lambda r: (_int_or_none(r.get('科目级次')) or 1, _str_or_empty(r.get('科目编号'))),
    )

    file_codes = {_str_or_empty(r.get('科目编号')) for r in sorted_rows}
    existing_codes = {
        row.account_code
        for row in Account.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
        ).all()
    }
    known_codes = file_codes | existing_codes
    for r in sorted_rows:
        code = _str_or_empty(r.get('科目编号'))
        parent = _str_or_empty(r.get('上级科目编号'))
        if parent and parent == code:
            return {'success': False, 'message': '上级科目不能是自己: %s' % code}
        if parent and parent not in known_codes:
            return {
                'success': False,
                'message': '上级科目不存在: %s（科目 %s）' % (parent, code),
            }

    archive_names = {
        item.archive_item_code: item.archive_item_name
        for item in CustomArchiveItem.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
        ).all()
    }

    if mode == 'append':
        for r in sorted_rows:
            code = _str_or_empty(r.get('科目编号'))
            exists = Account.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=code,
            ).first()
            if exists:
                return {
                    'success': False,
                    'message': 'append 模式下科目已存在，无法导入: %s' % code,
                }

    stats = {
        'accounts_inserted': 0,
        'accounts_updated': 0,
        'auxiliaries_created': 0,
        'rows_skipped': int(rows_skipped),
    }

    try:
        for r in sorted_rows:
            fields = _row_to_account_fields(r)
            code = fields['account_code']
            aux_names: list[str] = r.get('_auxiliary_names') or []
            aux_codes: list[str] = r.get('_auxiliary_codes') or []

            rec = Account.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=code,
            ).first()

            if rec:
                rec.account_name = fields['account_name']
                rec.account_level = fields['account_level']
                rec.account_type = fields['account_type']
                rec.balance_direction = fields['balance_direction']
                rec.is_leaf = fields['is_leaf']
                rec.is_enabled = fields['is_enabled']
                rec.parent_account_code = fields['parent_account_code']
                rec.remark = fields['remark']
                stats['accounts_updated'] += 1
            else:
                rec = Account(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    account_code=code,
                    account_name=fields['account_name'],
                    account_level=fields['account_level'],
                    account_type=fields['account_type'],
                    balance_direction=fields['balance_direction'],
                    is_leaf=fields['is_leaf'],
                    is_enabled=fields['is_enabled'],
                    parent_account_code=fields['parent_account_code'],
                    remark=fields['remark'],
                    status=1,
                )
                db.session.add(rec)
                stats['accounts_inserted'] += 1

            AccountAuxiliary.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=code,
            ).delete(synchronize_session=False)

            if aux_codes:
                seen_aux: set[str] = set()
                for aux_code in aux_codes:
                    if aux_code in seen_aux:
                        continue
                    seen_aux.add(aux_code)
                    db.session.add(
                        AccountAuxiliary(
                            account_book_code=account_book_code,
                            fiscal_year=fiscal_year,
                            account_code=code,
                            auxiliary_item_code=aux_code,
                            auxiliary_item_name=archive_names.get(aux_code) or aux_code,
                            corresponding_archive=aux_code,
                            auxiliary_item_description=None,
                            status=1,
                        )
                    )
                    stats['auxiliaries_created'] += 1
            else:
                for i, aux_name in enumerate(aux_names, start=1):
                    db.session.add(
                        AccountAuxiliary(
                            account_book_code=account_book_code,
                            fiscal_year=fiscal_year,
                            account_code=code,
                            auxiliary_item_code=str(i),
                            auxiliary_item_name=aux_name,
                            corresponding_archive=None,
                            auxiliary_item_description=None,
                            status=1,
                        )
                    )
                    stats['auxiliaries_created'] += 1

        db.session.commit()
        return {
            'success': True,
            'message': '会计科目导入成功',
            'stats': stats,
        }
    except IntegrityError as e:
        db.session.rollback()
        return {
            'success': False,
            'message': '导入失败（数据约束冲突，请检查上级科目是否存在或科目层级顺序）: %s' % str(e),
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': '导入失败: %s' % str(e)}
