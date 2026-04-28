# -*- coding: utf-8 -*-
"""
总账类 GL.xml 导入服务：根据解析后的 JSON 按类别保存或更新数据库。
依赖：先有账套和年度（account_book_fiscal_year），再处理总账数据。
"""
from typing import Any
from decimal import Decimal

from Model import (
    db,
    AccountBookFiscalYear,
    Account,
    AccountAuxiliary,
    GLBaseInfo,
    GLVoucherType,
    GLVoucher,
    GLVoucherEntry,
    GLVoucherEntryAuxiliary,
    GLAccountBalance,
)


def _int_or_none(v: Any) -> int | None:
    """转换为整数或None"""
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _str_or_empty(v: Any) -> str:
    """转换为字符串或空字符串"""
    if v is None:
        return ""
    return str(v).strip()


def _decimal_or_none(v: Any, precision: int = 2) -> Decimal | None:
    """转换为Decimal或None"""
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except (TypeError, ValueError):
        return None


def _ensure_fiscal_year(account_book_code: str, fiscal_year: int) -> None:
    """确保账套年度记录存在。"""
    existing = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code, fiscal_year=fiscal_year
    ).first()
    if not existing:
        db.session.add(
            AccountBookFiscalYear(account_book_code=account_book_code, fiscal_year=fiscal_year)
        )


def import_accounts_from_gl(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 GL.xml 中的会计科目（按账套+年度）。"""
    rows = gl_data.get("会计科目", [])
    if not rows:
        return 0
    
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("科目编号"))
        if not code:
            continue
        rec = Account.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=code,
        ).first()
        name = _str_or_empty(row.get("科目名称")) or code
        level = _int_or_none(row.get("科目级次")) or 1
        account_type = _str_or_empty(row.get("科目类型")) or "资产类"
        balance_direction = _str_or_empty(row.get("余额方向")) or "借"
        is_leaf = 1 if _str_or_empty(row.get("是否末级")) in ("1", "是", "true", "True", "Y", "y") else 0
        is_enabled = 1 if _str_or_empty(row.get("是否启用")) not in ("0", "否", "false", "False", "N", "n") else 0
        parent_code = _str_or_empty(row.get("上级科目编号")) or None
        
        if rec:
            rec.account_name = name
            rec.account_level = level
            rec.account_type = account_type
            rec.balance_direction = balance_direction
            rec.is_leaf = is_leaf
            rec.is_enabled = is_enabled
            rec.parent_account_code = parent_code
        else:
            db.session.add(
                Account(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    account_code=code,
                    account_name=name,
                    account_level=level,
                    account_type=account_type,
                    balance_direction=balance_direction,
                    is_leaf=is_leaf,
                    is_enabled=is_enabled,
                    parent_account_code=parent_code,
                    status=1,
                )
            )
        count += 1
    return count


def import_account_auxiliaries_from_gl(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 GL.xml 中的科目辅助核算（按账套+年度）。依赖 会计科目 已存在。"""
    rows = gl_data.get("科目辅助核算", [])
    if not rows:
        return 0
    
    count = 0
    for row in rows:
        account_code = _str_or_empty(row.get("科目编号"))
        auxiliary_item_code = _str_or_empty(row.get("辅助项编号"))
        if not account_code or not auxiliary_item_code:
            continue
        rec = AccountAuxiliary.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=account_code,
            auxiliary_item_code=auxiliary_item_code,
        ).first()
        auxiliary_item_name = _str_or_empty(row.get("辅助项名称")) or auxiliary_item_code
        corresponding_archive = _str_or_empty(row.get("对应档案")) or None
        auxiliary_item_description = _str_or_empty(row.get("辅助项描述")) or None
        
        if rec:
            rec.auxiliary_item_name = auxiliary_item_name
            rec.corresponding_archive = corresponding_archive
            rec.auxiliary_item_description = auxiliary_item_description
        else:
            db.session.add(
                AccountAuxiliary(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    account_code=account_code,
                    auxiliary_item_code=auxiliary_item_code,
                    auxiliary_item_name=auxiliary_item_name,
                    corresponding_archive=corresponding_archive,
                    auxiliary_item_description=auxiliary_item_description,
                )
            )
        count += 1
    return count


