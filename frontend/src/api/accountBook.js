import api from './index'

/**
 * 账套管理相关 API
 */
export const accountBookApi = {
  /**
   * 获取账套分页列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.account_book_code - 账套编码（可选）
   * @param {string} params.account_book_name - 账套名称（可选）
   * @param {string} params.accounting_entity - 核算主体（可选）
   * @param {string} params.status - 状态（可选）
   * @returns {Promise} 账套列表
   */
  getList(params = {}) {
    return api.get('/account_books', { params })
  },

  /**
   * 获取单个账套详情（含已导入的会计年度）
   * @param {string} accountBookCode - 账套编码
   * @returns {Promise} 账套详情
   */
  getDetail(accountBookCode) {
    return api.get(`/account_books/${accountBookCode}`)
  },

  /**
   * 创建账套
   * @param {Object} data - 账套数据
   * @param {string} data.account_book_code - 账套编码（必填）
   * @param {string} data.account_book_name - 账套名称（必填）
   * @param {string} data.accounting_entity - 核算主体（必填）
   * @param {string} data.unit_type - 单位类型（必填）
   * @param {string} data.base_currency - 基础货币（必填）
   * @param {string} data.standard_version - 准则版本（必填）
   * @returns {Promise} 创建结果
   */
  create(data) {
    return api.post('/account_books', data)
  },

  /**
   * 更新账套
   * @param {string} accountBookCode - 账套编码
   * @param {Object} data - 更新的账套数据
   * @returns {Promise} 更新结果
   */
  update(accountBookCode, data) {
    return api.put(`/account_books/${accountBookCode}`, data)
  },

  /**
   * 删除账套（级联删除会计年度）
   * @param {string} accountBookCode - 账套编码
   * @returns {Promise} 删除结果
   */
  delete(accountBookCode) {
    return api.delete(`/account_books/${accountBookCode}`)
  },

  /**
   * 获取账套下的会计年度列表
   * @param {string} accountBookCode - 账套编码
   * @returns {Promise} 会计年度列表
   */
  getFiscalYears(accountBookCode) {
    return api.get(`/account_books/${accountBookCode}/fiscal_years`)
  },

  /**
   * 为账套添加会计年度
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度（1990-2100）
   * @returns {Promise} 添加结果
   */
  addFiscalYear(accountBookCode, fiscalYear) {
    return api.post(`/account_books/${accountBookCode}/fiscal_years`, {
      fiscal_year: fiscalYear
    })
  },

  /**
   * 删除账套下的某个会计年度
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @returns {Promise} 删除结果
   */
  deleteFiscalYear(accountBookCode, fiscalYear) {
    return api.delete(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}`)
  }
}

export default accountBookApi
