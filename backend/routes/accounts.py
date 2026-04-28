# 会计科目(account)与科目辅助核算(account_auxiliary)接口
import importlib

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from Auth.auth import token_required
from Model import Account, AccountAuxiliary, AccountBookFiscalYear, db
from services.account_auxiliary_custom_archive_sync import upsert_custom_archive_for_auxiliary
from services.account_chart_excel_import import (
    parse_account_chart_excel,
    run_account_chart_excel_import,
)

accounts_bp = Blueprint('accounts', __name__)


def _ensure_fiscal_year(account_book_code: str, fiscal_year: int):
    """若账套年度不存在返回 (None, json_response)，否则返回 (row, None)。"""
    row = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
    ).first()
    if not row:
        return None, (
            jsonify({
                'success': False,
                'message': f'未找到账套年度: {account_book_code}/{fiscal_year}',
            }),
            404,
        )
    return row, None


def _normalize_page():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    if page < 1:
        page = 1
    if page_size not in (10, 20, 50, 100):
        page_size = 10
    return page, page_size


# ---------- 会计科目 Account ----------


@accounts_bp.route('/api/accounts', methods=['GET'])
@token_required
def list_accounts_query(current_user):
    """分页查询科目列表。查询参数：account_book_code、fiscal_year 必填；可选 account_code、account_name（模糊）、account_type、parent_account_code、is_leaf、is_enabled、status、page、page_size"""
    account_book_code = request.args.get('account_book_code', '').strip()
    fiscal_year = request.args.get('fiscal_year', type=int)
    return _list_accounts(current_user, account_book_code, fiscal_year)


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts', methods=['GET'])
@token_required
def list_accounts_nested(current_user, account_book_code, fiscal_year):
    """分页查询科目列表（路径参数指定账套、年度）"""
    return _list_accounts(current_user, account_book_code.strip(), fiscal_year)


