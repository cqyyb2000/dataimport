# @stagewise/toolbar 集成说明

## 集成概述

本项目已成功集成 `@stagewise/toolbar` 包，为档案管理系统添加了智能工具栏功能。

## 集成内容

### 1. 主应用初始化 (`main.js`)
```javascript
import { initToolbar } from '@stagewise/toolbar';

// 初始化 stagewise toolbar
initToolbar({
  environment: 'development', // 开发环境
  // 可以根据需要添加其他配置
  // apiKey: 'your-api-key', // 如果需要的话
  // theme: 'light', // 主题配置
});
```

### 2. 自定义插件组件

#### 档案管理助手 (`ArchiveHelper.vue`)
- **功能**: 提供快速操作工具
- **位置**: `src/components/ArchiveHelper.vue`
- **功能模块**:
  - 📋 文档操作: 快速搜索、批量上传、导出数据
  - ⚙️ 系统工具: 数据统计、用户管理、系统设置
  - 💡 智能助手: AI助手、使用帮助

#### 上传进度监控 (`UploadProgress.vue`)
- **功能**: 实时显示文件上传进度
- **位置**: `src/components/UploadProgress.vue`
- **功能特性**:
  - 实时进度显示
  - 文件状态跟踪
  - 总体进度统计
  - 清空列表功能

### 3. 页面集成

#### 主页面 (`HomeView.vue`)
```javascript
import { useToolbar } from '@stagewise/toolbar/plugin-ui'
import ArchiveHelper from '../components/ArchiveHelper.vue'
import UploadProgress from '../components/UploadProgress.vue'

// 使用 stagewise toolbar
const { addPlugin, removePlugin } = useToolbar()

// 初始化插件
const initStagewisePlugins = () => {
  // 添加档案管理助手插件
  archiveHelperPluginId = addPlugin({
    name: '档案管理助手',
    icon: '📁',
    component: ArchiveHelper,
    position: 'right'
  })
  
  // 添加上传进度插件
  uploadProgressPluginId = addPlugin({
    name: '上传进度',
    icon: '📤',
    component: UploadProgress,
    position: 'bottom'
  })
}
```

#### 文档上传页面 (`DocUpload.vue`)
- 集成了上传进度插件
- 提供实时上传状态监控
- 支持文件上传进度跟踪

## 功能特性

### 🎯 核心功能
1. **智能工具栏**: 可拖拽、可定制的工具栏界面
2. **插件系统**: 支持动态添加/移除插件
3. **响应式设计**: 适配不同屏幕尺寸
4. **主题支持**: 支持明暗主题切换

### 🔧 技术特性
1. **ES模块支持**: 完全支持现代JavaScript模块系统
2. **Vue 3兼容**: 完美支持Vue 3 Composition API
3. **TypeScript支持**: 提供完整的类型定义
4. **性能优化**: 按需加载，减少包体积

### 📱 用户体验
1. **直观操作**: 图标化界面，操作简单直观
2. **实时反馈**: 上传进度实时更新
3. **快捷导航**: 一键跳转到相关页面
4. **状态保持**: 插件状态在页面切换时保持

## 使用指南

### 访问工具栏
1. 启动应用后，工具栏会自动显示在页面右侧
2. 点击工具栏图标可以展开/收起插件面板
3. 插件面板支持拖拽调整位置

### 档案管理助手
1. 点击 📁 图标打开档案管理助手
2. 选择需要的功能模块
3. 点击按钮执行相应操作

### 上传进度监控
1. 点击 📤 图标查看上传进度
2. 实时监控文件上传状态
3. 支持清空已完成的上传记录

## 自定义扩展

### 添加新插件
```javascript
// 1. 创建插件组件
// 2. 在页面中导入并使用
import { useToolbar } from '@stagewise/toolbar/plugin-ui'
import MyPlugin from './MyPlugin.vue'

const { addPlugin } = useToolbar()

const pluginId = addPlugin({
  name: '我的插件',
  icon: '🚀',
  component: MyPlugin,
  position: 'right' // 或 'bottom'
})
```

### 插件配置选项
- `name`: 插件名称
- `icon`: 插件图标 (emoji或图标组件)
- `component`: 插件组件
- `position`: 插件位置 ('right' | 'bottom')
- `config`: 其他配置选项

## 故障排除

### 常见问题
1. **插件不显示**: 检查是否正确导入和初始化
2. **样式冲突**: 确保CSS样式作用域正确
3. **功能异常**: 检查控制台错误信息

### 调试方法
1. 打开浏览器开发者工具
2. 查看控制台日志信息
3. 检查网络请求状态
4. 验证组件是否正确挂载

## 更新日志

### v1.0.0 (当前版本)
- ✅ 完成基础集成
- ✅ 添加档案管理助手插件
- ✅ 添加上传进度监控插件
- ✅ 支持主页面和上传页面集成
- ✅ 实现插件动态管理

## 技术支持

如有问题或需要技术支持，请：
1. 查看控制台错误信息
2. 检查网络连接状态
3. 验证依赖包版本
4. 参考官方文档

---

**集成完成时间**: 2025年6月25日  
**版本**: v1.0.0  
**状态**: ✅ 已完成 