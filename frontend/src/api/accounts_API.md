会计科目与科目辅助核算 API 说明

本文档描述 routes/accounts.py 中实现的 会计科目（account） 与 科目辅助核算（account_auxiliary） 接口。





认证：所有接口均需登录，请求头携带 JWT：
Authorization: Bearer <token>



账套年度：除「列表/详情」在服务端会校验外，写入类接口要求 account_book_fiscal_year 中已存在对应 account_book_code + fiscal_year，否则返回 404。



分页：page 默认 1；page_size 仅允许 10、20、50、100，其他值按 10 处理。



一、会计科目 Account

对应数据表 account，主键为 (account_book_code, fiscal_year, account_code)。

1.1 分页列表

方式 A（查询参数）

GET /api/accounts







查询参数



类型



必填



说明





account_book_code



string



是



账套编码





fiscal_year



number



是



会计年度（4 位）





account_code



string



否



科目编号，模糊匹配





account_name



string



否



科目名称，模糊匹配





account_type



string



否



科目类型，精确匹配





parent_account_code



string



否



上级科目编号，精确匹配





is_leaf



number



否



是否末级：1/0





is_enabled



number



否



是否启用：1/0





status



number



否



状态：1/0





page



number



否



页码，默认 1





page_size



number



否



每页条数，默认 10

方式 B（路径参数，与方式 A 等价，仅账套、年度来源不同）

GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts

路径中的 account_book_code、fiscal_year 与方式 A 含义相同；其余筛选仍用查询参数（同上表）。

成功响应示例

{
  "success": true,
  "items": [
    {
      "account_book_code": "001",
      "fiscal_year": 2024,
      "account_code": "1001",
      "account_name": "库存现金",
      "account_level": 1,
      "account_type": "资产类",
      "balance_direction": "借",
      "is_leaf": 1,
      "is_enabled": 1,
      "parent_account_code": null,
      "remark": null,
      "status": 1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}



1.2 单条详情

GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}







路径参数



说明





account_book_code



账套编码





fiscal_year



会计年度





account_code



科目编号

成功响应

{
  "success": true,
  "data": { }
}

data 字段结构与列表项中单条 items[] 元素一致。



1.3 新建科目

方式 A（JSON 中带账套、年度）

POST /api/accounts
Content-Type: application/json

方式 B（路径中带账套、年度）

POST /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts
Content-Type: application/json

请求体字段







字段



类型



必填



说明





account_book_code



string



方式 A 必填



账套编码





fiscal_year



number



方式 A 必填



会计年度





account_code



string



是



科目编号





account_name



string



是



科目名称





account_level



number



是



科目级次





account_type



string



是



科目类型





balance_direction



string



是



余额方向，如 借/贷





parent_account_code



string



否



上级科目编号；若填写须在同年同账套下已存在





is_leaf



number



否



默认 0





is_enabled



number



否



默认 1





remark



string



否



备注





status



number



否



默认 1

成功响应示例

{
  "success": true,
  "message": "科目创建成功",
  "data": { }
}



1.4 更新科目

主键 (account_book_code, fiscal_year, account_code) 不可修改。

PUT /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}
Content-Type: application/json

可传字段（按需）：account_name、account_level、account_type、balance_direction、is_leaf、is_enabled、parent_account_code、remark、status。
更新 parent_account_code 时：不能指向自身；若填写非空值，该上级科目须已存在。

成功响应

{
  "success": true,
  "message": "科目更新成功",
  "data": { }
}



1.5 删除科目

DELETE /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}





若存在下级科目（其他科目的 parent_account_code 等于本科目编号），返回 400，提示先处理下级。



删除科目时，数据库对 account_auxiliary 通常为级联删除（以实际库表约束为准）。

成功响应

{
  "success": true,
  "message": "科目已删除"
}




1.6 Excel 导入会计科目

