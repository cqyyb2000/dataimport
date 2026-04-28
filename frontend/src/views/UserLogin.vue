<template>
  <div class="login-container">
    <div class="login-layout">
      <section class="brand-panel">
        <div class="brand-content">
          <span class="brand-badge">FINANCE OPS</span>
          <h1>
            <span class="title-line title-line-top">行政事业单位</span>
            <span class="title-line">财务数据管理系统</span>
          </h1>
          <p>统一、安全、可追溯的财政数据引入与管理平台。</p>
          <div class="brand-features">
            <div class="feature-item">
              <span class="feature-title">数据同步</span>
              <span class="feature-value">实时校验</span>
            </div>
            <div class="feature-item">
              <span class="feature-title">凭证处理</span>
              <span class="feature-value">流程闭环</span>
            </div>
            <div class="feature-item">
              <span class="feature-title">权限控制</span>
              <span class="feature-value">分级鉴权</span>
            </div>
          </div>
        </div>
      </section>

      <section class="login-panel">
        <div class="login-card">
          <div class="login-header">
            <div class="logo-wrapper">
              <div class="logo-icon">📁</div>
            </div>
            <h2>欢迎登录</h2>
            <p class="subtitle">请输入账号信息以继续访问系统</p>
          </div>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="0" class="login-form">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                size="large"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                size="large"
                show-password
                class="custom-input"
                @keyup.enter="handleSubmit(formRef)"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleSubmit(formRef)"
                class="login-button"
                size="large"
                :loading="loading"
              >
                <span v-if="!loading">登录系统</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import { login } from '@/api';
import { setAuthData } from '@/utils/auth';
import { ElMessage } from 'element-plus';

const router = useRouter();
const loading = ref(false);

const form = ref({
  username: '',
  password: ''
});

const rules = ref({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
});

const formRef = ref(null);

