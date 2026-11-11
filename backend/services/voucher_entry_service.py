# -*- coding: utf-8 -*-
"""手工录入记账凭证：按 gl_voucher / gl_voucher_entry / gl_voucher_entry_auxiliary 写入。"""
from __future__ import annotations

from typing import Any, Callable

from Model import (
    Account,
    AccountAuxiliary,
    AccountBookFiscalYear,
    CustomArchiveItem,
    CustomArchiveValue,
    GLVoucher,
    GLVoucherEntry,
    GLVoucherEntryAuxiliary,
    GLVoucherType,
    db,
)
from services.voucher_entry_rules import VoucherEntryError, _text, validate_manual_voucher


def _account_lookup(account_book_code: str, fiscal_year: int) -> Callable[[str], dict[str, Any] | None]:
    cache: dict[str, dict[str, Any] | None] = {}

    def lookup(account_code: str) -> dict[str, Any] | None:
        if account_code not in cache:
            row = Account.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=account_code,
            ).first()
            cache[account_code] = None if row is None else {
                'account_code': row.account_code,
                'account_name': row.account_name,
                'is_leaf': row.is_leaf,
                'is_enabled': row.is_enabled,
                'status': row.status,
            }
        return cache[account_code]

    return lookup


def _auxiliary_lookup(account_book_code: str, fiscal_year: int) -> Callable[[str], list[dict[str, Any]]]:
    cache: dict[str, list[dict[str, Any]]] = {}

    def lookup(account_code: str) -> list[dict[str, Any]]:
        if account_code not in cache:
            rows = AccountAuxiliary.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=account_code,
            ).order_by(AccountAuxiliary.auxiliary_item_code.asc()).all()
            cache[account_code] = [row.to_dict() for row in rows]
        return cache[account_code]

    return lookup


def _resolve_archive_item(account_book_code: str, fiscal_year: int, auxiliary: dict[str, Any]):
    candidates: list[str] = []
    for key in (_text(auxiliary.get('corresponding_archive')), _text(auxiliary.get('auxiliary_item_name'))):
        if key and key not in candidates:
            candidates.append(key)
    for key in candidates:
        item = CustomArchiveItem.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=key,
            status=1,
        ).first()
        if item:
            return item
        item = CustomArchiveItem.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_name=key,
            status=1,
        ).first()
        if item:
            return item
    return None


def _auxiliary_value_error(account_book_code: str, fiscal_year: int) -> Callable[[dict[str, Any], str], str | None]:
    def check(auxiliary: dict[str, Any], value: str) -> str | None:
        item = _resolve_archive_item(account_book_code, fiscal_year, auxiliary)
        if item is None:
            return None
        found = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=item.archive_item_code,
            archive_value_code=value,
            status=1,
        ).first()
        if found:
            return None
        name = _text(auxiliary.get('auxiliary_item_name')) or _text(auxiliary.get('auxiliary_item_code'))
        return f'辅助核算「{name}」的取值「{value}」不在档案「{item.archive_item_name}」中'

    return check


def _ensure_book_year(account_book_code: str, fiscal_year: int) -> None:
    row = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
    ).first()
    if row is None:
        raise VoucherEntryError(
            f'未找到账套年度: {account_book_code}/{fiscal_year}',
            status=404,
        )


def suggest_next_voucher_number(
    account_book_code: str,
    fiscal_year: int,
    period_number: int,
    voucher_type_code: str,
) -> str:
    """按「类型-期间-序号」给出下一张凭证号，例如 JZ-01-0002。"""
    account_book_code = _text(account_book_code)
    voucher_type_code = _text(voucher_type_code)
    if not account_book_code:
        raise VoucherEntryError('账套编码不能为空')
    if not (1990 <= fiscal_year <= 2100):
        raise VoucherEntryError('会计年度须为 1990 到 2100 的整数')
    if not (1 <= period_number <= 13):
        raise VoucherEntryError('会计期间须为 1 到 13 的整数')
    if not voucher_type_code:
        raise VoucherEntryError('凭证类型不能为空')

    _ensure_book_year(account_book_code, fiscal_year)
    voucher_type = GLVoucherType.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        voucher_type_code=voucher_type_code,
    ).first()
    if voucher_type is None:
        raise VoucherEntryError(
            f'未找到凭证类型: {voucher_type_code}',
            status=404,
        )

    prefix = f'{voucher_type_code}-{period_number:02d}-'
    rows = GLVoucher.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        period_number=period_number,
        voucher_type_code=voucher_type_code,
    ).all()
    max_seq = 0
    for row in rows:
        number = row.voucher_number or ''
        if not number.startswith(prefix):
            continue
        tail = number[len(prefix):]
        if tail.isdigit():
            max_seq = max(max_seq, int(tail))
    return f'{prefix}{max_seq + 1:04d}'


