# 自定义档案管理接口（custom_archive_item + custom_archive_value）
import io
import importlib

from flask import Blueprint, jsonify, request
from Auth.auth import token_required
from Model import (
    CustomArchiveItem,
    CustomArchiveValue,
    AccountBookFiscalYear,
    Account,
    AccountAuxiliary,
    db,
)

custom_archive_bp = Blueprint('custom_archive', __name__)


# ========== 自定义档案项（CustomArchiveItem）CRUD ==========

@custom_archive_bp.route('/api/custom_archive_items', methods=['GET'])
@token_required
def list_custom_archive_items(current_user):
    """分页查询自定义档案项列表，支持按账套编码、年度、档案编码、名称、状态筛选"""
    try:
        all_flag = request.args.get('all', '0') == '1'
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in [10, 20, 50, 100]:
            page_size = 1000

        query = CustomArchiveItem.query

        # 筛选条件
        account_book_code = request.args.get('account_book_code', '').strip()
        fiscal_year = request.args.get('fiscal_year', type=int)
        archive_item_code = request.args.get('archive_item_code', '').strip()
        archive_item_name = request.args.get('archive_item_name', '').strip()
        status = request.args.get('status', type=int)

        if account_book_code:
            query = query.filter(CustomArchiveItem.account_book_code == account_book_code)
        if fiscal_year:
            query = query.filter(CustomArchiveItem.fiscal_year == fiscal_year)
        if archive_item_code:
            query = query.filter(CustomArchiveItem.archive_item_code.like(f'%{archive_item_code}%'))
        if archive_item_name:
            query = query.filter(CustomArchiveItem.archive_item_name.like(f'%{archive_item_name}%'))
        if status is not None:
            query = query.filter(CustomArchiveItem.status == status)

        # 排序
        query = query.order_by(
            CustomArchiveItem.account_book_code,
            CustomArchiveItem.fiscal_year,
            CustomArchiveItem.archive_item_code
        )

        if all_flag:
            items = [item.to_dict() for item in query.all()]
            total = len(items)
            return jsonify({
                'success': True,
                'items': items,
                'total': total,
                'page': 1,
                'page_size': total,
                'total_pages': 1,
                'all': True
            })

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        items = [item.to_dict() for item in pagination.items]
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages,
            'all': False
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取自定义档案项列表失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_items/<account_book_code>/<int:fiscal_year>/<archive_item_code>', methods=['GET'])
@token_required
def get_custom_archive_item(current_user, account_book_code, fiscal_year, archive_item_code):
    """获取单个自定义档案项详情"""
    try:
        item = CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案项: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 404
        return jsonify({
            'success': True,
            'data': item.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取自定义档案项详情失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_items', methods=['POST'])
@token_required
def create_custom_archive_item(current_user):
    """创建自定义档案项"""
    try:
        data = request.json

        # 必填字段验证
        account_book_code = (data.get('account_book_code') or '').strip()
        fiscal_year = data.get('fiscal_year')
        archive_item_code = (data.get('archive_item_code') or '').strip()
        archive_item_name = (data.get('archive_item_name') or '').strip()

        if not account_book_code:
            return jsonify({'success': False, 'message': '账套编码不能为空'}), 400
        if not fiscal_year:
            return jsonify({'success': False, 'message': '会计年度不能为空'}), 400
        try:
            fiscal_year = int(fiscal_year)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '会计年度必须为4位整数'}), 400
        if fiscal_year < 1990 or fiscal_year > 2100:
            return jsonify({'success': False, 'message': '会计年度应在 1990～2100 之间'}), 400
        if not archive_item_code:
            return jsonify({'success': False, 'message': '档案编码不能为空'}), 400
        if not archive_item_name:
            return jsonify({'success': False, 'message': '档案名称不能为空'}), 400

        # 检查账套年度是否存在
        if not AccountBookFiscalYear.query.filter_by(account_book_code=account_book_code, fiscal_year=fiscal_year).first():
            return jsonify({
                'success': False,
                'message': f'账套年度不存在: {account_book_code}/{fiscal_year}'
            }), 400

        # 检查是否已存在
        if CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code)):
            return jsonify({
                'success': False,
                'message': f'自定义档案项已存在: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 400

        item = CustomArchiveItem(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=archive_item_code,
            archive_item_name=archive_item_name,
            archive_item_desc=(data.get('archive_item_desc') or '').strip() or None,
            has_hierarchy=data.get('has_hierarchy', 1),
            archive_code_rule=(data.get('archive_code_rule') or '').strip() or None,
            remark=(data.get('remark') or '').strip() or None,
            status=data.get('status', 1)
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案项创建成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建自定义档案项失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_items/<account_book_code>/<int:fiscal_year>/<archive_item_code>', methods=['PUT'])
@token_required
def update_custom_archive_item(current_user, account_book_code, fiscal_year, archive_item_code):
    """更新自定义档案项（主键不可修改）"""
    try:
        item = CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案项: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 404

        data = request.json

        if 'archive_item_name' in data:
            v = (data.get('archive_item_name') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '档案名称不能为空'}), 400
            item.archive_item_name = v
        if 'archive_item_desc' in data:
            item.archive_item_desc = (data.get('archive_item_desc') or '').strip() or None
        if 'has_hierarchy' in data:
            item.has_hierarchy = data.get('has_hierarchy', 1)
        if 'archive_code_rule' in data:
            item.archive_code_rule = (data.get('archive_code_rule') or '').strip() or None
        if 'remark' in data:
            item.remark = (data.get('remark') or '').strip() or None
        if 'status' in data:
            item.status = data.get('status', 1)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案项更新成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新自定义档案项失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_items/<account_book_code>/<int:fiscal_year>/<archive_item_code>', methods=['DELETE'])
@token_required
def delete_custom_archive_item(current_user, account_book_code, fiscal_year, archive_item_code):
    """删除自定义档案项（级联删除下属档案值）"""
    try:
        item = CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案项: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案项已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除自定义档案项失败: {str(e)}'
        }), 500