const handleSubmit = async (formEl) => {
  if (!formEl) return;
  try {
    loading.value = true;
    await formEl.validate();
    const response = await login(form.value.username, form.value.password);

    if (response.data.success) {
      setAuthData(
        response.data.token,
        { username: response.data.username },
        response.data.menus
      );
      
      router.push('/home/dashboard');
    } else {
      ElMessage.error('登录失败：' + response.data.message);
    }
  } catch (error) {
    if (error.response) {
      ElMessage.error('登录失败：' + error.response.data.message);
    } else {
      ElMessage.error('登录请求失败，请检查网络或服务器状态。');
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: grid;
  place-items: center;
  min-height: 100vh;
  background: radial-gradient(circle at 20% 20%, #143f75 0%, #06142e 45%, #030a18 100%);
  padding: 28px;
}

.login-layout {
  width: min(1180px, 100%);
  min-height: 600px;
  border-radius: 22px;
  border: 1px solid rgba(88, 144, 223, 0.35);
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  box-shadow: 0 22px 70px rgba(2, 11, 27, 0.55);
  background: linear-gradient(90deg, rgba(7, 33, 70, 0.85) 0%, rgba(2, 11, 25, 0.92) 100%);
}

.brand-panel {
  position: relative;
  background: linear-gradient(135deg, #0f427d 0%, #072957 55%, #041a3d 100%);
  padding: 58px 42px;
  display: flex;
  align-items: center;
  border-right: 1px solid rgba(126, 170, 235, 0.26);
}

.brand-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0) 40%);
  pointer-events: none;
}

.brand-content {
  position: relative;
  max-width: 500px;
  color: #dceaff;
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112px;
  height: 28px;
  padding: 0 14px;
  border-radius: 14px;
  background: rgba(66, 129, 210, 0.2);
  border: 1px solid rgba(135, 183, 245, 0.45);
  color: #b5d9ff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 24px;
}

.brand-content h1 {
  margin: 0;
  max-width: 430px;
  font-size: 52px;
  line-height: 1.15;
  letter-spacing: 1px;
  color: #f2f7ff;
  text-shadow: 0 8px 26px rgba(3, 14, 33, 0.45);
}

.title-line {
  display: block;
}

.title-line-top {
  font-size: 0.82em;
}

.brand-content p {
  margin: 22px 0 34px;
  color: rgba(210, 230, 255, 0.82);
  font-size: 18px;
  line-height: 1.6;
}

.brand-features {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.feature-item {
  min-height: 84px;
  border-radius: 14px;
  border: 1px solid rgba(119, 172, 240, 0.3);
  background: rgba(8, 34, 72, 0.45);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  row-gap: 8px;
  box-shadow: inset 0 0 22px rgba(101, 161, 240, 0.08);
}

.feature-title {
  font-size: 14px;
  color: rgba(179, 214, 255, 0.82);
}

.feature-value {
  font-size: 24px;
  font-weight: 700;
  color: #f4f8ff;
  line-height: 1.1;
}

.login-panel {
  display: grid;
  place-items: center;
  padding: 38px;
}

.login-card {
  width: min(420px, 100%);
  border-radius: 18px;
  background: #d6d9df;
  border: 1px solid rgba(255, 255, 255, 0.45);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.32);
  padding: 34px 34px 28px;
}

.login-header {
  text-align: center;
  margin-bottom: 26px;
}

.logo-wrapper {
  margin-bottom: 14px;
}

.logo-icon {
  width: 58px;
  height: 58px;
  margin: 0 auto;
  border-radius: 18px;
  background: linear-gradient(145deg, #1f7ff2 0%, #0d63d3 100%);
  display: grid;
  place-items: center;
  font-size: 28px;
  box-shadow: 0 10px 18px rgba(13, 99, 211, 0.32);
}

.login-header h2 {
  margin: 0;
  color: #182643;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: 1px;
}

.subtitle {
  margin: 12px 0 0;
  font-size: 14px;
  color: #4a6287;
  font-weight: 500;
}

.login-form {
  margin-top: 16px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  height: 48px;
  background: #eef2f6;
  border: 1px solid #c8d3e6;
  box-shadow: none;
  padding: 0 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: #8ba9d8;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #2f7ee9;
  box-shadow: 0 0 0 2px rgba(47, 126, 233, 0.15);
}

.custom-input :deep(.el-input__inner) {
  height: 46px;
  color: #263d61;
  font-size: 15px;
}

.custom-input :deep(.el-input__prefix) {
  color: #5d88c7;
  font-size: 16px;
}

.login-button {
  width: 100%;
  height: 46px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #1b75ea 0%, #4f9eff 100%);
  border: none;
  box-shadow: 0 8px 16px rgba(27, 117, 234, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.login-button:hover {
  transform: translateY(-1px);
  filter: brightness(1.02);
  box-shadow: 0 10px 20px rgba(27, 117, 234, 0.42);
}

.login-button:active {
  transform: translateY(0);
  box-shadow: 0 6px 10px rgba(27, 117, 234, 0.35);
}

.login-button.is-loading {
  opacity: 0.9;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .brand-content h1 {
    font-size: 44px;
  }

  .feature-value {
    font-size: 20px;
  }
}

@media (max-width: 992px) {
  .login-layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .brand-panel {
    padding: 40px 28px;
    border-right: none;
    border-bottom: 1px solid rgba(126, 170, 235, 0.26);
  }

  .brand-content h1 {
    max-width: none;
    font-size: 36px;
  }

  .login-panel {
    padding: 30px 20px 34px;
  }

  .login-card {
    max-width: 440px;
  }
}

@media (max-width: 640px) {
  .login-container {
    padding: 14px;
  }

  .brand-panel {
    padding: 32px 18px;
  }

  .brand-content h1 {
    font-size: 30px;
  }

  .brand-content p {
    font-size: 15px;
    margin-bottom: 22px;
  }

  .brand-features {
    grid-template-columns: 1fr;
  }

  .login-panel {
    padding: 22px 14px 24px;
  }

  .login-card {
    padding: 26px 16px 20px;
  }

  .login-header h2 {
    font-size: 34px;
  }
}
</style>