# 总账类数据表设计说明

## 概述

本文档说明总账类（GL.xml）对应的数据库表结构设计，依据 GB/T 24589.2-2010 数据接口规范。

## 表结构清单

总账类包含以下5个数据表：

1. **gl_base_info** - 总账基础信息表
2. **gl_voucher_type** - 记账凭证类型表
3. **gl_voucher** - 记账凭证表
4. **gl_voucher_entry** - 记账凭证分录行表
5. **gl_account_balance** - 科目余额表

## 设计原则

### 1. 账套+年度维度
- 所有表都关联 `account_book_code`（账套编码）和 `fiscal_year`（会计年度）
- 通过外键关联 `account_book_fiscal_year` 表
- 支持同一账套导入不同年度的总账数据

### 2. 数据完整性
- 必填字段设置为 `NOT NULL`
- 建立外键约束保证数据一致性
- 使用级联删除（CASCADE）保证数据清理

### 3. 索引设计
- 主键索引：保证唯一性
- 外键索引：提高关联查询性能
- 业务索引：按常用查询条件建立索引（年度、期间、凭证编号、科目编号等）

## 表结构详细说明

### 1. gl_base_info（总账基础信息表）

**用途**：存储总账的基础配置信息

**主键**：`(account_book_code, fiscal_year)`

**关键字段**：
- `structure_separator` - 结构分隔符
- `account_code_rule` - 会计科目编号规则
- `voucher_header_ext_fields` - 凭证头可扩展字段结构
- `entry_line_ext_fields` - 分录行可扩展字段结构

**特点**：
- 每个账套每个年度只有一条记录
- 存储总账的配置信息

### 2. gl_voucher_type（记账凭证类型表）

**用途**：定义记账凭证类型

**主键**：`(account_book_code, fiscal_year, voucher_type_code)`

**关键字段**：
- `voucher_type_code` - 记账凭证类型编号（必填）
- `voucher_type_name` - 记账凭证类型名称（必填）
- `voucher_type_abbreviation` - 记账凭证类型简称（可选）

**特点**：
- 同一账套同一年度下凭证类型编号唯一
- 被 `gl_voucher` 表引用

### 3. gl_voucher（记账凭证表）

**用途**：存储记账凭证头信息

**主键**：`(account_book_code, fiscal_year, period_number, voucher_number)`

**关键字段**：
- `voucher_number` - 凭证编号（必填）
- `voucher_date` - 凭证日期（必填，格式：YYYYMMDD）
- `fiscal_year` - 会计年度（必填）
- `period_number` - 会计期间号（必填；**0 表示期初凭证**，1–12 为各月，13 为调整期等，与 `gl.xml`/财政「凭证导入临时表」一致）
- `voucher_type_code` - 记账凭证类型编号（必填，外键；Excel 导入时若仅按期间区分，可自动使用 `QC` 期初凭证 / `JZ` 记账凭证，见 `services/voucher_detail_excel_import.py`）
- `prepared_by` - 制单人
- `reviewed_by` - 审核人
- `posted_by` - 记账人
- `voucher_status` - 凭证状态

**索引**：
- `idx_fiscal_year_period` - 按年度和期间查询
- `idx_voucher_number` - 按凭证编号查询
- `idx_voucher_date` - 按凭证日期查询
- `idx_voucher_type_code` - 按凭证类型查询

**特点**：
- 同一账套同一年度同一期间下凭证编号唯一
- 关联凭证类型表
- 被分录行表引用

### 4. gl_voucher_entry（记账凭证分录行表）

**用途**：存储记账凭证的分录明细

**主键**：`(account_book_code, fiscal_year, period_number, voucher_number, entry_line_number)`

**关键字段**：
- `voucher_number` - 凭证编号（必填，外键）
- `entry_line_number` - 分录行号（必填）
- `account_code` - 科目编号（必填）
- `debit_amount` - 借方金额
- `credit_amount` - 贷方金额
- `currency_code` - 币种编码
- `exchange_rate` - 汇率
- `original_currency_debit_amount` - 原币借方金额
- `original_currency_credit_amount` - 原币贷方金额
- `quantity` - 数量
- `unit_price` - 单价
- `auxiliary_item_code` - 辅助项编号
- `internal_organization_code` - 内设机构编码
- `project_code` - 项目编码
- `department_code` - 部门编码
- `employee_code` - 人员编码
- `unit_code` - 单位往来编码
- `personal_code` - 个人往来编码

**索引**：
- `idx_voucher_number` - 按凭证编号查询
- `idx_account_code` - 按科目编号查询
- `idx_fiscal_year_period` - 按年度和期间查询

**特点**：
- 同一凭证下分录行号唯一
- 关联凭证表（级联删除）
- 支持多币种、辅助核算、数量金额等扩展字段

