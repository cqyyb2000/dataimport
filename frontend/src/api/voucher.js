import api from './index'

/**
 * 凭证管理相关 API
 * 接口说明见：凭证查询接口使用说明
 */
export const voucherApi = {
  /**
   * 凭证列表查询（方式一：查询参数，推荐）
   * GET /api/vouchers?account_book_code=001&fiscal_year=2024&page=1&page_size=10
   */
  getList(params = {}) {
    const queryParams = {}
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        queryParams[key] = params[key]
      }
    })
    return api.get('/vouchers', { params: queryParams })
  },

  /**
   * 会计月份列表
   * GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/months
   */
  getMonths(accountBookCode, fiscalYear) {
    return api.get(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/months`)
  },

  /**
   * 凭证详情（方式一：完整路径，推荐）
   * GET /api/vouchers/{account_book_code}/{fiscal_year}/{period_number}/{voucher_number}
   * 示例: GET /api/vouchers/XZ001/2021/1/JZ-01-0001
   */
  getDetail(accountBookCode, fiscalYear, periodNumber, voucherNumber) {
    return api.get(`/vouchers/${accountBookCode}/${fiscalYear}/${periodNumber}/${voucherNumber}`)
  },

  /**
   * 凭证类型列表（查询参数方式）
   * GET /api/voucher_types?account_book_code=ZT01&fiscal_year=2024
   */
  getVoucherTypes(accountBookCode, fiscalYear) {
    return api.get('/voucher_types', {
      params: {
        account_book_code: accountBookCode,
        fiscal_year: fiscalYear
      }
    })
  },

  /**
   * 凭证类型列表（路径参数方式）
   * GET /api/account_books/{account_book_code}/fiscal_years/{fiscal_year}/voucher_types
   */
  getVoucherTypesByPath(accountBookCode, fiscalYear) {
    return api.get(`/account_books/${accountBookCode}/fiscal_years/${fiscalYear}/voucher_types`)
  }
}

export default voucherApi