def _list_accounts(current_user, account_book_code: str, fiscal_year: int | None):
    if not account_book_code:
        return jsonify({'success': False, 'message': '账套编码（account_book_code）不能为空'}), 400
    if fiscal_year is None:
        return jsonify({'success': False, 'message': '会计年度（fiscal_year）不能为空'}), 400

    err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if err[1]:
        return err[1]

    try:
        page, page_size = _normalize_page()
        query = Account.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
        )

        code_q = request.args.get('account_code', '').strip()
        name_q = request.args.get('account_name', '').strip()
        acc_type = request.args.get('account_type', '').strip()
        parent = request.args.get('parent_account_code', '').strip()
        is_leaf = request.args.get('is_leaf', type=int)
        is_enabled = request.args.get('is_enabled', type=int)
        status = request.args.get('status', type=int)

        if code_q:
            query = query.filter(Account.account_code.like(f'%{code_q}%'))
        if name_q:
            query = query.filter(Account.account_name.like(f'%{name_q}%'))
        if acc_type:
            query = query.filter(Account.account_type == acc_type)
        if parent:
            query = query.filter(Account.parent_account_code == parent)
        if is_leaf is not None:
            query = query.filter(Account.is_leaf == is_leaf)
        if is_enabled is not None:
            query = query.filter(Account.is_enabled == is_enabled)
        if status is not None:
            query = query.filter(Account.status == status)

        query = query.order_by(Account.account_code.asc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        items = [item.to_dict() for item in pagination.items]
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取科目列表失败: {str(e)}'}), 500


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>', methods=['GET'])
@token_required
def get_account(current_user, account_book_code, fiscal_year, account_code):
    """获取单个科目详情"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    try:
        row = Account.query.filter_by(
            account_book_code=account_book_code.strip(),
            fiscal_year=fiscal_year,
            account_code=account_code.strip(),
        ).first()
        if not row:
            return jsonify({
                'success': False,
                'message': f'未找到科目: {account_book_code}/{fiscal_year}/{account_code}',
            }), 404
        return jsonify({'success': True, 'data': row.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取科目详情失败: {str(e)}'}), 500


@accounts_bp.route('/api/accounts', methods=['POST'])
@token_required
def create_account_flat(current_user):
    """创建科目（JSON 中须含 account_book_code、fiscal_year）"""
    data = request.json or {}
    account_book_code = (data.get('account_book_code') or '').strip()
    fiscal_year = data.get('fiscal_year')
    try:
        fiscal_year = int(fiscal_year) if fiscal_year is not None else None
    except (TypeError, ValueError):
        fiscal_year = None
    return _create_account_body(current_user, account_book_code, fiscal_year, data)


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts', methods=['POST'])
@token_required
def create_account_nested(current_user, account_book_code, fiscal_year):
    """创建科目（路径指定账套、年度）"""
    data = request.json or {}
    return _create_account_body(current_user, account_book_code.strip(), fiscal_year, data)


def _create_account_body(current_user, account_book_code: str, fiscal_year: int | None, data: dict):
    if not account_book_code or fiscal_year is None:
        return jsonify({'success': False, 'message': 'account_book_code 与 fiscal_year 不能为空'}), 400
    _, fy_err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if fy_err:
        return fy_err

    account_code = (data.get('account_code') or '').strip()
    account_name = (data.get('account_name') or '').strip()
    if not account_code:
        return jsonify({'success': False, 'message': '科目编号（account_code）不能为空'}), 400
    if not account_name:
        return jsonify({'success': False, 'message': '科目名称（account_name）不能为空'}), 400

    account_level = data.get('account_level')
    account_type = (data.get('account_type') or '').strip()
    balance_direction = (data.get('balance_direction') or '').strip()
    if account_level is None:
        return jsonify({'success': False, 'message': '科目级次（account_level）不能为空'}), 400
    try:
        account_level = int(account_level)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'account_level 必须为整数'}), 400
    if not account_type:
        return jsonify({'success': False, 'message': '科目类型（account_type）不能为空'}), 400
    if not balance_direction:
        return jsonify({'success': False, 'message': '余额方向（balance_direction）不能为空'}), 400

    if Account.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        account_code=account_code,
    ).first():
        return jsonify({'success': False, 'message': f'科目编号已存在: {account_code}'}), 400

    parent_account_code = (data.get('parent_account_code') or '').strip() or None
    if parent_account_code:
        parent = Account.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=parent_account_code,
        ).first()
        if not parent:
            return jsonify({
                'success': False,
                'message': f'上级科目不存在: {parent_account_code}',
            }), 400

    is_leaf = data.get('is_leaf', 0)
    is_enabled = data.get('is_enabled', 1)
    status = data.get('status', 1)
    try:
        row = Account(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=account_code,
            account_name=account_name,
            account_level=account_level,
            account_type=account_type,
            balance_direction=balance_direction,
            is_leaf=is_leaf if is_leaf is not None else 0,
            is_enabled=is_enabled if is_enabled is not None else 1,
            parent_account_code=parent_account_code,
            remark=(data.get('remark') or '').strip() or None,
            status=status if status is not None else 1,
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({'success': True, 'message': '科目创建成功', 'data': row.to_dict()})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建科目失败（约束冲突）: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建科目失败: {str(e)}'}), 500


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>', methods=['PUT'])
@token_required
def update_account(current_user, account_book_code, fiscal_year, account_code):
    """更新科目（不可修改账套、年度、科目编号）"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    account_book_code = account_book_code.strip()
    account_code = account_code.strip()

    row = Account.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        account_code=account_code,
    ).first()
    if not row:
        return jsonify({'success': False, 'message': f'未找到科目: {account_code}'}), 404

    data = request.json or {}
    try:
        if 'account_name' in data:
            v = (data.get('account_name') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '科目名称不能为空'}), 400
            row.account_name = v
        if 'account_level' in data:
            row.account_level = int(data['account_level'])
        if 'account_type' in data:
            v = (data.get('account_type') or '').strip()
            if v:
                row.account_type = v
        if 'balance_direction' in data:
            v = (data.get('balance_direction') or '').strip()
            if v:
                row.balance_direction = v
        if 'is_leaf' in data:
            row.is_leaf = data.get('is_leaf')
        if 'is_enabled' in data:
            row.is_enabled = data.get('is_enabled')
        if 'remark' in data:
            row.remark = (data.get('remark') or '').strip() or None
        if 'status' in data:
            row.status = data.get('status')

        if 'parent_account_code' in data:
            parent_account_code = (data.get('parent_account_code') or '').strip() or None
            if parent_account_code == account_code:
                return jsonify({'success': False, 'message': '上级科目不能为自身'}), 400
            if parent_account_code:
                parent = Account.query.filter_by(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    account_code=parent_account_code,
                ).first()
                if not parent:
                    return jsonify({'success': False, 'message': f'上级科目不存在: {parent_account_code}'}), 400
            row.parent_account_code = parent_account_code

        db.session.commit()
        return jsonify({'success': True, 'message': '科目更新成功', 'data': row.to_dict()})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新科目失败（约束冲突）: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新科目失败: {str(e)}'}), 500


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>', methods=['DELETE'])
@token_required
def delete_account(current_user, account_book_code, fiscal_year, account_code):
    """删除科目（存在下级科目时禁止删除；级联删除该科目下辅助核算配置）"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    account_book_code = account_book_code.strip()
    account_code = account_code.strip()

    row = Account.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        account_code=account_code,
    ).first()
    if not row:
        return jsonify({'success': False, 'message': f'未找到科目: {account_code}'}), 404

    child = Account.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        parent_account_code=account_code,
    ).first()
    if child:
        return jsonify({
            'success': False,
            'message': '存在下级科目，无法删除。请先调整或删除下级科目。',
        }), 400

    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({'success': True, 'message': '科目已删除'})
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除科目失败（存在关联数据）: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除科目失败: {str(e)}'}), 500


# ---------- 会计科目 Excel 导入 ----------


def _import_accounts_excel_handler(account_book_code: str, fiscal_year: int | None):
    """multipart：file、mode（可选 upsert|append，默认 upsert）。返回 (jsonify, status_code)。"""
    try:
        importlib.import_module('openpyxl')
    except Exception:
        return jsonify({
            'success': False,
            'message': '缺少 openpyxl 依赖，请先安装：pip install openpyxl',
        }), 500

    account_book_code = (account_book_code or '').strip()
    if not account_book_code:
        return jsonify({'success': False, 'message': '账套编码（account_book_code）不能为空'}), 400
    if fiscal_year is None:
        return jsonify({'success': False, 'message': '会计年度（fiscal_year）不能为空'}), 400

    mode = (request.form.get('mode') or 'upsert').strip().lower()
    if mode not in ('upsert', 'append'):
        return jsonify({'success': False, 'message': 'mode 仅支持 upsert 或 append'}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请上传 Excel 文件（表单字段名：file）'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    filename = (file.filename or '').lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xlsm')):
        return jsonify({'success': False, 'message': '仅支持 .xlsx / .xlsm 文件'}), 400

    try:
        parsed_rows, rows_skipped = parse_account_chart_excel(file.read())
    except RuntimeError as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    result = run_account_chart_excel_import(
        account_book_code,
        fiscal_year,
        parsed_rows,
        mode=mode,
        rows_skipped=rows_skipped,
    )
    if result.get('success'):
        return jsonify(result), 200
    msg = result.get('message') or '导入失败'
    status = 404 if '未找到账套年度' in msg else 400
    return jsonify(result), status


@accounts_bp.route('/api/accounts/import_excel', methods=['POST'])
@token_required
def import_accounts_excel_flat(current_user):
    """从 Excel 导入会计科目及辅助核算（表单中提供账套、年度）。"""
    account_book_code = request.form.get('account_book_code', '')
    fiscal_year_raw = request.form.get('fiscal_year')
    fiscal_year = None
    if fiscal_year_raw not in (None, ''):
        try:
            fiscal_year = int(fiscal_year_raw)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '会计年度必须为整数'}), 400
    return _import_accounts_excel_handler(account_book_code, fiscal_year)


@accounts_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/import_excel',
    methods=['POST'],
)
@token_required
def import_accounts_excel_nested(current_user, account_book_code, fiscal_year):
    """从 Excel 导入会计科目及辅助核算（路径中指定账套、年度）。"""
    return _import_accounts_excel_handler(account_book_code, fiscal_year)


# ---------- 科目辅助核算 AccountAuxiliary ----------


@accounts_bp.route('/api/account_auxiliaries', methods=['GET'])
@token_required
def list_account_auxiliaries_query(current_user):
    """分页查询科目辅助核算。查询参数：account_book_code、fiscal_year 必填；可选 account_code、auxiliary_item_code、auxiliary_item_name（模糊）、status、page、page_size"""
    account_book_code = request.args.get('account_book_code', '').strip()
    fiscal_year = request.args.get('fiscal_year', type=int)
    return _list_account_auxiliaries(current_user, account_book_code, fiscal_year)


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>/auxiliaries', methods=['GET'])
@token_required
def list_account_auxiliaries_nested(current_user, account_book_code, fiscal_year, account_code):
    """某科目下的辅助核算列表（路径指定科目）"""
    return _list_account_auxiliaries(
        current_user,
        account_book_code.strip(),
        fiscal_year,
        fixed_account_code=account_code.strip(),
    )


def _list_account_auxiliaries(current_user, account_book_code: str, fiscal_year: int | None, fixed_account_code: str | None = None):
    if not account_book_code:
        return jsonify({'success': False, 'message': '账套编码（account_book_code）不能为空'}), 400
    if fiscal_year is None:
        return jsonify({'success': False, 'message': '会计年度（fiscal_year）不能为空'}), 400

    err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if err[1]:
        return err[1]

    try:
        page, page_size = _normalize_page()
        query = AccountAuxiliary.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
        )
        if fixed_account_code is not None:
            query = query.filter(AccountAuxiliary.account_code == fixed_account_code)
        else:
            ac = request.args.get('account_code', '').strip()
            if ac:
                query = query.filter(AccountAuxiliary.account_code == ac)
        code_q = request.args.get('auxiliary_item_code', '').strip()
        name_q = request.args.get('auxiliary_item_name', '').strip()
        status = request.args.get('status', type=int)
        if code_q:
            query = query.filter(AccountAuxiliary.auxiliary_item_code.like(f'%{code_q}%'))
        if name_q:
            query = query.filter(AccountAuxiliary.auxiliary_item_name.like(f'%{name_q}%'))
        if status is not None:
            query = query.filter(AccountAuxiliary.status == status)

        query = query.order_by(
            AccountAuxiliary.account_code.asc(),
            AccountAuxiliary.auxiliary_item_code.asc(),
        )
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        items = [item.to_dict() for item in pagination.items]
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取科目辅助核算列表失败: {str(e)}'}), 500


@accounts_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>/auxiliaries/<auxiliary_item_code>',
    methods=['GET'],
)
@token_required
def get_account_auxiliary(current_user, account_book_code, fiscal_year, account_code, auxiliary_item_code):
    """获取单条科目辅助核算"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    try:
        row = AccountAuxiliary.query.filter_by(
            account_book_code=account_book_code.strip(),
            fiscal_year=fiscal_year,
            account_code=account_code.strip(),
            auxiliary_item_code=auxiliary_item_code.strip(),
        ).first()
        if not row:
            return jsonify({'success': False, 'message': '未找到该辅助核算配置'}), 404
        return jsonify({'success': True, 'data': row.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取辅助核算详情失败: {str(e)}'}), 500


@accounts_bp.route('/api/account_auxiliaries', methods=['POST'])
@token_required
def create_account_auxiliary_flat(current_user):
    """新增辅助核算（JSON 须含 account_book_code、fiscal_year、account_code、auxiliary_item_code、auxiliary_item_name）"""
    data = request.json or {}
    return _create_account_auxiliary_body(current_user, data)


@accounts_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>/auxiliaries', methods=['POST'])
@token_required
def create_account_auxiliary_nested(current_user, account_book_code, fiscal_year, account_code):
    """新增辅助核算（路径含科目）"""
    data = request.json or {}
    data = {**data, 'account_book_code': account_book_code.strip(), 'fiscal_year': fiscal_year, 'account_code': account_code.strip()}
    return _create_account_auxiliary_body(current_user, data)


def _create_account_auxiliary_body(current_user, data: dict):
    # pylint: disable=attribute-defined-outside-init  # jsonify/Werkzeug Response 惰性属性误报
    account_book_code = (data.get('account_book_code') or '').strip()
    fiscal_year = data.get('fiscal_year')
    try:
        fiscal_year = int(fiscal_year) if fiscal_year is not None else None
    except (TypeError, ValueError):
        fiscal_year = None
    account_code = (data.get('account_code') or '').strip()
    auxiliary_item_code = (data.get('auxiliary_item_code') or '').strip()
    auxiliary_item_name = (data.get('auxiliary_item_name') or '').strip()

    if not account_book_code or fiscal_year is None:
        return jsonify({'success': False, 'message': 'account_book_code 与 fiscal_year 不能为空'}), 400
    err = _ensure_fiscal_year(account_book_code, fiscal_year)
    if err[1]:
        return err[1]
    if not account_code:
        return jsonify({'success': False, 'message': '科目编号（account_code）不能为空'}), 400
    if not auxiliary_item_code:
        return jsonify({'success': False, 'message': '辅助项编号（auxiliary_item_code）不能为空'}), 400
    if not auxiliary_item_name:
        return jsonify({'success': False, 'message': '辅助项名称（auxiliary_item_name）不能为空'}), 400

    if not Account.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        account_code=account_code,
    ).first():
        return jsonify({'success': False, 'message': f'科目不存在: {account_code}'}), 400

    if AccountAuxiliary.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        account_code=account_code,
        auxiliary_item_code=auxiliary_item_code,
    ).first():
        return jsonify({'success': False, 'message': '该辅助项编号已存在'}), 400

    try:
        #corresponding_archive = (data.get('corresponding_archive') or '').strip() or None
        # if not corresponding_archive:
        #     # 兼容前端可能传入的同义字段，避免因字段名差异导致未同步
        #     corresponding_archive = (
        #         (data.get('archive_item_code') or '').strip()
        #         or (data.get('custom_archive_code') or '').strip()
        #         or None
        #     )
        sync_custom_archive = data.get('sync_custom_archive', True)
        if isinstance(sync_custom_archive, str):
            sync_custom_archive = sync_custom_archive.strip().lower() not in ('0', 'false', 'no', 'off')

        row = AccountAuxiliary(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=account_code,
            auxiliary_item_code=auxiliary_item_code,
            auxiliary_item_name=auxiliary_item_name,
            #corresponding_archive=corresponding_archive,
            auxiliary_item_description=(data.get('auxiliary_item_description') or '').strip() or None,
            status=data.get('status', 1),
        )
        db.session.add(row)

        sync_stats = None
        sync_skipped_reason = None
        if sync_custom_archive : #是否同步
            try:
                sync_stats = upsert_custom_archive_for_auxiliary(
                    account_book_code,
                    fiscal_year,
                    auxiliary_item_code,
                    auxiliary_item_name,
                    archive_item_name=(data.get('archive_item_name') or '').strip() or None,
                    archive_item_desc=(data.get('archive_item_desc') or '').strip() or None,
                    archive_value_desc=(data.get('archive_value_desc') or '').strip() or None,
                    status=data.get('status', 1),
                )
            except ValueError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 400
       

        db.session.commit()
        resp = {'success': True, 'message': '辅助核算已创建', 'data': row.to_dict()}
        if sync_stats is not None:
            resp['custom_archive_sync'] = sync_stats
        if sync_skipped_reason:
            resp['custom_archive_sync_skipped'] = sync_skipped_reason
        return jsonify(resp)
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建失败（约束冲突）: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建辅助核算失败: {str(e)}'}), 500


