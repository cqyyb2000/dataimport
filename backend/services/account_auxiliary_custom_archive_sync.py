# -*- coding: utf-8 -*-
"""科目辅助核算与自定义档案(custom_archive_item)同步逻辑。"""
from __future__ import annotations

from typing import Any

from Model import CustomArchiveItem, db

def upsert_custom_archive_for_auxiliary(
    account_book_code: str,
    fiscal_year: int,
    archive_item_code: str,
    archive_value_name: str,
    *,
    archive_item_name: str | None = None,
    archive_item_desc: str | None = None,
    archive_value_desc: str | None = None,
    status: int | None = 1,
) -> dict[str, Any]:
    """同步自定义档案项。archive_value_name 为辅助项名称；可选覆盖来自前端的档案名称/描述。"""
    archive_item_code = (archive_item_code or '').strip()
    if not archive_item_code:
        raise ValueError('archive_item_code 不能为空')

    base_name = (archive_value_name or '').strip()
    item_name = (archive_item_name or '').strip() or base_name
    if not item_name:
        raise ValueError('档案名称不能为空（请提供 auxiliary 名称或 archive_item_name）')

    item_desc = (archive_item_desc or '').strip() or item_name
    remark = (archive_value_desc or '').strip() or None
    st = 1 if status is None else int(status)

    created_item = False
    item = CustomArchiveItem.query.filter_by(
        account_book_code=account_book_code,
        fiscal_year=fiscal_year,
        archive_item_code=archive_item_code,
    ).first()
    if not item:
        db.session.add(
            CustomArchiveItem(
                account_book_code=account_book_code,
                fiscal_year=fiscal_year,
                archive_item_code=archive_item_code,
                archive_item_name=item_name,
                archive_item_desc=item_desc,
                has_hierarchy=0,
                archive_code_rule=None,
                remark=remark,
                status=st,
            )
        )
        created_item = True

    return {
        'created_item': created_item,
        'updated_item': False,
        'created_value': False,
        'updated_value': False,
    }
