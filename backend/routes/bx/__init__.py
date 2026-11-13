# -*- coding: utf-8 -*-
"""报销台账接口。写入规则在 services.bx，这里只做角色、参数和返回。"""
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from Auth.auth import token_required
from Model import BxBudget, BxClaim, BxDepartment, BxProject, User
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
    delete_project,
    move_department,
    move_project,
    save_claim,
    update_budget_amount,
    update_department_name,
    update_project_name,
)
from services.bx.common import parse_date

bx_bp = Blueprint('bx', __name__)

_ACCOUNTANT_ONLY = '只有会计可以维护部门、项目、预算和报销单'
_CASHIER_ONLY = '只有出纳可以确认计入或取消确认'
_READER_ONLY = '没有报销台账的查看权限'


def _fail(exc):
    if isinstance(exc, BxOverspend):
        return jsonify({
            'success': False,
            'need_confirm': True,
            'message': exc.message,
            'budget_amount': f'{exc.budget_amount:.2f}',
            'confirmed_amount': f'{exc.confirmed_amount:.2f}',
            'this_amount': f'{exc.this_amount:.2f}',
        }), 409
    if isinstance(exc, BxNeedConfirm):
        return jsonify({
            'success': False,
            'need_confirm': True,
            'message': exc.message,
            'source_year': exc.source_year,
            'target_year': exc.target_year,
            'department_count': exc.department_count,
            'project_count': exc.project_count,
            'budget_count': exc.budget_count,
        }), 409
    if isinstance(exc, BxError):
        return jsonify({'success': False, 'message': exc.message}), 400
    raise exc


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _year(value):
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return value


def _flag(data, key):
    value = data.get(key, False)
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes')
    return value is True


def _query_year():
    return _year(request.args.get('fiscal_year'))


def _require_accountant(user):
    if user.is_admin or user.role == User.ROLE_ACCOUNTANT:
        return None
    return jsonify({'success': False, 'message': _ACCOUNTANT_ONLY}), 403


def _require_cashier(user):
    if user.is_admin or user.role == User.ROLE_CASHIER:
        return None
    return jsonify({'success': False, 'message': _CASHIER_ONLY}), 403


def _require_reader(user):
    if user.is_admin or user.role in (User.ROLE_ACCOUNTANT, User.ROLE_CASHIER):
        return None
    return jsonify({'success': False, 'message': _READER_ONLY}), 403


def _money(value):
    return f'{Decimal(str(value)):.2f}'


def _name_maps(fiscal_year):
    departments = {
        row.dept_code: row.dept_name
        for row in BxDepartment.query.filter_by(fiscal_year=fiscal_year).all()
    }
    projects = {
        row.project_code: row.project_name
        for row in BxProject.query.filter_by(fiscal_year=fiscal_year).all()
    }
    return departments, projects


def _archive_list(model, code_attr, name_attr, parent_attr, fiscal_year):
    rows = model.query.filter_by(fiscal_year=fiscal_year).order_by(model.level_no, getattr(model, code_attr)).all()
    parents = {getattr(row, parent_attr) for row in rows if getattr(row, parent_attr)}
    items = []
    for row in rows:
        data = row.to_dict()
        data['is_leaf'] = getattr(row, code_attr) not in parents
        items.append(data)
    return items


@bx_bp.route('/api/bx/departments', methods=['GET'])
@token_required
def list_departments(current_user):
    denied = _require_reader(current_user)
    if denied:
        return denied
    try:
        fiscal_year = _query_year()
        if not isinstance(fiscal_year, int):
            raise BxError('年度须为4位整数')
        rows = _archive_list(BxDepartment, 'dept_code', 'dept_name', 'parent_dept_code', fiscal_year)
        return jsonify({'success': True, 'items': rows})
    except BxError as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/departments', methods=['POST'])
