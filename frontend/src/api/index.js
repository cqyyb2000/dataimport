import axios from 'axios';


// 设置 API 基础路径，需根据实际情况修改
// 如果使用 Nginx 反向代理，使用相对路径 '/api' 即可
// 这样无论从哪个客户端访问，都会通过 Nginx 代理到后端
const baseURL = process.env.VUE_APP_API_BASE_URL || '/api'; 
console.log('API base URL:', baseURL);
const api = axios.create({
  baseURL,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  console.log('Current token:', token);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('Request headers:', config.headers);
  } else {
    console.warn('No token found in localStorage');
  }
  return config;
}, error => {
  console.error('Request interceptor error:', error);
  return Promise.reject(error);
});

// 添加响应拦截器用于调试
api.interceptors.response.use(
  response => {
    console.log('Response status:', response.status);
    return response;
  },
  error => {
    console.error('Response error:', error.response || error);
    return Promise.reject(error);
  }
);

// 导出所有 API
export { userApi } from './user'
export { menuApi } from './menu'
export { login, logout, getCurrentUser } from './auth'
export { permissionApi } from './permissions'
export { shareApi } from './share'
export { accountBookApi } from './accountBook'
export { glApi } from './gl'
export { voucherApi } from './voucher'
export { accountApi, accountAuxiliaryApi } from './account'
export { bxApi } from './bx'



export default api;    