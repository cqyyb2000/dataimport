# 生成 Token 的函数
import os
import jwt
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from Model.dataCls import User, Permission, Menu

SECRET_KEY = os.getenv('SECRET_KEY', 'key031125')


# 生成Token 的函数
def generate_token(username):
    # 设置 Token 的过期时间
    expiration = datetime.now() + timedelta(minutes=15)
    payload = {
        'user': username,
        'exp': expiration
    }
    # 使用 SECRET_KEY 对 payload 进行签名，生成 Token
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


# 验证 Token 的函数
def verify_token(token):
    try:
        # 尝试使用 SECRET_KEY 对 Token 进行解码
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# 获取用户菜单权限 @app.route('/api/getusermenus', methods=['GET'])

def get_user_menus(username):
    ##username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    print(user.id)

    permission_menu_ids = [p.menu_id for p in Permission.query.filter_by(user_id=user.id).all()]
    print(permission_menu_ids)
    all_menus = Menu.query.all()

    menu_dict = {menu.id: menu for menu in all_menus}
    print(menu_dict)
    try:
        for menu in all_menus:
            if menu.parent_id in menu_dict:
                print(menu_dict[menu.name])
                menu_dict[menu.parent_id].children.append(menu)

                print(menu_dict[menu.name])
    except Exception as e:
        print(e)

    def build_menu_tree(menu):
        if menu.id not in permission_menu_ids:
            return None
        menu_data = {
            'id': menu.id,
            'name': menu.name,
            'icon': menu.icon,
            'path': menu.path,
            'vue_page': ''  # menu.vue_page
        }
        children = [build_menu_tree(child) for child in menu.children if child.id in permission_menu_ids]
        menu_data['children'] = [child for child in children if child]
        return menu_data

    root_menus = [menu for menu in all_menus if menu.parent_id is None]
    user_menus = [build_menu_tree(menu) for menu in root_menus if menu.id in permission_menu_ids]
    user_menus = [menu for menu in user_menus if menu]
    return jsonify(user_menus)


def get_user_permissions(user_id):
    # 新增：获取用户对象并判断是否是管理员
    user = User.query.get(user_id)
    if user and user.is_admin:
        # 管理员获取所有菜单
        all_menus = Menu.query.order_by(Menu.parent_id, Menu.sort_order).all()
    else:
        # 原有逻辑保持不变
        permission_menu_ids = [p.menu_id for p in Permission.query.filter_by(user_id=user_id).all()]
        all_menus = Menu.query.filter(Menu.id.in_(permission_menu_ids)).order_by(Menu.parent_id, Menu.sort_order).all()

    # 以下保持原有代码不变
    menu_dict = {}
    for menu in all_menus:
        menu_dict[menu.id] = {
            'id': menu.id,
            'name': menu.name,
            'path': menu.path,
            'icon': menu.icon,
            'component': menu.component,
            'children': []
        }
        if menu.parent_id in menu_dict:
            menu_dict[menu.parent_id]['children'].append(menu_dict[menu.id])
        elif menu.parent_id == 0:
            menu_dict[menu.id] = menu_dict[menu.id]

    root_menus = [m for m in menu_dict.values() if Menu.query.get(m['id']).parent_id == 0]
    return sorted(root_menus, key=lambda x: x['id'])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': '缺少认证令牌'}), 401
        
        try:
            token = token.split(' ')[1]  # 移除 'Bearer ' 前缀
            payload = verify_token(token)
            if not payload:
                return jsonify({'message': '无效的认证令牌'}), 401
            
            current_user = User.query.filter_by(username=payload['user']).first()
            if not current_user:
                return jsonify({'message': '用户不存在'}), 401
                
            return f(current_user, *args, **kwargs)
        except Exception as e:
            print('token_required error:', e)
            return jsonify({'message': '认证失败'}), 401
            
    return decorated