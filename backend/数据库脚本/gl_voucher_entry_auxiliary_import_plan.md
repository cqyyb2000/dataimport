# 凭证分录辅助项导入实施计划

## 一、需求分析

### 1.1 数据来源（GL.xml 扁平格式）

```xml
<记账凭证>
  <科目编号>60010102</科目编号>
  <辅助项1编号>001</辅助项1编号>
  <辅助项2编号>2081101</辅助项2编号>
  <辅助项3编号/>
  ...
  <辅助项30编号/>
</记账凭证>
```

### 1.2 字段映射规则

| XML 字段 | 解析逻辑 | 目标表字段 | 说明 |
|---------|---------|-----------|------|
| 科目编号 | 直接取值 | `account_code` | 如 60010102 |
| 辅助项N编号 | 标签中的整数 N | `auxiliary_item_sequence` | 如 辅助项1编号 → 1 |
| 辅助项N编号 | 标签内的取值 | `auxiliary_value` | 如 001、2081101 |
| - | 从 account_auxiliary 查询 | `auxiliary_item_name` | 见下方查询逻辑 |

### 1.3 account_auxiliary 查询逻辑

根据 `(account_book_code, fiscal_year, account_code, auxiliary_item_code)` 查询 `account_auxiliary`：

- `account_book_code`：导入参数
- `fiscal_year`：导入参数
- `account_code`：来自 科目编号（如 60010102）
- `auxiliary_item_code`：辅助项序号转为字符串（如 1 → "1"）

查询结果取 `auxiliary_item_name`（如：单位往来、项目）填入 `gl_voucher_entry_auxiliary.auxiliary_item_name`。

若未查到，`auxiliary_item_name` 可为 NULL。

---

## 二、当前代码分析

### 2.1 gl_xml_parser.py

- **现状**：`_element_to_dict` 已将所有子元素转为 key-value，包含 `辅助项1编号`、`辅助项2编号` 等。
- **结论**：无需修改。

### 2.2 gl_voucher_entry 导入逻辑（gl_import_service.py）

- **现状**：仅取第一个非空辅助项（`auxiliary_item_code`、`auxiliary_item_name`），未写入 `gl_voucher_entry_auxiliary`。
- **问题**：未处理 辅助项1～30 的明细，未调用辅助项导入。

### 2.3 gl_voucher_entry_auxiliary 表结构

- **现状**：SQL 已包含 `auxiliary_item_name` 字段。
- **需确认**：是否有 `archive_type` 字段。当前设计为 `auxiliary_item_name` 存储 `account_auxiliary.auxiliary_item_name`。

### 2.4 Model 层

- **现状**：无 `GLVoucherEntryAuxiliary` 模型。
- **结论**：需新增模型。

---

## 三、实施计划

### 步骤 1：确认/修正 gl_voucher_entry_auxiliary 表结构

**文件**：`数据库脚本/gl_voucher_entry_auxiliary.sql`

**检查**：
- `auxiliary_item_sequence`：辅助项序号 1–30
- `auxiliary_value`：辅助项取值（001、2081101 等）
- `account_code`：科目编号（60010102）
- `auxiliary_item_name`：来自 `account_auxiliary.auxiliary_item_name`（单位往来、项目等）

**结论**：当前 SQL 结构满足需求。

---

### 步骤 2：新增 GLVoucherEntryAuxiliary 模型

**文件**：`Model/gl_voucher_entry_auxiliary.py`（新建）

**内容**：
- 对应表 `gl_voucher_entry_auxiliary`
- 主键：`account_book_code, fiscal_year, period_number, voucher_number, entry_line_number, auxiliary_item_sequence`
- 外键：指向 `gl_voucher_entry`
- 字段与表结构一致
- 提供 `to_dict()` 方法

**文件**：`Model/__init__.py`  
**修改**：导入并导出 `GLVoucherEntryAuxiliary`。

---

