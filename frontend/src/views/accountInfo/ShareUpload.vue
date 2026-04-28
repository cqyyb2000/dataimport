<template>
  <div class="share-upload">
    <!-- 页面头部：标题 + 步骤指示器 -->
    <div class="page-header">
      <h2 class="page-title">基础档案导入</h2>
      <div class="steps-bar">
        <div class="step-item" :class="{ active: currentStep >= 1 }">
          <span class="step-num">1</span>
          <span class="step-text">选择文件</span>
        </div>
        <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
        <div class="step-item" :class="{ active: currentStep >= 2 }">
          <span class="step-num">2</span>
          <span class="step-text">上传导入</span>
        </div>
        <div class="step-line" :class="{ active: currentStep >= 3 }"></div>
        <div class="step-item" :class="{ active: currentStep >= 3 }">
          <span class="step-num">3</span>
          <span class="step-text">查看结果</span>
        </div>
      </div>
    </div>

    <!-- 主体内容：左右两栏 -->
    <div class="main-content">
      <!-- 左侧：上传区域 -->
      <div class="left-panel">
        <div class="panel-title">选择文件</div>
        
        <!-- 拖拽上传区 -->
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          :before-upload="beforeUpload"
          accept=".xml"
        >
          <el-icon class="upload-icon"><upload-filled /></el-icon>
          <div class="upload-text">
            将 share.xml 拖到此处，或 <em>点击选择</em>
          </div>
          <div class="upload-tip">仅支持 .xml 格式的基础档案文件</div>
        </el-upload>

        <!-- 已选择的文件信息 -->
        <div v-if="selectedFile" class="file-section">
          <div class="section-label">已选择文件</div>
          <div class="file-card">
            <el-icon class="file-icon" :size="28" color="#409EFF"><Document /></el-icon>
            <div class="file-info">
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
            </div>
            <el-button 
              type="danger" 
              :icon="Delete" 
              circle 
              size="small" 
              @click="removeFile" 
            />
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading || uploadProgress > 0" class="progress-section">
          <div class="progress-label">
            <span>上传进度</span>
            <span class="progress-percent" :class="{ success: uploadProgress === 100 }">
              {{ uploadProgress }}%
            </span>
          </div>
          <el-progress 
            :percentage="uploadProgress" 
            :status="uploadStatus"
            :stroke-width="8"
            :show-text="false"
          />
        </div>

        <!-- 上传按钮 -->
        <div class="btn-area">
          <el-button 
            type="primary" 
            size="large"
            :loading="uploading"
            :disabled="!selectedFile"
            @click="handleUpload"
          >
            <el-icon v-if="!uploading"><Upload /></el-icon>
            {{ uploading ? '上传中...' : '开始上传' }}
          </el-button>
        </div>
      </div>

      <!-- 右侧：结果区域 -->
      <div class="right-panel" :class="{ 
        'has-result': uploadResult, 
        'success': uploadResult?.success,
        'error': uploadResult && !uploadResult.success 
      }">
        <!-- 无结果时的占位 -->
        <div v-if="!uploadResult" class="empty-result">
          <el-icon :size="48" color="#C0C4CC"><Document /></el-icon>
          <p>上传文件后将在此显示导入结果</p>
        </div>

        <!-- 有结果时显示 -->
        <template v-else>
          <!-- 结果头部 -->
          <div class="result-header">
            <el-icon v-if="uploadResult.success" :size="20" color="#67C23A">
              <SuccessFilled />
            </el-icon>
            <el-icon v-else :size="20" color="#F56C6C">
              <CircleCloseFilled />
            </el-icon>
            <span class="result-title" :class="uploadResult.success ? 'success' : 'error'">
              {{ uploadResult.success ? '导入成功' : '导入失败' }}
            </span>
          </div>

          <!-- 成功时显示详细信息 -->
          <template v-if="uploadResult.success">
            <!-- 账套信息 -->
            <div class="info-grid">
              <div class="info-box">
                <span class="info-label">账套代码</span>
                <span class="info-value primary">{{ uploadResult.account_book_code }}</span>
              </div>
              <div class="info-box">
                <span class="info-label">财务年度</span>
                <span class="info-value">{{ uploadResult.fiscal_year }}</span>
              </div>
            </div>

            <!-- 导入统计 -->
            <div class="stats-title">导入统计</div>
            <div class="stats-grid">
              <div 
                v-for="(item, index) in statsTableData" 
                :key="index"
                class="stat-item"
              >
                <span class="stat-name">{{ item.name }}</span>
                <el-tag type="success" size="small">{{ item.count }}</el-tag>
              </div>
            </div>
          </template>

          <!-- 失败时显示错误信息 -->
          <div v-else class="error-content">
            <el-alert
              :title="uploadResult.message || '上传失败，请重试'"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, 
  Upload, 
  Document, 
  Delete,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { shareApi } from '@/api/share'

// 响应式变量
const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref(null)

