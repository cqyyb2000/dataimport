# 凭证查询接口使用说明

本文档说明凭证查询相关接口的调用方式。

## 接口列表

### 1. 凭证列表查询接口 ⚠️ **必需**

#### 方式一：使用查询参数（推荐）
```
GET /api/vouchers
```

**请求头：**
```
Authorization: Bearer <token>
```

**查询参数：**
- `account_book_code` (string, 必填) - 账套编码
- `fiscal_year` (number, 必填) - 会计年度
- `month_start` (number, 可选) - 会计月起始（1-12）
- `month_end` (number, 可选) - 会计月结束（1-12）
- `voucher_no` (string, 可选) - 凭证号（支持模糊查询）
- `summary` (string, 可选) - 摘要（支持模糊查询）
- `page` (number, 默认1) - 页码
- `page_size` (number, 默认10) - 每页数量，可选值：10, 20, 50, 100

**示例请求：**
```bash
# 基本查询
GET /api/vouchers?account_book_code=001&fiscal_year=2024

# 查询指定月份的凭证
GET /api/vouchers?account_book_code=001&fiscal_year=2024&month_start=1&month_end=3

# 按凭证号模糊查询
GET /api/vouchers?account_book_code=001&fiscal_year=2024&voucher_no=0001

# 按摘要模糊查询
GET /api/vouchers?account_book_code=001&fiscal_year=2024&summary=工资

# 分页查询
GET /api/vouchers?account_book_code=001&fiscal_year=2024&page=1&page_size=20
```

**响应示例：**
```json
{
  "success": true,
  "items": [
    {
      "account_book_code": "001",
      "account_book_name": "测试账套",
      "fiscal_year": 2024,
      "period_number": 1,
      "voucher_no": "0001",
      "summary": "凭证摘要",
      "debit_amount": 1000.00,
      "credit_amount": 1000.00,
      "auxiliary_items": "辅助项信息1; 辅助项信息2",
      "voucher_date": "20240101",
      "voucher_type_code": "001",
      "prepared_by": "张三",
      "reviewed_by": "李四",
      "posted_by": "王五",
      "voucher_status": "已记账",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

#### 方式二：使用路径参数
```
GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/vouchers
```

**示例请求：**
```bash
GET /api/account_books/001/fiscal_years/2024/vouchers?month_start=1&month_end=3&page=1&page_size=20
```

**响应格式：** 与方式一相同

---

### 2. 会计月份数据接口 ⚠️ **建议新增**

```
GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/months
```

**请求头：**
```
Authorization: Bearer <token>
```

**路径参数：**
- `account_book_code` (string, 必填) - 账套编码
- `fiscal_year` (number, 必填) - 会计年度

**示例请求：**
```bash
GET /api/account_books/001/fiscal_years/2024/months
```

**响应示例：**
```json
{
  "success": true,
  "months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}
```

**说明：** 返回指定账套和年度下已导入数据的会计月份列表（1-12），如果没有数据则返回空数组 `[]`。

---

### 3. 凭证详情接口

获取指定凭证的完整信息（凭证头 + 分录行），含辅助项展示（`archive_value_name` 用 `\` 分隔）。

---

#### 调用方式一：完整路径（推荐）

```
GET /api/vouchers/{account_book_code}/{fiscal_year}/{period_number}/{voucher_number}
```

| 项目 | 说明 |
|------|------|
| 请求头 | `Authorization: Bearer <token>` |
| 路径参数 | `account_book_code` 账套编码 |
| | `fiscal_year` 会计年度（如 2024） |
| | `period_number` 会计期间号（1-12） |
| | `voucher_number` 凭证编号 |

**示例：**
```http
GET /api/vouchers/XZ001/2021/1/JZ-01-0001
Authorization: Bearer <your_token>
```

---

#### 调用方式二：账套路径 + 查询参数

```
GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/vouchers/{voucher_number}
```

| 项目 | 说明 |
|------|------|
| 请求头 | `Authorization: Bearer <token>` |
| 路径参数 | `account_book_code` 账套编码 |
| | `fiscal_year` 会计年度 |
| | `voucher_number` 凭证编号 |
| 查询参数 | `period_number` (必填) 会计期间号（1-12） |

**示例：**
```http
GET /api/account_books/XZ001/fiscal_years/2021/vouchers/JZ-01-0001?period_number=1
Authorization: Bearer <your_token>
```

---

#### 响应结构

| 字段 | 说明 |
|------|------|
| `data` | 凭证完整数据 |
| `data.entries` | 分录行列表 |
| `data.entries[].auxiliary_item_values` | 有辅助项的分录才有；多个辅助项用 `\` 分隔的 `archive_value_name` |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "account_book_code": "XZ001",
    "account_book_name": "测试账套",
    "fiscal_year": 2021,
    "period_number": 1,
    "voucher_number": "JZ-01-0001",
    "voucher_date": "20210115",
    "voucher_type_code": "JZ",
    "attachment_count": 2,
    "prepared_by": "张三",
    "reviewed_by": "李四",
    "posted_by": "王五",
    "voucher_status": "已记账",
    "summary": "凭证摘要",
    "debit_amount": 1000.00,
    "credit_amount": 1000.00,
    "entries": [
      {
        "account_code": "1122",
        "summary": "分录摘要",
        "debit_amount": 1000.00,
        "credit_amount": null,
        "auxiliary_item_values": "某某单位\\某某项目"
      },
      {
        "account_code": "1001",
        "summary": "分录摘要",
        "debit_amount": null,
        "credit_amount": 1000.00
      }
    ]
  }
}
```

---

## 错误响应

所有接口在出错时都会返回以下格式：

```json
{
  "success": false,
  "message": "错误信息描述"
}
```

**常见错误码：**
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 使用示例（JavaScript/Axios）

```javascript
// 1. 获取凭证列表
async function getVoucherList(accountBookCode, fiscalYear, options = {}) {
  const params = new URLSearchParams({
    account_book_code: accountBookCode,
    fiscal_year: fiscalYear,
    ...options
  });
  
  const response = await axios.get(`/api/vouchers?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return response.data;
}

