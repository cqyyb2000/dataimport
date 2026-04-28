import api from './index'

/**
 * 会计科目 API（见 src/api/accounts_API.md）
 */
export const accountApi = {
  /**
   * 分页列表（查询参数方式）
   */
  getList(params = {}) {
    const q = {}
    Object.keys(params).forEach((k) => {
      const v = params[k]
      if (v !== null && v !== undefined && v !== '') q[k] = v
    })
    return api.get('/accounts', { params: q })
  },

  /**
   * 分页列表（路径方式，与查询参数等价）
   */
  getListByPath(accountBookCode, fiscalYear, params = {}) {
    const q = {}
    Object.keys(params).forEach((k) => {
      const v = params[k]
      if (v !== null && v !== undefined && v !== '') q[k] = v
    })
    return api.get(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts`, { params: q })
  },

  getDetail(accountBookCode, fiscalYear, accountCode) {
    return api.get(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}`)
  },

  /** 方式 A：Body 含账套、年度 */
  create(data) {
    return api.post('/accounts', data)
  },

  /** 方式 B：路径含账套、年度 */
  createByPath(accountBookCode, fiscalYear, data) {
    return api.post(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts`, data)
  },

  update(accountBookCode, fiscalYear, accountCode, data) {
    return api.put(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}`, data)
  },

  delete(accountBookCode, fiscalYear, accountCode) {
    return api.delete(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}`)
  },

  /**
   * Excel 导入会计科目（方式 B：路径含账套、年度），见 accounts_API.md 1.6
   * @param {string} accountBookCode
   * @param {number|string} fiscalYear
   * @param {File} file
   * @param {{ mode?: 'upsert'|'append', onUploadProgress?: (percent: number) => void }} [options]
   */
  importExcelByPath(accountBookCode, fiscalYear, file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (options.mode) {
      formData.append('mode', options.mode)
    }
    const requestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000
    }
    if (options.onUploadProgress) {
      requestConfig.onUploadProgress = (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          options.onUploadProgress(percent)
        }
      }
    }
    return api.post(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/import_excel`,
      formData,
      requestConfig
    )
  }
}

/**
 * 新建/更新辅助核算时可传的「自定义档案同步」字段（见 accounts_API.md 2.3 / 2.4）
 * @typedef {Object} AccountAuxiliarySyncPayload
 * @property {boolean} [sync_custom_archive=true] - 为 true 且 corresponding_archive 非空时，同步 upsert 自定义档案项/值
 * @property {string} [archive_item_name] - 同步时档案项名称；不传则用 corresponding_archive 作为名称
 * @property {string} [archive_item_desc] - 同步时档案项描述
 * @property {string} [archive_value_desc] - 同步时档案值描述
 */

/**
 * 创建/更新成功时可选返回的同步结果
 * @typedef {Object} CustomArchiveSyncResult
 * @property {boolean} [created_item]
 * @property {boolean} [updated_item]
 * @property {boolean} [created_value]
 * @property {boolean} [updated_value]
 */

/**
 * 科目辅助核算 API
 */
export const accountAuxiliaryApi = {
  getList(params = {}) {
    const q = {}
    Object.keys(params).forEach((k) => {
      const v = params[k]
      if (v !== null && v !== undefined && v !== '') q[k] = v
    })
    return api.get('/account_auxiliaries', { params: q })
  },

  getListByAccount(accountBookCode, fiscalYear, accountCode, params = {}) {
    const q = {}
    Object.keys(params).forEach((k) => {
      const v = params[k]
      if (v !== null && v !== undefined && v !== '') q[k] = v
    })
    return api.get(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}/auxiliaries`,
      { params: q }
    )
  },

  getDetail(accountBookCode, fiscalYear, accountCode, auxiliaryItemCode) {
    return api.get(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}/auxiliaries/${auxiliaryItemCode}`
    )
  },

  /**
   * 新建辅助核算（方式 A）
   * @param {Object} data - 含 account_book_code、fiscal_year、account_code、auxiliary_item_code、auxiliary_item_name 等，以及 {@link AccountAuxiliarySyncPayload}
   * @returns {Promise<{ data: { success: boolean, message?: string, data?: object, custom_archive_sync?: CustomArchiveSyncResult } }>}
   */
  create(data) {
    return api.post('/account_auxiliaries', data)
  },

  /**
   * 新建辅助核算（方式 B）
   * @param {Object} data - 请求体；路径已含账套/年度/科目时可省略 account_book_code 等与路径重复字段；可含 {@link AccountAuxiliarySyncPayload}
   */
  createByPath(accountBookCode, fiscalYear, accountCode, data) {
    return api.post(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}/auxiliaries`,
      data
    )
  },

  /**
   * 更新辅助核算
   * @param {Object} data - 可传 auxiliary_item_name、corresponding_archive、auxiliary_item_description、status 及 {@link AccountAuxiliarySyncPayload}
   */
  update(accountBookCode, fiscalYear, accountCode, auxiliaryItemCode, data) {
    return api.put(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}/auxiliaries/${auxiliaryItemCode}`,
      data
    )
  },

  delete(accountBookCode, fiscalYear, accountCode, auxiliaryItemCode) {
    return api.delete(
      `/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/accounts/${accountCode}/auxiliaries/${auxiliaryItemCode}`
    )
  }
}

export default { accountApi, accountAuxiliaryApi }
