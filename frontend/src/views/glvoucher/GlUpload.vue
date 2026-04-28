<template>
  <div class="gl-upload">
    <!-- 页面头部：标题 + 步骤指示器 -->
    <div class="page-header">
      <h2 class="page-title">凭证与总账数据引入</h2>
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
        
        <!-- 账套和年度选择表单 -->
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="100px"
          label-position="top"
          class="upload-form"
        >
          <el-form-item label="导入方式">
            <el-radio-group v-model="importType" @change="onImportTypeChange">
              <el-radio label="xml">总账 GL.xml（全量科目/凭证等）</el-radio>
              <el-radio label="excel">凭证明细 Excel（临时表样式）</el-radio>
            </el-radio-group>
            <div class="form-tip">
              GL.xml 按财政接口规范；Excel 需表头含会计区间、凭证编码、会计科目编码等，且须选择会计年度。
            </div>
          </el-form-item>
          <el-form-item label="账套编码" prop="account_book_code">
            <el-select
              v-model="formData.account_book_code"
              placeholder="请选择账套"
              style="width: 100%"
              filterable
              @change="handleAccountBookChange"
            >
              <el-option
                v-for="item in accountBookOptions"
                :key="item.account_book_code"
                :label="`${item.account_book_code} - ${item.account_book_name}`"
                :value="item.account_book_code"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="会计年度" prop="fiscal_year">
            <el-select
              v-model="formData.fiscal_year"
              :placeholder="importType === 'xml' ? '可选，不选则从 XML 中提取' : '请选择会计年度（Excel 必填）'"
              style="width: 100%"
              :clearable="importType === 'xml'"
              :disabled="!formData.account_book_code"
            >
              <el-option
                v-for="year in fiscalYearOptions"
                :key="year"
                :label="year"
                :value="year"
              />
            </el-select>
            <div v-if="importType === 'xml'" class="form-tip">如不选择，系统将尝试从 XML 文件中提取会计年度</div>
            <div v-else class="form-tip">凭证明细 Excel 导入必须指定账套已维护的会计年度</div>
          </el-form-item>
        </el-form>

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
          :accept="uploadAccept"
        >
          <el-icon class="upload-icon"><upload-filled /></el-icon>
          <div class="upload-text">
            <template v-if="importType === 'xml'">
              将 GL.xml 拖到此处，或 <em>点击选择</em>
            </template>
            <template v-else>
              将凭证明细 Excel 拖到此处，或 <em>点击选择</em>
            </template>
          </div>
          <div class="upload-tip">{{ uploadTipText }}</div>
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
            :disabled="uploadSubmitDisabled"
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
                <span class="info-label">会计年度</span>
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

            <template v-if="uploadResult.row_count != null || uploadResult.rows_skipped_empty != null">
              <div class="stats-title sub">明细</div>
              <div class="extra-result-lines">
                <span v-if="uploadResult.row_count != null">有效行数：{{ uploadResult.row_count }}</span>
                <span v-if="uploadResult.rows_skipped_empty != null">跳过空行：{{ uploadResult.rows_skipped_empty }}</span>
              </div>
            </template>

            <div v-if="uploadResult.warnings && uploadResult.warnings.length" class="warnings-block">
              <div class="stats-title sub">提示</div>
              <el-alert type="info" :closable="false" show-icon>
                <ul class="warn-list">
                  <li v-for="(w, wi) in uploadResult.warnings" :key="wi">{{ w }}</li>
                </ul>
              </el-alert>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, 
  Upload, 
  Document, 
  Delete,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { glApi } from '@/api/gl'
import { accountBookApi } from '@/api/accountBook'

// 响应式变量
const uploadRef = ref(null)
const formRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref(null)
/** @type {import('vue').Ref<'xml'|'excel'>} */
const importType = ref('xml')

// 表单数据
const formData = ref({
  account_book_code: '',
  fiscal_year: null
})

// 表单验证规则
const formRules = {
  account_book_code: [
    { required: true, message: '请选择账套编码', trigger: 'change' }
  ]
}

// 账套选项
const accountBookOptions = ref([])
const fiscalYearOptions = ref([])

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

const uploadAccept = computed(() =>
  importType.value === 'xml' ? '.xml' : '.xlsx,.xlsm'
)

const uploadTipText = computed(() =>
  importType.value === 'xml'
    ? '仅支持 .xml 格式的总账类文件'
    : '仅支持 .xlsx / .xlsm（凭证导入临时表样式）'
)

const uploadSubmitDisabled = computed(() => {
  if (!selectedFile.value || !formData.value.account_book_code) return true
  if (importType.value === 'excel') {
    const y = formData.value.fiscal_year
    if (y === null || y === undefined || y === '') return true
  }
  return false
})

const statsTableData = computed(() => {
  if (!uploadResult.value?.stats) return []
  return Object.entries(uploadResult.value.stats).map(([name, count]) => ({
    name,
    count
  }))
})

