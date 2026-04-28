<template>
  <div class="account-book-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">账套管理</h2>
        <span class="page-subtitle">管理账套信息及会计年度</span>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建账套
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区域 -->
    <div class="filter-area">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索账套编码/名称..."
        clearable
        style="width: 280px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select 
        v-model="filterEntity" 
        placeholder="核算主体" 
        clearable
        style="width: 150px"
        @change="handleSearch"
      >
        <el-option
          v-for="item in entityOptions"
          :key="item"
          :label="item"
          :value="item"
        />
      </el-select>
      
      <el-select 
        v-model="filterStatus" 
        placeholder="状态" 
        clearable
        style="width: 120px"
        @change="handleSearch"
      >
        <el-option label="启用" :value="1" />
        <el-option label="停用" :value="0" />
      </el-select>
    </div>

    <!-- 数据表格 -->
    <div class="table-area">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="account_book_code" label="账套编码" width="120" />
        <el-table-column prop="account_book_name" label="账套名称" min-width="160" />
        <el-table-column prop="accounting_entity" label="核算主体" width="140" />
        <el-table-column prop="unit_type" label="单位类型" width="100" />
        <el-table-column prop="base_currency" label="币种" width="80" />
        <el-table-column label="已导入年度" width="140">
          <template #default="{ row }">
            <span v-if="row.imported_fiscal_years && row.imported_fiscal_years.length">
              {{ row.imported_fiscal_years.join(', ') }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="default" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-area">
      <span class="pagination-info">共 {{ total }} 条记录，第 {{ currentPage }}/{{ totalPages }} 页</span>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 新建/编辑账套弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑账套' : '新建账套'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="top"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="账套编码" prop="account_book_code">
              <el-input 
                v-model="formData.account_book_code" 
                placeholder="请输入账套编码"
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="账套名称" prop="account_book_name">
              <el-input v-model="formData.account_book_name" placeholder="请输入账套名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="核算主体" prop="accounting_entity">
              <el-input v-model="formData.accounting_entity" placeholder="请输入核算主体" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位类型" prop="unit_type">
              <el-select v-model="formData.unit_type" placeholder="请选择单位类型" style="width: 100%">
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
              <el-select v-model="formData.base_currency" placeholder="请选择基础币种" style="width: 100%">
                <el-option label="CNY (人民币)" value="CNY" />
                <el-option label="USD (美元)" value="USD" />
                <el-option label="EUR (欧元)" value="EUR" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="准则版本" prop="standard_version">
              <el-select v-model="formData.standard_version" placeholder="请选择准则版本" style="width: 100%">
                <el-option label="政府会计准则(2019)" value="政府会计准则(2019)" />
                <el-option label="企业会计准则(2006)" value="企业会计准则(2006)" />
                <el-option label="小企业会计准则(2011)" value="小企业会计准则(2011)" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" v-if="isEdit">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="启用" :value="1" />
                <el-option label="停用" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '创建账套' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { accountBookApi } from '@/api/accountBook'

const router = useRouter()

// 列表数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 搜索筛选
const searchKeyword = ref('')
const filterEntity = ref('')
const filterStatus = ref('')
const entityOptions = ref([])

// 计算总页数
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

// 弹窗相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const formData = reactive({
  account_book_code: '',
  account_book_name: '',
  accounting_entity: '',
  unit_type: '',
  base_currency: 'CNY',
  standard_version: '',
  status: 1
})

const formRules = {
  account_book_code: [
    { required: true, message: '请输入账套编码', trigger: 'blur' }
  ],
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

// 获取列表数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchKeyword.value) {
      params.account_book_code = searchKeyword.value
      params.account_book_name = searchKeyword.value
    }
    if (filterEntity.value) {
      params.accounting_entity = filterEntity.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    
    const response = await accountBookApi.getList(params)
    if (response.data.success) {
      tableData.value = response.data.items || []
      total.value = response.data.total || 0
      
      // 收集核算主体选项
      const entities = new Set(tableData.value.map(item => item.accounting_entity).filter(Boolean))
      entityOptions.value = [...entities]
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取账套列表失败:', error)
    ElMessage.error('获取账套列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

// 查看详情
const handleView = (row) => {
  router.push(`/home/accountInfo/detail/${row.account_book_code}`)
}

// 显示创建弹窗
const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, {
    account_book_code: row.account_book_code,
    account_book_name: row.account_book_name,
    accounting_entity: row.accounting_entity,
    unit_type: row.unit_type,
    base_currency: row.base_currency,
    standard_version: row.standard_version,
    status: row.status === 1 || row.status === '1' ? 1 : (row.status === 0 || row.status === '0' ? 0 : 1)
  })
  dialogVisible.value = true
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账套「${row.account_book_name}」吗？删除后将同时删除该账套下的所有会计年度数据。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await accountBookApi.delete(row.account_book_code)
    if (response.data.success) {
      ElMessage.success('删除成功')
      fetchData()
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

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    account_book_code: '',
    account_book_name: '',
    accounting_entity: '',
    unit_type: '',
    base_currency: 'CNY',
    standard_version: '',
    status: 1
  })
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    let response
    if (isEdit.value) {
      response = await accountBookApi.update(formData.account_book_code, formData)
    } else {
      response = await accountBookApi.create(formData)
    }
    
    if (response.data.success) {
      ElMessage.success(isEdit.value ? '修改成功' : '创建成功')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(response.data.message || (isEdit.value ? '修改失败' : '创建失败'))
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

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.account-book-list {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.page-subtitle {
  font-size: 13px;
  color: #909399;
}

/* 筛选区域 */
.filter-area {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

/* 表格区域 */
.table-area {
  flex: 1;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.text-muted {
  color: #909399;
}

/* 分页区域 */
.pagination-area {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.pagination-info {
  font-size: 13px;
  color: #606266;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .filter-area {
    flex-wrap: wrap;
  }
  
  .pagination-area {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
