# -*- coding: utf-8 -*-
"""部门和项目档案：多级、改名、调整上级、删除。"""
from __future__ import annotations

from dataclasses import dataclass

from Model import BxBudget, BxClaim, BxDepartment, BxProject, db

from .common import clean_text, require_year
from .errors import BxError


@dataclass(frozen=True)
class _Archive:
    model: type
    code_attr: str
    name_attr: str
    parent_attr: str
    label: str
    budget_attr: str
    claim_attr: str


_DEPARTMENT = _Archive(
    BxDepartment, 'dept_code', 'dept_name', 'parent_dept_code', '部门', 'dept_code', 'dept_code',
)
_PROJECT = _Archive(
    BxProject, 'project_code', 'project_name', 'parent_project_code', '项目', 'project_code', 'project_code',
)


def _blank_parent(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _get(_kind: _Archive, fiscal_year: int, code: str):
    row = _kind.model.query.filter_by(fiscal_year=fiscal_year, **{_kind.code_attr: code}).first()
    if row is None:
        raise BxError(f'{_kind.label}不存在')
    return row


def _children(_kind: _Archive, fiscal_year: int, code: str):
    return _kind.model.query.filter_by(fiscal_year=fiscal_year, **{_kind.parent_attr: code}).all()


def _has_budget(kind: _Archive, fiscal_year: int, code: str) -> bool:
    return BxBudget.query.filter_by(fiscal_year=fiscal_year, **{kind.budget_attr: code}).count() > 0


def _has_claim(kind: _Archive, fiscal_year: int, code: str) -> bool:
    return BxClaim.query.filter_by(fiscal_year=fiscal_year, **{kind.claim_attr: code}).count() > 0


def _assert_can_gain_child(kind: _Archive, fiscal_year: int, code: str) -> None:
    if _has_budget(kind, fiscal_year, code) or _has_claim(kind, fiscal_year, code):
        raise BxError(f'该{_kind_label(kind)}已有预算或报销单，不能再增加下级')


def _kind_label(kind: _Archive) -> str:
    return kind.label


def _ancestors(kind: _Archive, fiscal_year: int, code: str) -> set[str]:
    seen: set[str] = set()
    current = code
    while current:
        if current in seen:
            raise BxError(f'{kind.label}上级关系出现循环')
        seen.add(current)
        row = kind.model.query.filter_by(fiscal_year=fiscal_year, **{kind.code_attr: current}).first()
        if row is None:
            break
        current = getattr(row, kind.parent_attr)
    return seen


def _relevel(kind: _Archive, fiscal_year: int, code: str, level: int) -> None:
    row = _get(kind, fiscal_year, code)
    row.level_no = level
    for child in _children(kind, fiscal_year, code):
        _relevel(kind, fiscal_year, getattr(child, kind.code_attr), level + 1)


def _create(kind: _Archive, fiscal_year, code, name, parent_code):
    fiscal_year = require_year(fiscal_year)
    code = clean_text(code, f'{kind.label}代码', 50)
    name = clean_text(name, f'{kind.label}名称', 200)
    parent_code = _blank_parent(parent_code)
    if parent_code == code:
        raise BxError(f'{kind.label}的上级不能是自己')
    exists = kind.model.query.filter_by(fiscal_year=fiscal_year, **{kind.code_attr: code}).first()
    if exists is not None:
        raise BxError(f'{kind.label}代码已存在')
    if parent_code is None:
        level = 1
    else:
        parent_code = clean_text(parent_code, f'上级{kind.label}代码', 50)
        parent = _get(kind, fiscal_year, parent_code)
        _assert_can_gain_child(kind, fiscal_year, parent_code)
        level = parent.level_no + 1
    row = kind.model(**{
        'fiscal_year': fiscal_year,
        kind.code_attr: code,
        kind.name_attr: name,
        kind.parent_attr: parent_code,
        'level_no': level,
    })
    db.session.add(row)
    db.session.commit()
    return row


def _update_name(kind: _Archive, fiscal_year, code, name):
    fiscal_year = require_year(fiscal_year)
    code = clean_text(code, f'{kind.label}代码', 50)
    name = clean_text(name, f'{kind.label}名称', 200)
    row = _get(kind, fiscal_year, code)
    if _has_claim(kind, fiscal_year, code):
        raise BxError(f'该{kind.label}已被报销单使用，不能修改名称')
    setattr(row, kind.name_attr, name)
    db.session.commit()
    return row


def _move(kind: _Archive, fiscal_year, code, parent_code):
    fiscal_year = require_year(fiscal_year)
    code = clean_text(code, f'{kind.label}代码', 50)
    parent_code = _blank_parent(parent_code)
    row = _get(kind, fiscal_year, code)
    if parent_code == code:
        raise BxError(f'{kind.label}的上级不能是自己')
    if parent_code is None:
        level = 1
    else:
        parent_code = clean_text(parent_code, f'上级{kind.label}代码', 50)
        parent = _get(kind, fiscal_year, parent_code)
        if code in _ancestors(kind, fiscal_year, parent_code):
            raise BxError(f'不能把{kind.label}调整到自己的下级下面')
        _assert_can_gain_child(kind, fiscal_year, parent_code)
        level = parent.level_no + 1
    setattr(row, kind.parent_attr, parent_code)
    db.session.flush()
    _relevel(kind, fiscal_year, code, level)
    db.session.commit()
    return row


def _delete(kind: _Archive, fiscal_year, code):
    fiscal_year = require_year(fiscal_year)
    code = clean_text(code, f'{kind.label}代码', 50)
    row = _get(kind, fiscal_year, code)
    if _children(kind, fiscal_year, code):
        raise BxError(f'该{kind.label}还有下级，不能删除')
    if _has_budget(kind, fiscal_year, code) or _has_claim(kind, fiscal_year, code):
        raise BxError(f'该{kind.label}已被预算或报销单使用，不能删除')
    db.session.delete(row)
    db.session.commit()


def create_department(fiscal_year, dept_code, dept_name, parent_dept_code=None):
    return _create(_DEPARTMENT, fiscal_year, dept_code, dept_name, parent_dept_code)


def update_department_name(fiscal_year, dept_code, dept_name):
    return _update_name(_DEPARTMENT, fiscal_year, dept_code, dept_name)


def move_department(fiscal_year, dept_code, parent_dept_code=None):
    return _move(_DEPARTMENT, fiscal_year, dept_code, parent_dept_code)


def delete_department(fiscal_year, dept_code):
    _delete(_DEPARTMENT, fiscal_year, dept_code)


def create_project(fiscal_year, project_code, project_name, parent_project_code=None):
    return _create(_PROJECT, fiscal_year, project_code, project_name, parent_project_code)


def update_project_name(fiscal_year, project_code, project_name):
    return _update_name(_PROJECT, fiscal_year, project_code, project_name)


def move_project(fiscal_year, project_code, parent_project_code=None):
    return _move(_PROJECT, fiscal_year, project_code, parent_project_code)


def delete_project(fiscal_year, project_code):
    _delete(_PROJECT, fiscal_year, project_code)


def is_leaf_department(fiscal_year: int, dept_code: str) -> bool:
    return not _children(_DEPARTMENT, fiscal_year, dept_code)


def is_leaf_project(fiscal_year: int, project_code: str) -> bool:
    return not _children(_PROJECT, fiscal_year, project_code)
