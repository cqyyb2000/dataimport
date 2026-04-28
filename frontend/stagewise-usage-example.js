// @stagewise/toolbar 在Vue项目中的使用示例

// 1. 在 main.js 中初始化 stagewise toolbar
/*
import { createApp } from 'vue'
import App from './App.vue'
import { initToolbar } from '@stagewise/toolbar'

const app = createApp(App)

// 初始化 stagewise toolbar
initToolbar({
  // 配置选项
  apiKey: 'your-api-key', // 如果需要的话
  environment: 'development', // 或 'production'
  // 其他配置...
})

app.mount('#app')
*/

// 2. 在Vue组件中使用 stagewise 插件UI
/*
<template>
  <div>
    <h1>档案管理系统</h1>
    <!-- 其他内容 -->
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useToolbar, Button, Panel } from '@stagewise/toolbar/plugin-ui'

// 使用 stagewise toolbar hook
const { addPlugin, removePlugin } = useToolbar()

onMounted(() => {
  // 添加自定义插件
  const pluginId = addPlugin({
    name: '档案管理助手',
    icon: '📁',
    component: () => import('./components/ArchiveHelper.vue'),
    position: 'right'
  })
  
  // 组件卸载时清理
  onUnmounted(() => {
    removePlugin(pluginId)
  })
})
</script>
*/

// 3. 创建自定义插件组件示例
/*
<!-- components/ArchiveHelper.vue -->
<template>
  <Panel title="档案管理助手">
    <div class="archive-helper">
      <Button @click="quickSearch">快速搜索</Button>
      <Button @click="batchUpload">批量上传</Button>
      <Button @click="exportData">导出数据</Button>
    </div>
  </Panel>
</template>

<script setup>
import { Button, Panel } from '@stagewise/toolbar/plugin-ui'

const quickSearch = () => {
  console.log('执行快速搜索')
}

const batchUpload = () => {
  console.log('执行批量上传')
}

const exportData = () => {
  console.log('执行数据导出')
}
</script>

<style scoped>
.archive-helper {
  padding: 16px;
}

.archive-helper .el-button {
  margin: 4px;
}
</style>
*/

// 4. 在现有组件中集成 stagewise
/*
// 在 DocUpload.vue 中添加 stagewise 功能
import { useToolbar } from '@stagewise/toolbar/plugin-ui'

const { addPlugin } = useToolbar()

// 添加上传进度插件
const uploadProgressPlugin = addPlugin({
  name: '上传进度',
  icon: '📤',
  component: () => import('./components/UploadProgress.vue'),
  position: 'bottom'
})
*/

console.log('✅ @stagewise/toolbar 包已成功安装并可以正常使用！')
console.log('📋 主要功能:')
console.log('- initToolbar: 初始化工具栏')
console.log('- useToolbar: React hook 用于管理插件')
console.log('- UI组件: Button, Panel, Badge 等')
console.log('- 插件系统: 支持自定义插件开发')

console.log('\n🎯 使用建议:')
console.log('1. 在 main.js 中初始化 stagewise')
console.log('2. 在需要工具栏功能的组件中使用 useToolbar hook')
console.log('3. 创建自定义插件组件')
console.log('4. 根据需要添加/移除插件') 