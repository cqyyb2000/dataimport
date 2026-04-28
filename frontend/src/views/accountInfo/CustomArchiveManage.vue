<template>
  <div class="custom-archive-manage">
    <!-- 左侧导航树 -->
    <div class="left-panel">
      <div class="left-header">
        <span class="header-title">账套导航</span>
        <div class="header-actions">
          <el-button type="primary" link @click="showCreateItemDialog" title="新建档案项">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button type="primary" link @click="refreshTree" title="刷新">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>
      
      <div class="tree-container" v-loading="treeLoading">
        <el-tree
          ref="treeRef"
          :data="treeData"
          :props="treeProps"
          node-key="id"
          :expand-on-click-node="false"
          :highlight-current="true"
          :default-expanded-keys="expandedKeys"
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node" :class="{ 'is-active': currentNode?.id === data.id }">
              <el-icon class="node-icon" :style="{ color: getNodeIconColor(data) }">
                <component :is="getNodeIcon(data)" />
              </el-icon>
              <span class="node-label">{{ node.label }}</span>
              <el-tag 
                v-if="data.type === 'archive' && data.status !== undefined" 
                :type="data.status === 1 ? 'success' : 'info'" 
                size="small"
                class="node-tag"
              >
                {{ data.status === 1 ? '启用' : '停用' }}
              </el-tag>
              <!-- 档案项的操作按钮 -->
              <div v-if="data.type === 'archive'" class="node-actions" @click.stop>
                <el-button type="primary" link size="small" @click="handleEditItem(data)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" link size="small" @click="handleDeleteItem(data)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
        </el-tree>
        
        <el-empty v-if="!treeLoading && treeData.length === 0" description="暂无账套数据" />
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="right-panel">
      <!-- 未选择档案项时的提示 -->
      <div v-if="!currentArchive" class="empty-state">
        <el-empty description="请在左侧选择一个档案项查看详情">
          <template #image>
            <el-icon :size="60" color="#909399"><Folder /></el-icon>
          </template>
        </el-empty>
      </div>

      <!-- 已选择档案项时显示内容 -->
      <template v-else>
        <!-- 页面头部 -->
        <div class="page-header">
          <div class="title-section">
            <div class="breadcrumb">
              {{ currentArchive.accountBookName }} / {{ currentArchive.fiscalYear }}年度 / {{ currentArchive.archiveItemName }}
            </div>
            <h2 class="page-title">{{ currentArchive.archiveItemName }}列表</h2>
          </div>
          <div class="action-buttons">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索编码/名称..."
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button type="primary" @click="showCreateValueDialog">
              <el-icon><Plus /></el-icon>
              新增档案
            </el-button>
            <el-upload
              ref="excelUploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :limit="1"
              accept=".xlsx,.xls"
              :before-upload="beforeExcelUpload"
              :on-change="handleExcelFileChange"
              :on-exceed="handleExcelExceed"
            >
              <el-button type="success" :loading="importingExcel">
                <el-icon><Upload /></el-icon>
                {{ importingExcel ? '导入中...' : 'Excel导入' }}
              </el-button>
            </el-upload>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-container">
          <div class="table-area-inner">
            <el-table
              v-loading="tableLoading"
              :data="tableData"
              stripe
              border
              style="width: 100%"
              :height="'100%'"
              row-key="archive_value_code"
              :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
            >
            <el-table-column prop="archive_value_code" label="编码" width="150" />
            <el-table-column prop="archive_value_name" label="名称" min-width="200" />
            <el-table-column label="级次" width="80" align="center">
              <template #default="{ row }">
                {{ row.level ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="parent_value_code" label="上级编码" width="150">
              <template #default="{ row }">
                <span v-if="row.parent_value_code">{{ row.parent_value_code }}</span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleEditValue(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" link @click="handleDeleteValue(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-area">
          <span class="pagination-info">共 {{ total }} 条记录</span>
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
      </template>
    </div>

    <!-- 新建/编辑档案值弹窗 -->
    <el-dialog
      v-model="valueDialogVisible"
      :title="isEditValue ? '编辑档案值' : '新增档案值'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="valueFormRef"
        :model="valueFormData"
        :rules="valueFormRules"
        label-width="100px"
        label-position="top"
      >
        <el-form-item label="档案值编码" prop="archive_value_code">
          <el-input
            v-model="valueFormData.archive_value_code"
            placeholder="请输入档案值编码"
            :disabled="isEditValue"
            clearable
            @blur="valueFormData.archive_value_code = (valueFormData.archive_value_code || '').trim()"
          />
        </el-form-item>
        <el-form-item label="档案值名称" prop="archive_value_name">
          <el-input
            v-model="valueFormData.archive_value_name"
            placeholder="请输入档案值名称"
            clearable
            @blur="valueFormData.archive_value_name = (valueFormData.archive_value_name || '').trim()"
          />
        </el-form-item>
        <el-form-item label="上级档案值" prop="parent_value_code">
          <el-select
            v-model="valueFormData.parent_value_code"
            placeholder="请选择上级档案值（可选）"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="item in parentValueOptions"
              :key="item.archive_value_code"
              :label="`${item.archive_value_code} - ${item.archive_value_name}`"
              :value="item.archive_value_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="级次" prop="level">
          <el-input-number
            v-model="valueFormData.level"
            :min="1"
            :max="10"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item v-if="isEditValue" label="状态" prop="status">
          <el-select v-model="valueFormData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="valueDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitValue">
          {{ isEditValue ? '保存修改' : '创建档案' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建档案项弹窗 -->
    <el-dialog
      v-model="itemDialogVisible"
      :title="isEditItem ? '编辑档案项' : '新建档案项'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="itemFormRef"
        :model="itemFormData"
        :rules="itemFormRules"
        label-width="100px"
        label-position="top"
      >
        <el-form-item label="所属账套" prop="account_book_code">
          <el-select
            v-model="itemFormData.account_book_code"
            placeholder="请选择账套"
            style="width: 100%"
            :disabled="isEditItem"
            @change="handleAccountBookChange"
          >
            <el-option
              v-for="item in accountBookOptions"
              :key="item.account_book_code"
              :label="item.account_book_name"
              :value="item.account_book_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="会计年度" prop="fiscal_year">
          <el-select
            v-model="itemFormData.fiscal_year"
            placeholder="请选择年度"
            style="width: 100%"
            :disabled="isEditItem || !itemFormData.account_book_code"
          >
            <el-option
              v-for="year in fiscalYearOptions"
              :key="year"
              :label="`${year}年度`"
              :value="year"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="档案项编码" prop="archive_item_code">
          <el-input
            v-model="itemFormData.archive_item_code"
            placeholder="请输入档案项编码"
            :disabled="isEditItem"
          />
        </el-form-item>
        <el-form-item label="档案项名称" prop="archive_item_name">
          <el-input v-model="itemFormData.archive_item_name" placeholder="请输入档案项名称" />
        </el-form-item>
        <el-form-item v-if="isEditItem" label="状态" prop="status">
          <el-select v-model="itemFormData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmitItem">
          {{ isEditItem ? '保存修改' : '创建档案项' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Search, Refresh, Edit, Delete, Folder, Upload,
  DataBoard, Calendar, Document
} from '@element-plus/icons-vue'
import { accountBookApi } from '@/api/accountBook'
import { customArchiveItemApi, customArchiveValueApi } from '@/api/customArchive'

// 树形结构相关
const treeRef = ref(null)
const treeLoading = ref(false)
const treeData = ref([])
const expandedKeys = ref([])
const currentNode = ref(null)

const treeProps = {
  children: 'children',
  label: 'label'
}

// 当前选中的档案项信息
const currentArchive = ref(null)

// 表格相关
const tableLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')
const excelUploadRef = ref(null)
const importingExcel = ref(false)

// 档案值弹窗
const valueDialogVisible = ref(false)
const isEditValue = ref(false)
const valueFormRef = ref(null)
const submitting = ref(false)
const parentValueOptions = ref([])

const valueFormData = reactive({
  account_book_code: '',
  fiscal_year: '',
  archive_item_code: '',
  archive_value_code: '',
  archive_value_name: '',
  parent_value_code: '',
  level: 1,
  status: 1
})

const valueFormRules = {
  archive_value_code: [
    { required: true, message: '请输入档案值编码', trigger: 'blur' }
  ],
  archive_value_name: [
    { required: true, message: '请输入档案值名称', trigger: 'blur' }
  ],
  level: [
    { required: true, message: '请输入级次', trigger: 'blur' }
  ]
}

// 档案项弹窗
const itemDialogVisible = ref(false)
const isEditItem = ref(false)
const itemFormRef = ref(null)
const accountBookOptions = ref([])
const fiscalYearOptions = ref([])

const itemFormData = reactive({
  account_book_code: '',
  fiscal_year: '',
  archive_item_code: '',
  archive_item_name: '',
  status: 1
})

const itemFormRules = {
  account_book_code: [
    { required: true, message: '请选择账套', trigger: 'change' }
  ],
  fiscal_year: [
    { required: true, message: '请选择年度', trigger: 'change' }
  ],
  archive_item_code: [
    { required: true, message: '请输入档案项编码', trigger: 'blur' }
  ],
  archive_item_name: [
    { required: true, message: '请输入档案项名称', trigger: 'blur' }
  ]
}

// 获取节点图标
const getNodeIcon = (data) => {
  switch (data.type) {
    case 'accountBook':
      return DataBoard
    case 'year':
      return Calendar
    case 'archive':
      return Document
    default:
      return Folder
  }
}

// 获取节点图标颜色
const getNodeIconColor = (data) => {
  switch (data.type) {
    case 'accountBook':
      return '#E42313'
    case 'year':
      return '#0D0D0D'
    case 'archive':
      return currentNode.value?.id === data.id ? '#E42313' : '#7A7A7A'
    default:
      return '#7A7A7A'
  }
}

// 加载树形结构数据
const loadTreeData = async () => {
  treeLoading.value = true
  try {
    // 获取所有账套
    const response = await accountBookApi.getList({ page: 1, page_size: 1000 })
    if (!response.data.success) {
      ElMessage.error('获取账套列表失败')
      return
    }

    const accountBooks = response.data.items || []
    const tree = []
    const keys = []

    for (const book of accountBooks) {
      const bookNode = {
        id: `book_${book.account_book_code}`,
        type: 'accountBook',
        label: book.account_book_name,
        code: book.account_book_code,
        children: []
      }

      // 获取账套下的年度
      const years = book.imported_fiscal_years || []
      for (const year of years) {
        const yearNode = {
          id: `year_${book.account_book_code}_${year}`,
          type: 'year',
          label: `${year}年度`,
          accountBookCode: book.account_book_code,
          accountBookName: book.account_book_name,
          year: year,
          children: []
        }

        // 获取年度下的档案项
        try {
          const archiveResponse = await customArchiveItemApi.getListAll({
            account_book_code: book.account_book_code,
            fiscal_year: year,
            status: 1
          })
          if (archiveResponse.data.success) {
            const archives = archiveResponse.data.items || []
            yearNode.children = archives.map(archive => ({
              id: `archive_${book.account_book_code}_${year}_${archive.archive_item_code}`,
              type: 'archive',
              label: archive.archive_item_name,
              accountBookCode: book.account_book_code,
              accountBookName: book.account_book_name,
              fiscalYear: year,
              archiveItemCode: archive.archive_item_code,
              archiveItemName: archive.archive_item_name,
              status: archive.status
            }))
          }
        } catch (e) {
          console.error('获取档案项失败:', e)
        }

        if (yearNode.children.length > 0) {
          bookNode.children.push(yearNode)
          keys.push(yearNode.id)
        }
      }

      if (bookNode.children.length > 0 || years.length > 0) {
        tree.push(bookNode)
        keys.push(bookNode.id)
      }
    }

    treeData.value = tree
    expandedKeys.value = keys
  } catch (error) {
    console.error('加载树形数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    treeLoading.value = false
  }
}

// 刷新树
const refreshTree = () => {
  loadTreeData()
}

// 节点点击
const handleNodeClick = (data) => {
  currentNode.value = data
  
  if (data.type === 'archive') {
    currentArchive.value = {
      accountBookCode: data.accountBookCode,
      accountBookName: data.accountBookName,
      fiscalYear: data.fiscalYear,
      archiveItemCode: data.archiveItemCode,
      archiveItemName: data.archiveItemName
    }
    currentPage.value = 1
    searchKeyword.value = ''
    fetchTableData()
    loadParentValueOptions()
  }
}

// 获取表格数据
const fetchTableData = async () => {
  if (!currentArchive.value) return

  tableLoading.value = true
  try {
    const params = {
      account_book_code: currentArchive.value.accountBookCode,
      fiscal_year: currentArchive.value.fiscalYear,
      archive_item_code: currentArchive.value.archiveItemCode,
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (searchKeyword.value) {
      params.archive_value_code = searchKeyword.value
      params.archive_value_name = searchKeyword.value
    }

    const response = await customArchiveValueApi.getList(params)
    if (response.data.success) {
      tableData.value = response.data.items || []
      total.value = response.data.total || 0
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取档案值列表失败:', error)
    ElMessage.error('获取档案值列表失败')
  } finally {
    tableLoading.value = false
  }
}

// 加载上级档案值选项
const loadParentValueOptions = async () => {
  if (!currentArchive.value) return

  try {
    const response = await customArchiveItemApi.getValues(
      currentArchive.value.accountBookCode,
      currentArchive.value.fiscalYear,
      currentArchive.value.archiveItemCode
    )
    if (response.data.success) {
      parentValueOptions.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取上级档案值选项失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchTableData()
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  fetchTableData()
}

const handleCurrentChange = () => {
  fetchTableData()
}

// Excel导入校验
const beforeExcelUpload = (file) => {
  const isExcel = /\.(xlsx|xls)$/i.test(file.name || '')
  if (!isExcel) {
    ElMessage.error('仅支持上传 Excel 文件（.xlsx/.xls）')
    return false
  }
  return true
}

const handleExcelExceed = () => {
  ElMessage.warning('每次只能选择一个文件')
}

const handleExcelFileChange = async (uploadFile) => {
  if (!currentArchive.value) {
    ElMessage.warning('请先选择一个档案项')
    excelUploadRef.value?.clearFiles()
    return
  }

  const rawFile = uploadFile?.raw
  if (!rawFile) return

  const isExcel = /\.(xlsx|xls)$/i.test(rawFile.name || '')
  if (!isExcel) {
    ElMessage.error('仅支持上传 Excel 文件（.xlsx/.xls）')
    excelUploadRef.value?.clearFiles()
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定导入文件「${rawFile.name}」到档案项「${currentArchive.value.archiveItemName}」吗？`,
      '确认导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    importingExcel.value = true
    const response = await customArchiveValueApi.importExcel(
      rawFile,
      currentArchive.value.accountBookCode,
      currentArchive.value.fiscalYear,
      currentArchive.value.archiveItemCode
    )

    if (response.data.success) {
      ElMessage.success(response.data.message || 'Excel导入成功')
      fetchTableData()
      loadParentValueOptions()
    } else {
      ElMessage.error(response.data.message || 'Excel导入失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Excel导入失败:', error)
      ElMessage.error(error?.response?.data?.message || 'Excel导入失败')
    }
  } finally {
    importingExcel.value = false
    excelUploadRef.value?.clearFiles()
  }
}

// 显示创建档案值弹窗
const showCreateValueDialog = () => {
  isEditValue.value = false
  Object.assign(valueFormData, {
    account_book_code: currentArchive.value.accountBookCode,
    fiscal_year: currentArchive.value.fiscalYear,
    archive_item_code: currentArchive.value.archiveItemCode,
    archive_value_code: '',
    archive_value_name: '',
    parent_value_code: '',
    level: 1,
    status: 1
  })
  valueFormRef.value?.clearValidate()
  valueDialogVisible.value = true
}

// 编辑档案值
const handleEditValue = (row) => {
  isEditValue.value = true
  Object.assign(valueFormData, {
    account_book_code: currentArchive.value.accountBookCode,
    fiscal_year: currentArchive.value.fiscalYear,
    archive_item_code: currentArchive.value.archiveItemCode,
    archive_value_code: row.archive_value_code,
    archive_value_name: row.archive_value_name,
    parent_value_code: row.parent_value_code || '',
    level: row.level || 1,
    status: row.status
  })
  valueDialogVisible.value = true
}

// 删除档案值
const handleDeleteValue = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除档案值「${row.archive_value_name}」吗？如有子节点需先删除子节点。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await customArchiveValueApi.delete(
      currentArchive.value.accountBookCode,
      currentArchive.value.fiscalYear,
      currentArchive.value.archiveItemCode,
      row.archive_value_code
    )

    if (response.data.success) {
      ElMessage.success('删除成功')
      fetchTableData()
      loadParentValueOptions()
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

// 提交档案值
const handleSubmitValue = async () => {
  try {
    await valueFormRef.value.validate()
    submitting.value = true

    // 提交前规范化数据，避免空字符串触发后端 400 校验错误
    const payload = {
      account_book_code: valueFormData.account_book_code,
      fiscal_year: valueFormData.fiscal_year,
      archive_item_code: valueFormData.archive_item_code,
      archive_value_code: (valueFormData.archive_value_code || '').trim(),
      archive_value_name: (valueFormData.archive_value_name || '').trim(),
      level: valueFormData.level || 1,
      status: valueFormData.status
    }
    if (valueFormData.parent_value_code && String(valueFormData.parent_value_code).trim() !== '') {
      payload.parent_value_code = String(valueFormData.parent_value_code).trim()
    }

    if (!payload.archive_value_code) {
      ElMessage.warning('档案值编码不能为空')
      return
    }
    if (!payload.archive_value_name) {
      ElMessage.warning('档案值名称不能为空')
      return
    }

    let response
    if (isEditValue.value) {
      console.log('[CustomArchiveValue][UPDATE] request', {
        method: 'PUT',
        url: `/api/custom_archive_values/${payload.account_book_code}/${payload.fiscal_year}/${payload.archive_item_code}/${payload.archive_value_code}`,
        pathParams: {
          account_book_code: payload.account_book_code,
          fiscal_year: payload.fiscal_year,
          archive_item_code: payload.archive_item_code,
          archive_value_code: payload.archive_value_code
        },
        payload
      })
      response = await customArchiveValueApi.update(
        payload.account_book_code,
        payload.fiscal_year,
        payload.archive_item_code,
        payload.archive_value_code,
        payload
      )
    } else {
      console.log('[CustomArchiveValue][CREATE] request', {
        method: 'POST',
        url: '/api/custom_archive_values',
        payload
      })
      response = await customArchiveValueApi.create(payload)
    }

    console.log(`[CustomArchiveValue][${isEditValue.value ? 'UPDATE' : 'CREATE'}] response`, {
      status: response?.status,
      data: response?.data
    })

    if (response.data.success) {
      ElMessage.success(isEditValue.value ? '修改成功' : '创建成功')
      valueDialogVisible.value = false
      fetchTableData()
      loadParentValueOptions()
    } else {
      ElMessage.error(response.data.message || (isEditValue.value ? '修改失败' : '创建失败'))
    }
  } catch (error) {
    if (error !== false) {
      console.error(`[CustomArchiveValue][${isEditValue.value ? 'UPDATE' : 'CREATE'}] error`, {
        message: error?.message,
        code: error?.code,
        status: error?.response?.status,
        responseData: error?.response?.data,
        requestConfig: {
          method: error?.config?.method,
          url: error?.config?.url,
          baseURL: error?.config?.baseURL,
          params: error?.config?.params,
          data: error?.config?.data,
          headers: error?.config?.headers
        }
      })
      console.error('提交失败:', error)
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 加载账套选项
const loadAccountBookOptions = async () => {
  try {
    const response = await accountBookApi.getList({ page: 1, page_size: 1000 })
    if (response.data.success) {
      accountBookOptions.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取账套选项失败:', error)
  }
}

// 显示创建档案项弹窗
const showCreateItemDialog = () => {
  isEditItem.value = false
  Object.assign(itemFormData, {
    account_book_code: '',
    fiscal_year: '',
    archive_item_code: '',
    archive_item_name: '',
    status: 1
  })
  fiscalYearOptions.value = []
  itemFormRef.value?.clearValidate()
  itemDialogVisible.value = true
}

// 编辑档案项
const handleEditItem = (data) => {
  isEditItem.value = true
  Object.assign(itemFormData, {
    account_book_code: data.accountBookCode,
    fiscal_year: data.fiscalYear,
    archive_item_code: data.archiveItemCode,
    archive_item_name: data.archiveItemName,
    status: data.status
  })
  // 加载年度选项
  const book = accountBookOptions.value.find(b => b.account_book_code === data.accountBookCode)
  if (book && book.imported_fiscal_years) {
    fiscalYearOptions.value = book.imported_fiscal_years
  }
  itemDialogVisible.value = true
}

// 删除档案项
const handleDeleteItem = async (data) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除档案项「${data.archiveItemName}」吗？删除后将同时删除该档案项下的所有档案值。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await customArchiveItemApi.delete(
      data.accountBookCode,
      data.fiscalYear,
      data.archiveItemCode
    )

    if (response.data.success) {
      ElMessage.success('删除成功')
      // 如果删除的是当前选中的档案项，清空右侧内容
      if (currentArchive.value && 
          currentArchive.value.archiveItemCode === data.archiveItemCode) {
        currentArchive.value = null
        currentNode.value = null
      }
      loadTreeData()
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

// 账套变化时加载年度
const handleAccountBookChange = async (code) => {
  itemFormData.fiscal_year = ''
  fiscalYearOptions.value = []
  
  if (!code) return

  const book = accountBookOptions.value.find(b => b.account_book_code === code)
  if (book && book.imported_fiscal_years) {
    fiscalYearOptions.value = book.imported_fiscal_years
  }
}

// 提交档案项
const handleSubmitItem = async () => {
  try {
    await itemFormRef.value.validate()
    submitting.value = true

    let response
    if (isEditItem.value) {
      response = await customArchiveItemApi.update(
        itemFormData.account_book_code,
        itemFormData.fiscal_year,
        itemFormData.archive_item_code,
        itemFormData
      )
    } else {
      response = await customArchiveItemApi.create(itemFormData)
    }

    if (response.data.success) {
      ElMessage.success(isEditItem.value ? '修改成功' : '创建成功')
      itemDialogVisible.value = false
      loadTreeData()
    } else {
      ElMessage.error(response.data.message || (isEditItem.value ? '修改失败' : '创建失败'))
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
  try {
    loadTreeData()
    loadAccountBookOptions()
  } catch (error) {
    console.error('组件初始化失败:', error)
    ElMessage.error('页面加载失败，请刷新重试')
  }
})
</script>

<style scoped>
.custom-archive-manage {
  display: flex;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #f5f7fa;
}

/* 左侧面板 */
.left-panel {
  width: 280px;
  min-width: 280px;
  background: #fafafa;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.left-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #0d0d0d;
}

.tree-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  width: 100%;
}

.tree-node.is-active {
  background: #fef2f2;
}

.node-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #0d0d0d;
}

.node-tag {
  flex-shrink: 0;
}

.node-actions {
  display: none;
  gap: 4px;
  margin-left: auto;
}

.tree-node:hover .node-actions {
  display: flex;
}

.tree-node:hover .node-tag {
  display: none;
}

.header-actions {
  display: flex;
  gap: 4px;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 32px;
  overflow: hidden;
  background: #fff;
}

.empty-state {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 页面头部 */
.page-header {
  flex: 0 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breadcrumb {
  font-size: 12px;
  color: #7a7a7a;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #0d0d0d;
}

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 表格容器 */
.table-container {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

/* 内层固定高度容器：用 100% 承接 table-container 高度，避免对 .el-table 用 flex 导致内部 100% 链断裂 */
.table-area-inner {
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

/* 不覆盖 .el-table 的 display/flex，仅保证在父容器内可收缩，高度完全由 :height="100%" 提供 */
.table-area-inner :deep(.el-table) {
  min-height: 0;
}

/* body-wrapper 不设 overflow:auto，滚动由内部 el-scrollbar__wrap 负责 */
.table-area-inner :deep(.el-table__body-wrapper) {
  overflow: hidden;
}

/* 确保 el-scrollbar 及其 wrap 获得完整高度，wrap 为唯一纵向滚动容器 */
.table-area-inner :deep(.el-table__body-wrapper .el-scrollbar) {
  height: 100%;
}

.table-area-inner :deep(.el-table__body-wrapper .el-scrollbar__wrap) {
  height: 100% !important;
  max-height: 100% !important;
  overflow-y: auto !important;
  overflow-x: auto !important;
  /* 保证滚轮和拖拽能作用在 wrap 上 */
  touch-action: pan-y pan-x;
}

.text-muted {
  color: #909399;
}

/* 分页区域 */
.pagination-area {
  flex: 0 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  min-height: 44px;
}

.pagination-info {
  font-size: 12px;
  color: #7a7a7a;
}

/* Element Plus 树组件样式覆盖 */
:deep(.el-tree) {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 4px 16px;
}

:deep(.el-tree-node__expand-icon) {
  color: #7a7a7a;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: transparent;
}

:deep(.el-tree-node__content:hover) {
  background: #f5f5f5;
}

/* 响应式 */
@media (max-width: 1024px) {
  .left-panel {
    width: 240px;
    min-width: 240px;
  }

  .right-panel {
    padding: 20px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .action-buttons {
    flex-wrap: wrap;
  }
}
</style>
