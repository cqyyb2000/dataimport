# 账套管理接口（主表 account_book + 从表 account_book_fiscal_year）
from flask import Blueprint, jsonify, request
from Auth.auth import token_required
from Model.dataCls import AccountBook, AccountBookFiscalYear, db

account_book_bp = Blueprint('account_book', __name__)

# ---------- 账套主表 CRUD ----------

@account_book_bp.route('/api/account_books', methods=['GET'])
@token_required
def list_account_books(current_user):
    """分页查询账套列表，支持按账套编码、名称、会计核算单位筛选"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in [10, 20, 50, 100]:
            page_size = 10

        query = AccountBook.query
        code = request.args.get('account_book_code', '').strip()
        name = request.args.get('account_book_name', '').strip()
        entity = request.args.get('accounting_entity', '').strip()
        status = request.args.get('status', type=int)
        if code:
            query = query.filter(AccountBook.account_book_code.like(f'%{code}%'))
        if name:
            query = query.filter(AccountBook.account_book_name.like(f'%{name}%'))
        if entity:
            query = query.filter(AccountBook.accounting_entity.like(f'%{entity}%'))
        if status is not None:
            query = query.filter(AccountBook.status == status)

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        items = [item.to_dict() for item in pagination.items]
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取账套列表失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books/<account_book_code>', methods=['GET'])
@token_required
def get_account_book(current_user, account_book_code):
    """获取单个账套详情（含已导入年度列表 imported_fiscal_years）"""
    try:
        item = AccountBook.query.get(account_book_code)
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到账套: {account_book_code}'
            }), 404
        return jsonify({
            'success': True,
            'data': item.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取账套详情失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books', methods=['POST'])
@token_required
def create_account_book(current_user):
    """创建账套（主表字段，不含会计年度；会计年度通过从表接口维护）"""
    try:
        data = request.json
        code = (data.get('account_book_code') or '').strip()
        if not code:
            return jsonify({
                'success': False,
                'message': '账套编码不能为空'
            }), 400
        if AccountBook.query.get(code):
            return jsonify({
                'success': False,
                'message': f'账套编码已存在: {code}'
            }), 400

        name = (data.get('account_book_name') or '').strip()
        entity = (data.get('accounting_entity') or '').strip()
        unit_type = (data.get('unit_type') or '').strip()
        base_currency = (data.get('base_currency') or '').strip()
        standard_version = (data.get('standard_version') or '').strip()
        if not name:
            return jsonify({'success': False, 'message': '账套名称不能为空'}), 400
        if not entity:
            return jsonify({'success': False, 'message': '会计核算单位不能为空'}), 400
        if not unit_type:
            return jsonify({'success': False, 'message': '单位类型不能为空'}), 400
        if not base_currency:
            return jsonify({'success': False, 'message': '本位币不能为空'}), 400
        if not standard_version:
            return jsonify({'success': False, 'message': '标准版本号不能为空'}), 400

        item = AccountBook(
            account_book_code=code,
            account_book_name=name,
            accounting_entity=entity,
            organization_code=(data.get('organization_code') or '').strip() or None,
            unit_type=unit_type,
            industry=(data.get('industry') or '').strip() or None,
            administrative_division_code=(data.get('administrative_division_code') or '').strip() or None,
            budget_management_level=(data.get('budget_management_level') or '').strip() or None,
            funding_source=(data.get('funding_source') or '').strip() or None,
            developer=(data.get('developer') or '').strip() or None,
            version=(data.get('version') or '').strip() or None,
            base_currency=base_currency,
            standard_version=standard_version,
            default_fiscal_year=data.get('default_fiscal_year'),
            remark=(data.get('remark') or '').strip() or None,
            status=data.get('status', 1)
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '账套创建成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建账套失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books/<account_book_code>', methods=['PUT'])
@token_required
def update_account_book(current_user, account_book_code):
    """更新账套（账套编码不可修改）"""
    try:
        item = AccountBook.query.get(account_book_code)
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到账套: {account_book_code}'
            }), 404

        data = request.json
        if 'account_book_name' in data:
            v = (data.get('account_book_name') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '账套名称不能为空'}), 400
            item.account_book_name = v
        if 'accounting_entity' in data:
            v = (data.get('accounting_entity') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '会计核算单位不能为空'}), 400
            item.accounting_entity = v
        if 'organization_code' in data:
            item.organization_code = (data.get('organization_code') or '').strip() or None
        if 'unit_type' in data:
            v = (data.get('unit_type') or '').strip()
            if v:
                item.unit_type = v
        if 'industry' in data:
            item.industry = (data.get('industry') or '').strip() or None
        if 'administrative_division_code' in data:
            item.administrative_division_code = (data.get('administrative_division_code') or '').strip() or None
        if 'budget_management_level' in data:
            item.budget_management_level = (data.get('budget_management_level') or '').strip() or None
        if 'funding_source' in data:
            item.funding_source = (data.get('funding_source') or '').strip() or None
        if 'developer' in data:
            item.developer = (data.get('developer') or '').strip() or None
        if 'version' in data:
            item.version = (data.get('version') or '').strip() or None
        if 'base_currency' in data:
            v = (data.get('base_currency') or '').strip()
            if v:
                item.base_currency = v
        if 'standard_version' in data:
            v = (data.get('standard_version') or '').strip()
            if v:
                item.standard_version = v
        if 'default_fiscal_year' in data:
            item.default_fiscal_year = data.get('default_fiscal_year')
        if 'remark' in data:
            item.remark = (data.get('remark') or '').strip() or None
        if 'status' in data:
            item.status = data.get('status', 1)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': '账套更新成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新账套失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books/<account_book_code>', methods=['DELETE'])
@token_required
def delete_account_book(current_user, account_book_code):
    """删除账套（级联删除从表会计年度）"""
    try:
        item = AccountBook.query.get(account_book_code)
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到账套: {account_book_code}'
            }), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '账套已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除账套失败: {str(e)}'
        }), 500


# ---------- 账套—会计年度（从表）接口 ----------

@account_book_bp.route('/api/account_books/<account_book_code>/fiscal_years', methods=['GET'])
@token_required
def list_fiscal_years(current_user, account_book_code):
    """获取某账套的会计年度列表（从表）"""
    try:
        if not AccountBook.query.get(account_book_code):
            return jsonify({
                'success': False,
                'message': f'未找到账套: {account_book_code}'
            }), 404
        rows = AccountBookFiscalYear.query.filter_by(account_book_code=account_book_code).order_by(AccountBookFiscalYear.fiscal_year).all()
        items = [
            {
                'account_book_code': r.account_book_code,
                'fiscal_year': r.fiscal_year,
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in rows
        ]
        return jsonify({
            'success': True,
            'items': items,
            'total': len(items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取会计年度列表失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books/<account_book_code>/fiscal_years', methods=['POST'])
@token_required
def add_fiscal_year(current_user, account_book_code):
    """为某账套添加会计年度（从表）"""
    try:
        if not AccountBook.query.get(account_book_code):
            return jsonify({
                'success': False,
                'message': f'未找到账套: {account_book_code}'
            }), 404
        data = request.json
        fiscal_year = data.get('fiscal_year')
        if fiscal_year is None:
            return jsonify({
                'success': False,
                'message': '请提供 fiscal_year（4位整数，如 2021）'
            }), 400
        try:
            fiscal_year = int(fiscal_year)
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'message': 'fiscal_year 必须为4位整数'
            }), 400
        if fiscal_year < 1990 or fiscal_year > 2100:
            return jsonify({
                'success': False,
                'message': 'fiscal_year 应在 1990～2100 之间'
            }), 400

        existing = AccountBookFiscalYear.query.filter_by(account_book_code=account_book_code, fiscal_year=fiscal_year).first()
        if existing:
            return jsonify({
                'success': True,
                'message': '该年度已存在',
                'data': {
                    'account_book_code': existing.account_book_code,
                    'fiscal_year': existing.fiscal_year,
                    'created_at': existing.created_at.isoformat() if existing.created_at else None
                }
            })

        row = AccountBookFiscalYear(account_book_code=account_book_code, fiscal_year=fiscal_year)
        db.session.add(row)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '会计年度已添加',
            'data': {
                'account_book_code': row.account_book_code,
                'fiscal_year': row.fiscal_year,
                'created_at': row.created_at.isoformat() if row.created_at else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'添加会计年度失败: {str(e)}'
        }), 500


@account_book_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>', methods=['DELETE'])
@token_required
def remove_fiscal_year(current_user, account_book_code, fiscal_year):
    """删除某账套下某会计年度（从表）"""
    try:
        row = AccountBookFiscalYear.query.filter_by(account_book_code=account_book_code, fiscal_year=fiscal_year).first()
        if not row:
            return jsonify({
                'success': False,
                'message': f'未找到账套 {account_book_code} 下会计年度 {fiscal_year}'
            }), 404
        db.session.delete(row)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'已删除会计年度 {fiscal_year}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除会计年度失败: {str(e)}'
        }), 500
