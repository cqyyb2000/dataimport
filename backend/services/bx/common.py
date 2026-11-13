# -*- coding: utf-8 -*-
"""报销台账共用的年度、文本和金额整理。"""
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .errors import BxError

TWOPLACES = Decimal('0.01')


def clean_text(value: Any, label: str, max_len: int, *, required: bool = True) -> str:
    if value is None:
        text = ''
    else:
        text = str(value).strip()
    if required and not text:
        raise BxError(f'{label}不能为空')
    if len(text) > max_len:
        raise BxError(f'{label}不能超过{max_len}个字符')
    return text


def require_year(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1000 or value > 9999:
        raise BxError('年度须为4位整数')
    return value


def parse_money(value: Any, label: str, *, allow_zero: bool) -> Decimal:
    if isinstance(value, bool) or value is None or (isinstance(value, str) and not value.strip()):
        raise BxError(f'{label}不是有效金额')
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError):
        raise BxError(f'{label}不是有效金额') from None
    if amount.as_tuple().exponent < -2:
        raise BxError(f'{label}最多保留两位小数')
    amount = amount.quantize(TWOPLACES)
    if allow_zero:
        if amount < 0:
            raise BxError(f'{label}不能小于 0')
    elif amount <= 0:
        raise BxError(f'{label}必须大于 0')
    return amount


def parse_date(value: Any) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = clean_text(value, '报销时间', 10)
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise BxError('报销时间须为日期') from None


def as_money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(TWOPLACES)
