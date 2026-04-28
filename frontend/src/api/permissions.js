import api from './index';

// 权限管理相关接口
export const permissionApi = {
  // 获取所有用户列表（ID和用户名）
  getAllUsers: () => {
    return api.get('/users_permissions')
  },

  // 获取所有菜单
  getAllMenus: () => {
    return api.get('/menus')
  },

  // 获取用户权限
  getUserPermissions: (userId) => {
    return api.get(`/user_permissions/${userId}`)
  },

  // 更新用户权限
  updateUserPermissions: (userId, menuIds) => {
    return api.post(`/user_permissions/${userId}`, {
      menu_ids: menuIds
    })
  }
}; 