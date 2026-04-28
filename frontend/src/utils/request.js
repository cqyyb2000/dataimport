import axios from 'axios'
import { getToken, clearAuthData, isTokenExpiringSoon, updateTokenExpiration } from '@/utils/auth'
import router from '@/router'
import { login } from '@/api'

const service = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL,
  timeout: 30000 // 增加到30秒，避免大数据量查询超时
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
      
      // 如果token即将过期，自动更新过期时间
      if (isTokenExpiringSoon()) {
        updateTokenExpiration()
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 如果请求成功，更新token过期时间
    if (response.config.headers['Authorization']) {
      updateTokenExpiration()
    }
    return response
  },
  async error => {
    if (error.response) {
      let currentUser
      switch (error.response.status) {
        case 401:
          // token 过期或无效
          currentUser = JSON.parse(localStorage.getItem('user') || '{}')
          if (currentUser.username) {
            try {
              // 尝试使用当前用户信息重新登录
              const response = await login(currentUser.username, '')
              if (response.data.success) {
                // 重新登录成功，更新token
                localStorage.setItem('token', response.data.token)
                updateTokenExpiration()
                // 重试之前失败的请求
                const config = error.config
                config.headers['Authorization'] = `Bearer ${response.data.token}`
                return service(config)
              }
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError)
            }
          }
          // 如果刷新token失败，清除认证数据并重定向到登录页
          clearAuthData()
          router.push('/login')
          break
        default:
          console.error('请求错误:', error.response.data)
      }
    }
    return Promise.reject(error)
  }
)

export default service 