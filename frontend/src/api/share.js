import api from './index'

/**
 * 基础档案相关 API
 */
export const shareApi = {
  /**
   * 上传基础档案文件
   * @param {File} file - 要上传的 share.xml 文件
   * @param {Function} onUploadProgress - 上传进度回调函数
   * @returns {Promise} 上传结果
   */
  uploadShareFile(file, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    // 输出完整的接口调用路径
    const baseURL = api.defaults.baseURL || ''
    const fullPath = `${baseURL}/share/upload`
    console.log('上传接口完整路径:', fullPath)
    console.log('上传文件:', file.name, '文件大小:', file.size, 'bytes')
    
    return api.post('/share/upload', formData, {
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
  }
}

export default shareApi