# ========== 自定义档案值（CustomArchiveValue）CRUD ==========

@custom_archive_bp.route('/api/custom_archive_values', methods=['GET'])
@token_required
def list_custom_archive_values(current_user):
    """分页查询自定义档案值列表，支持按账套编码、年度、档案编码、值编码、名称、状态筛选"""
    try:
        all_flag = request.args.get('all', '0') == '1'
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in [10, 20, 50, 100]:
            page_size = 10

        query = CustomArchiveValue.query

        # 筛选条件
        account_book_code = request.args.get('account_book_code', '').strip()
        fiscal_year = request.args.get('fiscal_year', type=int)
        archive_item_code = request.args.get('archive_item_code', '').strip()
        archive_value_code = request.args.get('archive_value_code', '').strip()
        archive_value_name = request.args.get('archive_value_name', '').strip()
        parent_value_code = request.args.get('parent_value_code', '').strip()
        level = request.args.get('level', type=int)
        status = request.args.get('status', type=int)

        if account_book_code:
            query = query.filter(CustomArchiveValue.account_book_code == account_book_code)
        if fiscal_year:
            query = query.filter(CustomArchiveValue.fiscal_year == fiscal_year)
        if archive_item_code:
            query = query.filter(CustomArchiveValue.archive_item_code == archive_item_code)
        if archive_value_code:
            query = query.filter(CustomArchiveValue.archive_value_code.like(f'%{archive_value_code}%'))
        if archive_value_name:
            query = query.filter(CustomArchiveValue.archive_value_name.like(f'%{archive_value_name}%'))
        if parent_value_code:
            query = query.filter(CustomArchiveValue.parent_value_code == parent_value_code)
        if level is not None:
            query = query.filter(CustomArchiveValue.level == level)
        if status is not None:
            query = query.filter(CustomArchiveValue.status == status)

        # 排序
        query = query.order_by(
            CustomArchiveValue.account_book_code,
            CustomArchiveValue.fiscal_year,
            CustomArchiveValue.archive_item_code,
            CustomArchiveValue.archive_value_code
        )

        if all_flag:
            items = [item.to_dict() for item in query.all()]
            total = len(items)
            return jsonify({
                'success': True,
                'items': items,
                'total': total,
                'page': 1,
                'page_size': total,
                'total_pages': 1,
                'all': True
            })

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        items = [item.to_dict() for item in pagination.items]
        return jsonify({
            'success': True,
            'items': items,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages,
            'all': False
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取自定义档案值列表失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_values/<account_book_code>/<int:fiscal_year>/<archive_item_code>/<archive_value_code>', methods=['GET'])
@token_required
def get_custom_archive_value(current_user, account_book_code, fiscal_year, archive_item_code, archive_value_code):
    """获取单个自定义档案值详情"""
    try:
        item = CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, archive_value_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案值: {account_book_code}/{fiscal_year}/{archive_item_code}/{archive_value_code}'
            }), 404
        return jsonify({
            'success': True,
            'data': item.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取自定义档案值详情失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_values', methods=['POST'])
@token_required
def create_custom_archive_value(current_user):
    """创建自定义档案值"""
    try:
        data = request.json

        # 必填字段验证
        account_book_code = (data.get('account_book_code') or '').strip()
        fiscal_year = data.get('fiscal_year')
        archive_item_code = (data.get('archive_item_code') or '').strip()
        archive_value_code = (data.get('archive_value_code') or '').strip()
        archive_value_name = (data.get('archive_value_name') or '').strip()
        level = data.get('level')

        if not account_book_code:
            return jsonify({'success': False, 'message': '账套编码不能为空'}), 400
        if not fiscal_year:
            return jsonify({'success': False, 'message': '会计年度不能为空'}), 400
        try:
            fiscal_year = int(fiscal_year)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '会计年度必须为4位整数'}), 400
        if fiscal_year < 1990 or fiscal_year > 2100:
            return jsonify({'success': False, 'message': '会计年度应在 1990～2100 之间'}), 400
        if not archive_item_code:
            return jsonify({'success': False, 'message': '档案编码不能为空'}), 400
        if not archive_value_code:
            return jsonify({'success': False, 'message': '档案值编码不能为空'}), 400
        if not archive_value_name:
            return jsonify({'success': False, 'message': '档案值名称不能为空'}), 400
        if level is None:
            return jsonify({'success': False, 'message': '档案值级次不能为空'}), 400
        try:
            level = int(level)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '档案值级次必须为整数'}), 400

        # 检查档案项是否存在
        if not CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code)):
            return jsonify({
                'success': False,
                'message': f'自定义档案项不存在: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 400

        # 检查是否已存在
        if CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, archive_value_code)):
            return jsonify({
                'success': False,
                'message': f'自定义档案值已存在: {account_book_code}/{fiscal_year}/{archive_item_code}/{archive_value_code}'
            }), 400

        # 检查父节点是否存在（如果指定了父节点）
        parent_value_code = (data.get('parent_value_code') or '').strip() or None
        if parent_value_code:
            if not CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, parent_value_code)):
                return jsonify({
                    'success': False,
                    'message': f'父节点不存在: {parent_value_code}'
                }), 400

        item = CustomArchiveValue(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=archive_item_code,
            archive_value_code=archive_value_code,
            archive_value_name=archive_value_name,
            archive_value_desc=(data.get('archive_value_desc') or '').strip() or None,
            parent_value_code=parent_value_code,
            level=level,
            remark=(data.get('remark') or '').strip() or None,
            status=data.get('status', 1)
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案值创建成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建自定义档案值失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_values/<account_book_code>/<int:fiscal_year>/<archive_item_code>/<archive_value_code>', methods=['PUT'])
@token_required
def update_custom_archive_value(current_user, account_book_code, fiscal_year, archive_item_code, archive_value_code):
    """更新自定义档案值（主键不可修改）"""
    try:
        item = CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, archive_value_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案值: {account_book_code}/{fiscal_year}/{archive_item_code}/{archive_value_code}'
            }), 404

        data = request.json

        if 'archive_value_name' in data:
            v = (data.get('archive_value_name') or '').strip()
            if not v:
                return jsonify({'success': False, 'message': '档案值名称不能为空'}), 400
            item.archive_value_name = v
        if 'archive_value_desc' in data:
            item.archive_value_desc = (data.get('archive_value_desc') or '').strip() or None
        if 'parent_value_code' in data:
            parent_value_code = (data.get('parent_value_code') or '').strip() or None
            if parent_value_code:
                # 检查父节点是否存在
                if not CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, parent_value_code)):
                    return jsonify({
                        'success': False,
                        'message': f'父节点不存在: {parent_value_code}'
                    }), 400
                # 检查是否形成循环引用（不能将自己或后代设为父节点）
                if parent_value_code == archive_value_code:
                    return jsonify({
                        'success': False,
                        'message': '不能将自己设为父节点'
                    }), 400
            item.parent_value_code = parent_value_code
        if 'level' in data:
            level = data.get('level')
            if level is None:
                return jsonify({'success': False, 'message': '档案值级次不能为空'}), 400
            try:
                level = int(level)
            except (TypeError, ValueError):
                return jsonify({'success': False, 'message': '档案值级次必须为整数'}), 400
            item.level = level
        if 'remark' in data:
            item.remark = (data.get('remark') or '').strip() or None
        if 'status' in data:
            item.status = data.get('status', 1)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案值更新成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新自定义档案值失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_values/<account_book_code>/<int:fiscal_year>/<archive_item_code>/<archive_value_code>', methods=['DELETE'])
