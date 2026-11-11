# -*- coding: utf-8 -*-
"""手工凭证录入的会计校验，不连接数据库。"""
from decimal import Decimal

import pytest

from services.voucher_entry_rules import VoucherEntryError, parse_amount, validate_manual_voucher


ACCOUNTS = {
    '1001': {'account_code': '1001', 'is_leaf': 1, 'is_enabled': 1, 'status': 1, 'account_name': '库存现金'},
    '1002': {'account_code': '1002', 'is_leaf': 1, 'is_enabled': 1, 'status': 1, 'account_name': '银行存款'},
    '5001': {'account_code': '5001', 'is_leaf': 0, 'is_enabled': 1, 'status': 1, 'account_name': '业务活动费用'},
    '2201': {'account_code': '2201', 'is_leaf': 1, 'is_enabled': 0, 'status': 1, 'account_name': '应付账款'},
}

AUX = {
    '1002': [{
        'auxiliary_item_code': '1',
        'auxiliary_item_name': '部门',
        'corresponding_archive': 'DEPT',
        'status': 1,
    }],
}


def _lookups(archive_ok=True):
    def account_lookup(code):
        return ACCOUNTS.get(code)

    def auxiliary_lookup(code):
        return list(AUX.get(code, []))

    def auxiliary_value_error(aux, value):
        if aux.get('corresponding_archive') and not archive_ok:
            return f'辅助核算「{aux["auxiliary_item_name"]}」的取值「{value}」不在档案中'
        return None

    return account_lookup, auxiliary_lookup, auxiliary_value_error


def _payload(**overrides):
    data = {
        'account_book_code': 'ZT01',
        'fiscal_year': 2024,
        'period_number': 1,
        'voucher_number': 'JZ-01-0001',
        'voucher_date': '20240115',
        'voucher_type_code': 'JZ',
        'summary': '收到拨款',
        'entries': [
            {'account_code': '1001', 'debit_amount': '100.00', 'credit_amount': 0},
            {
                'account_code': '1002',
                'debit_amount': 0,
                'credit_amount': '100.00',
                'auxiliaries': [{'auxiliary_item_code': '1', 'auxiliary_value': '001'}],
            },
        ],
    }
    data.update(overrides)
    return data


def test_parse_amount_rejects_extra_decimals_and_negatives():
    amount, error = parse_amount('12.30', '借方金额')
    assert error is None
    assert amount == Decimal('12.30')
    assert parse_amount('12.301', '借方金额')[1] == '借方金额最多保留两位小数'
    assert parse_amount('-1', '借方金额')[1] == '借方金额不能为负数'
    assert parse_amount(None, '借方金额')[0] == Decimal('0.00')


def test_balanced_voucher_is_accepted_and_copies_summary():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    result = validate_manual_voucher(
        _payload(),
        account_lookup=account_lookup,
        auxiliary_lookup=auxiliary_lookup,
        auxiliary_value_error=auxiliary_value_error,
    )
    assert result['debit_total'] == result['credit_total'] == Decimal('100.00')
    assert result['entries'][0]['summary'] == '收到拨款'
    assert result['entries'][1]['auxiliaries'][0]['auxiliary_item_sequence'] == 1
    assert result['entries'][0]['entry_line_number'] == 1


def test_unbalanced_voucher_is_rejected():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload()
    payload['entries'][1]['credit_amount'] = '80.00'
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert '借贷不平衡' in exc.value.message
    assert exc.value.status == 400


def test_line_cannot_have_both_debit_and_credit():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload()
    payload['entries'][0]['credit_amount'] = '1.00'
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('不能同时填写借方和贷方' in item for item in exc.value.errors)


def test_auxiliary_is_required_when_account_has_it():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload()
    payload['entries'][1]['auxiliaries'] = []
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('辅助核算' in item and '未填写' in item for item in exc.value.errors)


def test_archive_value_must_exist_when_linked():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups(archive_ok=False)
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            _payload(),
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('不在档案中' in item for item in exc.value.errors)


def test_only_leaf_enabled_accounts_can_be_posted():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload()
    payload['entries'][0]['account_code'] = '5001'
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('不是末级科目' in item for item in exc.value.errors)

    payload = _payload()
    payload['entries'][0]['account_code'] = '2201'
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('已停用' in item for item in exc.value.errors)


def test_date_must_match_year_and_period():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload(voucher_date='20240215')
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('月份须与会计期间一致' in item for item in exc.value.errors)


def test_all_blank_lines_are_rejected():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload(entries=[{}, {'summary': ''}])
    with pytest.raises(VoucherEntryError) as exc:
        validate_manual_voucher(
            payload,
            account_lookup=account_lookup,
            auxiliary_lookup=auxiliary_lookup,
            auxiliary_value_error=auxiliary_value_error,
        )
    assert any('至少录入' in item for item in exc.value.errors)


def test_blank_lines_are_ignored():
    account_lookup, auxiliary_lookup, auxiliary_value_error = _lookups()
    payload = _payload()
    payload['entries'].append({})
    result = validate_manual_voucher(
        payload,
        account_lookup=account_lookup,
        auxiliary_lookup=auxiliary_lookup,
        auxiliary_value_error=auxiliary_value_error,
    )
    assert len(result['entries']) == 2