将符合表头约定的 .xlsx / .xlsm 文件中的每一行导入为一条 account 记录；若该行包含「辅助核算项」列且单元格内有多个名称（用英文逗号、中文逗号、顿号或分号分隔，如 单位往来,项目），则为该科目写入多条 account_auxiliary，其中 auxiliary_item_code 按从左到右的顺序为 "1", "2", "3" …，auxiliary_item_name 为拆分后的名称。导入不会调用自定义档案同步（corresponding_archive 为空）。

默认模式 mode=upsert：科目已存在则更新科目字段，并删除该科目下原有全部辅助核算后按 Excel 重建；不存在则新增科目并写入辅助核算。
mode=append：仅允许新增科目；若某科目编号在库中已存在，整次导入失败且不提交。

请求：multipart/form-data，需登录，请求头：Authorization: Bearer <token>

方式 A（表单中带账套、年度）

POST /api/accounts/import_excel

表单字段：
- file（file，必填）Excel 文件，字段名必须为 file
- account_book_code（string，必填）账套编码
- fiscal_year（number，必填）会计年度（4 位整数）
- mode（string，否）upsert（默认）或 append

方式 B（路径中带账套、年度）

POST /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/import_excel

表单字段：
- file（file，必填）Excel 文件
- mode（string，否）upsert 或 append，默认 upsert

服务端会校验 account_book_fiscal_year 是否存在；不存在时返回 404。

表头（在前 15 行内自动匹配一行作为表头）

| 逻辑列 | 必填 | 表头（任选一列名匹配即可） |
|--------|------|----------------------------|
| 科目编号 | 是 | 科目编号、科目编码、科目代码 |
| 科目名称 | 是 | 科目名称 |
| 科目级次 | 是 | 科目级次 |
| 科目类型 | 是 | 科目类型 |
| 余额方向 | 是 | 余额方向 |
| 是否末级 | 否 | 是否末级（语义与单条创建/Share 导入一致：1/是 等为末级） |
| 是否启用 | 否 | 是否启用（与 Share 导入一致） |
| 上级科目编号 | 否 | 上级科目编号、上级科目、父科目编号 |
| 辅助核算项 | 否 | 辅助核算项、辅助核算、辅助项；多值分隔符：, ， 、 ; ； |

数据行按科目级次升序、再按科目编号写入。空行跳过并计入统计 stats.rows_skipped。

成功响应示例

{
  "success": true,
  "message": "会计科目导入成功",
  "stats": {
    "accounts_inserted": 10,
    "accounts_updated": 5,
    "auxiliaries_created": 8,
    "rows_skipped": 2
  }
}

依赖：openpyxl（未安装时接口返回 500 并提示 pip install openpyxl）。



二、科目辅助核算 AccountAuxiliary

对应数据表 account_auxiliary，主键为 (account_book_code, fiscal_year, account_code, auxiliary_item_code)。
依赖：同一账套、年度、科目编号必须在 account 表中已存在。

2.1 分页列表

方式 A（查询参数）

GET /api/account_auxiliaries







查询参数



类型



必填



说明





account_book_code



string



是



账套编码





fiscal_year



number



是



会计年度





account_code



string



否



科目编号，精确匹配





auxiliary_item_code



string



否



辅助项编号，模糊匹配





auxiliary_item_name



string



否



辅助项名称，模糊匹配





status



number



否



状态：1/0





page



number



否



页码





page_size



number



否



每页条数

方式 B（路径限定某一科目）

GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}/auxiliaries

等价于在方式 A 中固定 account_code 为路径中的科目编号；仍可使用 auxiliary_item_code、auxiliary_item_name、status、page、page_size 等查询参数。

成功响应示例

{
  "success": true,
  "items": [
    {
      "account_book_code": "001",
      "fiscal_year": 2024,
      "account_code": "1001",
      "auxiliary_item_code": "1",
      "auxiliary_item_name": "项目",
      "corresponding_archive": "XM01",
      "auxiliary_item_description": null,
      "status": 1,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}



2.2 单条详情

GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}/auxiliaries/{auxiliary_item_code}

成功响应

{
  "success": true,
  "data": { }
}



2.3 新建辅助核算

方式 A（JSON 中带账套、年度、科目）

POST /api/account_auxiliaries
Content-Type: application/json

方式 B（路径中带账套、年度、科目）

POST /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}/auxiliaries
Content-Type: application/json