@token_required
def delete_custom_archive_value(current_user, account_book_code, fiscal_year, archive_item_code, archive_value_code):
    """删除自定义档案值"""
    try:
        item = CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, archive_value_code))
        if not item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案值: {account_book_code}/{fiscal_year}/{archive_item_code}/{archive_value_code}'
            }), 404

        # 检查是否有子节点
        children = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=archive_item_code,
            parent_value_code=archive_value_code
        ).first()
        if children:
            return jsonify({
                'success': False,
                'message': '该档案值下有子节点，请先删除子节点'
            }), 400

        db.session.delete(item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '自定义档案值已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除自定义档案值失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/custom_archive_values/import_excel', methods=['POST'])
@token_required
def import_custom_archive_values_excel(current_user):
    """
    Excel 导入 custom_archive_value。
    表头要求（同一行）至少包含：编码、名称；可选：助记码。

    表单字段（multipart/form-data）：
    - file: Excel 文件（.xlsx/.xlsm）
    - account_book_code: 账套编码（必填）
    - fiscal_year: 会计年度（必填）
    - archive_item_code: 档案编码（必填）
    - mode: append|replace（默认 append）
    """
    try:
        # 使用动态导入，避免静态分析器在未安装依赖时提示无法解析导入
        openpyxl_module = importlib.import_module('openpyxl')
        load_workbook = openpyxl_module.load_workbook
    except Exception:
        return jsonify({
            'success': False,
            'message': '缺少 openpyxl 依赖，请先安装：pip install openpyxl'
        }), 500

    try:
        account_book_code = (request.form.get('account_book_code') or '').strip()
        fiscal_year_raw = request.form.get('fiscal_year')
        archive_item_code = (request.form.get('archive_item_code') or '').strip()
        mode = (request.form.get('mode') or 'append').strip().lower()

        if not account_book_code:
            return jsonify({'success': False, 'message': '账套编码不能为空'}), 400
        if not fiscal_year_raw:
            return jsonify({'success': False, 'message': '会计年度不能为空'}), 400
        try:
            fiscal_year = int(fiscal_year_raw)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '会计年度必须为4位整数'}), 400
        if fiscal_year < 1990 or fiscal_year > 2100:
            return jsonify({'success': False, 'message': '会计年度应在 1990～2100 之间'}), 400
        if not archive_item_code:
            return jsonify({'success': False, 'message': '档案编码不能为空'}), 400
        if mode not in ('append', 'replace'):
            return jsonify({'success': False, 'message': 'mode 仅支持 append 或 replace'}), 400

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请上传Excel文件（字段名：file）'}), 400
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400
        filename = file.filename.lower()
        if not (filename.endswith('.xlsx') or filename.endswith('.xlsm')):
            return jsonify({'success': False, 'message': '仅支持 .xlsx / .xlsm 文件'}), 400

        # 检查档案项是否存在
        archive_item = CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code))
        if not archive_item:
            return jsonify({
                'success': False,
                'message': f'自定义档案项不存在: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 400

        # 读取 Excel（默认第一张表）
        wb = load_workbook(filename=io.BytesIO(file.read()), data_only=True, read_only=True)
        ws = wb.worksheets[0]

        # 在前 10 行内自动识别表头，必须包含 编码/名称
        header_row_no = None
        idx_code = -1
        idx_name = -1
        idx_memo = -1
        for row_no, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), start=1):
            headers = [str(v).strip() if v is not None else '' for v in row]
            if '编码' in headers and '名称' in headers:
                header_row_no = row_no
                idx_code = headers.index('编码')
                idx_name = headers.index('名称')
                idx_memo = headers.index('助记码') if '助记码' in headers else -1
                break

        if header_row_no is None:
            return jsonify({'success': False, 'message': '表头必须包含“编码”“名称”'}), 400

        rows = []
        seen_codes = set()
        for row in ws.iter_rows(min_row=header_row_no + 1, values_only=True):
            code = str(row[idx_code]).strip() if idx_code < len(row) and row[idx_code] is not None else ''
            name = str(row[idx_name]).strip() if idx_name < len(row) and row[idx_name] is not None else ''
            memo = str(row[idx_memo]).strip() if idx_memo >= 0 and idx_memo < len(row) and row[idx_memo] is not None else ''

            # 空行跳过
            if not code and not name and not memo:
                continue
            if not code or not name:
                return jsonify({
                    'success': False,
                    'message': f'存在编码或名称为空的行：编码={code or ""}，名称={name or ""}'
                }), 400
            if code in seen_codes:
                return jsonify({'success': False, 'message': f'Excel 中存在重复编码：{code}'}), 400
            seen_codes.add(code)
            rows.append({'code': code, 'name': name, 'memo': memo})

        if not rows:
            return jsonify({'success': False, 'message': '未读取到有效数据行'}), 400

        # 预取现有数据
        existing_values = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=archive_item_code
        ).all()

        existing_level_map = {v.archive_value_code: int(v.level) for v in existing_values}
        existing_code_set = set(existing_level_map.keys())
        import_code_set = {r['code'] for r in rows}

        # replace: 先清空该档案项下所有值
        if mode == 'replace':
            CustomArchiveValue.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                archive_item_code=archive_item_code
            ).delete(synchronize_session=False)
            existing_level_map = {}
            existing_code_set = set()

        # 支持父级来自“库中已有”或“本次导入”
        candidate_code_set = existing_code_set | import_code_set
        level_map = dict(existing_level_map)

        # 按编码长度升序，确保父级先处理
        rows_sorted = sorted(rows, key=lambda x: (len(x['code']), x['code']))

        inserted = 0
        updated = 0
        skipped = 0

        for r in rows_sorted:
            code = r['code']
            name = r['name']
            memo = r['memo'] or None

            parent_code = None
            for i in range(len(code) - 1, 0, -1):
                prefix = code[:i]
                if prefix in candidate_code_set:
                    parent_code = prefix
                    break

            if parent_code:
                level = int(level_map.get(parent_code, 1)) + 1
            else:
                level = 1

            obj = CustomArchiveValue.query.get((account_book_code, fiscal_year, archive_item_code, code))
            if obj:
                obj.archive_value_name = name
                obj.remark = memo
                obj.parent_value_code = parent_code
                obj.level = level
                obj.status = 1
                updated += 1
            else:
                db.session.add(CustomArchiveValue(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    archive_item_code=archive_item_code,
                    archive_value_code=code,
                    archive_value_name=name,
                    archive_value_desc=None,
                    parent_value_code=parent_code,
                    level=level,
                    remark=memo,
                    status=1
                ))
                inserted += 1

            level_map[code] = level

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Excel导入成功',
            'data': {
                'inserted': inserted,
                'updated': updated,
                'skipped': skipped,
                'total': len(rows),
                'mode': mode
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Excel导入失败: {str(e)}'
        }), 500