// 获取账套列表
const fetchAccountBooks = async () => {
  try {
    const response = await accountBookApi.getList({ page_size: 1000 })
    if (response.data.success) {
      accountBookOptions.value = response.data.items || []
    } else {
      ElMessage.error(response.data.message || '获取账套列表失败')
    }
  } catch (error) {
    console.error('获取账套列表失败:', error)
    ElMessage.error('获取账套列表失败')
  }
}

// 获取会计年度列表
const fetchFiscalYears = async (accountBookCode) => {
  if (!accountBookCode) {
    fiscalYearOptions.value = []
    formData.value.fiscal_year = null
    return
  }
  
  try {
    const response = await accountBookApi.getFiscalYears(accountBookCode)
    if (response.data.success) {
      const items = response.data.items || []
      // 提取年度数字：如果items是对象数组，提取fiscal_year字段；如果是数字数组，直接使用
      fiscalYearOptions.value = items.map(item => {
        return typeof item === 'object' && item !== null ? item.fiscal_year : item
      }).filter(year => year !== null && year !== undefined).sort((a, b) => b - a) // 降序排列
    } else {
      fiscalYearOptions.value = []
      ElMessage.warning(response.data.message || '获取会计年度列表失败')
    }
  } catch (error) {
    console.error('获取会计年度列表失败:', error)
    fiscalYearOptions.value = []
    ElMessage.error('获取会计年度列表失败，请稍后重试')
  }
}

// 账套选择变化
const handleAccountBookChange = (value) => {
  if (value) {
    fetchFiscalYears(value)
  } else {
    fiscalYearOptions.value = []
    formData.value.fiscal_year = null
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function fileMatchesImportType(name) {
  const lower = name.toLowerCase()
  if (importType.value === 'xml') return lower.endsWith('.xml')
  return lower.endsWith('.xlsx') || lower.endsWith('.xlsm')
}

// 文件选择前的验证
const beforeUpload = (file) => {
  if (!fileMatchesImportType(file.name)) {
    ElMessage.error(
      importType.value === 'xml'
        ? '只能上传 XML 格式的文件'
        : '只能上传 .xlsx 或 .xlsm 文件'
    )
    return false
  }
  return true
}

// 处理文件变化
const handleFileChange = (uploadFile) => {
  if (uploadFile.raw) {
    if (!fileMatchesImportType(uploadFile.name)) {
      ElMessage.error(
        importType.value === 'xml'
          ? '只能上传 XML 格式的文件'
          : '只能上传 .xlsx 或 .xlsm 文件'
      )
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

const onImportTypeChange = () => {
  removeFile()
}

// 处理上传
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  // 验证表单
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (error) {
    ElMessage.warning('请先选择账套编码')
    return
  }

  if (importType.value === 'excel') {
    const y = formData.value.fiscal_year
    if (y === null || y === undefined || y === '') {
      ElMessage.warning('凭证明细 Excel 导入必须选择会计年度')
      return
    }
  }

  const confirmText =
    importType.value === 'xml'
      ? '确定要导入该 GL.xml 吗？将按接口规则写入或更新总账类数据。'
      : '确定要导入该 Excel 吗？将写入或更新凭证明细（凭证头、分录、辅助项等）。'

  try {
    await ElMessageBox.confirm(confirmText, '确认导入', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    uploading.value = true
    uploadProgress.value = 0
    uploadResult.value = null

    let response
    if (importType.value === 'xml') {
      response = await glApi.uploadGlFile(
        selectedFile.value,
        formData.value.account_book_code,
        formData.value.fiscal_year,
        (progress) => {
          uploadProgress.value = progress
        }
      )
    } else {
      response = await glApi.uploadVoucherExcel(
        selectedFile.value,
        formData.value.account_book_code,
        formData.value.fiscal_year,
        (progress) => {
          uploadProgress.value = progress
        }
      )
    }

    if (response.data.success) {
      uploadResult.value = response.data
      ElMessage.success(response.data.message || '导入成功')
    } else {
      uploadResult.value = {
        success: false,
        message: response.data.message || '导入失败',
        account_book_code: formData.value.account_book_code,
        fiscal_year: formData.value.fiscal_year || response.data.fiscal_year
      }
      ElMessage.error(response.data.message || '导入失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('上传失败:', error)
      uploadResult.value = {
        success: false,
        message: error.response?.data?.message || error.message || '上传失败，请重试',
        account_book_code: formData.value.account_book_code,
        fiscal_year: formData.value.fiscal_year
      }
      ElMessage.error('上传失败，请重试')
    }
  } finally {
    uploading.value = false
  }
}

// 初始化
onMounted(() => {
  fetchAccountBooks()
})
</script>

<style scoped>
.gl-upload {
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

/* 表单样式 */
.upload-form {
  margin-bottom: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
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

.stats-title.sub {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

.extra-result-lines {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.warnings-block {
  margin-top: 4px;
}

.warn-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
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
  .gl-upload {
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
