# -*- coding: utf-8 -*-
"""
公共档案 Share.xml 导入服务：根据解析后的 JSON 按类别保存或更新数据库。
依赖：先有 电子账簿 得到 account_book_code 与 fiscal_year，再处理其他按账套+年度的表。
"""
from typing import Any

from Model import (
    db,
    AccountBook,
    AccountBookFiscalYear,
    Account,
    AccountAuxiliary,
    InternalOrganization,
    Item,
    Currency,
    ExchangeRateType,
    CustomArchiveItem,
    CustomArchiveValue,
)


def _int_or_none(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _str_or_empty(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _ensure_fiscal_year(account_book_code: str, fiscal_year: int) -> None:
    """确保账套年度记录存在。"""
    existing = AccountBookFiscalYear.query.filter_by(
        account_book_code=account_book_code, fiscal_year=fiscal_year
    ).first()
    if not existing:
        db.session.add(
            AccountBookFiscalYear(account_book_code=account_book_code, fiscal_year=fiscal_year)
        )


def import_account_books(share_data: dict[str, list[dict[str, Any]]]) -> tuple[str | None, int | None]:
    """
    导入 电子账簿：创建或更新账套，并确保对应会计年度存在。
    返回 (account_book_code, fiscal_year) 供后续类别使用；若没有电子账簿数据则返回 (None, None)。
    """
    rows = share_data.get("电子账簿", [])
    if not rows:
        return None, None
    # 取第一条作为本文件的账套+年度（通常 SHARE.xml 仅一个账套一个年度）
    row = rows[0]
    code = _str_or_empty(row.get("电子账簿编号"))
    year_str = _str_or_empty(row.get("会计年度"))
    if not code:
        return None, None
    fiscal_year = _int_or_none(year_str) if year_str else None
    if fiscal_year is None:
        fiscal_year = _int_or_none(row.get("会计年度"))

    existing = AccountBook.query.get(code)
    if existing:
        existing.account_book_name = _str_or_empty(row.get("电子账簿名称")) or existing.account_book_name
        existing.accounting_entity = _str_or_empty(row.get("会计核算单位")) or existing.accounting_entity
        existing.organization_code = _str_or_empty(row.get("组织机构代码")) or None
        existing.unit_type = _str_or_empty(row.get("单位类型")) or existing.unit_type
        existing.industry = _str_or_empty(row.get("行业")) or None
        existing.administrative_division_code = _str_or_empty(row.get("行政区划代码")) or None
        existing.budget_management_level = _str_or_empty(row.get("预算管理级次")) or None
        existing.funding_source = _str_or_empty(row.get("经费来源")) or None
        existing.developer = _str_or_empty(row.get("开发单位")) or None
        existing.version = _str_or_empty(row.get("版本号")) or None
        existing.base_currency = _str_or_empty(row.get("本位币")) or existing.base_currency
        existing.standard_version = _str_or_empty(row.get("标准版本号")) or existing.standard_version
        if fiscal_year is not None:
            existing.default_fiscal_year = fiscal_year
    else:
        db.session.add(
            AccountBook(
                account_book_code=code,
                account_book_name=_str_or_empty(row.get("电子账簿名称")) or "未命名",
                accounting_entity=_str_or_empty(row.get("会计核算单位")) or "未命名",
                organization_code=_str_or_empty(row.get("组织机构代码")) or None,
                unit_type=_str_or_empty(row.get("单位类型")) or "行政单位",
                industry=_str_or_empty(row.get("行业")) or None,
                administrative_division_code=_str_or_empty(row.get("行政区划代码")) or None,
                budget_management_level=_str_or_empty(row.get("预算管理级次")) or None,
                funding_source=_str_or_empty(row.get("经费来源")) or None,
                developer=_str_or_empty(row.get("开发单位")) or None,
                version=_str_or_empty(row.get("版本号")) or None,
                base_currency=_str_or_empty(row.get("本位币")) or "人民币元",
                standard_version=_str_or_empty(row.get("标准版本号")) or "1.0",
                default_fiscal_year=fiscal_year,
                status=1,
            )
        )
    if fiscal_year is not None:
        _ensure_fiscal_year(code, fiscal_year)
    return code, fiscal_year


def import_internal_organizations(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 内设机构（按账套+年度）。"""
    rows = share_data.get("内设机构", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("内设机构编码"))
        if not code:
            continue
        rec = InternalOrganization.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            internal_org_code=code,
        ).first()
        name = _str_or_empty(row.get("内设机构名称")) or code
        parent = _str_or_empty(row.get("上级机构编码")) or None
        if rec:
            rec.internal_org_name = name
            rec.parent_org_code = parent
        else:
            db.session.add(
                InternalOrganization(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    internal_org_code=code,
                    internal_org_name=name,
                    parent_org_code=parent,
                    status=1,
                )
            )
        count += 1
    return count


def import_items(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 项目（按账套+年度）。"""
    rows = share_data.get("项目", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("项目编码"))
        if not code:
            continue
        rec = Item.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            item_code=code,
        ).first()
        name = _str_or_empty(row.get("项目名称")) or code
        level = _int_or_none(row.get("级次")) or 1
        item_type = _str_or_empty(row.get("项目类型")) or None
        item_category = _str_or_empty(row.get("项目类别")) or None
        item_attribute = _str_or_empty(row.get("项目属性")) or None
        start_date = _str_or_empty(row.get("项目起始日期")) or None
        end_date = _str_or_empty(row.get("项目结束日期")) or None
        if rec:
            rec.item_name = name
            rec.level = level
            rec.item_type = item_type
            rec.item_category = item_category
            rec.item_attribute = item_attribute
            rec.item_start_date = start_date
            rec.item_end_date = end_date
        else:
            db.session.add(
                Item(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    item_code=code,
                    item_name=name,
                    level=level,
                    item_type=item_type,
                    item_category=item_category,
                    item_attribute=item_attribute,
                    item_start_date=start_date,
                    item_end_date=end_date,
                    status=1,
                )
            )
        count += 1
    return count


def import_currencies(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 币种（按账套+年度）。"""
    rows = share_data.get("币种", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("币种编码"))
        if not code:
            continue
        rec = Currency.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            currency_code=code,
        ).first()
        name = _str_or_empty(row.get("币种名称")) or code
        if rec:
            rec.currency_name = name
        else:
            db.session.add(
                Currency(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    currency_code=code,
                    currency_name=name,
                    status=1,
                )
            )
        count += 1
    return count


def import_exchange_rate_types(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 汇率类型（按账套+年度）。"""
    rows = share_data.get("汇率类型", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("汇率类型编号"))
        if not code:
            continue
        rec = ExchangeRateType.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            exchange_rate_type_code=code,
        ).first()
        name = _str_or_empty(row.get("汇率类型名称")) or code
        if rec:
            rec.exchange_rate_type_name = name
        else:
            db.session.add(
                ExchangeRateType(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    exchange_rate_type_code=code,
                    exchange_rate_type_name=name,
                    status=1,
                )
            )
        count += 1
    return count


def import_custom_archive_items(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 自定义档案项（按账套+年度）。"""
    rows = share_data.get("自定义档案项", [])
    count = 0
    for row in rows:
        code = _str_or_empty(row.get("档案编码"))
        if not code:
            continue
        rec = CustomArchiveItem.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=code,
        ).first()
        name = _str_or_empty(row.get("档案名称")) or code
        desc = _str_or_empty(row.get("档案描述")) or None
        has_hierarchy = 1 if _str_or_empty(row.get("是否有层级特征")) in ("1", "是", "true", "True") else 0
        code_rule = _str_or_empty(row.get("档案编码规则")) or None
        if rec:
            rec.archive_item_name = name
            rec.archive_item_desc = desc
            rec.has_hierarchy = has_hierarchy
            rec.archive_code_rule = code_rule
        else:
            db.session.add(
                CustomArchiveItem(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    archive_item_code=code,
                    archive_item_name=name,
                    archive_item_desc=desc,
                    has_hierarchy=has_hierarchy,
                    archive_code_rule=code_rule,
                    status=1,
                )
            )
        count += 1
    return count


def import_custom_archive_values(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 自定义档案值（按账套+年度）。依赖 自定义档案项 已存在。"""
    rows = share_data.get("自定义档案值", [])
    count = 0
    for row in rows:
        item_code = _str_or_empty(row.get("档案编码"))
        value_code = _str_or_empty(row.get("档案值编码"))
        if not item_code or not value_code:
            continue
        rec = CustomArchiveValue.query.filter_by(
            account_book_code=account_book_code,
            fiscal_year=fiscal_year,
            archive_item_code=item_code,
            archive_value_code=value_code,
        ).first()
        name = _str_or_empty(row.get("档案值名称")) or value_code
        desc = _str_or_empty(row.get("档案值描述")) or None
        parent = _str_or_empty(row.get("档案值父节点")) or None
        level = _int_or_none(row.get("档案值级次")) or 1
        if rec:
            rec.archive_value_name = name
            rec.archive_value_desc = desc
            rec.parent_value_code = parent
            rec.level = level
        else:
            db.session.add(
                CustomArchiveValue(
                    account_book_code=account_book_code,
                    fiscal_year=fiscal_year,
                    archive_item_code=item_code,
                    archive_value_code=value_code,
                    archive_value_name=name,
                    archive_value_desc=desc,
                    parent_value_code=parent,
                    level=level,
                    status=1,
                )
            )
        count += 1
    return count


def import_accounts(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 会计科目（按账套+年度）。"""
    rows = share_data.get("会计科目", [])
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


def import_account_auxiliaries(
    share_data: dict[str, list[dict[str, Any]]],
    account_book_code: str,
    fiscal_year: int,
) -> int:
    """导入 科目辅助核算（按账套+年度）。依赖 会计科目 已存在。"""
    rows = share_data.get("科目辅助核算", [])
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


def run_share_import(share_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """
    执行完整导入：先处理电子账簿得到账套+年度，再按类别保存/更新。
    返回统计信息及可能的错误。
    """
    stats = {
        "电子账簿": 0,
        "会计科目": 0,
        "科目辅助核算": 0,
        "内设机构": 0,
        "项目": 0,
        "币种": 0,
        "汇率类型": 0,
        "自定义档案项": 0,
        "自定义档案值": 0,
    }
    account_book_code, fiscal_year = import_account_books(share_data)
    if share_data.get("电子账簿"):
        stats["电子账簿"] = len(share_data["电子账簿"])

    if account_book_code is None:
        return {
            "success": False,
            "message": "未解析到电子账簿数据，无法确定账套与会计年度",
            "stats": stats,
        }

    if fiscal_year is None:
        return {
            "success": False,
            "message": "电子账簿中未包含有效会计年度",
            "stats": stats,
            "account_book_code": account_book_code,
        }

    try:
        stats["会计科目"] = import_accounts(share_data, account_book_code, fiscal_year)
        stats["科目辅助核算"] = import_account_auxiliaries(share_data, account_book_code, fiscal_year)
        stats["内设机构"] = import_internal_organizations(share_data, account_book_code, fiscal_year)
        stats["项目"] = import_items(share_data, account_book_code, fiscal_year)
        stats["币种"] = import_currencies(share_data, account_book_code, fiscal_year)
        stats["汇率类型"] = import_exchange_rate_types(share_data, account_book_code, fiscal_year)
        stats["自定义档案项"] = import_custom_archive_items(share_data, account_book_code, fiscal_year)
        stats["自定义档案值"] = import_custom_archive_values(share_data, account_book_code, fiscal_year)
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
