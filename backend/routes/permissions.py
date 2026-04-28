from flask import Blueprint, jsonify, request
from Auth.auth import token_required
from Model.dataCls import Menu, db, Permission, User
from sqlalchemy.exc import SQLAlchemyError

permission_bp = Blueprint('permission', __name__, url_prefix='/api')

# 获取所有用户列表（ID和用户名）
@permission_bp.route('/users_permissions', methods=['GET'])
@token_required
def get_all_users(_current_user):
    """获取所有用户列表（ID和用户名）"""
    # users = User.query.with_entities(User.id, User.username,User.is_admin).all()
    # return jsonify([{'id': u.id, 'username': u.username,'is_admin':u.is_admin} for u in users])
    # 按用户名排序
    users = User.query.with_entities(User.id, User.username, User.is_admin).order_by(User.username).all()
    return jsonify([{'id': u.id, 'username': u.username, 'is_admin': u.is_admin} for u in users])

# 获取所有菜单
@permission_bp.route('/menus', methods=['GET'])
@token_required
def get_all_menus(_current_user):
    """获取所有菜单列表"""
    menus = Menu.query.order_by(Menu.parent_id, Menu.sort_order).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'component': m.component,
        'path': m.path,
        'icon': m.icon,
        'parent_id': m.parent_id
    } for m in menus])

# 获取用户权限
@permission_bp.route('/user_permissions/<int:user_id>', methods=['GET'])
@token_required
def get_user_permissions(_current_user: User, user_id: int):
    """获取指定用户的权限菜单ID列表"""
    # 获取用户信息
    user = User.query.get(user_id)
    
    # 检查用户是否存在
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 如果是管理员，返回所有菜单ID
    if user.is_admin:
        all_menus = Menu.query.all()
        return jsonify([menu.id for menu in all_menus])
    
    # 非管理员返回其权限菜单ID
    permissions = Permission.query.filter_by(user_id=user_id).all()
    return jsonify([p.menu_id for p in permissions])

# 更新用户权限
@permission_bp.route('/user_permissions/<int:user_id>', methods=['POST'])
@token_required
def update_user_permissions(_current_user: User, user_id: int):
    """更新指定用户的权限菜单"""
    try:
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 验证请求数据
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        if 'menu_ids' not in data:
            return jsonify({'success': False, 'message': '缺少 menu_ids 参数'}), 400
        
        if not isinstance(data['menu_ids'], list):
            return jsonify({'success': False, 'message': 'menu_ids 必须是数组'}), 400
        
        # 删除旧权限
        Permission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        if data['menu_ids']:
            new_permissions = [Permission(user_id=user_id, menu_id=menu_id) for menu_id in data['menu_ids']]
            db.session.bulk_save_objects(new_permissions)
        
        db.session.commit()
        return jsonify({'success': True})
    except (KeyError, TypeError, ValueError) as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'数据格式错误: {str(e)}'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'数据库操作失败: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新权限失败: {str(e)}'}), 500