// 当前步骤
const currentStep = computed(() => {
  if (uploadResult.value) return 3
  if (uploading.value || uploadProgress.value > 0) return 2
  if (selectedFile.value) return 1
  return 1
})

// 计算属性
const uploadStatus = computed(() => {
  if (uploadProgress.value === 100) return 'success'
  return ''
})

const statsTableData = computed(() => {
  if (!uploadResult.value?.stats) return []
  return Object.entries(uploadResult.value.stats).map(([name, count]) => ({
    name,
    count
  }))
})

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 文件选择前的验证
const beforeUpload = (file) => {
  const isXML = file.name.toLowerCase().endsWith('.xml')
  if (!isXML) {
    ElMessage.error('只能上传 XML 格式的文件!')
    return false
  }
  return true
}

// 处理文件变化
const handleFileChange = (uploadFile) => {
  if (uploadFile.raw) {
    const isXML = uploadFile.name.toLowerCase().endsWith('.xml')
    if (!isXML) {
      ElMessage.error('只能上传 XML 格式的文件!')
      selectedFile.value = null
      return
    }
    selectedFile.value = uploadFile.raw
    uploadResult.value = null // 清除之前的结果
    uploadProgress.value = 0
  }
}

// 处理超出文件数量限制
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先删除已选择的文件')
}

// 移除已选择的文件
const removeFile = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  uploadResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 处理上传
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要导入该基础档案文件吗？导入后将覆盖现有的基础档案数据。',
      '确认导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    uploading.value = true
    uploadProgress.value = 0
    uploadResult.value = null

    const response = await shareApi.uploadShareFile(
      selectedFile.value,
      (progress) => {
        uploadProgress.value = progress
      }
    )

    if (response.data.success) {
      uploadResult.value = response.data
      ElMessage.success(response.data.message || '导入成功')
    } else {
      uploadResult.value = {
        success: false,
        message: response.data.message || '导入失败'
      }
      ElMessage.error(response.data.message || '导入失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('上传失败:', error)
      uploadResult.value = {
        success: false,
        message: error.response?.data?.message || error.message || '上传失败，请重试'
      }
      ElMessage.error('上传失败，请重试')
    }
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.share-upload {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #F5F7FA;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* 步骤指示器 */
.steps-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid #DCDFE6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #909399;
  background: #fff;
}

.step-text {
  font-size: 13px;
  color: #909399;
}

.step-item.active .step-num {
  background: #409EFF;
  border-color: #409EFF;
  color: #fff;
}

.step-item.active .step-text {
  color: #409EFF;
}

.step-line {
  width: 32px;
  height: 2px;
  background: #DCDFE6;
}

.step-line.active {
  background: #409EFF;
}

/* 主体内容 */
.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

/* 左侧面板 */
.left-panel {
  flex: 1;
  background: #fff;
  border: 1px solid #E4E7ED;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

/* 上传区域 */
.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload) {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px;
}

.upload-icon {
  font-size: 36px;
  color: #409EFF;
}

.upload-text {
  font-size: 13px;
  color: #606266;
}

.upload-text em {
  color: #409EFF;
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

/* 文件信息 */
.file-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 13px;
  color: #606266;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #F5F7FA;
  border: 1px solid #E4E7ED;
  border-radius: 4px;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

/* 进度区域 */
.progress-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

.progress-percent {
  font-weight: 500;
}

.progress-percent.success {
  color: #67C23A;
}

/* 按钮区域 */
.btn-area {
  display: flex;
  justify-content: center;
  padding-top: 8px;
  margin-top: auto;
}

.btn-area .el-button {
  min-width: 140px;
}

/* 右侧面板 */
.right-panel {
  width: 420px;
  background: #fff;
  border: 1px solid #E4E7ED;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.right-panel.success {
  border-left: 3px solid #67C23A;
}

.right-panel.error {
  border-left: 3px solid #F56C6C;
}

/* 空结果占位 */
.empty-result {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;
}

.empty-result p {
  margin: 0;
  font-size: 13px;
}

/* 结果头部 */
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-title {
  font-size: 15px;
  font-weight: 600;
}

.result-title.success {
  color: #67C23A;
}

.result-title.error {
  color: #F56C6C;
}

/* 账套信息网格 */
.info-grid {
  display: flex;
  gap: 12px;
}

.info-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: #F5F7FA;
  border-radius: 4px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.info-value.primary {
  color: #409EFF;
}

/* 统计标题 */
.stats-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

/* 统计网格 */
.stats-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: #E4E7ED;
  border: 1px solid #E4E7ED;
  border-radius: 4px;
  overflow: hidden;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #fff;
}

.stat-name {
  font-size: 13px;
  color: #606266;
}

/* 错误内容 */
.error-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .main-content {
    flex-direction: column;
  }
  
  .right-panel {
    width: 100%;
    min-height: 300px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 576px) {
  .share-upload {
    padding: 12px;
  }
  
  .steps-bar {
    display: none;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