# ========== 附加接口：获取档案项下的树形档案值 ==========

@custom_archive_bp.route('/api/custom_archive_items/<account_book_code>/<int:fiscal_year>/<archive_item_code>/values', methods=['GET'])
@token_required
def list_archive_item_values(current_user, account_book_code, fiscal_year, archive_item_code):
    """获取某档案项下的所有档案值（可选树形结构）"""
    try:
        # 检查档案项是否存在
        archive_item = CustomArchiveItem.query.get((account_book_code, fiscal_year, archive_item_code))
        if not archive_item:
            return jsonify({
                'success': False,
                'message': f'未找到自定义档案项: {account_book_code}/{fiscal_year}/{archive_item_code}'
            }), 404

        # 获取所有档案值
        values = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=archive_item_code
        ).order_by(CustomArchiveValue.archive_value_code).all()

        # 是否返回树形结构
        as_tree = request.args.get('as_tree', '0') == '1'

        if as_tree and archive_item.has_hierarchy:
            # 构建树形结构
            items_dict = {v.archive_value_code: v.to_dict() for v in values}
            for item in items_dict.values():
                item['children'] = []

            tree = []
            for item in items_dict.values():
                parent_code = item.get('parent_value_code')
                if parent_code and parent_code in items_dict:
                    items_dict[parent_code]['children'].append(item)
                else:
                    tree.append(item)

            return jsonify({
                'success': True,
                'archive_item': archive_item.to_dict(),
                'items': tree,
                'total': len(values)
            })
        else:
            # 返回扁平列表
            items = [v.to_dict() for v in values]
            return jsonify({
                'success': True,
                'archive_item': archive_item.to_dict(),
                'items': items,
                'total': len(items)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取档案值列表失败: {str(e)}'
        }), 500


