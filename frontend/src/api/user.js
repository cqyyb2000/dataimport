import api from './index';

// 用户管理相关 API
export const userApi = {
  // 获取用户列表
  getUsers: (params) => {
    console.log('API call - getUsers with params:', params)
    return api.get('/users', { params })
  },
  
  // 创建用户
  createUser: (userData) => {
    console.log('API call - createUser with data:', userData)
    return api.post('/create_user', userData)
  },
  
  // 更新用户
  updateUser: (id, userData) => {
    console.log('API call - updateUser:', { id, userData })
    return api.put(`/users/${id}`, userData)
  },
  
  // 删除用户
  deleteUser: (id) => {
    console.log('API call - deleteUser:', id)
    return api.delete(`/users/${id}`)
  },

  // 获取用户权限
  getUserPermissions: (userId) => {
    return api.get(`/users/${userId}/permissions`)
  },

  // 保存用户权限
  saveUserPermissions: (userId, menuIds) => {
    return api.post(`/users/${userId}/permissions`, { menu_ids: menuIds })
  }
}; 