请求体字段







字段



类型



必填



说明





account_book_code



string



方式 A 必填



账套编码





fiscal_year



number



方式 A 必填



会计年度





account_code



string



方式 A 必填



科目编号（方式 B 以路径为准，可省略或与路径一致）





auxiliary_item_code



string



是



辅助项编号





auxiliary_item_name



string



是



辅助项名称





corresponding_archive



string



否



对应档案（自定义档案项编码，与 custom_archive_item.archive_item_code 一致）





auxiliary_item_description



string



否



辅助项描述





status



number



否



默认 1





sync_custom_archive



boolean



否



默认 true；为 true 且 corresponding_archive 非空时，同步写入自定义档案表





archive_item_name



string



否



同步时档案项名称；不传则用 corresponding_archive 作为名称





archive_item_desc



string



否



同步时档案项描述





archive_value_desc



string



否



同步时档案值描述

自定义档案同步规则（创建 / 更新辅助核算时）





当 sync_custom_archive=true（默认）且 corresponding_archive 非空时，在同一事务内 upsert：





custom_archive_item：archive_item_code = corresponding_archive



custom_archive_value：archive_item_code = corresponding_archive，archive_value_code = auxiliary_item_code，archive_value_name = auxiliary_item_name



若 corresponding_archive 为空，则不会写入自定义档案表（与 SHARE 导入语义一致：对应档案 为空时无档案维度）。



若需仅维护 account_auxiliary 而不动档案表，传 sync_custom_archive=false。

成功响应

{
  "success": true,
  "message": "辅助核算已创建",
  "data": { },
  "custom_archive_sync": {
    "created_item": true,
    "updated_item": false,
    "created_value": true,
    "updated_value": false
  }
}

custom_archive_sync 仅在发生同步时出现。



2.4 更新辅助核算

主键四字段 不可修改。

PUT /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}/auxiliaries/{auxiliary_item_code}
Content-Type: application/json

可传：auxiliary_item_name、corresponding_archive、auxiliary_item_description、status、sync_custom_archive、archive_item_name、archive_item_desc、archive_value_desc。

更新后若 corresponding_archive 非空且 sync_custom_archive=true（默认），会按 2.3 中规则再次 upsert 自定义档案项/值。

成功响应

{
  "success": true,
  "message": "辅助核算已更新",
  "data": { },
  "custom_archive_sync": {
    "created_item": false,
    "updated_item": true,
    "created_value": false,
    "updated_value": true
  }
}



2.5 删除辅助核算

DELETE /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/accounts/{account_code}/auxiliaries/{auxiliary_item_code}

成功响应

{
  "success": true,
  "message": "辅助核算已删除"
}



三、错误响应

失败时统一形如：

{
  "success": false,
  "message": "错误说明"
}

常见 HTTP 状态码：400（参数或业务校验失败）、404（账套年度或资源不存在）、500（服务器异常）。



四、相关接口（非本蓝图）

以下接口在 routes/custom_archive.py 中实现，用于「科目 + 辅助项 + 自定义档案值」的聚合展示，不是 account / account_auxiliary 的 CRUD：





GET /api/account_auxiliary_mapping



GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/account_auxiliary_mapping

详见该模块内注释或单独文档。



五、调用示例（curl）

# 科目列表（路径形式）
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5000/api/account_books/001/fiscal_years/2024/accounts?page=1&page_size=20"

# 新建辅助核算（路径形式）
curl -s -X POST -H "Authorization: Bearer YOUR_TOKEN" -H "Content-Type: application/json" \
  -d "{\"auxiliary_item_code\":\"1\",\"auxiliary_item_name\":\"项目\",\"corresponding_archive\":\"XM01\"}" \
  "http://localhost:5000/api/account_books/001/fiscal_years/2024/accounts/1001/auxiliaries"

将 YOUR_TOKEN、主机与端口替换为实际环境配置。