### 5. gl_account_balance（科目余额表）

**用途**：存储科目的期初余额和期末余额

**主键**：`id`（自增主键）

**唯一索引**：`uk_account_balance` - `(account_book_code, fiscal_year, period_number, account_code, currency_code)`

**关键字段**：
- `account_code` - 科目编号（必填）
- `fiscal_year` - 会计年度（必填）
- `period_number` - 会计期间号（必填，0表示期初）
- `opening_balance` - 期初余额
- `opening_balance_direction` - 期初余额方向（借/贷）
- `current_period_debit_amount` - 本期借方发生额
- `current_period_credit_amount` - 本期贷方发生额
- `closing_balance` - 期末余额
- `closing_balance_direction` - 期末余额方向（借/贷）
- `currency_code` - 币种编码（可选）
- `ParentCode` - 父级科目编号（可选）

**索引**：
- `idx_fiscal_year_period` - 按年度和期间查询
- `idx_account_code` - 按科目编号查询
- `idx_account_book_fiscal_year` - 按账套和年度查询
- `idx_currency_code` - 按币种

**特点**：
- 使用自增ID作为主键；唯一约束为账套+年度+期间+科目+币种
- 支持多币种（不同 `currency_code` 分行）
- 期间号为0表示期初余额

## 数据关系图

```
account_book_fiscal_year (账套年度表)
    ├── gl_base_info (总账基础信息)
    ├── gl_voucher_type (凭证类型)
    │       └── gl_voucher (凭证)
    │               └── gl_voucher_entry (凭证分录行)
    └── gl_account_balance (科目余额)
```

## 注意事项

### 1. 凭证借贷平衡验证
- 同一凭证的所有分录行，借方金额合计应等于贷方金额合计
- 需要在应用层进行验证

### 2. 科目余额一致性
- 科目余额应与凭证数据一致
- 期末余额 = 期初余额 + 本期借方发生额 - 本期贷方发生额
- 需要在应用层进行验证

### 3. 期间号说明
- 凭证表与分录行表：期间号可为 **0（期初凭证）**、1–12（月度）或 13（调整期等），与财政「凭证导入临时表」/业务约定一致
- 科目余额表：期间号为 0（期初）、1–12（各期间）

### 4. 可选字段处理
- 科目余额表中的可选字段（`currency_code`、`ParentCode`）可能为 NULL
- MySQL 中唯一索引对 NULL 的语义需结合版本与需求理解；同键唯一定位以「账套+年+期+科目+币种」为准
- 查询时需要注意 NULL 值的处理

### 5. 数据导入顺序
1. 先导入账套年度（account_book_fiscal_year）
2. 导入总账基础信息（gl_base_info）
3. 导入凭证类型（gl_voucher_type）
4. 导入凭证（gl_voucher）
5. 导入凭证分录行（gl_voucher_entry）
6. 导入科目余额（gl_account_balance）

## 索引优化建议

### 常用查询场景
1. **按账套+年度查询凭证**
   - 使用：`idx_fiscal_year_period` 或 `idx_account_book_fiscal_year`

2. **按凭证编号查询**
   - 使用：`idx_voucher_number`

3. **按科目查询余额**
   - 使用：`idx_account_code` + `idx_fiscal_year_period`

4. **按期间查询余额**
   - 使用：`idx_fiscal_year_period`

## 数据验证规则

### 1. 凭证验证
- 凭证编号在同一账套+年度+期间下唯一
- 凭证日期格式正确（YYYYMMDD）
- 凭证类型编号存在

### 2. 分录行验证
- 分录行号在同一凭证下唯一
- 科目编号存在（需关联会计科目表）
- 借方金额和贷方金额至少有一个不为空
- 同一凭证的借贷金额平衡

### 3. 科目余额验证
- 科目编号存在（需关联会计科目表）
- 期初余额方向与期末余额方向一致（或符合科目余额方向）
- 余额计算正确：期末余额 = 期初余额 + 本期借方 - 本期贷方

## 扩展说明

### 1. 多年度支持
- 所有表都包含 `fiscal_year` 字段
- 支持同一账套导入多个年度的数据
- 查询时需要指定年度范围

### 2. 辅助核算支持
- 分录行表和科目余额表都支持辅助核算字段
- 包括：辅助项、内设机构、项目、部门、人员、单位往来、个人往来

### 3. 多币种支持
- 分录行表和科目余额表都支持多币种
- 包含原币金额和汇率字段

### 4. 数量金额支持
- 分录行表支持数量金额核算
- 包含数量和单价字段

---

**文档版本**：1.0  
**最后更新**：2026-02  
**依据标准**：GB/T 24589.2-2010
