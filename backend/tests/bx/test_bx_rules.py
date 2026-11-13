# -*- coding: utf-8 -*-
"""报销台账服务规则。"""
import datetime
from decimal import Decimal

import pytest

from Model import BxClaim, BxDepartment, BxDocSeq, BxProject, db
from services.bx import (
    BxError,
    BxNeedConfirm,
    BxOverspend,
    budget_usage,
    cancel_confirm,
    confirm_claim,
    copy_year,
    create_budget,
    create_department,
    create_project,
    delete_budget,
    delete_claim,
    delete_department,
    move_department,
    save_claim,
    update_budget_amount,
    update_department_name,
)


def _leaf_pair(year=2026):
    create_department(year, 'D', '宣传部')
    create_department(year, 'D1', '新闻科', 'D')
    create_project(year, 'P', '品牌')
    create_project(year, 'P1', '活动', 'P')
    create_budget(year, 'D1', 'P1', '1000.00')


def test_department_tree_levels_and_move(db_ctx):
    root = create_department(2026, 'D', '宣传部')
    child = create_department(2026, 'D1', '新闻科', 'D')
    grand = create_department(2026, 'D2', '外宣', 'D1')
    assert (root.level_no, child.level_no, grand.level_no) == (1, 2, 3)

    moved = move_department(2026, 'D1', None)
    grand = db.session.get(BxDepartment, (2026, 'D2'))
    assert moved.level_no == 1
    assert grand.level_no == 2
    with pytest.raises(BxError, match='自己的下级'):
        move_department(2026, 'D1', 'D2')


def test_budget_only_on_leaf_and_blocks_new_child(db_ctx):
    create_department(2026, 'D', '宣传部')
    create_department(2026, 'D1', '新闻科', 'D')
    create_project(2026, 'P1', '活动')
    with pytest.raises(BxError, match='最明细'):
        create_budget(2026, 'D', 'P1', 100)
    create_budget(2026, 'D1', 'P1', 100)
    with pytest.raises(BxError, match='不能再增加下级'):
        create_department(2026, 'D3', '小组', 'D1')
    delete_budget(2026, 'D1', 'P1')
    create_department(2026, 'D3', '小组', 'D1')


def test_name_lock_follows_claims_not_budget(db_ctx):
    _leaf_pair()
    update_department_name(2026, 'D1', '新闻宣传科')
    claim = save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '10')
    with pytest.raises(BxError, match='不能修改名称'):
        update_department_name(2026, 'D1', '再改')
    delete_claim(claim.id)
    renamed = update_department_name(2026, 'D1', '再改')
    assert renamed.dept_name == '再改'


def test_cannot_delete_department_in_use_or_with_child(db_ctx):
    _leaf_pair()
    with pytest.raises(BxError, match='还有下级'):
        delete_department(2026, 'D')
    with pytest.raises(BxError, match='不能删除'):
        delete_department(2026, 'D1')


def test_budget_amount_can_drop_below_confirmed(db_ctx):
    _leaf_pair()
    claim = save_claim(2026, datetime.date(2026, 5, 2), 'D1', 'P1', '张三', '差旅', '80')
    confirm_claim(claim.id)
    update_budget_amount(2026, 'D1', 'P1', 50)
    usage = budget_usage(2026, 'D1', 'P1')
    assert usage['balance'] == Decimal('-30.00')
    with pytest.raises(BxError, match='不能删除'):
        delete_budget(2026, 'D1', 'P1')


def test_save_overspend_does_not_write_or_consume_number(db_ctx):
    _leaf_pair()
    with pytest.raises(BxOverspend):
        save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '1000.01')
    assert BxClaim.query.count() == 0
    assert BxDocSeq.query.count() == 0
    saved = save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '1000.01', allow_overspend=True)
    assert saved.status == '待支出'
    assert saved.doc_no == '2026050001'
    assert budget_usage(2026, 'D1', 'P1')['balance'] == Decimal('1000.00')