// 使用示例
const vouchers = await getVoucherList('001', 2024, {
  month_start: 1,
  month_end: 3,
  page: 1,
  page_size: 20
});

// 2. 获取会计月份列表
async function getMonths(accountBookCode, fiscalYear) {
  const response = await axios.get(
    `/api/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/months`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return response.data.months;
}

// 3. 获取凭证详情（方式一：完整路径）
async function getVoucherDetail(accountBookCode, fiscalYear, periodNumber, voucherNumber) {
  const response = await axios.get(
    `/api/vouchers/${accountBookCode}/${fiscalYear}/${periodNumber}/${voucherNumber}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.data.data;
}

// 3. 获取凭证详情（方式二：账套路径 + period_number 查询参数）
async function getVoucherDetailByAccountBook(accountBookCode, fiscalYear, voucherNumber, periodNumber) {
  const response = await axios.get(
    `/api/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/vouchers/${voucherNumber}`,
    {
      params: { period_number: periodNumber },
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.data.data;
}
```

---

## 注意事项

1. **认证要求**：所有接口都需要在请求头中携带有效的 JWT token
2. **账套和年度验证**：接口会自动验证账套编码和会计年度是否存在
3. **分页限制**：`page_size` 只能选择 10, 20, 50, 100 中的一个值
4. **月份范围**：`month_start` 和 `month_end` 必须在 1-12 之间，且 `month_start` 不能大于 `month_end`
5. **模糊查询**：`voucher_no` 和 `summary` 参数支持模糊查询（使用 LIKE）
6. **排序规则**：凭证列表按会计期间号（period_number）和凭证号（voucher_number）升序排序
7. **金额汇总**：列表接口中的 `debit_amount` 和 `credit_amount` 是该凭证所有分录行的汇总金额
