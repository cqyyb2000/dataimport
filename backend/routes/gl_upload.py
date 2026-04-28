# -*- coding: utf-8 -*-
"""接收 gl.xml 上传，解析为 JSON 后按类别保存或更新"""
from flask import Blueprint, jsonify, request

from Auth.auth import token_required
from unit.gl_xml_parser import parse_gl_xml
from services.gl_import_service import run_gl_import

gl_upload_bp = Blueprint("gl_upload", __name__)

ALLOWED_EXTENSIONS = {"xml"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS


@gl_upload_bp.route("/api/gl/upload", methods=["POST"])
@token_required
def upload_gl_xml(current_user):
    """
    接收上传的 gl.xml（总账类），解析为 JSON 后按类别保存或更新：
    总账基础信息、记账凭证类型、记账凭证、记账凭证分录行、科目余额。
    
    请求参数：
    - file: XML文件（必填）
    - account_book_code: 账套编码（必填，表单字段或JSON）
    - fiscal_year: 会计年度（可选，如果不提供则从XML中提取）
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "请选择要上传的 gl.xml 文件（表单字段名：file）"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "未选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "仅支持 .xml 文件"}), 400

    # 获取账套编码和会计年度（支持表单和JSON两种方式）
    account_book_code = None
    fiscal_year = None
    
    # 优先从表单获取
    if request.form:
        account_book_code = request.form.get("account_book_code")
        fiscal_year_str = request.form.get("fiscal_year")
        if fiscal_year_str:
            try:
                fiscal_year = int(fiscal_year_str)
            except ValueError:
                pass
    
    # 如果表单没有，尝试从JSON获取
    if not account_book_code and request.is_json:
        json_data = request.get_json()
        if json_data:
            account_book_code = json_data.get("account_book_code")
            fiscal_year = json_data.get("fiscal_year")
    
    if not account_book_code:
        return jsonify({"success": False, "message": "账套编码（account_book_code）不能为空"}), 400

    try:
        # 解析 XML 为按类别分组的 JSON（支持文件流）
        gl_data = parse_gl_xml(file, encoding="utf-8", as_dict=True)
    except FileNotFoundError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except ValueError as e:
        return jsonify({"success": False, "message": f"XML 格式错误: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"解析 XML 失败: {str(e)}"}), 400

    result = run_gl_import(gl_data, account_book_code, fiscal_year)
    if result.get("success"):
        return jsonify(result), 200
    return jsonify(result), 400
