# -*- coding: utf-8 -*-
"""把来源年度的部门、项目和预算复制到目标年度。报销单不复制。"""
from __future__ import annotations

from Model import BxBudget, BxClaim, BxDepartment, BxProject, db

from .common import require_year
from .errors import BxError, BxNeedConfirm


def _count(model, fiscal_year: int) -> int:
    return model.query.filter_by(fiscal_year=fiscal_year).count()


def _delete_nodes(model, fiscal_year: int) -> None:
    rows = model.query.filter_by(fiscal_year=fiscal_year).order_by(model.level_no.desc()).all()
    for row in rows:
        db.session.delete(row)
    db.session.flush()


def copy_year(source_year, target_year, confirmed=False):
    source_year = require_year(source_year)
    target_year = require_year(target_year)
    if source_year == target_year:
        raise BxError('来源年度和目标年度不能相同')
    if _count(BxDepartment, source_year) + _count(BxProject, source_year) + _count(BxBudget, source_year) == 0:
        raise BxError('来源年度没有可复制的部门、项目和预算')
    if _count(BxClaim, target_year):
        raise BxError('目标年度还有报销单，请先处理后再复制')

    department_count = _count(BxDepartment, target_year)
    project_count = _count(BxProject, target_year)
    budget_count = _count(BxBudget, target_year)
    if (department_count or project_count or budget_count) and not confirmed:
        raise BxNeedConfirm(
            '目标年度已有部门、项目或预算，继续将先删除后再复制',
            source_year,
            target_year,
            department_count,
            project_count,
            budget_count,
        )

    try:
        if department_count or project_count or budget_count:
            BxBudget.query.filter_by(fiscal_year=target_year).delete(synchronize_session=False)
            db.session.flush()
            _delete_nodes(BxProject, target_year)
            _delete_nodes(BxDepartment, target_year)
        departments = BxDepartment.query.filter_by(fiscal_year=source_year).order_by(BxDepartment.level_no.asc()).all()
        for row in departments:
            db.session.add(BxDepartment(
                fiscal_year=target_year,
                dept_code=row.dept_code,
                dept_name=row.dept_name,
                parent_dept_code=row.parent_dept_code,
                level_no=row.level_no,
            ))
        projects = BxProject.query.filter_by(fiscal_year=source_year).order_by(BxProject.level_no.asc()).all()
        for row in projects:
            db.session.add(BxProject(
                fiscal_year=target_year,
                project_code=row.project_code,
                project_name=row.project_name,
                parent_project_code=row.parent_project_code,
                level_no=row.level_no,
            ))
        db.session.flush()
        budgets = BxBudget.query.filter_by(fiscal_year=source_year).all()
        for row in budgets:
            db.session.add(BxBudget(
                fiscal_year=target_year,
                dept_code=row.dept_code,
                project_code=row.project_code,
                amount=row.amount,
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {
        'source_year': source_year,
        'target_year': target_year,
        'department_count': len(departments),
        'project_count': len(projects),
        'budget_count': len(budgets),
    }
