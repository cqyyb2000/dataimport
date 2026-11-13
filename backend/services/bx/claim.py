# -*- coding: utf-8 -*-
"""报销单保存、删除、确认计入和取消确认，以及单据号。"""
from __future__ import annotations

from Model import BxClaim, BxDocSeq, db

from .budget import assert_can_apply
from .common import clean_text, parse_date, parse_money, require_year
from .errors import BxError


def _allocate_doc_no(fiscal_year: int, month: int) -> str:
    query = BxDocSeq.query.filter_by(fiscal_year=fiscal_year, fiscal_month=month)
    if db.engine.dialect.name != 'sqlite':
        query = query.with_for_update()
    row = query.first()
    if row is None:
        row = BxDocSeq(fiscal_year=fiscal_year, fiscal_month=month, max_seq=1)
        db.session.add(row)
        seq = 1
    else:
        if row.max_seq >= 9999:
            raise BxError('当月单据号已超过 9999')
        row.max_seq += 1
        seq = row.max_seq
    db.session.flush()
    return f'{fiscal_year:04d}{month:02d}{seq:04d}'


def _get_claim(claim_id: int) -> BxClaim:
    if isinstance(claim_id, bool) or not isinstance(claim_id, int):
        raise BxError('报销单不存在')
    row = db.session.get(BxClaim, claim_id)
    if row is None:
        raise BxError('报销单不存在')
    return row


def save_claim(fiscal_year, expense_date, dept_code, project_code, claimant, summary, amount,
               claim_id=None, allow_overspend=False):
    """会计保存。成功后仍是待支出，不改变余额。超支且未确认时不写库。"""
    fiscal_year = require_year(fiscal_year)
    expense_date = parse_date(expense_date)
    if expense_date.year != fiscal_year:
        raise BxError('报销时间的年份必须等于所选年度')
    dept_code = clean_text(dept_code, '部门代码', 50)
    project_code = clean_text(project_code, '项目代码', 50)
    claimant = clean_text(claimant, '报销人', 100)
    summary = clean_text(summary, '摘要', 500)
    money = parse_money(amount, '报销金额', allow_zero=False)
    row = None
    if claim_id is not None:
        row = _get_claim(claim_id)
        if row.status != BxClaim.STATUS_PENDING:
            raise BxError('已计入的报销单不能修改')
        if row.fiscal_year != fiscal_year:
            raise BxError('不能修改报销单所属年度')
    try:
        assert_can_apply(
            fiscal_year, dept_code, project_code, money,
            allow_overspend=allow_overspend, action='保存',
        )
        if row is None:
            doc_no = _allocate_doc_no(fiscal_year, expense_date.month)
            row = BxClaim(
                doc_no=doc_no,
                fiscal_year=fiscal_year,
                expense_date=expense_date,
                dept_code=dept_code,
                project_code=project_code,
                claimant=claimant,
                summary=summary,
                amount=money,
                status=BxClaim.STATUS_PENDING,
            )
            db.session.add(row)
        else:
            if expense_date.month != row.expense_date.month:
                row.doc_no = _allocate_doc_no(fiscal_year, expense_date.month)
            row.expense_date = expense_date
            row.dept_code = dept_code
            row.project_code = project_code
            row.claimant = claimant
            row.summary = summary
            row.amount = money
        db.session.commit()
        return row
    except Exception:
        db.session.rollback()
        raise


def delete_claim(claim_id):
    row = _get_claim(claim_id)
    if row.status != BxClaim.STATUS_PENDING:
        raise BxError('已计入的报销单不能删除')
    db.session.delete(row)
    db.session.commit()


def confirm_claim(claim_id, allow_overspend=False):
    """出纳确认计入。未超支时直接计入；超支且未确认时不改变状态。"""
    try:
        row = _get_claim(claim_id)
        if row.status != BxClaim.STATUS_PENDING:
            raise BxError('该报销单已经计入')
        assert_can_apply(
            row.fiscal_year, row.dept_code, row.project_code, row.amount,
            allow_overspend=allow_overspend, action='确认',
        )
        row.status = BxClaim.STATUS_CONFIRMED
        db.session.commit()
        return row
    except Exception:
        db.session.rollback()
        raise


def cancel_confirm(claim_id):
    try:
        row = _get_claim(claim_id)
        if row.status != BxClaim.STATUS_CONFIRMED:
            raise BxError('该报销单尚未计入')
        row.status = BxClaim.STATUS_PENDING
        db.session.commit()
        return row
    except Exception:
        db.session.rollback()
        raise