def create_manual_voucher(payload: dict[str, Any], default_prepared_by: str | None = None) -> dict[str, Any]:
    """校验并写入一张未记账凭证。不改科目余额，余额仍由「数据记账」重算。"""
    data = dict(payload or {})
    if not _text(data.get('prepared_by')) and default_prepared_by:
        data['prepared_by'] = default_prepared_by

    account_book_code = _text(data.get('account_book_code'))
    try:
        fiscal_year = int(data.get('fiscal_year'))
    except (TypeError, ValueError):
        fiscal_year = None
    if account_book_code and fiscal_year is not None:
        _ensure_book_year(account_book_code, fiscal_year)

    normalized = validate_manual_voucher(
        data,
        account_lookup=_account_lookup(account_book_code, fiscal_year or 0),
        auxiliary_lookup=_auxiliary_lookup(account_book_code, fiscal_year or 0),
        auxiliary_value_error=_auxiliary_value_error(account_book_code, fiscal_year or 0),
    )

    voucher_type = GLVoucherType.query.filter_by(
        account_book_code=normalized['account_book_code'],
        fiscal_year=normalized['fiscal_year'],
        voucher_type_code=normalized['voucher_type_code'],
    ).first()
    if voucher_type is None:
        raise VoucherEntryError(
            f"未找到凭证类型: {normalized['voucher_type_code']}",
            status=404,
        )

    existing = GLVoucher.query.filter_by(
        account_book_code=normalized['account_book_code'],
        fiscal_year=normalized['fiscal_year'],
        period_number=normalized['period_number'],
        voucher_number=normalized['voucher_number'],
    ).first()
    if existing is not None:
        raise VoucherEntryError(
            f"凭证已存在: {normalized['voucher_number']}",
            status=409,
        )

    voucher = GLVoucher(
        account_book_code=normalized['account_book_code'],
        fiscal_year=normalized['fiscal_year'],
        period_number=normalized['period_number'],
        voucher_number=normalized['voucher_number'],
        voucher_date=normalized['voucher_date'],
        voucher_type_code=normalized['voucher_type_code'],
        attachment_count=normalized['attachment_count'],
        prepared_by=normalized['prepared_by'],
        reviewed_by=None,
        posted_by=None,
        voucher_status='未记账',
        summary=normalized['summary'],
    )
    db.session.add(voucher)

    for line in normalized['entries']:
        db.session.add(GLVoucherEntry(
            account_book_code=normalized['account_book_code'],
            fiscal_year=normalized['fiscal_year'],
            period_number=normalized['period_number'],
            voucher_number=normalized['voucher_number'],
            entry_line_number=line['entry_line_number'],
            account_code=line['account_code'],
            summary=line['summary'],
            debit_amount=line['debit_amount'],
            credit_amount=line['credit_amount'],
        ))
        for aux in line['auxiliaries']:
            db.session.add(GLVoucherEntryAuxiliary(
                account_book_code=normalized['account_book_code'],
                fiscal_year=normalized['fiscal_year'],
                period_number=normalized['period_number'],
                voucher_number=normalized['voucher_number'],
                entry_line_number=line['entry_line_number'],
                auxiliary_item_sequence=aux['auxiliary_item_sequence'],
                account_code=line['account_code'],
                auxiliary_value=aux['auxiliary_value'],
                auxiliary_item_name=aux['auxiliary_item_name'],
            ))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    result = voucher.to_dict()
    result['debit_amount'] = float(normalized['debit_total'])
    result['credit_amount'] = float(normalized['credit_total'])
    result['entry_count'] = len(normalized['entries'])
    return result
