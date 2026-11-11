# 凭证查询接口
import importlib

from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_, or_
from Auth.auth import token_required
from services.voucher_entry_service import (
    VoucherEntryError,
    create_manual_voucher,
    suggest_next_voucher_number,
)
from Model import (
    GLVoucher,
    GLVoucherEntry,
    GLVoucherEntryAuxiliary,
    GLVoucherType,
    AccountBook,
    AccountBookFiscalYear,
    CustomArchiveItem,
    CustomArchiveValue,
    db,
)

vouchers_bp = Blueprint('vouchers', __name__)


def _resolve_entry_auxiliary_values(account_book_code, fiscal_year, period_number, voucher_number, entry_line_number, account_code):
    """
    辅助项展示名解析：
    1) gl_voucher_entry_auxiliary.auxiliary_item_name 为辅助项分类；
    2) 在 custom_archive_item 中匹配得 archive_item_code（先 archive_item_name，再 archive_item_code）；
    3) 在 custom_archive_value 中按 archive_item_code + auxiliary_value(作 archive_value_code) 取 archive_value_name。

    无分类名、无档案项或值时退回 auxiliary_value。多个辅助项用 \\ 拼接。
    account_code 入参仅兼容旧调用，此处不再查 account_auxiliary。
    """
    _ = account_code
    aux_records = GLVoucherEntryAuxiliary.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        period_number=period_number,
        voucher_number=voucher_number,
        entry_line_number=entry_line_number
    ).order_by(GLVoucherEntryAuxiliary.auxiliary_item_sequence.asc()).all()

    if not aux_records:
        return None

    names = []
    for aux in aux_records:
        category = (aux.auxiliary_item_name or '').strip()
        aux_val = (aux.auxiliary_value or '').strip()
        if not category:
            names.append(aux_val)
            continue

        cai = CustomArchiveItem.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_name=category,
            status=1
        ).first()
        if not cai:
            cai = CustomArchiveItem.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                archive_item_code=category,
                status=1
            ).first()
        if not cai:
            names.append(aux_val)
            continue

        resolved_code = cai.archive_item_code
        cav = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=resolved_code,
            archive_value_code=aux_val,
            status=1
        ).first()
        if cav and cav.archive_value_name is not None and str(cav.archive_value_name).strip() != '':
            names.append(cav.archive_value_name)
        else:
            names.append(aux_val)

    return '\\'.join(names) if names else None


@vouchers_bp.route('/api/voucher_types', methods=['GET'])
@token_required
def list_voucher_types(current_user):
    """
    凭证类型列表接口

    查询参数：
    - account_book_code (string, 必填) - 账套编码
    - fiscal_year (number, 必填) - 会计年度
    """
    try:
        account_book_code = request.args.get('account_book_code', '').strip()
        fiscal_year = request.args.get('fiscal_year', type=int)

        if not account_book_code:
            return jsonify({
                'success': False,
                'message': '账套编码（account_book_code）不能为空'
            }), 400

        if not fiscal_year:
            return jsonify({
                'success': False,
                'message': '会计年度（fiscal_year）不能为空'
            }), 400

        fiscal_year_obj = AccountBookFiscalYear.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).first()

        if not fiscal_year_obj:
            return jsonify({
                'success': False,
                'message': f'未找到账套 {account_book_code} 下会计年度 {fiscal_year}'
            }), 404

        types = GLVoucherType.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).order_by(GLVoucherType.voucher_type_code.asc()).all()

        return jsonify({
            'success': True,
            'items': [t.to_dict() for t in types]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取凭证类型列表失败: {str(e)}'
        }), 500


@vouchers_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/voucher_types', methods=['GET'])
@token_required
def list_voucher_types_by_account_book(current_user, account_book_code, fiscal_year):
    """凭证类型列表接口（通过路径参数）"""
    request.args = request.args.copy()
    request.args['account_book_code'] = account_book_code
    request.args['fiscal_year'] = str(fiscal_year)
    return list_voucher_types(current_user)


