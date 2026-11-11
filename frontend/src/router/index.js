/* eslint-disable no-unused-vars */
import { createRouter, createWebHistory } from 'vue-router';
import UserLogin from '@/views/UserLogin.vue';
import HomeView from '@/views/HomeView.vue';
import { generateRoutesFromMenu } from '@/utils/dynamicRoutes';
import { isAuthenticated, clearAuthData } from '@/utils/auth';

//router/index.js

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'login',
    component: UserLogin
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true },
    redirect: '/home/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/DashBoard.vue'),
        meta: { requiresAuth: true, title: '数据看板', isDefault: true }
      },
      {
        path: 'accountInfo/list',
        name: 'accountBookList',
        component: () => import('@/views/accountInfo/AccountBookList.vue'),
        meta: { requiresAuth: true, title: '账套管理' }
      },
      {
        path: 'accountInfo/detail/:code',
        name: 'accountBookDetail',
        component: () => import('@/views/accountInfo/AccountBookDetail.vue'),
        meta: { requiresAuth: true, title: '账套详情' }
      },
      {
        path: 'accountInfo/CustomArchiveManage',
        name: 'customArchiveManage',
        component: () => import('@/views/accountInfo/CustomArchiveManage.vue'),
        meta: { requiresAuth: true, title: '自定义档案管理' }
      },
      {
        path: 'accountInfo/customArchiveManage',
        name: 'customArchiveManageLower',
        component: () => import('@/views/accountInfo/CustomArchiveManage.vue'),
        meta: { requiresAuth: true, title: '自定义档案管理' }
      },
      {
        path: 'glvoucher/upload',
        name: 'glUpload',
        component: () => import('@/views/glvoucher/GlUpload.vue'),
        meta: { requiresAuth: true, title: '凭证GL.xml引入' }
      },
      {
        path: 'glvoucher/list',
        name: 'voucherList',
        component: () => import('@/views/glvoucher/VoucherList.vue'),
        meta: { requiresAuth: true, title: '凭证列表' }
      },
      {
        path: 'glvoucher/entry',
        name: 'voucherEntry',
        component: () => import('@/views/glvoucher/VoucherEntry.vue'),
        meta: { requiresAuth: true, title: '凭证录入' }
      },
      {
        path: 'glvoucher/data-bookkeeping',
        name: 'dataBookkeeping',
        component: () => import('@/views/glvoucher/DataBookkeeping.vue'),
        meta: { requiresAuth: true, title: '数据记账' }
      },
      {
        path: 'reportCenter/account-balance',
        name: 'accountBalanceReport',
        component: () => import('@/views/reportCenter/AccountBalanceReport.vue'),
        meta: { requiresAuth: true, title: '科目余额表' }
      },
      {
        path: '/accountInfo/AccountArchiveManage',
        name: 'AccountArchiveManage',
        component: () => import('@/views/accountInfo/AccountArchiveManage.vue'),
        meta: { requiresAuth: true, title: '科目档案' }
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL || '/'),
  routes,
});

// 动态注册菜单路由
function addDynamicRoutes() {
  const menus = JSON.parse(localStorage.getItem('menus') || '[]');
  const dynamicRoutes = generateRoutesFromMenu(menus);
  dynamicRoutes.forEach(route => {
    router.addRoute('home', route); // 修改为使用 'home' 作为父路由名称
  });
}

// 页面刷新时自动注册动态路由
addDynamicRoutes();

// 全局前置守卫，用于验证登录状态
router.beforeEach((to, from, next) => {
  // 访问根路径时，未登录跳转登录页，已登录跳转首页
  if (to.path === '/') {
    next(isAuthenticated() ? '/home' : '/login');
    return;
  }
  if (to.meta.requiresAuth) {
    if (!isAuthenticated()) {
      clearAuthData();
      next('/login');
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;
