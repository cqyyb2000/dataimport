import api from './index';

// 登录相关 API
export const login = (username, password) => {
  return api.post('/login', { username, password });
};

// 登出
export const logout = () => {
  return api.post('/logout');
};

// 获取当前用户信息
export const getCurrentUser = () => {
  return api.get('/users/current');
}; 