@vouchers_bp.route('/api/vouchers', methods=['GET'])
@token_required
def list_vouchers(current_user):
    """
    凭证列表查询接口
    
    查询参数：
    - account_book_code (string, 必填) - 账套编码
    - fiscal_year (number, 必填) - 会计年度
    - month_start (number, 可选) - 会计月起始（1-12）
    - month_end (number, 可选) - 会计月结束（1-12）
    - voucher_no (string, 可选) - 凭证号（支持模糊查询）
    - summary (string, 可选) - 摘要（支持模糊查询）
    - page (number, 默认1) - 页码
    - page_size (number, 默认10) - 每页数量
    """
    try:
        # 获取必填参数
        account_book_code = request.args.get('account_book_code', '').strip()
        fiscal_year = request.args.get('fiscal_year', type=int)
        
        if not account_book_code:
            return jsonify({
                'success': False,
                'message': '账套编码（account_book_code）不能为空'
            }), 400
        
        if not fiscal_year:
            return jsonify({
                'success': False,
                'message': '会计年度（fiscal_year）不能为空'
            }), 400
        
        # 验证账套和年度是否存在
        fiscal_year_obj = AccountBookFiscalYear.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).first()
        
        if not fiscal_year_obj:
            return jsonify({
                'success': False,
                'message': f'未找到账套 {account_book_code} 下会计年度 {fiscal_year}'
            }), 404
        
        # 获取账套名称
        account_book = AccountBook.query.get(account_book_code)
        account_book_name = account_book.account_book_name if account_book else account_book_code
        
        # 获取可选参数
        month_start = request.args.get('month_start', type=int)
        month_end = request.args.get('month_end', type=int)
        voucher_no = request.args.get('voucher_no', '').strip()
        summary = request.args.get('summary', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        
        # 参数验证
        if page < 1:
            page = 1
        if page_size not in [10, 20, 50, 100]:
            page_size = 10
        
        if month_start is not None and (month_start < 1 or month_start > 12):
            return jsonify({
                'success': False,
                'message': 'month_start 必须在 1-12 之间'
            }), 400
        
        if month_end is not None and (month_end < 1 or month_end > 12):
            return jsonify({
                'success': False,
                'message': 'month_end 必须在 1-12 之间'
            }), 400
        
        if month_start is not None and month_end is not None and month_start > month_end:
            return jsonify({
                'success': False,
                'message': 'month_start 不能大于 month_end'
            }), 400
        
        # 构建查询
        query = GLVoucher.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        )
        
        # 会计月份筛选
        if month_start is not None:
            query = query.filter(GLVoucher.period_number >= month_start)
        if month_end is not None:
            query = query.filter(GLVoucher.period_number <= month_end)
        
        # 凭证号筛选（模糊查询）
        if voucher_no:
            query = query.filter(GLVoucher.voucher_number.like(f'%{voucher_no}%'))
        
        # 摘要筛选（模糊查询）
        if summary:
            query = query.filter(GLVoucher.summary.like(f'%{summary}%'))
        
        # 排序：按期间号、凭证号排序
        query = query.order_by(
            GLVoucher.period_number.asc(),
            GLVoucher.voucher_number.asc()
        )
        
        # 分页
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        # 获取每个凭证的借贷金额汇总
        items = []
        for voucher in pagination.items:
            # 查询该凭证的所有分录行的借贷金额汇总
            debit_credit = db.session.query(
                func.sum(GLVoucherEntry.debit_amount).label('debit_total'),
                func.sum(GLVoucherEntry.credit_amount).label('credit_total')
            ).filter_by(
                account_book_code=voucher.account_book_code,
                fiscal_year=voucher.fiscal_year,
                period_number=voucher.period_number,
                voucher_number=voucher.voucher_number
            ).first()
            
            debit_amount = float(debit_credit.debit_total) if debit_credit.debit_total else 0.0
            credit_amount = float(debit_credit.credit_total) if debit_credit.credit_total else 0.0
            
            # 获取辅助项信息（从 gl_voucher_entry_auxiliary 表提取）
            aux_records = GLVoucherEntryAuxiliary.query.filter_by(
                account_book_code=voucher.account_book_code,
                fiscal_year=voucher.fiscal_year,
                period_number=voucher.period_number,
                voucher_number=voucher.voucher_number
            ).all()
            auxiliary_items = [r.auxiliary_item_name for r in aux_records if r.auxiliary_item_name]
            auxiliary_items_str = '; '.join(dict.fromkeys(auxiliary_items)) if auxiliary_items else None
            
            items.append({
                'account_book_code': voucher.account_book_code,
                'account_book_name': account_book_name,
                'fiscal_year': voucher.fiscal_year,
                'period_number': voucher.period_number,
                'voucher_no': voucher.voucher_number,
                'summary': voucher.summary,
                'debit_amount': debit_amount,
                'credit_amount': credit_amount,
                'auxiliary_items': auxiliary_items_str,
                'voucher_date': voucher.voucher_date,
                'voucher_type_code': voucher.voucher_type_code,
                'prepared_by': voucher.prepared_by,
                'reviewed_by': voucher.reviewed_by,
                'posted_by': voucher.posted_by,
                'voucher_status': voucher.voucher_status,
                'created_at': voucher.created_at.isoformat() if voucher.created_at else None
            })
        
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
            'message': f'获取凭证列表失败: {str(e)}'
        }), 500


