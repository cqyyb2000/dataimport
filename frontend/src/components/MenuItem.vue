<template>
  <el-sub-menu 
    v-if="menuItem.children && menuItem.children.length"
    :index="menuItem.path"
  >
    <template #title>
      <el-icon v-if="menuItem.icon && Icons[menuItem.icon]">
        <component :is="Icons[menuItem.icon]" />
      </el-icon>
      <span>{{ menuItem.name }}</span>
    </template>
    <menu-item
      v-for="child in menuItem.children"
      :key="child.path"
      :menu-item="child"
      @menu-click="emitMenuClick"
    />
  </el-sub-menu>
  <el-menu-item v-else :index="menuItem.path" @click="emitMenuClick">
    <el-icon v-if="menuItem.icon && Icons[menuItem.icon]">
      <component :is="Icons[menuItem.icon]" />
    </el-icon>
    <span>{{ menuItem.name }}</span>
  </el-menu-item>
</template>

<script setup>
import { defineEmits, defineProps } from 'vue'
import * as Icons from '@element-plus/icons-vue'

const props = defineProps({
  menuItem: {
    type: Object,
    required: true,
    validator: (value) => {
      return value && typeof value === 'object' && 'path' in value && 'name' in value
    }
  }
})
const emit = defineEmits(['menu-click'])

function emitMenuClick() {
  //console.log(props.menuItem.path)
  emit('menu-click', { path: props.menuItem.path, title: props.menuItem.name })
}
</script>