### 步骤 3：新增 import_voucher_entry_auxiliaries 函数

**文件**：`services/gl_import_service.py`

**逻辑**：

1. 数据源：与 `import_voucher_entries` 相同（`记账凭证` 或 `记账凭证分录行`）。
2. 遍历每条记录：
   - 解析 `account_book_code`、`fiscal_year`、`period_number`、`voucher_number`、`entry_line_number`、`account_code`。
   - 遍历 i = 1..30：
     - 字段名：`辅助项{i}编号`
     - 取值 `val = row.get(f"辅助项{i}编号")`
     - 若 `val` 非空：
       - `auxiliary_item_sequence` = i
       - `auxiliary_value` = val
       - 查询 `AccountAuxiliary.query.filter_by(account_book_code=..., fiscal_year=..., account_code=account_code, auxiliary_item_code=str(i)).first()`
       - `auxiliary_item_name` = `aa.auxiliary_item_name if aa else None`
       - 若记录不存在则 `db.session.add(GLVoucherEntryAuxiliary(...))`
3. 依赖：必须先导入 `gl_voucher_entry`，再导入 `gl_voucher_entry_auxiliary`。
4. 注意：只处理 `gl_voucher_entry` 中已存在的分录，避免外键错误。

---

### 步骤 4：在 run_gl_import 中挂接导入

**文件**：`services/gl_import_service.py`

**修改**：
- 在 `import_voucher_entries` 之后调用 `import_voucher_entry_auxiliaries`。
- 在 `stats` 中增加 `"凭证分录辅助项": count`。

---

### 步骤 5：导入顺序与依赖

```
1. 会计科目
2. 科目辅助核算  ← 辅助项导入依赖此表
3. 总账基础信息
4. 记账凭证类型
5. 记账凭证
6. 记账凭证分录行  ← 辅助项导入依赖此表
7. 凭证分录辅助项  ← 新增
8. 科目余额
```

---

## 四、数据流示意

```
GL.xml 记账凭证
    │
    ├─ 科目编号: 60010102
    ├─ 辅助项1编号: 001
    ├─ 辅助项2编号: 2081101
    └─ ...
    │
    ▼
import_voucher_entry_auxiliaries
    │
    ├─ 辅助项1: 查询 account_auxiliary(account_code=60010102, auxiliary_item_code='1')
    │              → auxiliary_item_name = "单位往来"
    │   INSERT gl_voucher_entry_auxiliary(auxiliary_item_sequence=1, auxiliary_value='001', auxiliary_item_name='单位往来')
    │
    └─ 辅助项2: 查询 account_auxiliary(account_code=60010102, auxiliary_item_code='2')
                   → auxiliary_item_name = "项目"
        INSERT gl_voucher_entry_auxiliary(auxiliary_item_sequence=2, auxiliary_value='2081101', auxiliary_item_name='项目')
```

---

## 五、边界与异常

| 场景 | 处理方式 |
|-----|---------|
| 分录在 gl_voucher_entry 中不存在 | 跳过该分录的辅助项（或先保证分录已导入） |
| account_auxiliary 中无匹配记录 | `auxiliary_item_name` 置为 NULL |
| 辅助项值为空字符串 | 不插入该辅助项记录 |
| 同一 (分录, 辅助项序号) 已存在 | 按 upsert 更新或跳过 |

---

## 六、实施清单

- [ ] 1. 执行 `gl_voucher_entry_auxiliary.sql` 建表（如未执行）
- [ ] 2. 新建 `Model/gl_voucher_entry_auxiliary.py`
- [ ] 3. 在 `Model/__init__.py` 中导出 `GLVoucherEntryAuxiliary`
- [ ] 4. 在 `gl_import_service.py` 中新增 `import_voucher_entry_auxiliaries`
- [ ] 5. 在 `run_gl_import` 中调用 `import_voucher_entry_auxiliaries` 并更新 `stats`