@vouchers_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/vouchers', methods=['GET'])
@token_required
def list_vouchers_by_account_book(current_user, account_book_code, fiscal_year):
    """
    凭证列表查询接口（通过路径参数）
    
    查询参数：
    - month_start (number, 可选) - 会计月起始（1-12）
    - month_end (number, 可选) - 会计月结束（1-12）
    - voucher_no (string, 可选) - 凭证号（支持模糊查询）
    - summary (string, 可选) - 摘要（支持模糊查询）
    - page (number, 默认1) - 页码
    - page_size (number, 默认10) - 每页数量
    """
    # 将路径参数添加到request.args中，然后调用上面的函数
    request.args = request.args.copy()
    request.args['account_book_code'] = account_book_code
    request.args['fiscal_year'] = str(fiscal_year)
    return list_vouchers(current_user)


@vouchers_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/months', methods=['GET'])
@token_required
def list_months(current_user, account_book_code, fiscal_year):
    """
    会计月份数据接口
    
    获取指定账套和年度下已导入数据的会计月份列表
    """
    try:
        # 验证账套和年度是否存在
        fiscal_year_obj = AccountBookFiscalYear.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).first()
        
        if not fiscal_year_obj:
            return jsonify({
                'success': False,
                'message': f'未找到账套 {account_book_code} 下会计年度 {fiscal_year}'
            }), 404
        
        # 查询该账套和年度下所有有凭证的月份
        months_query = db.session.query(GLVoucher.period_number).filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).distinct().order_by(GLVoucher.period_number.asc())
        
        months = [row[0] for row in months_query.all()]
        
        return jsonify({
            'success': True,
            'months': months
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取会计月份列表失败: {str(e)}'
        }), 500


@vouchers_bp.route('/api/vouchers/<account_book_code>/<int:fiscal_year>/<int:period_number>/<voucher_number>', methods=['GET'])
@token_required
def get_voucher_detail(current_user, account_book_code, fiscal_year, period_number, voucher_number, *args, **kwargs):
    """
    凭证详情接口（通过路径参数）
    
    返回凭证的详细信息，包括凭证头和所有分录行
    """
    try:
        # 查询凭证
        voucher = GLVoucher.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            voucher_number=voucher_number
        ).first()
        
        if not voucher:
            return jsonify({
                'success': False,
                'message': f'未找到凭证: {account_book_code}/{fiscal_year}/{period_number}/{voucher_number}'
            }), 404
        
        # 获取账套名称
        account_book = AccountBook.query.get(account_book_code)
        account_book_name = account_book.account_book_name if account_book else account_book_code
        
        # 查询凭证的所有分录行
        entries = GLVoucherEntry.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            voucher_number=voucher_number
        ).order_by(GLVoucherEntry.entry_line_number.asc()).all()
        
        # 计算借贷金额汇总
        debit_credit = db.session.query(
            func.sum(GLVoucherEntry.debit_amount).label('debit_total'),
            func.sum(GLVoucherEntry.credit_amount).label('credit_total')
        ).filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            voucher_number=voucher_number
        ).first()
        
        debit_amount = float(debit_credit.debit_total) if debit_credit.debit_total else 0.0
        credit_amount = float(debit_credit.credit_total) if debit_credit.credit_total else 0.0
        
        # 构建返回数据：每条分录如有辅助项，解析 archive_value_name 用 \ 拼接
        voucher_data = voucher.to_dict()
        voucher_data['account_book_name'] = account_book_name
        voucher_data['debit_amount'] = debit_amount
        voucher_data['credit_amount'] = credit_amount

        entry_list = []
        for entry in entries:
            ed = entry.to_dict()
            aux_display = _resolve_entry_auxiliary_values(
                account_book_code, fiscal_year, period_number, voucher_number,
                entry.entry_line_number, entry.account_code
            )
            if aux_display:
                ed['auxiliary_item_values'] = aux_display
            entry_list.append(ed)
        voucher_data['entries'] = entry_list
        
        return jsonify({
            'success': True,
            'data': voucher_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取凭证详情失败: {str(e)}'
        }), 500


@vouchers_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/vouchers/<voucher_number>', methods=['GET'])
@token_required
def get_voucher_detail_by_account_book(current_user, account_book_code, fiscal_year, voucher_number):
    """
    凭证详情接口（通过账套路径，需要period_number参数）
    
    查询参数：
    - period_number (number, 必填) - 会计期间号（1-12）
    """
    try:
        period_number = request.args.get('period_number', type=int)
        
        if not period_number:
            return jsonify({
                'success': False,
                'message': '会计期间号（period_number）不能为空'
            }), 400
        
        return get_voucher_detail(current_user, account_book_code, fiscal_year, period_number, voucher_number)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取凭证详情失败: {str(e)}'
        }), 500