@accounts_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>/auxiliaries/<auxiliary_item_code>',
    methods=['PUT'],
)
@token_required
def update_account_auxiliary(current_user, account_book_code, fiscal_year, account_code, auxiliary_item_code):
    """更新辅助核算（主键不可改）"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    row = AccountAuxiliary.query.filter_by(
        account_book_code=account_book_code.strip(),
        fiscal_year=fiscal_year,
        account_code=account_code.strip(),
        auxiliary_item_code=auxiliary_item_code.strip(),
    ).first()
    if not row:
        return jsonify({'success': False, 'message': '未找到该辅助核算配置'}), 404

    data = request.json or {}
    try:
        if 'auxiliary_item_name' in data:
            v = (data.get('auxiliary_item_name') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '辅助项名称不能为空'}), 400
            row.auxiliary_item_name = v
        if 'corresponding_archive' in data:
            row.corresponding_archive = (data.get('corresponding_archive') or '').strip() or None
        elif 'archive_item_code' in data:
            # 兼容前端同义字段
            row.corresponding_archive = (data.get('archive_item_code') or '').strip() or None
        elif 'custom_archive_code' in data:
            # 兼容前端同义字段
            row.corresponding_archive = (data.get('custom_archive_code') or '').strip() or None
        if 'auxiliary_item_description' in data:
            row.auxiliary_item_description = (data.get('auxiliary_item_description') or '').strip() or None
        if 'status' in data:
            row.status = data.get('status')

        sync_custom_archive = data.get('sync_custom_archive', True)
        if isinstance(sync_custom_archive, str):
            sync_custom_archive = sync_custom_archive.strip().lower() not in ('0', 'false', 'no', 'off')

        sync_stats = None
        sync_skipped_reason = None
        if sync_custom_archive and row.corresponding_archive:
            try:
                sync_stats = upsert_custom_archive_for_auxiliary(
                    account_book_code.strip(),
                    fiscal_year,
                    row.corresponding_archive,
                    row.auxiliary_item_name,
                    archive_item_name=(data.get('archive_item_name') or '').strip() or None,
                    archive_item_desc=(data.get('archive_item_desc') or '').strip() or None,
                    archive_value_desc=(data.get('archive_value_desc') or '').strip() or None,
                    status=row.status,
                )
            except ValueError as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 400
        elif sync_custom_archive and not row.corresponding_archive:
            sync_skipped_reason = '未提供对应档案编码（corresponding_archive 或 archive_item_code），已跳过自定义档案同步'

        db.session.commit()
        resp = {'success': True, 'message': '辅助核算已更新', 'data': row.to_dict()}
        if sync_stats is not None:
            resp['custom_archive_sync'] = sync_stats
        if sync_skipped_reason:
            resp['custom_archive_sync_skipped'] = sync_skipped_reason
        return jsonify(resp)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新辅助核算失败: {str(e)}'}), 500


@accounts_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/accounts/<account_code>/auxiliaries/<auxiliary_item_code>',
    methods=['DELETE'],
)
@token_required
def delete_account_auxiliary(current_user, account_book_code, fiscal_year, account_code, auxiliary_item_code):
    """删除辅助核算配置"""
    err = _ensure_fiscal_year(account_book_code.strip(), fiscal_year)
    if err[1]:
        return err[1]
    row = AccountAuxiliary.query.filter_by(
        account_book_code=account_book_code.strip(),
        fiscal_year=fiscal_year,
        account_code=account_code.strip(),
        auxiliary_item_code=auxiliary_item_code.strip(),
    ).first()
    if not row:
        return jsonify({'success': False, 'message': '未找到该辅助核算配置'}), 404
    try:
        db.session.delete(row)
        db.session.commit()
        return jsonify({'success': True, 'message': '辅助核算已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除辅助核算失败: {str(e)}'}), 500