def test_pending_does_not_affect_confirm_check(db_ctx):
    _leaf_pair()
    first = save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '800')
    second = save_claim(2026, '2026-05-03', 'D1', 'P1', '李四', '会议', '300')
    confirm_claim(first.id)
    db.session.refresh(second)
    with pytest.raises(BxOverspend):
        confirm_claim(second.id)
    db.session.refresh(second)
    assert second.status == '待支出'
    confirmed = confirm_claim(second.id, allow_overspend=True)
    assert confirmed.status == '已计入'
    assert budget_usage(2026, 'D1', 'P1')['balance'] == Decimal('-100.00')


def test_month_change_replaces_doc_no_without_reusing_old(db_ctx):
    _leaf_pair()
    claim = save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '10')
    assert claim.doc_no == '2026050001'
    same_month = save_claim(
        2026, '2026-05-20', 'D1', 'P1', '张三', '差旅改日', '10', claim_id=claim.id,
    )
    assert same_month.doc_no == '2026050001'
    moved = save_claim(
        2026, '2026-06-01', 'D1', 'P1', '张三', '改到六月', '10', claim_id=claim.id,
    )
    assert moved.doc_no == '2026060001'
    assert BxClaim.query.filter_by(doc_no='2026050001').count() == 0
    may = db.session.get(BxDocSeq, (2026, 5))
    assert may.max_seq == 1
    delete_claim(moved.id)
    again = save_claim(2026, '2026-06-02', 'D1', 'P1', '张三', '新单', '10')
    assert again.doc_no == '2026060002'


def test_confirmed_claim_cannot_be_edited_until_cancelled(db_ctx):
    _leaf_pair()
    claim = save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '10')
    confirm_claim(claim.id)
    with pytest.raises(BxError, match='不能修改'):
        save_claim(2026, '2026-05-03', 'D1', 'P1', '张三', '改', '10', claim_id=claim.id)
    with pytest.raises(BxError, match='不能删除'):
        delete_claim(claim.id)
    cancel_confirm(claim.id)
    updated = save_claim(2026, '2026-05-03', 'D1', 'P1', '王五', '改后', '12', claim_id=claim.id)
    assert updated.status == '待支出'
    assert updated.claimant == '王五'


def test_doc_seq_stops_at_9999(db_ctx):
    _leaf_pair()
    db.session.add(BxDocSeq(fiscal_year=2026, fiscal_month=5, max_seq=9999))
    db.session.commit()
    with pytest.raises(BxError, match='9999'):
        save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '10')
    assert BxClaim.query.count() == 0


def test_copy_year_requires_confirm_and_skips_claims(db_ctx):
    _leaf_pair()
    save_claim(2026, '2026-05-02', 'D1', 'P1', '张三', '差旅', '10')
    create_department(2027, 'X', '旧部门')
    with pytest.raises(BxNeedConfirm) as warned:
        copy_year(2026, 2027)
    assert warned.value.department_count == 1
    assert BxDepartment.query.filter_by(fiscal_year=2027, dept_code='X').count() == 1

    copied = copy_year(2026, 2027, confirmed=True)
    assert copied['budget_count'] == 1
    assert BxDepartment.query.filter_by(fiscal_year=2027, dept_code='X').count() == 0
    assert BxDepartment.query.filter_by(fiscal_year=2027, dept_code='D1').one().level_no == 2
    assert BxProject.query.filter_by(fiscal_year=2027, project_code='P1').one().parent_project_code == 'P'
    assert BxClaim.query.filter_by(fiscal_year=2027).count() == 0
    assert BxClaim.query.filter_by(fiscal_year=2026).count() == 1


def test_copy_refuses_when_target_has_claims(db_ctx):
    _leaf_pair()
    copy_year(2026, 2027)
    claim = save_claim(2027, '2027-01-08', 'D1', 'P1', '张三', '已有', '5')
    assert claim.doc_no == '2027010001'
    with pytest.raises(BxError, match='还有报销单'):
        copy_year(2026, 2027, confirmed=True)
    assert BxClaim.query.filter_by(fiscal_year=2027).count() == 1


def test_expense_date_must_stay_in_selected_year(db_ctx):
    _leaf_pair()
    with pytest.raises(BxError, match='年份'):
        save_claim(2026, '2025-12-31', 'D1', 'P1', '张三', '跨年', '10')
    with pytest.raises(BxError, match='最明细'):
        create_budget(2026, 'D', 'P', 1)
