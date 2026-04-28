<template>
  <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar-container">
  <el-menu
      :default-active="$route.path"
    class="side-menu"
    :collapse="isCollapse"
    :unique-opened="true"
    background-color="#545c64"
    text-color="#fff"
    active-text-color="#ffd04b"
      router
      @select="handleMenuSelect"
  >
    <template v-for="item in menuData" :key="item.id || item.path">
        <el-sub-menu v-if="item.children && item.children.length" :index="String(item.id || item.name)">
          <template #title>
            <el-icon v-if="item.icon && Icons[item.icon]">
              <component :is="Icons[item.icon]" />
            </el-icon>
            <span>{{ item.name }}</span>
          </template>
          <menu-item
            v-for="child in item.children"
            :key="child.path"
            :menu-item="child"
            @menu-click="emitMenuClick"
          />
        </el-sub-menu>
        <el-menu-item v-else :index="item.path" @click="emitMenuClick(item)">
          <el-icon v-if="item.icon && Icons[item.icon]">
            <component :is="Icons[item.icon]" />
          </el-icon>
          <span>{{ item.name }}</span>
        </el-menu-item>
    </template>
  </el-menu>
    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon>
        <Expand v-if="isCollapse" />
        <Fold v-else />
      </el-icon>
    </div>
  </el-aside>
</template>

<script setup lang="js">
import { ref, defineEmits, defineProps, watch } from 'vue'
import { Expand, Fold } from '@element-plus/icons-vue'
import * as Icons from '@element-plus/icons-vue'
import MenuItem from './MenuItem.vue'

const props = defineProps({
  menuList: {
    type: Array,
    required: true,
    validator: (value) => {
      return Array.isArray(value) && value.every(item => 
        item && typeof item === 'object' && 'path' in item && 'name' in item
      )
    }
  }
})
const emit = defineEmits(['menu-click'])

// 当前激活的菜单项
const menuData = ref(props.menuList)

// 监听 menuList 变化
watch(() => props.menuList, (newVal) => {
  menuData.value = newVal
}, { deep: true, immediate: true })

// 是否折叠菜单
const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

function emitMenuClick(item) {
  emit('menu-click', { path: item.path, title: item.name })
}

function handleMenuSelect(index) {
  // index 是 path，找到对应的菜单项
  function findMenuByPath(list, path) {
    for (const item of list) {
      if (item.path === path) return item
      if (item.children && item.children.length) {
        const found = findMenuByPath(item.children, path)
        if (found) return found
      }
    }
    return null
  }
  const menu = findMenuByPath(props.menuList, index)
  if (menu) {
    emitMenuClick(menu)
  }
}
</script>

<style scoped>
.sidebar-container {
  transition: width 0.3s;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: #545c64;
}

.side-menu {
  flex: 1;
  border-right: none;
}

.side-menu:not(.el-menu--collapse) {
  width: 200px;
}

.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background-color: #434a50;
  color: #fff;
  transition: background-color 0.3s;
  border-top: 1px solid #4a4a4a;
  position: absolute;
  bottom: 0;
  right: 0;
  width: 40px;
  border-left: 1px solid #4a4a4a;
}

.collapse-btn:hover {
  background-color: #363b3f;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-sub-menu .el-sub-menu__title) {
  color: #fff !important;
}

:deep(.el-sub-menu .el-sub-menu__title:hover) {
  background-color: #434a50 !important;
}

:deep(.el-menu-item) {
  color: #fff !important;
}

:deep(.el-menu-item:hover) {
  background-color: #434a50 !important;
}

:deep(.el-menu-item.is-active) {
  color: #ffd04b !important;
  background-color: #434a50 !important;
}

:deep(.el-sub-menu__icon-arrow) {
  display: inline-block !important;
  color: #fff !important;
  opacity: 1 !important;
  width: 1em;
  height: 1em;
}

:deep(.el-menu-item.is-active .el-sub-menu__icon-arrow) {
  color: #409eff !important;
}

/*
:deep(.el-sub-menu__icon-arrow) {
  color: #fff !important;
  font-size: 12px;
  margin-top: -3px;
  transition: transform 0.3s;
}

:deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  transform: rotateZ(180deg);
}

:deep(.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none;
}
*/
</style> 