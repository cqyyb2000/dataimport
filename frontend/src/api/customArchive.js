import api from './index'

/**
 * 自定义档案项 API
 */
export const customArchiveItemApi = {
  /**
   * 获取档案项分页列表
   * @param {Object} params - 查询参数
   */
  getList(params = {}) {
    return api.get('/custom_archive_items', { params })
  },

  /**
   * 获取档案项全量列表（后端支持 all=1）
   * @param {Object} params - 查询参数（如 account_book_code, fiscal_year, status）
   */
  getListAll(params = {}) {
    return api.get('/custom_archive_items', {
      params: {
        ...params,
        all: 1
      }
    })
  },

  /**
   * 获取单个档案项详情
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   */
  getDetail(accountBookCode, fiscalYear, archiveItemCode) {
    return api.get(`/custom_archive_items/${accountBookCode}/${fiscalYear}/${archiveItemCode}`)
  },

  /**
   * 创建档案项
   * @param {Object} data - 档案项数据
   */
  create(data) {
    return api.post('/custom_archive_items', data)
  },

  /**
   * 更新档案项
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {Object} data - 更新数据
   */
  update(accountBookCode, fiscalYear, archiveItemCode, data) {
    return api.put(`/custom_archive_items/${accountBookCode}/${fiscalYear}/${archiveItemCode}`, data)
  },

  /**
   * 删除档案项（级联删除下属值）
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   */
  delete(accountBookCode, fiscalYear, archiveItemCode) {
    return api.delete(`/custom_archive_items/${accountBookCode}/${fiscalYear}/${archiveItemCode}`)
  },

  /**
   * 获取档案项下所有值
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {boolean} asTree - 是否返回树形结构
   */
  getValues(accountBookCode, fiscalYear, archiveItemCode, asTree = false) {
    const params = asTree ? { as_tree: 1 } : {}
    return api.get(`/custom_archive_items/${accountBookCode}/${fiscalYear}/${archiveItemCode}/values`, { params })
  }
}

/**
 * 自定义档案值 API
 */
export const customArchiveValueApi = {
  /**
   * 获取档案值分页列表
   * @param {Object} params - 查询参数
   */
  getList(params = {}) {
    return api.get('/custom_archive_values', { params })
  },

  /**
   * 获取单个档案值详情
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {string} archiveValueCode - 档案值编码
   */
  getDetail(accountBookCode, fiscalYear, archiveItemCode, archiveValueCode) {
    return api.get(`/custom_archive_values/${accountBookCode}/${fiscalYear}/${archiveItemCode}/${archiveValueCode}`)
  },

  /**
   * 创建档案值
   * @param {Object} data - 档案值数据
   */
  create(data) {
    return api.post('/custom_archive_values', data)
  },

  /**
   * 更新档案值
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {string} archiveValueCode - 档案值编码
   * @param {Object} data - 更新数据
   */
  update(accountBookCode, fiscalYear, archiveItemCode, archiveValueCode, data) {
    return api.put(`/custom_archive_values/${accountBookCode}/${fiscalYear}/${archiveItemCode}/${archiveValueCode}`, data)
  },

  /**
   * 删除档案值（需先删除子节点）
   * @param {string} accountBookCode - 账套编码
   * @param {number} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {string} archiveValueCode - 档案值编码
   */
  delete(accountBookCode, fiscalYear, archiveItemCode, archiveValueCode) {
    return api.delete(`/custom_archive_values/${accountBookCode}/${fiscalYear}/${archiveItemCode}/${archiveValueCode}`)
  },

  /**
   * Excel导入档案值
   * @param {File} file - Excel文件
   * @param {string} accountBookCode - 账套编码
   * @param {number|string} fiscalYear - 会计年度
   * @param {string} archiveItemCode - 档案项编码
   * @param {Function} onUploadProgress - 上传进度回调
   */
  async importExcel(file, accountBookCode, fiscalYear, archiveItemCode, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_book_code', accountBookCode)
    formData.append('fiscal_year', fiscalYear)
    formData.append('archive_item_code', archiveItemCode)

    const requestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000,
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(percent)
        }
      }
    }

    return api.post('/custom_archive_values/import_excel', formData, requestConfig)
  }
}

export default {
  item: customArchiveItemApi,
  value: customArchiveValueApi
}
