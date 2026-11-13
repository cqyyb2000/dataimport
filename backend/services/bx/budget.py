# -*- coding: utf-8 -*-
"""预算的建立、改金额和删除，以及已计入、待支出合计。"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func

from Model import BxBudget, BxClaim, BxDepartment, BxProject, db

from .archive import is_leaf_department, is_leaf_project
from .common import as_money, clean_text, parse_money, require_year
from .errors import BxError, BxOverspend


def _budget(fiscal_year: int, dept_code: str, project_code: str) -> BxBudget:
    row = BxBudget.query.filter_by(
        fiscal_year=fiscal_year,
        dept_code=dept_code,
        project_code=project_code,
    ).first()
    if row is None:
        raise BxError('预算不存在')
    return row


def _sum_claims(fiscal_year: int, dept_code: str, project_code: str, status: str) -> Decimal:
    total = db.session.query(func.coalesce(func.sum(BxClaim.amount), 0)).filter_by(
        fiscal_year=fiscal_year,
        dept_code=dept_code,
        project_code=project_code,
        status=status,
    ).scalar()
    return as_money(total)


def confirmed_amount(fiscal_year: int, dept_code: str, project_code: str) -> Decimal:
    return _sum_claims(fiscal_year, dept_code, project_code, BxClaim.STATUS_CONFIRMED)


def pending_amount(fiscal_year: int, dept_code: str, project_code: str) -> Decimal:
    return _sum_claims(fiscal_year, dept_code, project_code, BxClaim.STATUS_PENDING)


def budget_usage(fiscal_year, dept_code, project_code) -> dict:
    fiscal_year = require_year(fiscal_year)
    dept_code = clean_text(dept_code, '部门代码', 50)
    project_code = clean_text(project_code, '项目代码', 50)
    row = _budget(fiscal_year, dept_code, project_code)
    confirmed = confirmed_amount(fiscal_year, dept_code, project_code)
    pending = pending_amount(fiscal_year, dept_code, project_code)
    amount = as_money(row.amount)
    return {
        'fiscal_year': fiscal_year,
        'dept_code': dept_code,
        'project_code': project_code,
        'budget_amount': amount,
        'confirmed_amount': confirmed,
        'pending_amount': pending,
        'balance': (amount - confirmed).quantize(Decimal('0.01')),
    }


def assert_can_apply(fiscal_year, dept_code, project_code, this_amount: Decimal, *, allow_overspend: bool, action: str):
    """已计入加本次金额超过预算时，未确认则中止。待支出不参与比较。"""
    row = _budget(fiscal_year, dept_code, project_code)
    confirmed = confirmed_amount(fiscal_year, dept_code, project_code)
    budget_amount = as_money(row.amount)
    if confirmed + this_amount > budget_amount and not allow_overspend:
        raise BxOverspend(
            f'{action}后该预算余额将为负数',
            budget_amount,
            confirmed,
            this_amount,
        )


def _require_leaf(fiscal_year: int, dept_code: str, project_code: str) -> None:
    if BxDepartment.query.filter_by(fiscal_year=fiscal_year, dept_code=dept_code).first() is None:
        raise BxError('部门不存在')
    if BxProject.query.filter_by(fiscal_year=fiscal_year, project_code=project_code).first() is None:
        raise BxError('项目不存在')
    if not is_leaf_department(fiscal_year, dept_code) or not is_leaf_project(fiscal_year, project_code):
        raise BxError('只能选择最明细级的部门和项目')


def create_budget(fiscal_year, dept_code, project_code, amount):
    fiscal_year = require_year(fiscal_year)
    dept_code = clean_text(dept_code, '部门代码', 50)
    project_code = clean_text(project_code, '项目代码', 50)
    money = parse_money(amount, '预算金额', allow_zero=True)
    _require_leaf(fiscal_year, dept_code, project_code)
    exists = BxBudget.query.filter_by(
        fiscal_year=fiscal_year,
        dept_code=dept_code,
        project_code=project_code,
    ).first()
    if exists is not None:
        raise BxError('该部门项目的预算已存在')
    row = BxBudget(
        fiscal_year=fiscal_year,
        dept_code=dept_code,
        project_code=project_code,
        amount=money,
    )
    db.session.add(row)
    db.session.commit()
    return row


def update_budget_amount(fiscal_year, dept_code, project_code, amount):
    fiscal_year = require_year(fiscal_year)
    dept_code = clean_text(dept_code, '部门代码', 50)
    project_code = clean_text(project_code, '项目代码', 50)
    money = parse_money(amount, '预算金额', allow_zero=True)
    row = _budget(fiscal_year, dept_code, project_code)
    row.amount = money
    db.session.commit()
    return row


def delete_budget(fiscal_year, dept_code, project_code):
    fiscal_year = require_year(fiscal_year)
    dept_code = clean_text(dept_code, '部门代码', 50)
    project_code = clean_text(project_code, '项目代码', 50)
    row = _budget(fiscal_year, dept_code, project_code)
    claim_count = BxClaim.query.filter_by(
        fiscal_year=fiscal_year,
        dept_code=dept_code,
        project_code=project_code,
    ).count()
    if claim_count:
        raise BxError('该预算已有报销单，不能删除')
    db.session.delete(row)
    db.session.commit()
