# 会计科目表和辅助核算表优化说明

## 调整内容

### 1. 会计科目表 (account) 优化

#### 1.1 添加上级科目自引用外键约束
**调整前**：
- `parent_account_code` 字段只有索引，没有外键约束

**调整后**：
- 添加自引用外键约束：`fk_account_parent_account`
- 确保上级科目编号必须引用同一账套同一年度下存在的科目
- 使用 `ON DELETE RESTRICT`：防止删除有子科目的父科目
- 使用 `ON UPDATE CASCADE`：上级科目编号更新时自动更新

**SQL示例**：
```sql
CONSTRAINT `fk_account_parent_account` 
  FOREIGN KEY (`account_book_code`, `fiscal_year`, `parent_account_code`) 
  REFERENCES `account` (`account_book_code`, `fiscal_year`, `account_code`) 
  ON DELETE RESTRICT ON UPDATE CASCADE
```

**注意事项**：
- NULL值会被MySQL自动忽略，不会触发外键检查
- 自引用外键确保科目层级结构的完整性
- RESTRICT防止误删除有子科目的父科目

#### 1.2 添加联合索引
**调整**：
- 添加 `idx_account_book_fiscal_year` 联合索引
- 提高按账套+年度查询科目的性能

### 2. 科目辅助核算表 (account_auxiliary) 优化

#### 2.1 添加 status 字段
**调整原因**：
- 与其他公共档案表（item、currency、internal_organization等）保持一致
- 支持启用/停用辅助核算项

**字段定义**：
```sql
`status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用'
```

#### 2.2 添加联合索引
**调整**：
- 添加 `idx_account_book_fiscal_year_account` 联合索引
- 提高按账套+年度+科目查询辅助核算项的性能

**索引定义**：
```sql
KEY `idx_account_book_fiscal_year_account` (`account_book_code`, `fiscal_year`, `account_code`) USING BTREE
```

## 数据完整性改进

### 1. 科目层级完整性
- 通过自引用外键确保上级科目必须存在
- 防止数据不一致（如上级科目编号指向不存在的科目）

### 2. 辅助核算项管理
- 通过status字段支持启用/停用管理
- 与其他档案表保持一致的管理方式

## 性能优化

### 1. 索引优化
- **科目表**：添加 `(account_book_code, fiscal_year)` 联合索引
- **辅助核算表**：添加 `(account_book_code, fiscal_year, account_code)` 联合索引

### 2. 查询场景优化
- **按账套+年度查询所有科目**：使用 `idx_account_book_fiscal_year`
- **按科目查询所有辅助核算项**：使用 `idx_account_book_fiscal_year_account`
- **查询科目的子科目**：使用 `idx_parent_account_code`

## 外键约束说明

### 科目表外键约束

1. **fk_account_account_book_fiscal_year**
   - 关联：`account_book_fiscal_year`
   - 删除策略：CASCADE（删除账套年度时，级联删除所有科目）
   - 更新策略：CASCADE（账套年度更新时，自动更新）

2. **fk_account_parent_account**（新增）
   - 关联：`account`（自引用）
   - 删除策略：RESTRICT（有子科目时，禁止删除父科目）
   - 更新策略：CASCADE（上级科目编号更新时，自动更新）
   - NULL处理：parent_account_code为NULL时，不触发外键检查

### 辅助核算表外键约束

1. **fk_account_auxiliary_account_book_fiscal_year**
   - 关联：`account_book_fiscal_year`
   - 删除策略：CASCADE

2. **fk_account_auxiliary_account**
   - 关联：`account`
   - 删除策略：CASCADE（删除科目时，级联删除所有辅助核算项）
   - 更新策略：CASCADE

## Model 更新

### Account Model
- 添加自引用外键约束定义
- 保持字段类型一致性（SmallInteger对应SQL的tinyint）

### AccountAuxiliary Model
- 添加 `status` 字段
- 更新 `to_dict()` 方法包含status字段

## 使用注意事项

### 1. 科目删除
- 删除科目前，需要先删除或修改所有子科目的 `parent_account_code`
- 或者先删除所有子科目，再删除父科目

### 2. 数据导入顺序
- 导入科目时，建议先导入父科目，再导入子科目
- 如果XML中科目顺序不确定，可能需要多次导入或调整导入逻辑

### 3. 辅助核算项状态
- 默认状态为启用（status=1）
- 可以通过status字段控制辅助核算项的启用/停用

## 兼容性说明

### 向后兼容
- 新增的status字段有默认值，不影响现有数据
- 新增的索引不影响现有查询
- 新增的外键约束只影响新数据，现有数据需要满足约束条件

### 数据迁移
如果已有数据，执行以下SQL确保数据完整性：

```sql
-- 检查并修复无效的上级科目引用
UPDATE account a1
LEFT JOIN account a2 ON a1.account_book_code = a2.account_book_code 
  AND a1.fiscal_year = a2.fiscal_year 
  AND a1.parent_account_code = a2.account_code
SET a1.parent_account_code = NULL
WHERE a1.parent_account_code IS NOT NULL 
  AND a2.account_code IS NULL;

-- 为所有辅助核算项设置默认状态
UPDATE account_auxiliary SET status = 1 WHERE status IS NULL;
```

---

**文档版本**：1.0  
**最后更新**：2026-02  
**依据标准**：GB/T 24589.2-2010
