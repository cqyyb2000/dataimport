from flask import Blueprint, jsonify, request
from Auth.auth import token_required
from Model.dataCls import Menu, db

menus_bp = Blueprint('menus', __name__)


@menus_bp.route('/api/menus', methods=['POST'])
@token_required
def create_menu(current_user):
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    data = request.get_json()
    new_menu = Menu(
        name=data.get('name'),
        component=data.get('component'),
        parent_id=data.get('parent_id', 0),
        path=data.get('path'),
        icon=data.get('icon'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(new_menu)
    db.session.commit()
    return jsonify({"success": True, "message": "菜单创建成功", "id": new_menu.id}), 201


@menus_bp.route('/api/menus', methods=['GET'])
def get_all_menus():
    menus = Menu.query.all()
    menu_list = []
    for menu in menus:
        menu_list.append({
            'id': menu.id,
            'name': menu.name,
            'component': menu.component,
            'parent_id': menu.parent_id,
            'path': menu.path,
            'icon': menu.icon,
            'sort_order': menu.sort_order
        })
    return jsonify({"success": True, "data": menu_list}), 200


@menus_bp.route('/api/menus/<int:menu_id>', methods=['GET'])
def get_menu(menu_id):
    menu = Menu.query.get(menu_id)
    if menu:
        return jsonify({
            "success": True,
            "data": {
                'id': menu.id,
                'name': menu.name,
                'component': menu.component,
                'parent_id': menu.parent_id,
                'path': menu.path,
                'icon': menu.icon,
                'sort_order': menu.sort_order
            }
        }), 200
    return jsonify({"success": False, "message": "菜单未找到"}), 404


@menus_bp.route('/api/menus/<int:menu_id>', methods=['PUT'])
@token_required
def update_menu(current_user, menu_id):
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({"success": False, "message": "菜单未找到"}), 404
    data = request.get_json()
    menu.name = data.get('name', menu.name)
    menu.component = data.get('component', menu.component)
    menu.parent_id = data.get('parent_id', menu.parent_id)
    menu.path = data.get('path', menu.path)
    menu.icon = data.get('icon', menu.icon)
    menu.sort_order = data.get('sort_order', menu.sort_order)
    db.session.commit()
    return jsonify({"success": True, "message": "菜单更新成功"}), 200


@menus_bp.route('/api/menus/<int:menu_id>', methods=['DELETE'])
@token_required
def delete_menu(current_user, menu_id):
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '权限不足'
        }), 403
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({"success": False, "message": "菜单未找到"}), 404
    db.session.delete(menu)
    db.session.commit()
    return jsonify({"success": True, "message": "菜单删除成功"}), 200