# ========== 辅助项对应关系接口：科目 -> 辅助项名称 -> 档案值 ==========

@custom_archive_bp.route('/api/account_auxiliary_mapping', methods=['GET'])
@token_required
def get_account_auxiliary_mapping(current_user):
    """
    根据会计科目、科目辅助项、自定义档案、档案值，返回科目与辅助项名称及可选值的对应关系。

    查询参数：
    - account_book_code (string, 必填) - 账套编码
    - fiscal_year (number, 必填) - 会计年度
    - account_code (string, 可选) - 科目编号，不传则返回该账套年度下所有有辅助项的科目
    """
    try:
        account_book_code = request.args.get('account_book_code', '').strip()
        fiscal_year = request.args.get('fiscal_year', type=int)
        account_code = request.args.get('account_code', '').strip() or None

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

        # 校验账套年度
        if not AccountBookFiscalYear.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year
        ).first():
            return jsonify({
                'success': False,
                'message': f'未找到账套年度: {account_book_code}/{fiscal_year}'
            }), 404

        # 查询有辅助项配置的科目（可能按 account_code 筛选）
        aux_query = AccountAuxiliary.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            status=1
        )
        if account_code:
            aux_query = aux_query.filter_by(account_code=account_code)
        aux_list = aux_query.order_by(
            AccountAuxiliary.account_code,
            AccountAuxiliary.auxiliary_item_code
        ).all()

        if not aux_list:
            return jsonify({
                'success': True,
                'items': [],
                'message': '没有符合条件的科目辅助项配置'
            })

        # 按科目分组
        account_codes = list({a.account_code for a in aux_list})
        accounts = {
            (a.account_book_code, a.fiscal_year, a.account_code): a
            for a in Account.query.filter(
                Account.account_book_code == account_book_code,
                Account.fiscal_year == fiscal_year,
                Account.account_code.in_(account_codes)
            ).all()
        }

        # 预拉取该账套年度下所有自定义档案项、档案值（按 archive_item_code 分组）
        archive_items = {
            (c.account_book_code, c.fiscal_year, c.archive_item_code): c
            for c in CustomArchiveItem.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                status=1
            ).all()
        }
        archive_values_raw = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            status=1
        ).all()
        archive_values_by_item = {}
        for v in archive_values_raw:
            key = v.archive_item_code
            if key not in archive_values_by_item:
                archive_values_by_item[key] = []
            archive_values_by_item[key].append({
                'archive_value_code': v.archive_value_code,
                'archive_value_name': v.archive_value_name,
            })

        # 按科目构建：科目 -> 辅助项列表（辅助项名称 + 对应档案值）
        by_account = {}
        for aux in aux_list:
            key = (aux.account_book_code, aux.fiscal_year, aux.account_code)
            if key not in by_account:
                acc = accounts.get(key)
                by_account[key] = {
                    'account_code': aux.account_code,
                    'account_name': acc.account_name if acc else aux.account_code,
                    'auxiliary_items': []
                }
            # 当前辅助项对应的档案编码
            corr_archive = (aux.corresponding_archive or '').strip() or None
            archive_item = archive_items.get((account_book_code, fiscal_year, corr_archive)) if corr_archive else None
            values = archive_values_by_item.get(corr_archive, []) if corr_archive else []
            by_account[key]['auxiliary_items'].append({
                'auxiliary_item_code': aux.auxiliary_item_code,
                'auxiliary_item_name': aux.auxiliary_item_name,
                'corresponding_archive': corr_archive,
                'archive_item_name': archive_item.archive_item_name if archive_item else None,
                'values': values,
            })

        items = list(by_account.values())
        return jsonify({
            'success': True,
            'items': items,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取科目辅助项对应关系失败: {str(e)}'
        }), 500


@custom_archive_bp.route('/api/account_books/<account_book_code>/fiscal_years/<int:fiscal_year>/account_auxiliary_mapping', methods=['GET'])
@token_required
def get_account_auxiliary_mapping_by_path(current_user, account_book_code, fiscal_year):
    """辅助项对应关系接口（路径参数），可选 account_code 查询参数"""
    request.args = request.args.copy()
    request.args['account_book_code'] = account_book_code
    request.args['fiscal_year'] = str(fiscal_year)
    return get_account_auxiliary_mapping(current_user)
