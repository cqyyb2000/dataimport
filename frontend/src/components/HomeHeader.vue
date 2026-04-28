<template>
  <div class="header-container">
    <div class="left-section">
      <div class="logo">
        <img src="../assets/logo.png" alt="Logo" />
        <span class="title">财政数据管理系统</span>
      </div>
    </div>
    <div class="right-section">
      <el-dropdown>
        <span class="user-info">
          <el-avatar :size="32" :src="userAvatar" />
          <span class="username">{{ username }}</span>
          <el-icon class="el-icon--right">
            <arrow-down />
          </el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>个人信息</el-dropdown-item>
            <el-dropdown-item>修改密码</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const username = ref(JSON.parse(localStorage.getItem('user'))?.username || '未登录')
const userAvatar = ref('')

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('menus')
  router.push('/login')
}

</script>

<style scoped>
.header-container {
  height: 60px;
  background: linear-gradient(to right, #1e88e5, #1976d2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.left-section {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo img {
  height: 40px;
  width: auto;
}

.title {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.right-section {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.username {
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-dropdown-menu__item) {
  font-size: 14px;
  padding: 8px 20px;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f5f7fa;
  color: #409eff;
}

:deep(.el-dropdown-menu__item--divided) {
  border-top: 1px solid #ebeef5;
  margin: 6px 0;
}
</style>    