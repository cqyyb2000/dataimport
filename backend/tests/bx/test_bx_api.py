# -*- coding: utf-8 -*-
"""报销台账接口的角色限制、超支确认和菜单。"""
import pytest
from werkzeug.security import generate_password_hash

from Auth.auth import generate_token, get_user_permissions
from Model import Menu, User, db
from routes.bx import bx_bp


@pytest.fixture
def client(bx_app, db_ctx):
    if 'bx' not in bx_app.blueprints:
        bx_app.register_blueprint(bx_bp)
    return bx_app.test_client()


def _user(username, role):
    user = User(
        username=username,
        password_hash=generate_password_hash('pass1234'),
        is_admin=False,
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _auth(user):
    return {'Authorization': 'Bearer ' + generate_token(user.username)}


def _prepare(client, headers):
    client.post('/api/bx/departments', json={
        'fiscal_year': 2026, 'dept_code': 'D', 'dept_name': '宣传部',
    }, headers=headers)
    client.post('/api/bx/departments', json={
        'fiscal_year': 2026, 'dept_code': 'D1', 'dept_name': '新闻科', 'parent_dept_code': 'D',
    }, headers=headers)
    client.post('/api/bx/projects', json={
        'fiscal_year': 2026, 'project_code': 'P1', 'project_name': '活动',
    }, headers=headers)
    created = client.post('/api/bx/budgets', json={
        'fiscal_year': 2026, 'dept_code': 'D1', 'project_code': 'P1', 'amount': '10.00',
    }, headers=headers)
    assert created.status_code == 200


def test_cashier_cannot_maintain_and_accountant_cannot_confirm(client, db_ctx):
    accountant = _user('acc', User.ROLE_ACCOUNTANT)
    cashier = _user('cash', User.ROLE_CASHIER)
    accountant_headers = _auth(accountant)
    cashier_headers = _auth(cashier)
    _prepare(client, accountant_headers)

    denied = client.post('/api/bx/departments', json={
        'fiscal_year': 2026, 'dept_code': 'D2', 'dept_name': '外宣',
    }, headers=cashier_headers)
    assert denied.status_code == 403

    over = client.post('/api/bx/claims', json={
        'fiscal_year': 2026,
        'expense_date': '2026-05-02',
        'dept_code': 'D1',
        'project_code': 'P1',
        'claimant': '张三',
        'summary': '差旅',
        'amount': '10.01',
    }, headers=accountant_headers)
    assert over.status_code == 409
    assert over.get_json()['need_confirm'] is True

    saved = client.post('/api/bx/claims', json={
        'fiscal_year': 2026,
        'expense_date': '2026-05-02',
        'dept_code': 'D1',
        'project_code': 'P1',
        'claimant': '张三',
        'summary': '差旅',
        'amount': '10.01',
        'allow_overspend': True,
    }, headers=accountant_headers)
    assert saved.status_code == 200
    claim_id = saved.get_json()['data']['id']
    assert saved.get_json()['data']['status'] == '待支出'

    cannot_confirm = client.post(f'/api/bx/claims/{claim_id}/confirm', json={}, headers=accountant_headers)
    assert cannot_confirm.status_code == 403
    confirmed = client.post(
        f'/api/bx/claims/{claim_id}/confirm',
        json={'allow_overspend': True},
        headers=cashier_headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.get_json()['data']['status'] == '已计入'

    summary = client.get('/api/bx/summary?fiscal_year=2026&group_by=department', headers=cashier_headers)
    assert summary.status_code == 200
    group = summary.get_json()['groups'][0]
    assert group['code'] == 'D1'
    assert group['balance'] == '-0.01'


def test_cashier_menu_only_includes_detail_and_summary(db_ctx):
    parent = Menu(name='报销台账', component='', parent_id=0, path='', icon='Wallet', sort_order=1)
    db.session.add(parent)
    db.session.flush()
    db.session.add(Menu(
        name='报销录入', component='bx/ClaimEntry', parent_id=parent.id,
        path='/bx/entry', icon='Edit', sort_order=1,
    ))
    db.session.add(Menu(
        name='报销明细', component='bx/ClaimList', parent_id=parent.id,
        path='/bx/claims', icon='List', sort_order=2,
    ))
    user = User(username='cash-menu', password_hash='x', is_admin=False, role=User.ROLE_CASHIER)
    db.session.add(user)
    db.session.commit()

    menus = get_user_permissions(user.id)
    assert [item['name'] for item in menus] == ['报销台账']
    assert [item['name'] for item in menus[0]['children']] == ['报销明细']