def _extract_and_create_accounts_from_references(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """
    从GL.xml的凭证分录行和科目余额中提取科目编号，自动创建不存在的科目记录（当GL.xml中没有会计科目数据时使用）。
    返回创建的科目数量。
    """
    account_codes: set[str] = set()
    
    # 从凭证分录行中提取科目编号
    entries = gl_data.get("记账凭证分录行", [])
    for entry in entries:
        account_code = _str_or_empty(entry.get("科目编号"))
        if account_code:
            account_codes.add(account_code)
    
    # 从科目余额中提取科目编号
    balances = gl_data.get("科目余额", [])
    for balance in balances:
        account_code = _str_or_empty(balance.get("科目编号"))
        if account_code:
            account_codes.add(account_code)
    
    created_count = 0
    # 建立科目编号到科目信息的映射（从科目余额中收集）
    account_info_map: dict[str, dict[str, Any]] = {}
    
    # 从科目余额中收集科目信息
    for balance in balances:
        code = _str_or_empty(balance.get("科目编号"))
        if not code or code in account_info_map:
            continue
        
        info: dict[str, Any] = {
            "account_name": f"科目{code}",  # 默认名称
            "balance_direction": "借",  # 默认余额方向
            "account_type": "资产类",  # 默认科目类型
        }
        
        # 从余额方向推断
        opening_dir = _str_or_empty(balance.get("期初余额方向"))
        closing_dir = _str_or_empty(balance.get("期末余额方向"))
        if opening_dir:
            info["balance_direction"] = opening_dir
        elif closing_dir:
            info["balance_direction"] = closing_dir
        
        # 根据科目编号前缀推断科目类型（行政事业单位会计科目编码规则）
        code_prefix = account_code[:1] if len(account_code) >= 1 else ""
        if code_prefix == "1":
            info["account_type"] = "资产类"
            info["balance_direction"] = "借"
        elif code_prefix == "2":
            info["account_type"] = "负债类"
            info["balance_direction"] = "贷"
        elif code_prefix == "3":
            info["account_type"] = "净资产类"
            info["balance_direction"] = "贷"
        elif code_prefix == "4":
            info["account_type"] = "收入类"
            info["balance_direction"] = "贷"
        elif code_prefix == "5":
            info["account_type"] = "支出类"
            info["balance_direction"] = "借"
        
        account_info_map[code] = info
    
    # 分录行中的「科目名称」（如 Excel 导入）优先生为占位科目名
    entry_account_name: dict[str, str] = {}
    for entry in gl_data.get("记账凭证分录行", []):
        c = _str_or_empty(entry.get("科目编号"))
        n = _str_or_empty(entry.get("科目名称"))
        if c and n and c not in entry_account_name:
            entry_account_name[c] = n

    for account_code in account_codes:
        # 检查科目是否已存在
        existing = Account.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            account_code=account_code,
        ).first()
        
        if not existing:
            # 获取科目信息（优先从余额中获取，否则使用分录行科目名称/默认值）
            info = account_info_map.get(account_code, {})
            account_name = info.get("account_name") or entry_account_name.get(account_code) or f"科目{account_code}"
            balance_direction = info.get("balance_direction", "借")
            account_type = info.get("account_type", "资产类")
            
            # 如果余额方向与科目类型不一致，根据科目类型调整
            if account_type == "资产类" or account_type == "支出类":
                balance_direction = "借"
            elif account_type in ("负债类", "净资产类", "收入类"):
                balance_direction = "贷"
            
            # 推断科目级次（根据科目编号长度或格式）
            account_level = 1
            if "-" in account_code:
                # 如果有分隔符，级次为分隔符数量+1
                account_level = len(account_code.split("-"))
            elif "." in account_code:
                # 如果有点号分隔符
                account_level = len(account_code.split("."))
            elif len(account_code) >= 4:
                # 根据编号长度推断（如4位为1级，6位为2级，8位为3级等）
                account_level = min((len(account_code) - 2) // 2 + 1, 10)
            
            # 创建科目记录
            db.session.add(
                Account(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    account_code=account_code,
                    account_name=account_name,
                    account_level=account_level,
                    account_type=account_type,
                    balance_direction=balance_direction,
                    is_leaf=1,  # 默认为末级（从GL.xml中无法确定是否有下级科目）
                    is_enabled=1,
                    parent_account_code=None,  # 无法从GL.xml推断上级科目
                    status=1,
                )
            )
            created_count += 1
    
    return created_count


def import_base_info(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 总账基础信息（按账套+年度）。"""
    rows = gl_data.get("总账基础信息", [])
    if not rows:
        return 0
    
    # 总账基础信息每个账套每个年度只有一条记录
    row = rows[0]
    rec = GLBaseInfo.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
    ).first()
    
    if rec:
        rec.structure_separator = _str_or_empty(row.get("结构分隔符")) or None
        rec.account_code_rule = _str_or_empty(row.get("会计科目编号规则")) or None
        rec.voucher_header_ext_fields = _str_or_empty(row.get("凭证头可扩展字段结构")) or None
        rec.voucher_header_ext_archives = _str_or_empty(row.get("凭证头可扩展结构对应档案")) or None
        rec.entry_line_ext_fields = _str_or_empty(row.get("分录行可扩展字段结构")) or None
        rec.entry_line_ext_archives = _str_or_empty(row.get("分录行可扩展字段对应档案")) or None
    else:
        db.session.add(
            GLBaseInfo(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                structure_separator=_str_or_empty(row.get("结构分隔符")) or None,
                account_code_rule=_str_or_empty(row.get("会计科目编号规则")) or None,
                voucher_header_ext_fields=_str_or_empty(row.get("凭证头可扩展字段结构")) or None,
                voucher_header_ext_archives=_str_or_empty(row.get("凭证头可扩展结构对应档案")) or None,
                entry_line_ext_fields=_str_or_empty(row.get("分录行可扩展字段结构")) or None,
                entry_line_ext_archives=_str_or_empty(row.get("分录行可扩展字段对应档案")) or None,
            )
        )
    return 1


def import_voucher_types(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 记账凭证类型（按账套+年度）。"""
    rows = gl_data.get("记账凭证类型", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("记账凭证类型编号"))
        if not code:
            continue
        rec = GLVoucherType.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            voucher_type_code=code,
        ).first()
        name = _str_or_empty(row.get("记账凭证类型名称")) or code
        abbreviation = _str_or_empty(row.get("记账凭证类型简称")) or None
        if rec:
            rec.voucher_type_name = name
            rec.voucher_type_abbreviation = abbreviation
        else:
            db.session.add(
                GLVoucherType(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    voucher_type_code=code,
                    voucher_type_name=name,
                    voucher_type_abbreviation=abbreviation,
                )
            )
        count += 1
    return count


def import_vouchers(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """
    导入 记账凭证（按账套+年度+期间）。
    支持两种格式：
    1. 标准格式：凭证头和分录行分开
    2. 扁平格式：每个记账凭证元素包含凭证头和分录行信息
    """
    rows = gl_data.get("记账凭证", [])
    if not rows:
        return 0
    
    # 用于去重的集合，记录已处理的凭证编号
    processed_vouchers: set[tuple[str, int]] = set()
    count = 0
    
    for row in rows:
        # 支持两种字段名：标准格式和扁平格式
        voucher_number = _str_or_empty(row.get("凭证编号")) or _str_or_empty(row.get("记账凭证编号"))
        period_number = _int_or_none(row.get("会计期间号"))
        if not voucher_number or period_number is None:
            continue
        
        # 如果该凭证已经处理过，跳过（扁平格式中同一凭证会有多条记录）
        voucher_key = (voucher_number, period_number)
        if voucher_key in processed_vouchers:
            continue
        
        rec = GLVoucher.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            voucher_number=voucher_number,
        ).first()
        
        # 支持两种字段名格式
        voucher_date = _str_or_empty(row.get("凭证日期")) or _str_or_empty(row.get("记账凭证日期"))
        voucher_type_code = _str_or_empty(row.get("记账凭证类型编号"))
        attachment_count = _int_or_none(row.get("附单据数")) or _int_or_none(row.get("附件数"))
        prepared_by = _str_or_empty(row.get("制单人")) or None
        reviewed_by = _str_or_empty(row.get("审核人")) or None
        posted_by = _str_or_empty(row.get("记账人")) or None
        # 凭证状态：支持多种字段名
        voucher_status = _str_or_empty(row.get("凭证状态")) or None
        if not voucher_status:
            # 根据记账标志和作废标志推断状态
            posted_flag = _str_or_empty(row.get("记账标志"))
            cancelled_flag = _str_or_empty(row.get("作废标志"))
            if cancelled_flag == "1":
                voucher_status = "作废"
            elif posted_flag == "1":
                voucher_status = "已记账"
            else:
                voucher_status = "未记账"
        summary = _str_or_empty(row.get("摘要")) or _str_or_empty(row.get("记账凭证摘要")) or None
        
        if rec:
            if voucher_date:
                rec.voucher_date = voucher_date
            if voucher_type_code:
                rec.voucher_type_code = voucher_type_code
            if attachment_count is not None:
                rec.attachment_count = attachment_count
            if prepared_by:
                rec.prepared_by = prepared_by
            if reviewed_by:
                rec.reviewed_by = reviewed_by
            if posted_by:
                rec.posted_by = posted_by
            if voucher_status:
                rec.voucher_status = voucher_status
            if summary:
                rec.summary = summary
        else:
            db.session.add(
                GLVoucher(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    period_number=period_number,
                    voucher_number=voucher_number,
                    voucher_date=voucher_date,
                    voucher_type_code=voucher_type_code,
                    attachment_count=attachment_count,
                    prepared_by=prepared_by,
                    reviewed_by=reviewed_by,
                    posted_by=posted_by,
                    voucher_status=voucher_status,
                    summary=summary,
                )
            )
            processed_vouchers.add(voucher_key)
            count += 1
    
    return count


def import_voucher_entries(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """
    导入 记账凭证分录行（按账套+年度+期间+凭证编号）。
    支持两种格式：
    1. 标准格式：单独的"记账凭证分录行"类别
    2. 扁平格式：从"记账凭证"类别中提取分录行信息
    """
    # 优先使用标准格式的分录行数据
    rows = gl_data.get("记账凭证分录行", [])
    
    # 如果没有标准格式的分录行（空列表或不存在），则从扁平格式的凭证中提取
    # 注意：需要检查是否有"分录行号"或"记账凭证行号"字段来判断是否为标准格式
    if not rows:
        voucher_rows = gl_data.get("记账凭证", [])
        # 检查是否有标准格式的分录行字段（"分录行号"）
        # 如果没有，则假设是扁平格式，使用凭证数据作为分录行
        rows = voucher_rows
    else:
        # 如果有标准格式的分录行，检查是否为空列表
        # 如果为空列表，尝试从凭证中提取
        if len(rows) == 0:
            rows = gl_data.get("记账凭证", [])
    
    count = 0
    
    # 建立凭证编号到期间号的映射（从凭证表中）
    voucher_period_map: dict[str, int] = {}
    vouchers = gl_data.get("记账凭证", [])
    for voucher in vouchers:
        v_num = _str_or_empty(voucher.get("凭证编号")) or _str_or_empty(voucher.get("记账凭证编号"))
        v_period = _int_or_none(voucher.get("会计期间号"))
        if v_num and v_period is not None:
            voucher_period_map[v_num] = v_period
    
    for row in rows:
        # 支持两种字段名格式
        voucher_number = _str_or_empty(row.get("凭证编号")) or _str_or_empty(row.get("记账凭证编号"))
        entry_line_number = _int_or_none(row.get("分录行号")) or _int_or_none(row.get("记账凭证行号"))
        
        # 优先从分录行获取期间号，如果没有则从凭证映射中获取
        period_number = _int_or_none(row.get("会计期间号"))
        if period_number is None and voucher_number in voucher_period_map:
            period_number = voucher_period_map[voucher_number]
        
        if not voucher_number or entry_line_number is None or period_number is None:
            continue
        
        rec = GLVoucherEntry.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            voucher_number=voucher_number,
            entry_line_number=entry_line_number,
        ).first()
        
        account_code = _str_or_empty(row.get("科目编号"))
        # 支持两种摘要字段名
        summary = _str_or_empty(row.get("摘要")) or _str_or_empty(row.get("记账凭证摘要")) or None
        
        # 支持两种金额字段名（标准格式和扁平格式）
        debit_amount = _decimal_or_none(row.get("借方金额")) or _decimal_or_none(row.get("借方本币金额"))
        credit_amount = _decimal_or_none(row.get("贷方金额")) or _decimal_or_none(row.get("贷方本币金额"))
        currency_code = _str_or_empty(row.get("币种编码")) or None
        exchange_rate = _decimal_or_none(row.get("汇率"), precision=6)
        original_currency_debit_amount = _decimal_or_none(row.get("原币借方金额")) or _decimal_or_none(row.get("借方原币金额"))
        original_currency_credit_amount = _decimal_or_none(row.get("原币贷方金额")) or _decimal_or_none(row.get("贷方原币金额"))
        
        # 数量字段：支持借方数量和贷方数量
        debit_quantity = _decimal_or_none(row.get("借方数量"), precision=4)
        credit_quantity = _decimal_or_none(row.get("贷方数量"), precision=4)
        quantity = debit_quantity if debit_quantity else credit_quantity
        
        unit_price = _decimal_or_none(row.get("单价"), precision=4)
        
        # 辅助项明细已移至 gl_voucher_entry_auxiliary 表，由 import_voucher_entry_auxiliaries 处理
        
        if rec:
            if account_code:
                rec.account_code = account_code
            if summary is not None:
                rec.summary = summary
            if debit_amount is not None:
                rec.debit_amount = debit_amount
            if credit_amount is not None:
                rec.credit_amount = credit_amount
            if currency_code:
                rec.currency_code = currency_code
            if exchange_rate is not None:
                rec.exchange_rate = exchange_rate
            if original_currency_debit_amount is not None:
                rec.original_currency_debit_amount = original_currency_debit_amount
            if original_currency_credit_amount is not None:
                rec.original_currency_credit_amount = original_currency_credit_amount
            if quantity is not None:
                rec.quantity = quantity
            if unit_price is not None:
                rec.unit_price = unit_price
        else:
            db.session.add(
                GLVoucherEntry(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    period_number=period_number,
                    voucher_number=voucher_number,
                    entry_line_number=entry_line_number,
                    account_code=account_code,
                    summary=summary,
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    original_currency_debit_amount=original_currency_debit_amount,
                    original_currency_credit_amount=original_currency_credit_amount,
                    quantity=quantity,
                    unit_price=unit_price,
                )
            )
        count += 1
    return count


def import_voucher_entry_auxiliaries(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """
    导入 凭证分录辅助项明细（gl_voucher_entry_auxiliary）。
    从记账凭证中解析 辅助项1编号~辅助项30编号，写入辅助项明细表。
    依赖：gl_voucher_entry 已导入，account_auxiliary 已导入（用于获取 auxiliary_item_name）。
    """
    rows = gl_data.get("记账凭证分录行", [])
    if not rows:
        rows = gl_data.get("记账凭证", [])

    voucher_period_map: dict[str, int] = {}
    for v in gl_data.get("记账凭证", []):
        v_num = _str_or_empty(v.get("凭证编号")) or _str_or_empty(v.get("记账凭证编号"))
        v_period = _int_or_none(v.get("会计期间号"))
        if v_num and v_period is not None:
            voucher_period_map[v_num] = v_period

    count = 0
    for row in rows:
        voucher_number = _str_or_empty(row.get("凭证编号")) or _str_or_empty(row.get("记账凭证编号"))
        entry_line_number = _int_or_none(row.get("分录行号")) or _int_or_none(row.get("记账凭证行号"))
        period_number = _int_or_none(row.get("会计期间号"))
        if period_number is None and voucher_number in voucher_period_map:
            period_number = voucher_period_map[voucher_number]

        if not voucher_number or entry_line_number is None or period_number is None:
            continue

        account_code = _str_or_empty(row.get("科目编号"))
        if not account_code:
            continue

        for i in range(1, 31):
            aux_value = _str_or_empty(row.get(f"辅助项{i}编号"))
            if not aux_value:
                continue

            rec = GLVoucherEntryAuxiliary.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                period_number=period_number,
                voucher_number=voucher_number,
                entry_line_number=entry_line_number,
                auxiliary_item_sequence=i,
            ).first()

            aa = AccountAuxiliary.query.filter_by(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                account_code=account_code,
                auxiliary_item_code=str(i),
            ).first()
            auxiliary_item_name = aa.auxiliary_item_name if aa else None

            if rec:
                rec.auxiliary_value = aux_value
                rec.account_code = account_code
                rec.auxiliary_item_name = auxiliary_item_name
            else:
                db.session.add(
                    GLVoucherEntryAuxiliary(
                        account_book_code=account_book_code,
                        fiscal_year=fiscal_year,
                        period_number=period_number,
                        voucher_number=voucher_number,
                        entry_line_number=entry_line_number,
                        auxiliary_item_sequence=i,
                        account_code=account_code,
                        auxiliary_value=aux_value,
                        auxiliary_item_name=auxiliary_item_name,
                    )
                )
            count += 1
    return count


def import_account_balances(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 科目余额（按账套+年度+期间）。"""
    rows = gl_data.get("科目余额", [])
    count = 0
    for row in rows:
        account_code = _str_or_empty(row.get("科目编号"))
        period_number = _int_or_none(row.get("会计期间号"))
        if not account_code or period_number is None:
            continue
        
        currency_code = _str_or_empty(row.get("币种编码")) or None
        parent_code = _str_or_empty(row.get("父级科目编号")) or _str_or_empty(
            row.get("ParentCode")
        ) or None

        # 使用唯一索引字段查询
        rec = GLAccountBalance.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            period_number=period_number,
            account_code=account_code,
            currency_code=currency_code,
        ).first()
        
        opening_balance = _decimal_or_none(row.get("期初余额"))
        opening_balance_direction = _str_or_empty(row.get("期初余额方向")) or None
        current_period_debit_amount = _decimal_or_none(row.get("本期借方发生额"))
        current_period_credit_amount = _decimal_or_none(row.get("本期贷方发生额"))
        closing_balance = _decimal_or_none(row.get("期末余额"))
        closing_balance_direction = _str_or_empty(row.get("期末余额方向")) or None
        
        if rec:
            rec.opening_balance = opening_balance
            rec.opening_balance_direction = opening_balance_direction
            rec.current_period_debit_amount = current_period_debit_amount
            rec.current_period_credit_amount = current_period_credit_amount
            rec.closing_balance = closing_balance
            rec.closing_balance_direction = closing_balance_direction
            rec.parent_code = parent_code
        else:
            db.session.add(
                GLAccountBalance(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    period_number=period_number,
                    account_code=account_code,
                    opening_balance=opening_balance,
                    opening_balance_direction=opening_balance_direction,
                    current_period_debit_amount=current_period_debit_amount,
                    current_period_credit_amount=current_period_credit_amount,
                    closing_balance=closing_balance,
                    closing_balance_direction=closing_balance_direction,
                    currency_code=currency_code,
                    parent_code=parent_code,
                )
            )
        count += 1
    return count


def run_gl_import(
    gl_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int | None = None,
) -> dict[str, Any]:
    """
    执行完整导入：先确保账套年度存在，再按类别保存/更新。
    
    :param gl_data: 解析后的GL.xml数据
    :param account_book_code: 账套编码（必填）
    :param fiscal_year: 会计年度（可选，如果为None则从凭证数据中提取）
    :return: 统计信息及可能的错误
    """
    stats = {
        "会计科目": 0,
        "科目辅助核算": 0,
        "总账基础信息": 0,
        "记账凭证类型": 0,
        "记账凭证": 0,
        "记账凭证分录行": 0,
        "凭证分录辅助项": 0,
        "科目余额": 0,
    }
    
    # 如果没有提供年度，尝试从凭证数据中提取
    if fiscal_year is None:
        vouchers = gl_data.get("记账凭证", [])
        if vouchers:
            fiscal_year = _int_or_none(vouchers[0].get("会计年度"))
        if fiscal_year is None:
            balances = gl_data.get("科目余额", [])
            if balances:
                fiscal_year = _int_or_none(balances[0].get("会计年度"))
    
    if account_book_code is None or account_book_code == "":
        return {
            "success": False,
            "message": "账套编码不能为空",
            "stats": stats,
        }
    
    if fiscal_year is None:
        return {
            "success": False,
            "message": "无法确定会计年度，请提供fiscal_year参数或确保XML中包含会计年度信息",
            "stats": stats,
            "account_book_code": account_book_code,
        }
    
    # 确保账套年度记录存在
    _ensure_fiscal_year(account_book_code, fiscal_year)
    
    try:
        # 先导入会计科目（如果GL.xml中包含）
        stats["会计科目"] = import_accounts_from_gl(gl_data, account_book_code, fiscal_year)
        
        # 如果GL.xml中没有会计科目数据，则从凭证分录行和科目余额中提取并创建
        if stats["会计科目"] == 0:
            stats["会计科目"] = _extract_and_create_accounts_from_references(gl_data, account_book_code, fiscal_year)
        
        # 导入科目辅助核算（如果GL.xml中包含）
        stats["科目辅助核算"] = import_account_auxiliaries_from_gl(gl_data, account_book_code, fiscal_year)
        
        stats["总账基础信息"] = import_base_info(gl_data, account_book_code, fiscal_year)
        stats["记账凭证类型"] = import_voucher_types(gl_data, account_book_code, fiscal_year)
        stats["记账凭证"] = import_vouchers(gl_data, account_book_code, fiscal_year)
        stats["记账凭证分录行"] = import_voucher_entries(gl_data, account_book_code, fiscal_year)
        stats["凭证分录辅助项"] = import_voucher_entry_auxiliaries(gl_data, account_book_code, fiscal_year)
        stats["科目余额"] = import_account_balances(gl_data, account_book_code, fiscal_year)
        
        db.session.commit()
        return {
            "success": True,
            "message": "导入完成",
            "account_book_code": account_book_code,
            "fiscal_year": fiscal_year,
            "stats": stats,
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": str(e),
            "stats": stats,
            "account_book_code": account_book_code,
            "fiscal_year": fiscal_year,
        }
