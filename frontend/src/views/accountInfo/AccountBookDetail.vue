<template>
  <div class="account-book-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span class="breadcrumb-item" @click="goBack">账套管理</span>
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-current">账套详情</span>
      </div>
      <div class="title-row">
        <h2 class="page-title">{{ detailData.account_book_name }} ({{ detailData.account_book_code }})</h2>
        <div class="header-actions">
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
          <el-button type="primary" @click="showEditDialog">
            <el-icon><Edit /></el-icon>
            编辑账套
          </el-button>
        </div>
      </div>
    </div>

    <!-- 基本信息卡片 -->
    <div class="info-card" v-loading="loading">
      <div class="card-title">基本信息</div>
      <div class="info-grid">
        <div class="info-col">
          <div class="info-item">
            <span class="info-label">账套编码</span>
            <span class="info-value">{{ detailData.account_book_code }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">账套名称</span>
            <span class="info-value">{{ detailData.account_book_name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">核算主体</span>
            <span class="info-value">{{ detailData.accounting_entity }}</span>
          </div>
        </div>
        <div class="info-col">
          <div class="info-item">
            <span class="info-label">单位类型</span>
            <span class="info-value">{{ detailData.unit_type }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">基础币种</span>
            <span class="info-value">{{ formatCurrency(detailData.base_currency) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">准则版本</span>
            <span class="info-value">{{ detailData.standard_version }}</span>
          </div>
        </div>
        <div class="info-col">
          <div class="info-item">
            <span class="info-label">状态</span>
            <span class="info-value">
              <el-tag :type="detailData.status === 1 ? 'success' : 'info'" size="small">
                {{ detailData.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 会计年度卡片 -->
    <div class="fiscal-year-card">
      <div class="card-header">
        <div class="card-title">已导入会计年度</div>
        <el-button type="primary" size="small" @click="showAddYearDialog">
          <el-icon><Plus /></el-icon>
          添加年度
        </el-button>
      </div>
      <el-table
        v-loading="yearLoading"
        :data="fiscalYears"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="fiscal_year" label="会计年度" width="200">
          <template #default="{ row }">
            <span class="year-value">{{ row.fiscal_year }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="导入时间" width="200">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewVouchers(row)">查看凭证</el-button>
            <el-button type="danger" link @click="handleDeleteYear(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="fiscalYears.length === 0 && !yearLoading" class="empty-tip">
        <el-empty description="暂无会计年度数据" :image-size="80" />
      </div>
    </div>

    <!-- 编辑账套弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑账套"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editFormData"
        :rules="editFormRules"
        label-width="100px"
        label-position="top"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="账套编码">
              <el-input v-model="editFormData.account_book_code" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账套名称" prop="account_book_name">
              <el-input v-model="editFormData.account_book_name" placeholder="请输入账套名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="核算主体" prop="accounting_entity">
              <el-input v-model="editFormData.accounting_entity" placeholder="请输入核算主体" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位类型" prop="unit_type">
              <el-select v-model="editFormData.unit_type" placeholder="请选择单位类型" style="width: 100%">
                <el-option label="行政单位" value="行政单位" />
                <el-option label="事业单位" value="事业单位" />
                <el-option label="企业单位" value="企业单位" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="基础币种" prop="base_currency">
              <el-select v-model="editFormData.base_currency" placeholder="请选择基础币种" style="width: 100%">
                <el-option label="CNY (人民币)" value="CNY" />
                <el-option label="USD (美元)" value="USD" />
                <el-option label="EUR (欧元)" value="EUR" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="准则版本" prop="standard_version">
              <el-select v-model="editFormData.standard_version" placeholder="请选择准则版本" style="width: 100%">
                <el-option label="政府会计准则(2019)" value="政府会计准则(2019)" />
                <el-option label="企业会计准则(2006)" value="企业会计准则(2006)" />
                <el-option label="小企业会计准则(2011)" value="小企业会计准则(2011)" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="editFormData.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="启用" :value="1" />
                <el-option label="停用" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleEditSubmit">
          保存修改
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加会计年度弹窗 -->
    <el-dialog
      v-model="addYearDialogVisible"
      title="添加会计年度"
      width="480px"
      :close-on-click-modal="false"
    >
      <div class="add-year-content">
        <el-form
          ref="yearFormRef"
          :model="yearFormData"
          :rules="yearFormRules"
          label-position="top"
          class="year-form"
        >
          <el-form-item label="会计年度" prop="fiscal_year" class="year-field">
            <el-select 
              v-model="yearFormData.fiscal_year" 
              placeholder="请选择会计年度" 
              style="width: 100%"
              filterable
            >
              <el-option
                v-for="year in availableYears"
                :key="year"
                :label="year"
                :value="year"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="year-actions">
          <el-button @click="addYearDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="yearSubmitting" @click="handleAddYear">
            添加年度
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Plus } from '@element-plus/icons-vue'
import { accountBookApi } from '@/api/accountBook'

const router = useRouter()
const route = useRoute()

// 账套编码
const accountBookCode = computed(() => route.params.code)

// 详情数据
const loading = ref(false)
const detailData = ref({})

// 会计年度数据
const yearLoading = ref(false)
const fiscalYears = ref([])

// 编辑弹窗
const editDialogVisible = ref(false)
const submitting = ref(false)
const editFormRef = ref(null)
const editFormData = reactive({
  account_book_code: '',
  account_book_name: '',
  accounting_entity: '',
  unit_type: '',
  base_currency: '',
  standard_version: '',
  status: ''
})

const editFormRules = {
  account_book_name: [
    { required: true, message: '请输入账套名称', trigger: 'blur' }
  ],
  accounting_entity: [
    { required: true, message: '请输入核算主体', trigger: 'blur' }
  ],
  unit_type: [
    { required: true, message: '请选择单位类型', trigger: 'change' }
  ],
  base_currency: [
    { required: true, message: '请选择基础币种', trigger: 'change' }
  ],
  standard_version: [
    { required: true, message: '请选择准则版本', trigger: 'change' }
  ]
}

// 添加年度弹窗
const addYearDialogVisible = ref(false)
const yearSubmitting = ref(false)
const yearFormRef = ref(null)
const yearFormData = reactive({
  fiscal_year: new Date().getFullYear()
})

const yearFormRules = {
  fiscal_year: [
    { required: true, message: '请选择会计年度', trigger: 'change' }
  ]
}

// 可选年度列表（排除已导入的年度）
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  const importedYears = fiscalYears.value.map(item => item.fiscal_year)
  const years = []
  for (let year = currentYear + 5; year >= 1990; year--) {
    if (!importedYears.includes(year)) {
      years.push(year)
    }
  }
  return years
})

// 格式化货币
const formatCurrency = (currency) => {
  const map = {
    CNY: 'CNY (人民币)',
    USD: 'USD (美元)',
    EUR: 'EUR (欧元)'
  }
  return map[currency] || currency
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取详情
const fetchDetail = async () => {
  loading.value = true
  try {
    const response = await accountBookApi.getDetail(accountBookCode.value)
    if (response.data.success) {
      detailData.value = response.data.data || {}
      // 如果接口返回了会计年度，直接使用
      if (response.data.data?.imported_fiscal_years) {
        fiscalYears.value = response.data.data.imported_fiscal_years.map(year => ({
          fiscal_year: year,
          created_at: null
        }))
      }
    } else {
      ElMessage.error(response.data.message || '获取详情失败')
    }
  } catch (error) {
    console.error('获取账套详情失败:', error)
    ElMessage.error('获取账套详情失败')
  } finally {
    loading.value = false
  }
}

// 获取会计年度列表
const fetchFiscalYears = async () => {
  yearLoading.value = true
  try {
    const response = await accountBookApi.getFiscalYears(accountBookCode.value)
    if (response.data.success) {
      fiscalYears.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取会计年度失败:', error)
  } finally {
    yearLoading.value = false
  }
}

// 返回列表
const goBack = () => {
  router.push('/home/accountInfo/list')
}

// 显示编辑弹窗
const showEditDialog = () => {
  const status = detailData.value.status
  Object.assign(editFormData, {
    account_book_code: detailData.value.account_book_code,
    account_book_name: detailData.value.account_book_name,
    accounting_entity: detailData.value.accounting_entity,
    unit_type: detailData.value.unit_type,
    base_currency: detailData.value.base_currency,
    standard_version: detailData.value.standard_version,
    status: status === 1 || status === '1' ? 1 : (status === 0 || status === '0' ? 0 : 1)
  })
  editDialogVisible.value = true
}

// 提交编辑
const handleEditSubmit = async () => {
  try {
    await editFormRef.value.validate()
    
    submitting.value = true
    const response = await accountBookApi.update(editFormData.account_book_code, editFormData)
    
    if (response.data.success) {
      ElMessage.success('修改成功')
      editDialogVisible.value = false
      fetchDetail()
    } else {
      ElMessage.error(response.data.message || '修改失败')
    }
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 显示添加年度弹窗
const showAddYearDialog = () => {
  yearFormData.fiscal_year = availableYears.value[0] || new Date().getFullYear()
  addYearDialogVisible.value = true
}

// 添加年度
const handleAddYear = async () => {
  try {
    await yearFormRef.value.validate()
    
    yearSubmitting.value = true
    const response = await accountBookApi.addFiscalYear(
      accountBookCode.value,
      yearFormData.fiscal_year
    )
    
    if (response.data.success) {
      ElMessage.success('添加成功')
      addYearDialogVisible.value = false
      fetchFiscalYears()
      fetchDetail()
    } else {
      ElMessage.error(response.data.message || '添加失败')
    }
  } catch (error) {
    if (error !== false) {
      console.error('添加失败:', error)
      ElMessage.error('添加失败')
    }
  } finally {
    yearSubmitting.value = false
  }
}

// 查看凭证
const handleViewVouchers = (row) => {
  ElMessage.info(`查看 ${row.fiscal_year} 年度凭证功能开发中...`)
}

// 删除年度
const handleDeleteYear = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.fiscal_year} 年度吗？`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await accountBookApi.deleteFiscalYear(
      accountBookCode.value,
      row.fiscal_year
    )
    
    if (response.data.success) {
      ElMessage.success('删除成功')
      fetchFiscalYears()
      fetchDetail()
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  if (accountBookCode.value) {
    fetchDetail()
    fetchFiscalYears()
  } else {
    ElMessage.error('账套编码不能为空')
    goBack()
  }
})
</script>

<style scoped>
.account-book-detail {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #f5f7fa;
  overflow-y: auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.breadcrumb-item {
  color: #909399;
  cursor: pointer;
}

.breadcrumb-item:hover {
  color: #409eff;
}

.breadcrumb-sep {
  color: #c0c4cc;
}

.breadcrumb-current {
  color: #303133;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 信息卡片 */
.info-card {
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  padding: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.info-grid {
  display: flex;
  gap: 48px;
}

.info-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

/* 会计年度卡片 */
.fiscal-year-card {
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
}

.year-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.empty-tip {
  padding: 40px 0;
}

/* 添加年度弹窗内容 */
.add-year-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.year-form {
  flex: 1;
}

.year-field {
  margin-bottom: 0;
}

.year-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

/* 响应式 */
@media (max-width: 992px) {
  .info-grid {
    flex-direction: column;
    gap: 20px;
  }
  
  .title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
