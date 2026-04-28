# -*- coding: utf-8 -*-
"""接收 share.xml 上传，解析为 JSON 后按类别保存或更新"""
from flask import Blueprint, jsonify, request

from Auth.auth import token_required
from unit.share_xml_parser import parse_share_xml
from services.share_import_service import run_share_import

share_upload_bp = Blueprint("share_upload", __name__)

ALLOWED_EXTENSIONS = {"xml"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS


@share_upload_bp.route("/api/share/upload", methods=["POST"])
@token_required
def upload_share_xml(current_user):
    """
    接收上传的 share.xml（公共档案类），解析为 JSON 后按类别保存或更新：
    电子账簿、会计年度、内设机构、项目、币种、汇率类型、自定义档案项、自定义档案值。
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "请选择要上传的 share.xml 文件（表单字段名：file）"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "未选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "仅支持 .xml 文件"}), 400

    try:
        # 解析 XML 为按类别分组的 JSON（支持文件流）
        share_data = parse_share_xml(file, encoding="utf-8", as_dict=True)
    except FileNotFoundError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except ValueError as e:
        return jsonify({"success": False, "message": f"XML 格式错误: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"解析 XML 失败: {str(e)}"}), 400

    result = run_share_import(share_data)
    if result.get("success"):
        return jsonify(result), 200
    return jsonify(result), 400
