import api from './index';

// 菜单管理相关接口
export const menuApi = {
  // 创建菜单
  createMenu: (data) => api.post('/menus', data),
  
  // 获取所有菜单
  getAllMenus: () => api.get('/menus'),
  
  // 获取单个菜单
  getMenu: (menuId) => api.get(`/menus/${menuId}`),
  
  // 更新菜单
  updateMenu: (menuId, data) => api.put(`/menus/${menuId}`, data),
  
  // 删除菜单
  deleteMenu: (menuId) => api.delete(`/menus/${menuId}`)
}; 