@token_required
def add_department(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = create_department(
            _year(data.get('fiscal_year')),
            data.get('dept_code'),
            data.get('dept_name'),
            data.get('parent_dept_code'),
        )
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/departments/name', methods=['PUT'])
@token_required
def rename_department(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = update_department_name(_year(data.get('fiscal_year')), data.get('dept_code'), data.get('dept_name'))
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/departments/parent', methods=['PUT'])
@token_required
def reparent_department(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = move_department(_year(data.get('fiscal_year')), data.get('dept_code'), data.get('parent_dept_code'))
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/departments', methods=['DELETE'])
@token_required
def remove_department(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        delete_department(_query_year(), request.args.get('dept_code'))
        return jsonify({'success': True})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/projects', methods=['GET'])
@token_required
def list_projects(current_user):
    denied = _require_reader(current_user)
    if denied:
        return denied
    try:
        fiscal_year = _query_year()
        if not isinstance(fiscal_year, int):
            raise BxError('年度须为4位整数')
        return jsonify({
            'success': True,
            'items': _archive_list(BxProject, 'project_code', 'project_name', 'parent_project_code', fiscal_year),
        })
    except BxError as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/projects', methods=['POST'])
@token_required
def add_project(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = create_project(
            _year(data.get('fiscal_year')),
            data.get('project_code'),
            data.get('project_name'),
            data.get('parent_project_code'),
        )
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/projects/name', methods=['PUT'])
@token_required
def rename_project(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = update_project_name(_year(data.get('fiscal_year')), data.get('project_code'), data.get('project_name'))
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/projects/parent', methods=['PUT'])
@token_required
def reparent_project(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = move_project(_year(data.get('fiscal_year')), data.get('project_code'), data.get('parent_project_code'))
        return jsonify({'success': True, 'data': row.to_dict()})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/projects', methods=['DELETE'])
@token_required
def remove_project(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        delete_project(_query_year(), request.args.get('project_code'))
        return jsonify({'success': True})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/copy-year', methods=['POST'])
@token_required
def copy_fiscal_year(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        result = copy_year(_year(data.get('source_year')), _year(data.get('target_year')), _flag(data, 'confirmed'))
        return jsonify({'success': True, 'data': result})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


def _budget_item(row, departments, projects):
    usage = budget_usage(row.fiscal_year, row.dept_code, row.project_code)
    return {
        'fiscal_year': row.fiscal_year,
        'dept_code': row.dept_code,
        'dept_name': departments.get(row.dept_code),
        'project_code': row.project_code,
        'project_name': projects.get(row.project_code),
        'budget_amount': _money(usage['budget_amount']),
        'confirmed_amount': _money(usage['confirmed_amount']),
        'pending_amount': _money(usage['pending_amount']),
        'balance': _money(usage['balance']),
    }


@bx_bp.route('/api/bx/budgets', methods=['GET'])
@token_required
def list_budgets(current_user):
    denied = _require_reader(current_user)
    if denied:
        return denied
    try:
        fiscal_year = _query_year()
        if not isinstance(fiscal_year, int):
            raise BxError('年度须为4位整数')
        departments, projects = _name_maps(fiscal_year)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in (10, 20, 50, 100):
            page_size = 10
        pagination = BxBudget.query.filter_by(fiscal_year=fiscal_year).order_by(
            BxBudget.dept_code, BxBudget.project_code,
        ).paginate(page=page, per_page=page_size, error_out=False)
        return jsonify({
            'success': True,
            'items': [_budget_item(row, departments, projects) for row in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
        })
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/budgets', methods=['POST'])
@token_required
def add_budget(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = create_budget(
            _year(data.get('fiscal_year')),
            data.get('dept_code'),
            data.get('project_code'),
            data.get('amount'),
        )
        departments, projects = _name_maps(row.fiscal_year)
        return jsonify({'success': True, 'data': _budget_item(row, departments, projects)})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/budgets/amount', methods=['PUT'])
@token_required
def change_budget_amount(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    data = _body()
    try:
        row = update_budget_amount(
            _year(data.get('fiscal_year')),
            data.get('dept_code'),
            data.get('project_code'),
            data.get('amount'),
        )
        departments, projects = _name_maps(row.fiscal_year)
        return jsonify({'success': True, 'data': _budget_item(row, departments, projects)})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/budgets', methods=['DELETE'])
@token_required
def remove_budget(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        delete_budget(_query_year(), request.args.get('dept_code'), request.args.get('project_code'))
        return jsonify({'success': True})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


def _claim_filters(fiscal_year):
    query = BxClaim.query.filter_by(fiscal_year=fiscal_year)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from:
        query = query.filter(BxClaim.expense_date >= parse_date(date_from))
    if date_to:
        query = query.filter(BxClaim.expense_date <= parse_date(date_to))
    dept_code = (request.args.get('dept_code') or '').strip()
    project_code = (request.args.get('project_code') or '').strip()
    claimant = (request.args.get('claimant') or '').strip()
    summary = (request.args.get('summary') or '').strip()
    doc_no = (request.args.get('doc_no') or '').strip()
    status = (request.args.get('status') or '').strip()
    if dept_code:
        query = query.filter(BxClaim.dept_code == dept_code)
    if project_code:
        query = query.filter(BxClaim.project_code == project_code)
    if claimant:
        query = query.filter(BxClaim.claimant.like(f'%{claimant}%'))
    if summary:
        query = query.filter(BxClaim.summary.like(f'%{summary}%'))
    if doc_no:
        query = query.filter(BxClaim.doc_no == doc_no)
    if status:
        if status not in (BxClaim.STATUS_PENDING, BxClaim.STATUS_CONFIRMED):
            raise BxError('状态只能是待支出或已计入')
        query = query.filter(BxClaim.status == status)
    return query


def _sum_status(query, status):
    total = query.filter(BxClaim.status == status).with_entities(func.coalesce(func.sum(BxClaim.amount), 0)).scalar()
    return _money(total)


@bx_bp.route('/api/bx/claims', methods=['GET'])
@token_required
def list_claims(current_user):
    denied = _require_reader(current_user)
    if denied:
        return denied
    try:
        fiscal_year = _query_year()
        if not isinstance(fiscal_year, int):
            raise BxError('年度须为4位整数')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in (10, 20, 50, 100):
            page_size = 10
        query = _claim_filters(fiscal_year)
        confirmed_total = _sum_status(query, BxClaim.STATUS_CONFIRMED)
        pending_total = _sum_status(query, BxClaim.STATUS_PENDING)
        pagination = query.order_by(BxClaim.expense_date, BxClaim.doc_no).paginate(
            page=page, per_page=page_size, error_out=False,
        )
        departments, projects = _name_maps(fiscal_year)
        items = []
        for row in pagination.items:
            data = row.to_dict()
            data['dept_name'] = departments.get(row.dept_code)
            data['project_name'] = projects.get(row.project_code)
            items.append(data)
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'confirmed_total': confirmed_total,
            'pending_total': pending_total,
        })
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


def _save_from_body(data, claim_id=None):
    return save_claim(
        _year(data.get('fiscal_year')),
        data.get('expense_date'),
        data.get('dept_code'),
        data.get('project_code'),
        data.get('claimant'),
        data.get('summary'),
        data.get('amount'),
        claim_id=claim_id,
        allow_overspend=_flag(data, 'allow_overspend'),
    )


def _claim_response(row):
    departments, projects = _name_maps(row.fiscal_year)
    data = row.to_dict()
    data['dept_name'] = departments.get(row.dept_code)
    data['project_name'] = projects.get(row.project_code)
    return jsonify({'success': True, 'data': data})


@bx_bp.route('/api/bx/claims', methods=['POST'])
@token_required
def add_claim(current_user):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        return _claim_response(_save_from_body(_body()))
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/claims/<int:claim_id>', methods=['PUT'])
@token_required
def edit_claim(current_user, claim_id):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        return _claim_response(_save_from_body(_body(), claim_id))
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/claims/<int:claim_id>', methods=['DELETE'])
@token_required
def remove_claim(current_user, claim_id):
    denied = _require_accountant(current_user)
    if denied:
        return denied
    try:
        delete_claim(claim_id)
        return jsonify({'success': True})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/claims/<int:claim_id>/confirm', methods=['POST'])
@token_required
def confirm_claim_route(current_user, claim_id):
    denied = _require_cashier(current_user)
    if denied:
        return denied
    try:
        row = confirm_claim(claim_id, _flag(_body(), 'allow_overspend'))
        return _claim_response(row)
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


@bx_bp.route('/api/bx/claims/<int:claim_id>/cancel-confirm', methods=['POST'])
@token_required
def cancel_claim_route(current_user, claim_id):
    denied = _require_cashier(current_user)
    if denied:
        return denied
    try:
        return _claim_response(cancel_confirm(claim_id))
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


def _summary_line(budget, confirmed, pending, departments, projects):
    budget_amount = Decimal(str(budget.amount))
    return {
        'dept_code': budget.dept_code,
        'dept_name': departments.get(budget.dept_code),
        'project_code': budget.project_code,
        'project_name': projects.get(budget.project_code),
        'budget_amount': _money(budget_amount),
        'confirmed_amount': _money(confirmed),
        'pending_amount': _money(pending),
        'balance': _money(budget_amount - confirmed),
    }


def _add_amounts(lines, key):
    return _money(sum(Decimal(line[key]) for line in lines))


@bx_bp.route('/api/bx/summary', methods=['GET'])
@token_required
def claim_summary(current_user):
    denied = _require_reader(current_user)
    if denied:
        return denied
    try:
        fiscal_year = _query_year()
        if not isinstance(fiscal_year, int):
            raise BxError('年度须为4位整数')
        group_by = (request.args.get('group_by') or 'department').strip()
        if group_by not in ('department', 'project'):
            raise BxError('汇总方式只能是 department 或 project')
        departments, projects = _name_maps(fiscal_year)
        totals = {}
        for dept_code, project_code, status, amount in _claim_status_sums(fiscal_year):
            bucket = totals.setdefault((dept_code, project_code), {'confirmed': Decimal('0.00'), 'pending': Decimal('0.00')})
            if status == BxClaim.STATUS_CONFIRMED:
                bucket['confirmed'] = Decimal(str(amount))
            elif status == BxClaim.STATUS_PENDING:
                bucket['pending'] = Decimal(str(amount))
        budgets = BxBudget.query.filter_by(fiscal_year=fiscal_year).all()
        lines = []
        for budget in budgets:
            bucket = totals.get((budget.dept_code, budget.project_code), {})
            lines.append(_summary_line(
                budget,
                bucket.get('confirmed', Decimal('0.00')),
                bucket.get('pending', Decimal('0.00')),
                departments,
                projects,
            ))
        if group_by == 'department':
            groups = _group_lines(lines, 'dept_code', 'dept_name', 'project_code')
        else:
            groups = _group_lines(lines, 'project_code', 'project_name', 'dept_code')
        return jsonify({'success': True, 'fiscal_year': fiscal_year, 'group_by': group_by, 'groups': groups})
    except (BxError, BxOverspend, BxNeedConfirm) as exc:
        return _fail(exc)


def _claim_status_sums(fiscal_year):
    from Model.base import db
    return db.session.query(
        BxClaim.dept_code,
        BxClaim.project_code,
        BxClaim.status,
        func.coalesce(func.sum(BxClaim.amount), 0),
    ).filter(BxClaim.fiscal_year == fiscal_year).group_by(
        BxClaim.dept_code, BxClaim.project_code, BxClaim.status,
    ).all()


def _group_lines(lines, group_code_key, group_name_key, line_sort_key):
    grouped = {}
    for line in lines:
        grouped.setdefault(line[group_code_key], []).append(line)
    groups = []
    for code in sorted(grouped):
        children = sorted(grouped[code], key=lambda item: item[line_sort_key])
        groups.append({
            'code': code,
            'name': children[0][group_name_key],
            'budget_amount': _add_amounts(children, 'budget_amount'),
            'confirmed_amount': _add_amounts(children, 'confirmed_amount'),
            'pending_amount': _add_amounts(children, 'pending_amount'),
            'balance': _add_amounts(children, 'balance'),
            'lines': children,
        })
    return groups
