<template>
  <div class="upload-progress">
    <div class="progress-header">
      <h3>📤 上传进度</h3>
      <button class="close-btn" @click="closeProgress">×</button>
    </div>
    
    <div class="progress-content">
      <div v-if="uploadingFiles.length === 0" class="empty-state">
        <div class="empty-icon">📁</div>
        <p>暂无上传任务</p>
      </div>
      
      <div v-else class="file-list">
        <div 
          v-for="(file, index) in uploadingFiles" 
          :key="index"
          class="file-item"
        >
          <div class="file-info">
            <div class="file-name">{{ file.name }}</div>
            <div class="file-size">{{ formatFileSize(file.size) }}</div>
          </div>
          
          <div class="progress-bar">
            <div 
              class="progress-fill"
              :style="{ width: `${file.progress || 0}%` }"
              :class="getProgressClass(file.status)"
            ></div>
          </div>
          
          <div class="file-status">
            <span v-if="file.status === 'uploading'" class="status uploading">
              {{ file.progress || 0 }}%
            </span>
            <span v-else-if="file.status === 'success'" class="status success">
              ✅ 完成
            </span>
            <span v-else-if="file.status === 'error'" class="status error">
              ❌ 失败
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="uploadingFiles.length > 0" class="total-progress">
        <div class="total-info">
          <span>总体进度: {{ totalProgress }}%</span>
          <span>{{ completedCount }}/{{ uploadingFiles.length }}</span>
        </div>
        <div class="total-bar">
          <div 
            class="total-fill"
            :style="{ width: `${totalProgress}%` }"
          ></div>
        </div>
      </div>
    </div>
    
    <div class="progress-footer">
      <button 
        v-if="uploadingFiles.length > 0"
        class="clear-btn" 
        @click="clearAll"
      >
        清空列表
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

// 模拟上传文件数据（实际使用时应该从父组件传入）
const uploadingFiles = ref([
  {
    name: '示例文档.pdf',
    size: 1024000,
    progress: 75,
    status: 'uploading'
  },
  {
    name: '图片文件.jpg',
    size: 512000,
    progress: 100,
    status: 'success'
  },
  {
    name: '数据表格.xlsx',
    size: 2048000,
    progress: 0,
    status: 'error'
  }
]);

// 计算总体进度
const totalProgress = computed(() => {
  if (uploadingFiles.value.length === 0) return 0;
  
  const total = uploadingFiles.value.reduce((sum, file) => {
    if (file.status === 'success') return sum + 100;
    if (file.status === 'error') return sum;
    return sum + (file.progress || 0);
  }, 0);
  
  return Math.round(total / uploadingFiles.value.length);
});

// 计算完成数量
const completedCount = computed(() => {
  return uploadingFiles.value.filter(file => file.status === 'success').length;
});

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 获取进度条样式类
const getProgressClass = (status) => {
  switch (status) {
    case 'success': return 'success';
    case 'error': return 'error';
    default: return 'uploading';
  }
};

// 关闭进度面板
const closeProgress = () => {
  console.log('关闭上传进度面板');
  // 这里可以触发关闭事件
};

// 清空所有文件
const clearAll = () => {
  uploadingFiles.value = [];
  console.log('清空上传列表');
};

// 模拟更新进度（实际使用时应该从上传事件中获取）
let progressInterval;
onMounted(() => {
  progressInterval = setInterval(() => {
    uploadingFiles.value.forEach(file => {
      if (file.status === 'uploading' && file.progress < 100) {
        file.progress = Math.min(file.progress + Math.random() * 10, 100);
        if (file.progress >= 100) {
          file.status = 'success';
        }
      }
    });
  }, 2000);
});

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval);
  }
});
</script>

<style scoped>
.upload-progress {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  min-width: 320px;
  max-height: 400px;
  overflow-y: auto;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.progress-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #e9ecef;
  color: #495057;
}

.progress-content {
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: #6c757d;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.file-list {
  space-y: 12px;
}

.file-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: #495057;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: #6c757d;
  margin-left: 8px;
}

.progress-bar {
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-fill.uploading {
  background: #007bff;
}

.progress-fill.success {
  background: #28a745;
}

.progress-fill.error {
  background: #dc3545;
}

.file-status {
  text-align: right;
}

.status {
  font-size: 11px;
  font-weight: 500;
}

.status.uploading {
  color: #007bff;
}

.status.success {
  color: #28a745;
}

.status.error {
  color: #dc3545;
}

.total-progress {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.total-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #495057;
}

.total-bar {
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.total-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.progress-footer {
  text-align: center;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.clear-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.clear-btn:hover {
  background: #5a6268;
}
</style> 