def _voucher_excel_import_handler(account_book_code: str, fiscal_year: int):
    """凭证明细 Excel 导入：multipart 字段 file。路径或表单提供账套、年度。"""
    try:
        importlib.import_module('openpyxl')
    except Exception:
        return jsonify({
            'success': False,
            'message': '缺少 openpyxl 依赖，请先安装：pip install openpyxl',
        }), 500

    ab = (account_book_code or '').strip()
    if not ab:
        return jsonify({'success': False, 'message': '账套编码（account_book_code）不能为空'}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请上传 Excel 文件（表单字段名：file）'}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    filename = (f.filename or '').lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xlsm')):
        return jsonify({'success': False, 'message': '仅支持 .xlsx / .xlsm 文件'}), 400

    from services.voucher_detail_excel_import import run_voucher_detail_excel_import

    result = run_voucher_detail_excel_import(f.read(), ab, fiscal_year)
    if result.get('success'):
        return jsonify(result), 200
    msg = result.get('message') or '导入失败'
    status = 404 if '未找到账套年度' in msg else 400
    return jsonify(result), status


@vouchers_bp.route('/api/vouchers/import_excel', methods=['POST'])
@token_required
def import_vouchers_excel_flat(current_user):
    """
    从「凭证导入临时表」样式 Excel 导入 gl_voucher / gl_voucher_entry / gl_voucher_entry_auxiliary。
    表单：file、account_book_code、fiscal_year
    """
    account_book_code = request.form.get('account_book_code', '')
    raw = request.form.get('fiscal_year')
    if raw in (None, ''):
        return jsonify({'success': False, 'message': '会计年度（fiscal_year）不能为空'}), 400
    try:
        fiscal_year = int(raw)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': '会计年度必须为整数'}), 400
    return _voucher_excel_import_handler(account_book_code, fiscal_year)


@vouchers_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/vouchers/import_excel',
    methods=['POST'],
)
@token_required
def import_vouchers_excel_nested(current_user, account_book_code, fiscal_year):
    """同上，账套、年度在 URL 中。"""
    return _voucher_excel_import_handler(account_book_code, fiscal_year)


def _voucher_entry_error_response(exc: VoucherEntryError):
    return jsonify({
        'success': False,
        'message': exc.message,
        'errors': exc.errors,
    }), exc.status


def _create_voucher_handler(current_user, payload, account_book_code=None, fiscal_year=None):
    data = dict(payload or {})
    if account_book_code is not None:
        data['account_book_code'] = account_book_code
    if fiscal_year is not None:
        data['fiscal_year'] = fiscal_year
    try:
        saved = create_manual_voucher(data, default_prepared_by=getattr(current_user, 'username', None))
    except VoucherEntryError as exc:
        return _voucher_entry_error_response(exc)
    except Exception as exc:
        return jsonify({
            'success': False,
            'message': f'保存凭证失败: {exc}',
        }), 500
    return jsonify({
        'success': True,
        'message': '凭证保存成功',
        'data': saved,
    }), 201


@vouchers_bp.route('/api/vouchers/next_number', methods=['GET'])
@token_required
def next_voucher_number(current_user):
    """按账套、年度、期间、凭证类型给出下一张凭证号。"""
    account_book_code = request.args.get('account_book_code', '')
    fiscal_year = request.args.get('fiscal_year', type=int)
    period_number = request.args.get('period_number', type=int)
    voucher_type_code = request.args.get('voucher_type_code', '')
    if fiscal_year is None or period_number is None:
        return jsonify({
            'success': False,
            'message': '会计年度和会计期间不能为空',
        }), 400
    try:
        number = suggest_next_voucher_number(
            account_book_code,
            fiscal_year,
            period_number,
            voucher_type_code,
        )
    except VoucherEntryError as exc:
        return _voucher_entry_error_response(exc)
    return jsonify({
        'success': True,
        'voucher_number': number,
    })


@vouchers_bp.route('/api/vouchers', methods=['POST'])
@token_required
def create_voucher(current_user):
    """
    手工录入记账凭证。
    写入 gl_voucher、gl_voucher_entry、gl_voucher_entry_auxiliary。
    保存前检查：末级科目、有辅助核算时必须填写、借贷金额相等。
    不重算科目余额。
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({'success': False, 'message': '请求体须为 JSON'}), 400
    return _create_voucher_handler(current_user, payload)


@vouchers_bp.route(
    '/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/vouchers',
    methods=['POST'],
)
@token_required
def create_voucher_by_account_book(current_user, account_book_code, fiscal_year):
    """同上，账套与年度在路径中。"""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({'success': False, 'message': '请求体须为 JSON'}), 400
    return _create_voucher_handler(current_user, payload, account_book_code, fiscal_year)
