# 模型分组说明（Model）

本文档按“基础档案 / 权限菜单 / 总账业务”三类整理当前项目中的 ORM 实体与数据库表对应关系，便于开发、联调与数据排查。

## 一、基础档案

| 实体（Model 类） | 表名 | 中文说明 |
|---|---|---|
| `AccountBook` | `account_book` | 账套主表，存储账套基础信息。 |
| `AccountBookFiscalYear` | `account_book_fiscal_year` | 账套年度表，表示某账套在某会计年度下的数据范围。 |
| `Account` | `account` | 会计科目表，存储科目编码、名称、层级等信息。 |
| `AccountAuxiliary` | `account_auxiliary` | 科目辅助核算配置表，记录科目可挂接的辅助核算类型。 |
| `InternalOrganization` | `internal_organization` | 内设机构表，存储部门/机构等组织维度信息。 |
| `Item` | `item` | 项目档案表，存储项目编码、名称等基础档案信息。 |
| `CustomArchiveItem` | `custom_archive_item` | 自定义档案项定义表，定义自定义档案的字段结构。 |
| `CustomArchiveValue` | `custom_archive_value` | 自定义档案值表，存储自定义档案项的具体取值。 |
| `Currency` | `currency` | 币种表，存储币种编码、名称等信息。 |
| `ExchangeRateType` | `exchange_rate_type` | 汇率类型表，定义汇率类别（如即期、期末等）。 |

## 二、权限菜单

| 实体（Model 类） | 表名 | 中文说明 |
|---|---|---|
| `User` | `users` | 用户信息表，存储系统登录用户及基础资料。 |
| `Menu` | `menus` | 菜单表，定义系统菜单结构、路由及展示信息。 |
| `Permission` | `permissions` | 权限表，定义接口或功能的权限点。 |

## 三、总账业务

| 实体（Model 类） | 表名 | 中文说明 |
|---|---|---|
| `GLBaseInfo` | `gl_base_info` | 总账基础信息表，对应 GL.xml 的基础配置数据。 |
| `GLVoucherType` | `gl_voucher_type` | 记账凭证类型表，存储凭证类别/凭证字信息。 |
| `GLVoucher` | `gl_voucher` | 记账凭证主表（凭证头），存储凭证日期、编号、状态等。 |
| `GLVoucherEntry` | `gl_voucher_entry` | 记账凭证分录行表（凭证明细），存储借贷分录数据。 |
| `GLVoucherEntryAuxiliary` | `gl_voucher_entry_auxiliary` | 凭证分录辅助核算表，存储分录关联的辅助核算明细。 |
| `GLAccountBalance` | `gl_account_balance` | 科目余额表，存储期初、本期发生、期末等余额信息。 |

## 备注

- 以上分组基于当前项目 `Model` 目录中的 SQLAlchemy 模型定义。
- 若后续新增模型，请同步更新本文档，确保“实体-表名-业务分类”保持一致。
