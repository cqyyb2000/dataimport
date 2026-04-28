<template>
  <div class="home-container">
    <HomeHeader />
    <div class="content-container">
      <HomeSidebar :menuList="menuList" @menu-click="handleMenuClick" />
      <div class="main-container">
        <el-tabs
          v-model="activeTab"
          type="card"
          closable
          @tab-click="handleTabClick"
          @tab-remove="handleTabRemove"
          class="main-tabs"
        >
          <el-tab-pane
            v-for="item in visitedViews"
            :key="item.path"
            :label="item.title"
            :name="item.path"
            :closable="item.path !== '/home/dashboard'"
          >
          </el-tab-pane>
        </el-tabs>
        <div class="tab-content">
          <router-view v-slot="{ Component }">
            <keep-alive :include="['DocQuery']">
              <component :is="Component" :key="$route.fullPath" />
            </keep-alive>
          </router-view>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HomeHeader from '../components/HomeHeader.vue'
import HomeSidebar from '../components/HomeSidebar.vue'

const route = useRoute()
const router = useRouter()
const activeTab = ref('')
const visitedViews = ref([])
const menuList = ref([])

// 添加页签 - 移到顶部定义
const addTab = (view) => {
  // 检查是否存在相同路径或相同标题的页签（避免重复）
  const existingTab = visitedViews.value.find(v => 
    v.path === view.path || (v.title === view.title && v.title !== '未命名页面')
  )
  
  if (existingTab) {
    // 如果页面已存在，更新路径（可能路径格式不同但是同一个页面）并激活
    existingTab.path = view.path
    activeTab.value = view.path
  } else {
    // 如果页面不存在，则添加新标签
    visitedViews.value.push(view)
    activeTab.value = view.path
  }
}

// 初始化菜单数据
onMounted(() => {
  const menus = localStorage.getItem('menus')
  if (menus) {
    try {
      menuList.value = JSON.parse(menus)
      console.log('Initialized menuList:', menuList.value)
    } catch (error) {
      console.error('Failed to parse menus:', error)
      menuList.value = []
    }
  }
  
  // 自动添加仪表盘作为默认页签
  const dashboardTab = {
    path: '/home/dashboard',
    title: '数据看板'
  }
  addTab(dashboardTab)
  
  // 如果当前路径是 /home，则重定向到仪表盘
  if (route.path === '/home') {
    router.push('/home/dashboard')
  }
})

// 监听路由变化，添加页签
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/home') {
      // 如果访问的是 /home，重定向到仪表盘
      router.push('/home/dashboard')
      return
    }
    
    const view = {
      path: newPath,
      title: route.meta.title || '未命名页面'
    }
    // 无论页面是否存在，都调用 addTab，确保关闭后再次点击能重新打开
    addTab(view)
  },
  { immediate: true }
)

// 点击页签
const handleTabClick = (tab) => {
  router.push(tab.props.name)
}

// 关闭页签
const handleTabRemove = (targetPath) => {
  // 不允许关闭仪表盘页签
  if (targetPath === '/home/dashboard') {
    return
  }
  
  const tabs = visitedViews.value
  let activePath = activeTab.value
  
  if (activePath === targetPath) {
    tabs.forEach((tab, index) => {
      if (tab.path === targetPath) {
        const nextTab = tabs[index + 1] || tabs[index - 1]
        if (nextTab) {
          activePath = nextTab.path
        } else {
          // 如果没有其他页签，默认回到仪表盘
          activePath = '/home/dashboard'
        }
      }
    })
  }
  
  activeTab.value = activePath
  visitedViews.value = tabs.filter(tab => tab.path !== targetPath)
  
  // 确保至少保留仪表盘页签
  if (visitedViews.value.length === 0) {
    const dashboardTab = {
      path: '/home/dashboard',
      title: '数据看板'
    }
    visitedViews.value.push(dashboardTab)
    activeTab.value = '/home/dashboard'
  }
  
  router.push(activePath)
}

// 处理菜单点击
function handleMenuClick(view) {
  addTab({ path: view.path, title: view.title })
  router.push(view.path)
}
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.content-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: margin-left 0.3s;
}

.main-tabs {
  flex: none;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 20px;
}

:deep(.el-tabs__nav) {
  border: none;
}

:deep(.el-tabs__item) {
  height: 40px;
  line-height: 40px;
  border: 1px solid #e4e7ed;
  border-bottom: none;
  margin-right: 4px;
  border-radius: 4px 4px 0 0;
  background-color: #f5f7fa;
}

:deep(.el-tabs__item.is-active) {
  background-color: #fff;
  border-bottom-color: #fff;
}

/* 仪表盘页签的特殊样式 */
:deep(.el-tabs__item[id*="dashboard"]) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
}

:deep(.el-tabs__item[id*="dashboard"].is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-color: #fff;
}

:deep(.el-tabs__content) {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.el-header {
  background-color: #f5f5f5;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-aside {
  background-color: #333;
  color: white;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* 路由页面占满 tab 内容区，避免内容撑高导致分页等被挤出视口 */
.tab-content > * {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
}
</style>    