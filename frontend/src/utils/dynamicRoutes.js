/**
 * 动态路由配置
 */

// 组件映射对象 - 使用动态导入
const componentMap = {
  // 系统管理组件
  'system/UserManage': () => import('@/views/system/UserManage.vue'),
  'system/MenuManage': () => import('@/views/system/MenuManage.vue'),
  'system/PermissionManage': () => import('@/views/system/PermissionManage.vue'),

  // 基础档案管理组件
  'accountInfo/ShareUpload': () => import('@/views/accountInfo/ShareUpload.vue'),
  'accountInfo/AccountBookList': () => import('@/views/accountInfo/AccountBookList.vue'),
  'accountInfo/AccountBookDetail': () => import('@/views/accountInfo/AccountBookDetail.vue'),
  'accountInfo/CustomArchiveManage': () => import('@/views/accountInfo/CustomArchiveManage.vue'),
  'accountInfo/AccountArchiveManage': () => import('@/views/accountInfo/AccountArchiveManage.vue'),
  'glvoucher/GlUpload': () => import('@/views/glvoucher/GlUpload.vue'),
  'glvoucher/DataBookkeeping': () => import('@/views/glvoucher/DataBookkeeping.vue'),

  // 凭证管理组件
  'glvoucher/VoucherList': () => import('@/views/glvoucher/VoucherList.vue'),

  // 报表中心
  'reportCenter/AccountBalanceReport': () => import('@/views/reportCenter/AccountBalanceReport.vue')
}



export function generateRoutesFromMenu(menuList) {
  const routes = []
  menuList.forEach(menu => {
    if (menu.component) {
      // 标准化组件路径
      const safeComponent = menu.component.replace(/[\\/]+/g, '/').trim()
      console.log('处理菜单组件:', safeComponent)

      // 获取组件加载函数
      const component = componentMap[safeComponent]
      if (!component) {
        console.warn(`Warning: Component ${safeComponent} not found in componentMap`)
        return
      }

      routes.push({
        path: menu.path,
        name: menu.component,
        component: component,
        meta: { title: menu.name },
        children: menu.children ? generateRoutesFromMenu(menu.children) : []
      })
    } else if (menu.children && menu.children.length) {
      routes.push(...generateRoutesFromMenu(menu.children))
    }
  })
  return routes
}