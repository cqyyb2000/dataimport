from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from Auth.auth import generate_token, get_user_permissions, token_required
from Model.dataCls import User, db

users_bp = Blueprint('users', __name__)


def _clean_role(role):
    if role is None or role == '':
        return None
    if role not in (User.ROLE_ACCOUNTANT, User.ROLE_CASHIER):
        raise ValueError('角色只能是会计或出纳')
    return role


@users_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        token = generate_token(data['username'])
        usermenus = get_user_permissions(user.id)
        return jsonify(
            {
                'success': True,
                'isAdmin': user.is_admin,
                'role': user.role,
                'token': token,
                'username': data['username'],
                'menus': usermenus
            })
    return jsonify({'success': False, 'message': '用户名和密码不正确！'}), 401

@users_bp.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        if page < 1:
            page = 1
        if page_size not in [10, 20, 50, 100]:
            page_size = 10
        pagination = User.query.paginate(
            page=page, 
            per_page=page_size, 
            error_out=False
        )
        users = pagination.items
        return jsonify({
            'success': True,
            'items': [user.to_dict() for user in users],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'total_pages': pagination.pages
        })
    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500

@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    try:
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': '权限不足'
            }), 403
        user = User.query.get_or_404(user_id)
        data = request.json
        if 'username' in data:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({
                    'success': False,
                    'message': '用户名已存在'
                }), 400
            user.username = data['username']
        if 'password' in data:
            user.password_hash = generate_password_hash(data['password'])
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'role' in data:
            user.role = _clean_role(data.get('role'))
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'data': user.to_dict()
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500

@users_bp.route('/api/create_user', methods=['POST'])
def create_user():
    data = request.json or {}
    try:
        role = _clean_role(data.get('role'))
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        is_admin=data.get('is_admin', False),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True})
