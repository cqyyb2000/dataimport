import api from './index'

/**
 * GL.xml 总账类相关 API
 */
export const glApi = {
  /**
   * 上传GL.xml总账文件
   * @param {File} file - 要上传的 GL.xml 文件
   * @param {string} accountBookCode - 账套编码（必填）
   * @param {number|null} fiscalYear - 会计年度（可选）
   * @param {Function} onUploadProgress - 上传进度回调函数
   * @returns {Promise} 上传结果
   */
  uploadGlFile(file, accountBookCode, fiscalYear = null, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_book_code', accountBookCode)
    
    // 如果提供了会计年度，添加到表单数据中
    if (fiscalYear !== null && fiscalYear !== undefined && fiscalYear !== '') {
      formData.append('fiscal_year', fiscalYear)
    }
    
    // 输出完整的接口调用路径
    const baseURL = api.defaults.baseURL || ''
    const fullPath = `${baseURL}/gl/upload`
    console.log('上传接口完整路径:', fullPath)
    console.log('上传文件:', file.name, '文件大小:', file.size, 'bytes')
    console.log('账套编码:', accountBookCode, '会计年度:', fiscalYear)
    
    return api.post('/gl/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000, // 5分钟超时，大文件上传需要更长时间
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(percentCompleted)
        }
      }
    })
  },

  /**
   * 上传「凭证导入临时表」样式 Excel（凭证明细 → gl_voucher / gl_voucher_entry / gl_voucher_entry_auxiliary）
   * @param {File} file - .xlsx / .xlsm
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度（必填）
   * @param {Function} onUploadProgress - 进度回调
   */
  uploadVoucherExcel(file, accountBookCode, fiscalYear, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_book_code', accountBookCode)
    formData.append('fiscal_year', fiscalYear)
    return api.post('/vouchers/import_excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000,
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(percentCompleted)
        }
      }
    })
  },

  /**
   * 按账套、年度从凭证明细重算总账级科目余额（写入 gl_account_balance）
   * POST /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/gl_account_balance/recalculate_from_vouchers
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {Object} [payload] - 可选 { level_pattern: '422' }，每位为一级编码长度增量(1-9)，累计为各级总长度；不传则仅按凭证明细科目出账
   */
  recalculateAccountBalanceFromVouchers(accountBookCode, fiscalYear, payload = {}) {
    const body = {}
    if (payload.level_pattern != null && String(payload.level_pattern).trim() !== '') {
      body.level_pattern = String(payload.level_pattern).trim()
    }
    return api.post(
      `/account_books/${encodeURIComponent(accountBookCode)}/fiscal_years/${fiscalYear}/gl_account_balance/recalculate_from_vouchers`,
      Object.keys(body).length ? body : undefined
    )
  },

  /**
   * 科目余额表分页查询
   * GET /api/account_books/{code}/fiscal_years/{year}/gl_account_balance
   * @param {string} accountBookCode
   * @param {number} fiscalYear
   * @param {Object} [params] period_number, period_start, period_end, account_code, account_name, summary_only, page, page_size
   * 树懒加载：lazy_tree=true、period_number、parent_key（根级用 __root__ 或省略由前端传）
   */
  listAccountBalance(accountBookCode, fiscalYear, params = {}) {
    return api.get(
      `/account_books/${encodeURIComponent(accountBookCode)}/fiscal_years/${fiscalYear}/gl_account_balance`,
      { params }
    )
  },

  /**
   * 科目余额表导出 Excel（返回 blob 下载）
   * GET .../gl_account_balance/export
   * @param {string} accountBookCode
   * @param {number} fiscalYear
   * @param {Object} [params] 与 list 相同筛选
   * @param {import('axios').AxiosRequestConfig} [config] responseType: 'blob' 在调用方传入
   */
  exportAccountBalanceUrl(accountBookCode, fiscalYear, params = {}) {
    const usp = new URLSearchParams()
    Object.keys(params).forEach((k) => {
      const v = params[k]
      if (v !== null && v !== undefined && v !== '') {
        usp.set(k, v)
      }
    })
    const q = usp.toString()
    const base = `/account_books/${encodeURIComponent(accountBookCode)}/fiscal_years/${fiscalYear}/gl_account_balance/export`
    return q ? `${base}?${q}` : base
  },

  /**
   * 下载科目余额表 Excel（axios blob，需自行 window.URL 触发下载或保存）
   */
  exportAccountBalanceBlob(accountBookCode, fiscalYear, params = {}) {
    const p = { ...params }
    return api.get(
      `/account_books/${encodeURIComponent(accountBookCode)}/fiscal_years/${fiscalYear}/gl_account_balance/export`,
      { params: p, responseType: 'blob', timeout: 300000 }
    )
  }
}

export default glApi
