<template>
    <el-sub-menu v-if="menuItem.children && menuItem.children.length" :index="menuItem.path">
      <template #title>
        <el-icon v-if="iconMap[menuItem.icon]">
          <component :is="iconMap[menuItem.icon]" />
        </el-icon>
        <span>{{ menuItem.name }}</span>
        <!-- debug: {{ menuItem.icon }} -->
      </template>
      <template v-for="child in menuItem.children" :key="child.path">
        <recursive-menu-item :menu-item="child" />
      </template>
    </el-sub-menu>
  
    <el-menu-item v-else :index="menuItem.path">
      <el-icon v-if="iconMap[menuItem.icon]">
        <component :is="iconMap[menuItem.icon]" />
      </el-icon>
      <span>{{ menuItem.name }}</span>
    </el-menu-item>
  </template>
  
  <script setup>
  import { User, Menu, Lock, SettingFilled, Setting } from '@element-plus/icons-vue'

  const iconMap = {
    'el-icon-user': User,
    'el-icon-menu': Menu,
    'el-icon-lock': Lock,
    'el-icon-setting': Setting,
    'el-icon-setting-filled': SettingFilled
  }

  defineProps({
    menuItem: {
      type: Object,
      required: true
    }
  })
  </script>
  
  <style scoped>
  .el-menu-item, .el-sub-menu {
    text-align: left;
  }
  
  .el-icon {
    margin-right: 8px;
    vertical-align: middle;
  }
  
  :deep(.el-sub-menu__title) {
    display: flex;
    align-items: center;
  }
  
  :deep(.el-sub-menu__title i) {
    margin-right: 8px;
  }
  
  :deep(.el-sub-menu__title span) {
    flex: 1;
  }
  
  /*
  :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    transition: transform 0.3s;
  }
  
  :deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
    transform: translateY(-50%) rotateZ(180deg);
  }
  */
  </style> 