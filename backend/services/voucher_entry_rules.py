# -*- coding: utf-8 -*-
"""手工凭证的会计校验。不访问数据库，供录入服务和单元测试共用。"""
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

TWOPLACES = Decimal('0.01')
MAX_LINES = 500


class VoucherEntryError(Exception):
    """录入校验或保存失败。status 为 HTTP 状态码。"""

    def __init__(self, message: str, errors: list[str] | None = None, status: int = 400):
        super().__init__(message)
        self.message = message
        self.errors = errors or [message]
        self.status = status


def _text(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def parse_amount(value: Any, label: str) -> tuple[Decimal | None, str | None]:
    """金额须为非负、最多两位小数。空值按 0 处理。"""
    if value is None or value == '':
        return Decimal('0.00'), None
    if isinstance(value, bool):
        return None, f'{label}不是有效金额'
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        return None, f'{label}不是有效金额'
    if amount < 0:
        return None, f'{label}不能为负数'
    quantized = amount.quantize(TWOPLACES)
    if quantized != amount:
        return None, f'{label}最多保留两位小数'
    return quantized, None


def _check_voucher_date(voucher_date: str, fiscal_year: int, period_number: int) -> str | None:
    if len(voucher_date) != 8 or not voucher_date.isdigit():
        return '凭证日期格式应为 YYYYMMDD'
    try:
        day = datetime.date(int(voucher_date[:4]), int(voucher_date[4:6]), int(voucher_date[6:8]))
    except ValueError:
        return '凭证日期不是有效日期'
    if day.year != fiscal_year:
        return '凭证日期的年份须与会计年度一致'
    if 1 <= period_number <= 12 and day.month != period_number:
        return '凭证日期的月份须与会计期间一致'
    if period_number == 13 and day.month != 12:
        return '调整期（13）的凭证日期须落在 12 月'
    return None


def _is_blank_line(line: dict[str, Any]) -> bool:
    if _text(line.get('summary')) or _text(line.get('account_code')):
        return False
    auxiliaries = line.get('auxiliaries') or []
    if isinstance(auxiliaries, list) and any(_text(item.get('auxiliary_value')) for item in auxiliaries if isinstance(item, dict)):
        return False
    debit, debit_err = parse_amount(line.get('debit_amount'), '借方金额')
    credit, credit_err = parse_amount(line.get('credit_amount'), '贷方金额')
    if debit_err or credit_err:
        return False
    return (debit or Decimal('0')) == 0 and (credit or Decimal('0')) == 0


def _sequence_for(auxiliary_item_code: str, used: set[int]) -> int | None:
    code = auxiliary_item_code.strip()
    if code.isdigit():
        number = int(code)
        if 1 <= number <= 30 and number not in used:
            return number
    for number in range(1, 31):
        if number not in used:
            return number
    return None


def validate_manual_voucher(
    payload: dict[str, Any],
    *,
    account_lookup: Callable[[str], dict[str, Any] | None],
    auxiliary_lookup: Callable[[str], list[dict[str, Any]]],
    auxiliary_value_error: Callable[[dict[str, Any], str], str | None],
) -> dict[str, Any]:
    """
    校验手工凭证。查找函数由调用方注入，便于不连数据库做规则测试。

    返回规范化后的 header 与 lines。失败时抛出 VoucherEntryError。
    """
    if not isinstance(payload, dict):
        raise VoucherEntryError('请求体须为 JSON 对象')

    errors: list[str] = []
    account_book_code = _text(payload.get('account_book_code'))
    voucher_number = _text(payload.get('voucher_number'))
    voucher_date = _text(payload.get('voucher_date'))
    voucher_type_code = _text(payload.get('voucher_type_code'))
    summary = _text(payload.get('summary'))
    prepared_by = _text(payload.get('prepared_by')) or None

    fiscal_year = payload.get('fiscal_year')
    period_number = payload.get('period_number')
    try:
        fiscal_year = int(fiscal_year)
    except (TypeError, ValueError):
        fiscal_year = None
    try:
        period_number = int(period_number)
    except (TypeError, ValueError):
        period_number = None

    if not account_book_code:
        errors.append('账套编码不能为空')
    if fiscal_year is None or not (1990 <= fiscal_year <= 2100):
        errors.append('会计年度须为 1990 到 2100 的整数')
    if period_number is None or not (1 <= period_number <= 13):
        errors.append('会计期间须为 1 到 13 的整数，13 表示调整期')
    if not voucher_number:
        errors.append('凭证号不能为空')
    elif len(voucher_number) > 50:
        errors.append('凭证号不能超过 50 个字符')
    elif any(ch in voucher_number for ch in '/\\?#%'):
        errors.append('凭证号不能包含 / \\ ? # %')
    if not voucher_type_code:
        errors.append('凭证类型不能为空')
    elif len(voucher_type_code) > 50:
        errors.append('凭证类型编号不能超过 50 个字符')
    if not summary:
        errors.append('凭证摘要不能为空')
    elif len(summary) > 500:
        errors.append('凭证摘要不能超过 500 个字符')
    if prepared_by and len(prepared_by) > 50:
        errors.append('制单人不能超过 50 个字符')

    if fiscal_year is not None and period_number is not None and voucher_date:
        date_error = _check_voucher_date(voucher_date, fiscal_year, period_number)
        if date_error:
            errors.append(date_error)
    elif not voucher_date:
        errors.append('凭证日期不能为空')

    attachment_count = payload.get('attachment_count')
    if attachment_count in (None, ''):
        attachment_count = None
    else:
        try:
            attachment_count = int(attachment_count)
        except (TypeError, ValueError):
            errors.append('附单据数须为整数')
            attachment_count = None
        else:
            if attachment_count < 0:
                errors.append('附单据数不能为负数')

    raw_lines = payload.get('entries')
    if not isinstance(raw_lines, list) or not raw_lines:
        errors.append('至少录入一条借方分录和一条贷方分录')
        raw_lines = []
    elif len(raw_lines) > MAX_LINES:
        errors.append(f'分录行不能超过 {MAX_LINES} 行')

    if errors:
        message = errors[0] if len(errors) == 1 else '凭证校验未通过'
        raise VoucherEntryError(message, errors)

    normalized_lines: list[dict[str, Any]] = []
    debit_total = Decimal('0.00')
    credit_total = Decimal('0.00')

    for index, line in enumerate(raw_lines, start=1):
        if not isinstance(line, dict):
            errors.append(f'第 {index} 行格式不正确')
            continue
        if _is_blank_line(line):
            continue

        line_summary = _text(line.get('summary')) or summary
        if line_summary and len(line_summary) > 500:
            errors.append(f'第 {index} 行摘要不能超过 500 个字符')
        account_code = _text(line.get('account_code'))
        debit, debit_err = parse_amount(line.get('debit_amount'), f'第 {index} 行借方金额')
        credit, credit_err = parse_amount(line.get('credit_amount'), f'第 {index} 行贷方金额')
        if debit_err:
            errors.append(debit_err)
            debit = Decimal('0.00')
        if credit_err:
            errors.append(credit_err)
            credit = Decimal('0.00')
        debit = debit or Decimal('0.00')
        credit = credit or Decimal('0.00')

        if not account_code:
            errors.append(f'第 {index} 行请选择科目')
            continue
        if len(account_code) > 50:
            errors.append(f'第 {index} 行科目编号不能超过 50 个字符')
            continue

        if debit > 0 and credit > 0:
            errors.append(f'第 {index} 行不能同时填写借方和贷方金额')
        elif debit == 0 and credit == 0:
            errors.append(f'第 {index} 行请填写借方或贷方金额')

        account = account_lookup(account_code)
        if account is None:
            errors.append(f'第 {index} 行科目 {account_code} 在当前账套年度中不存在')
            aux_rows: list[dict[str, Any]] = []
        else:
            if account.get('is_enabled') == 0 or account.get('status') == 0:
                errors.append(f'第 {index} 行科目 {account_code} 已停用')
            if account.get('is_leaf') != 1:
                errors.append(f'第 {index} 行科目 {account_code} 不是末级科目，不能记账')
            aux_rows = [
                row for row in auxiliary_lookup(account_code)
                if row.get('status') in (None, 1)
            ]

        provided = line.get('auxiliaries') or []
        if not isinstance(provided, list):
            errors.append(f'第 {index} 行辅助核算格式不正确')
            provided = []
        provided_by_code: dict[str, str] = {}
        for item in provided:
            if not isinstance(item, dict):
                errors.append(f'第 {index} 行辅助核算格式不正确')
                continue
            code = _text(item.get('auxiliary_item_code'))
            if not code:
                errors.append(f'第 {index} 行辅助核算缺少辅助项编号')
                continue
            provided_by_code[code] = _text(item.get('auxiliary_value'))

        required_codes = {_text(row.get('auxiliary_item_code')) for row in aux_rows}
        unknown = [code for code in provided_by_code if code not in required_codes]
        if unknown:
            errors.append(f'第 {index} 行科目 {account_code} 不存在辅助项：{"、".join(unknown)}')

        used_sequences: set[int] = set()
        auxiliaries: list[dict[str, Any]] = []
        for aux in aux_rows:
            code = _text(aux.get('auxiliary_item_code'))
            name = _text(aux.get('auxiliary_item_name')) or code
            value = provided_by_code.get(code, '')
            if not value:
                errors.append(f'第 {index} 行科目 {account_code} 的辅助核算「{name}」未填写')
                continue
            if len(value) > 50:
                errors.append(f'第 {index} 行辅助核算「{name}」的取值不能超过 50 个字符')
                continue
            value_error = auxiliary_value_error(aux, value)
            if value_error:
                errors.append(f'第 {index} 行{value_error}')
                continue
            sequence = _sequence_for(code, used_sequences)
            if sequence is None:
                errors.append(f'第 {index} 行辅助核算超过 30 项')
                continue
            used_sequences.add(sequence)
            auxiliaries.append({
                'auxiliary_item_sequence': sequence,
                'auxiliary_item_code': code,
                'auxiliary_item_name': name or None,
                'auxiliary_value': value,
            })

        debit_total += debit
        credit_total += credit
        normalized_lines.append({
            'entry_line_number': len(normalized_lines) + 1,
            'account_code': account_code,
            'summary': line_summary or None,
            'debit_amount': debit,
            'credit_amount': credit,
            'auxiliaries': auxiliaries,
        })

    if not normalized_lines:
        errors.append('至少录入一条借方分录和一条贷方分录')
    elif debit_total <= 0 or credit_total <= 0:
        errors.append('凭证须同时有借方金额和贷方金额')
    elif debit_total != credit_total:
        errors.append(f'借贷不平衡：借方合计 {debit_total}，贷方合计 {credit_total}')

    if errors:
        message = errors[0] if len(errors) == 1 else '凭证校验未通过'
        raise VoucherEntryError(message, errors)

    return {
        'account_book_code': account_book_code,
        'fiscal_year': fiscal_year,
        'period_number': period_number,
        'voucher_number': voucher_number,
        'voucher_date': voucher_date,
        'voucher_type_code': voucher_type_code,
        'attachment_count': attachment_count,
        'prepared_by': prepared_by,
        'summary': summary,
        'entries': normalized_lines,
        'debit_total': debit_total,
        'credit_total': credit_total,
    }
