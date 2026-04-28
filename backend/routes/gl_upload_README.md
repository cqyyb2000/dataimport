# GL.xml 上传功能说明

## 概述

本功能用于上传和导入总账类 GL.xml 文件，依据 GB/T 24589.2-2010 数据接口规范。

## API 端点

**POST** `/api/gl/upload`

## 功能说明

接收上传的 GL.xml 文件，解析后按类别保存或更新数据库：
- 总账基础信息
- 记账凭证类型
- 记账凭证
- 记账凭证分录行
- 科目余额

## 请求方式

### 方式一：表单上传（推荐）

```bash
curl -X POST http://localhost:5000/api/gl/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@GL.xml" \
  -F "account_book_code=XZ001" \
  -F "fiscal_year=2021"
```

### 方式二：JSON + 文件上传

```bash
curl -X POST http://localhost:5000/api/gl/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@GL.xml" \
  -F "account_book_code=XZ001" \
  -F "fiscal_year=2021"
```

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | GL.xml 文件 |
| account_book_code | String | 是 | 账套编码 |
| fiscal_year | Integer | 否 | 会计年度（如果不提供，会尝试从XML中提取） |

## 响应格式

### 成功响应（200）

```json
{
  "success": true,
  "message": "导入完成",
  "account_book_code": "XZ001",
  "fiscal_year": 2021,
  "stats": {
    "总账基础信息": 1,
    "记账凭证类型": 3,
    "记账凭证": 150,
    "记账凭证分录行": 450,
    "科目余额": 200
  }
}
```

### 失败响应（400）

```json
{
  "success": false,
  "message": "错误信息",
  "stats": {
    "总账基础信息": 0,
    "记账凭证类型": 0,
    "记账凭证": 0,
    "记账凭证分录行": 0,
    "科目余额": 0
  },
  "account_book_code": "XZ001",
  "fiscal_year": 2021
}
```

## 错误处理

### 常见错误

1. **文件不存在**
   ```json
   {
     "success": false,
     "message": "文件不存在: /path/to/GL.xml"
   }
   ```

2. **XML格式错误**
   ```json
   {
     "success": false,
     "message": "XML 格式错误: 根元素应为「总账」，当前为: 其他"
   }
   ```

3. **账套编码为空**
   ```json
   {
     "success": false,
     "message": "账套编码（account_book_code）不能为空"
   }
   ```

4. **无法确定会计年度**
   ```json
   {
     "success": false,
     "message": "无法确定会计年度，请提供fiscal_year参数或确保XML中包含会计年度信息"
   }
   ```

## 数据导入顺序

导入服务会按以下顺序处理数据：

1. **总账基础信息** - 每个账套每个年度只有一条记录
2. **记账凭证类型** - 凭证类型定义
3. **记账凭证** - 凭证头信息
4. **记账凭证分录行** - 凭证分录明细（依赖凭证）
5. **科目余额** - 科目余额数据

## 数据验证

### 凭证验证
- 凭证编号在同一账套+年度+期间下唯一
- 凭证类型必须存在
- 凭证分录借贷必须平衡（需要在应用层验证）

### 分录行验证
- 分录行号在同一凭证下唯一
- 科目编号必须存在（需关联会计科目表）
- 借方金额和贷方金额至少有一个不为空

### 科目余额验证
- 科目编号必须存在（需关联会计科目表）
- 期间号：0表示期初，1-12表示各期间

## 注意事项

1. **账套和年度**：导入前需要确保账套和年度已存在（可通过导入 SHARE.xml 创建）
2. **数据覆盖**：如果数据已存在，会更新现有记录
3. **事务处理**：所有数据在一个事务中处理，失败会回滚
4. **分录行期间号**：如果分录行中没有期间号，会从关联的凭证中获取

## 依赖关系

- 需要先导入 SHARE.xml（公共档案类）创建账套和年度
- 凭证类型必须在导入凭证之前导入
- 凭证必须在导入分录行之前导入

## 示例代码

### Python 请求示例

```python
import requests

url = "http://localhost:5000/api/gl/upload"
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}
files = {
    "file": open("GL.xml", "rb")
}
data = {
    "account_book_code": "XZ001",
    "fiscal_year": 2021
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### JavaScript 请求示例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('account_book_code', 'XZ001');
formData.append('fiscal_year', '2021');

fetch('http://localhost:5000/api/gl/upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## 文件结构

```
backend/
├── unit/
│   └── gl_xml_parser.py          # GL.xml 解析器
├── services/
│   └── gl_import_service.py      # GL.xml 导入服务
└── routes/
    └── gl_upload.py              # GL.xml 上传路由
```

---

**文档版本**：1.0  
**最后更新**：2026-02  
**依据标准**：GB/T 24589.2-2010
