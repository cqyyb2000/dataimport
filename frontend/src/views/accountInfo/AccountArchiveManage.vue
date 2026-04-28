<template>
  <div class="account-archive-manage">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">科目档案</h2>
        <span class="page-subtitle">维护会计科目及科目辅助核算</span>
      </div>
      <div class="header-right">
        <el-select
          v-model="importMode"
          :disabled="!canQuery"
          class="header-import-mode"
          placeholder="导入模式"
        >
          <el-option label="更新或新增 (upsert)" value="upsert" />
          <el-option label="仅新增 (append)" value="append" />
        </el-select>
        <el-tooltip
          content="upsert：已存在则更新科目并重建辅助核算。append：仅允许新科目，若编号已存在则整单失败。"
          placement="bottom"
        >
          <el-icon class="header-mode-hint"><QuestionFilled /></el-icon>
        </el-tooltip>
        <el-upload
          ref="excelUploadRef"
          :auto-upload="false"
          :show-file-list="false"
          :limit="1"
          accept=".xlsx,.xlsm"
          :disabled="!canQuery"
          :before-upload="beforeAccountExcelUpload"
          :on-change="handleAccountExcelFileChange"
          :on-exceed="handleAccountExcelExceed"
        >
          <el-button type="success" :loading="importingExcel" :disabled="!canQuery">
            <el-icon><Upload /></el-icon>
            {{ importingExcel ? '导入中...' : 'Excel 导入' }}
          </el-button>
        </el-upload>
        <el-button type="primary" :disabled="!canQuery" @click="openAccountDialog(false)">
          <el-icon><Plus /></el-icon>
          新建科目
        </el-button>
      </div>
    </div>

    <div class="filter-area">
      <el-select
        v-model="query.account_book_code"
        placeholder="账套"
        filterable
        clearable
        style="width: 200px"
        @change="onBookChange"
      >
        <el-option
          v-for="b in accountBookOptions"
          :key="b.account_book_code"
          :label="`${b.account_book_name} (${b.account_book_code})`"
          :value="b.account_book_code"
        />
      </el-select>
      <el-select
        v-model="query.fiscal_year"
        placeholder="会计年度"
        clearable
        style="width: 140px"
        @change="onFiscalYearChange"
      >
        <el-option v-for="y in fiscalYearOptions" :key="y" :label="`${y} 年`" :value="y" />
      </el-select>
      <el-input
        v-model="query.account_code"
        placeholder="科目编号"
        clearable
        style="width: 140px"
        @keyup.enter="handleSearchAccounts"
      />
      <el-input
        v-model="query.account_name"
        placeholder="科目名称"
        clearable
        style="width: 160px"
        @keyup.enter="handleSearchAccounts"
      />
      <el-select v-model="query.account_type" placeholder="科目类型" clearable style="width: 130px">
        <el-option v-for="t in accountTypes" :key="t" :label="t" :value="t" />
      </el-select>
      <el-input
        v-model="query.parent_account_code"
        placeholder="上级科目"
        clearable
        style="width: 120px"
        @keyup.enter="handleSearchAccounts"
      />
      <el-select v-model="query.is_leaf" placeholder="末级" clearable style="width: 100px">
        <el-option label="是" :value="1" />
        <el-option label="否" :value="0" />
      </el-select>
      <el-select v-model="query.is_enabled" placeholder="启用" clearable style="width: 100px">
        <el-option label="是" :value="1" />
        <el-option label="否" :value="0" />
      </el-select>
      <el-select v-model="query.status" placeholder="状态" clearable style="width: 100px">
        <el-option label="启用" :value="1" />
        <el-option label="停用" :value="0" />
      </el-select>
      <el-button type="primary" :disabled="!canQuery" @click="handleSearchAccounts">
        <el-icon><Search /></el-icon>
        查询
      </el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div class="split-panels">
      <div class="panel accounts-panel">
        <div class="panel-head">
          <span class="panel-title">会计科目</span>
          <el-button type="primary" link :disabled="!selectedAccount" @click="openAccountDialog(true)">
            <el-icon><Edit /></el-icon>
            编辑当前
          </el-button>
          <el-button type="danger" link :disabled="!selectedAccount" @click="handleDeleteAccount">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
        <el-table
          ref="accountTableRef"
          v-loading="accountLoading"
          :data="accountRows"
          stripe
          border
          row-key="account_code"
          highlight-current-row
          height="100%"
          style="width: 100%"
          @current-change="onAccountRowChange"
        >
          <el-table-column prop="account_code" label="科目编号" width="120" fixed />
          <el-table-column prop="account_name" label="科目名称" min-width="160" />
          <el-table-column prop="account_level" label="级次" width="72" align="center" />
          <el-table-column prop="account_type" label="类型" width="110" />
          <el-table-column prop="balance_direction" label="余额方向" width="90" />
          <el-table-column label="末级" width="72" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_leaf === 1 ? 'success' : 'info'" size="small">
                {{ row.is_leaf === 1 ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="启用" width="72" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_enabled === 1 ? 'success' : 'info'" size="small">
                {{ row.is_enabled === 1 ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="parent_account_code" label="上级科目" width="120">
            <template #default="{ row }">
              <span v-if="row.parent_account_code">{{ row.parent_account_code }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-area">
          <span class="pagination-info">共 {{ accountTotal }} 条</span>
          <el-pagination
            v-model:current-page="accountPage"
            v-model:page-size="accountPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="accountTotal"
            layout="sizes, prev, pager, next"
            @size-change="fetchAccounts"
            @current-change="fetchAccounts"
          />
        </div>
      </div>

      <div class="panel aux-panel">
        <div class="panel-head">
          <span class="panel-title">
            科目辅助核算
            <template v-if="selectedAccount">
              <span class="sub">（{{ selectedAccount.account_code }} {{ selectedAccount.account_name }}）</span>
            </template>
          </span>
          <el-button type="primary" :disabled="!selectedAccount" @click="openAuxDialog(false)">
            <el-icon><Plus /></el-icon>
            新建辅助项
          </el-button>
        </div>
        <div v-if="!selectedAccount" class="aux-empty">
          <el-empty description="请在上方表格中选择一条会计科目" />
        </div>
        <template v-else>
          <el-table
            v-loading="auxLoading"
            :data="auxRows"
            stripe
            border
            height="100%"
            style="width: 100%"
          >
            <el-table-column prop="auxiliary_item_code" label="辅助项编号" width="120" />
            <el-table-column prop="auxiliary_item_name" label="名称" min-width="140" />
            <el-table-column prop="corresponding_archive" label="对应档案" width="120">
              <template #default="{ row }">
                <span v-if="row.corresponding_archive">{{ row.corresponding_archive }}</span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="auxiliary_item_description" label="描述" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.auxiliary_item_description">{{ row.auxiliary_item_description }}</span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openAuxDialog(true, row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button type="danger" link @click="handleDeleteAux(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-area">
            <span class="pagination-info">共 {{ auxTotal }} 条</span>
            <el-pagination
              v-model:current-page="auxPage"
              v-model:page-size="auxPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="auxTotal"
              layout="sizes, prev, pager, next"
              @size-change="fetchAuxiliaries"
              @current-change="fetchAuxiliaries"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- 科目 -->
    <el-dialog
      v-model="accountDialogVisible"
      :title="accountDialogEdit ? '编辑科目' : '新建科目'"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetAccountForm"
    >
      <el-form
        ref="accountFormRef"
        :model="accountForm"
        :rules="accountRules"
        label-width="110px"
        label-position="top"
      >
        <el-form-item v-if="!accountDialogEdit" label="科目编号" prop="account_code">
          <el-input v-model="accountForm.account_code" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item label="科目名称" prop="account_name">
          <el-input v-model="accountForm.account_name" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item label="科目级次" prop="account_level">
          <el-input-number v-model="accountForm.account_level" :min="1" :max="99" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="科目类型" prop="account_type">
          <el-select v-model="accountForm.account_type" placeholder="必填" style="width: 100%">
            <el-option v-for="t in accountTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="余额方向" prop="balance_direction">
          <el-select v-model="accountForm.balance_direction" placeholder="必填" style="width: 100%">
            <el-option v-for="d in balanceDirections" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="上级科目编号">
          <el-input v-model="accountForm.parent_account_code" placeholder="可选" clearable />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="是否末级">
              <el-select v-model="accountForm.is_leaf" style="width: 100%">
                <el-option label="否" :value="0" />
                <el-option label="是" :value="1" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否启用">
              <el-select v-model="accountForm.is_enabled" style="width: 100%">
                <el-option label="否" :value="0" />
                <el-option label="是" :value="1" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-select v-model="accountForm.status" style="width: 100%">
            <el-option label="停用" :value="0" />
            <el-option label="启用" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="accountForm.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="accountSubmitting" @click="submitAccount">确定</el-button>
      </template>
    </el-dialog>

    <!-- 辅助核算 -->
    <el-dialog
      v-model="auxDialogVisible"
      :title="auxDialogEdit ? '编辑辅助核算' : '新建辅助核算'"
      width="560px"
      :close-on-click-modal="false"
      @open="onAuxDialogOpen"
      @closed="resetAuxForm"
    >
      <el-form ref="auxFormRef" :model="auxForm" :rules="auxRules" label-width="120px" label-position="top">
        <el-form-item v-if="!auxDialogEdit" label="辅助项编号" prop="auxiliary_item_code">
          <el-input v-model="auxForm.auxiliary_item_code" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item label="辅助项名称" prop="auxiliary_item_name">
          <el-input v-model="auxForm.auxiliary_item_name" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item label="对应档案（自定义档案项编码）">
          <el-select
            v-model="auxForm.corresponding_archive"
            placeholder="可选，从档案项选择或留空后手输"
            filterable
            allow-create
            default-first-option
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="a in archiveItemOptions"
              :key="a.archive_item_code"
              :label="`${a.archive_item_name} (${a.archive_item_code})`"
              :value="a.archive_item_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="auxForm.auxiliary_item_description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="auxForm.status" style="width: 100%">
            <el-option label="停用" :value="0" />
            <el-option label="启用" :value="1" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">同步到自定义档案（2.3）</el-divider>
        <p class="aux-sync-hint">
          开启且「对应档案」非空时，将 upsert 档案项与档案值；仅维护本科目辅助项、不写档案表时请关闭。
        </p>
        <el-form-item label="同步写入档案表">
          <el-switch v-model="auxForm.sync_custom_archive" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="同步时档案项名称">
          <el-input v-model="auxForm.archive_item_name" placeholder="可选；不传则用对应档案编码作为名称" clearable />
        </el-form-item>
        <el-form-item label="同步时档案项描述">
          <el-input v-model="auxForm.archive_item_desc" type="textarea" :rows="2" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="同步时档案值描述">
          <el-input v-model="auxForm.archive_value_desc" type="textarea" :rows="2" placeholder="可选" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auxDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="auxSubmitting" @click="submitAux">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Upload, QuestionFilled } from '@element-plus/icons-vue'
import { accountBookApi, accountApi, accountAuxiliaryApi } from '@/api'
import { customArchiveItemApi } from '@/api/customArchive'

const accountTypes = ['资产类', '负债类', '共同类', '所有者权益类', '成本类', '损益类']
const balanceDirections = ['借', '贷']

const accountBookOptions = ref([])
const fiscalYearOptions = ref([])

const query = reactive({
  account_book_code: '',
  fiscal_year: '',
  account_code: '',
  account_name: '',
  account_type: '',
  parent_account_code: '',
  is_leaf: '',
  is_enabled: '',
  status: ''
})

const canQuery = computed(() => !!query.account_book_code && query.fiscal_year !== '' && query.fiscal_year !== null)

const accountLoading = ref(false)
const accountRows = ref([])
const accountTotal = ref(0)
const accountPage = ref(1)
const accountPageSize = ref(10)
const accountTableRef = ref(null)
const selectedAccount = ref(null)

const excelUploadRef = ref(null)
const importingExcel = ref(false)
const importMode = ref('upsert')

const auxLoading = ref(false)
const auxRows = ref([])
const auxTotal = ref(0)
const auxPage = ref(1)
const auxPageSize = ref(10)

const accountDialogVisible = ref(false)
const accountDialogEdit = ref(false)
const accountFormRef = ref(null)
const accountSubmitting = ref(false)
const accountForm = reactive({
  account_code: '',
  account_name: '',
  account_level: 1,
  account_type: '资产类',
  balance_direction: '借',
  parent_account_code: '',
  is_leaf: 0,
  is_enabled: 1,
  remark: '',
  status: 1
})

const accountRules = {
  account_code: [{ required: true, message: '请输入科目编号', trigger: 'blur' }],
  account_name: [{ required: true, message: '请输入科目名称', trigger: 'blur' }],
  account_level: [{ required: true, message: '请输入级次', trigger: 'change' }],
  account_type: [{ required: true, message: '请选择科目类型', trigger: 'change' }],
  balance_direction: [{ required: true, message: '请选择余额方向', trigger: 'change' }]
}

const auxDialogVisible = ref(false)
const auxDialogEdit = ref(false)
const auxFormRef = ref(null)
const auxSubmitting = ref(false)
const archiveItemOptions = ref([])
const auxForm = reactive({
  auxiliary_item_code: '',
  auxiliary_item_name: '',
  corresponding_archive: '',
  auxiliary_item_description: '',
  status: 1,
  sync_custom_archive: true,
  archive_item_name: '',
  archive_item_desc: '',
  archive_value_desc: ''
})

const auxRules = {
  auxiliary_item_code: [{ required: true, message: '请输入辅助项编号', trigger: 'blur' }],
  auxiliary_item_name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

function apiErr(e, fallback) {
  const msg = e?.response?.data?.message || e?.message || fallback
  ElMessage.error(msg)
}

function beforeAccountExcelUpload(file) {
  const ok = /\.(xlsx|xlsm)$/i.test(file.name || '')
  if (!ok) {
    ElMessage.error('仅支持 .xlsx / .xlsm 文件')
    return false
  }
  return true
}

function handleAccountExcelExceed() {
  ElMessage.warning('每次只能选择一个文件')
}

async function handleAccountExcelFileChange(uploadFile) {
  if (!canQuery.value) {
    ElMessage.warning('请先选择账套与会计年度')
    excelUploadRef.value?.clearFiles()
    return
  }
  const rawFile = uploadFile?.raw
  if (!rawFile) return
  if (!/\.(xlsx|xlsm)$/i.test(rawFile.name || '')) {
    ElMessage.error('仅支持 .xlsx / .xlsm 文件')
    excelUploadRef.value?.clearFiles()
    return
  }

  importingExcel.value = true
  try {
    const res = await accountApi.importExcelByPath(
      query.account_book_code,
      query.fiscal_year,
      rawFile,
      { mode: importMode.value }
    )
    if (res.data?.success) {
      const s = res.data.stats
      let detail = ''
      if (s && typeof s === 'object') {
        const ins = s.accounts_inserted ?? 0
        const upd = s.accounts_updated ?? 0
        const aux = s.auxiliaries_created ?? 0
        const skip = s.rows_skipped ?? 0
        detail = `（新增 ${ins}，更新 ${upd}，辅助项 ${aux}，跳过行 ${skip}）`
      }
      ElMessage.success((res.data.message || '导入成功') + detail)
      await fetchAccounts()
    } else {
      ElMessage.error(res.data?.message || '导入失败')
    }
  } catch (e) {
    apiErr(e, '导入失败')
  } finally {
    importingExcel.value = false
    excelUploadRef.value?.clearFiles()
  }
}

async function loadAccountBooks() {
  try {
    const res = await accountBookApi.getList({ page: 1, page_size: 100 })
    if (!res.data?.success) {
      ElMessage.error('获取账套列表失败')
      return
    }
    accountBookOptions.value = res.data.items || []
  } catch (e) {
    apiErr(e, '获取账套列表失败')
  }
}

function onBookChange() {
  query.fiscal_year = ''
  fiscalYearOptions.value = []
  const book = accountBookOptions.value.find((b) => b.account_book_code === query.account_book_code)
  if (book?.imported_fiscal_years?.length) {
    fiscalYearOptions.value = [...book.imported_fiscal_years].sort((a, b) => b - a)
    query.fiscal_year = fiscalYearOptions.value[0]
  }
  selectedAccount.value = null
  accountRows.value = []
  accountTotal.value = 0
  auxRows.value = []
  auxTotal.value = 0
}

function onFiscalYearChange() {
  selectedAccount.value = null
  accountRows.value = []
  accountTotal.value = 0
  auxRows.value = []
  auxTotal.value = 0
}

function resetFilters() {
  query.account_code = ''
  query.account_name = ''
  query.account_type = ''
  query.parent_account_code = ''
  query.is_leaf = ''
  query.is_enabled = ''
  query.status = ''
  accountPage.value = 1
  if (canQuery.value) fetchAccounts()
}

async function fetchAccounts() {
  if (!canQuery.value) {
    ElMessage.warning('请先选择账套与会计年度')
    return
  }
  accountLoading.value = true
  try {
    const params = {
      account_book_code: query.account_book_code,
      fiscal_year: query.fiscal_year,
      page: accountPage.value,
      page_size: accountPageSize.value
    }
    if (query.account_code) params.account_code = query.account_code
    if (query.account_name) params.account_name = query.account_name
    if (query.account_type) params.account_type = query.account_type
    if (query.parent_account_code) params.parent_account_code = query.parent_account_code
    if (query.is_leaf !== '' && query.is_leaf !== null) params.is_leaf = query.is_leaf
    if (query.is_enabled !== '' && query.is_enabled !== null) params.is_enabled = query.is_enabled
    if (query.status !== '' && query.status !== null) params.status = query.status

    const res = await accountApi.getList(params)
    if (!res.data?.success) {
      ElMessage.error('获取科目列表失败')
      return
    }
    accountRows.value = res.data.items || []
    accountTotal.value = res.data.total ?? 0

    await nextTick()
    if (selectedAccount.value) {
      const still = accountRows.value.find((r) => r.account_code === selectedAccount.value.account_code)
      if (still) {
        accountTableRef.value?.setCurrentRow(still)
        fetchAuxiliaries()
      } else {
        selectedAccount.value = null
        auxRows.value = []
        auxTotal.value = 0
        accountTableRef.value?.setCurrentRow()
      }
    } else {
      accountTableRef.value?.setCurrentRow()
    }
  } catch (e) {
    apiErr(e, '获取科目列表失败')
  } finally {
    accountLoading.value = false
  }
}

function handleSearchAccounts() {
  accountPage.value = 1
  fetchAccounts()
}

function onAccountRowChange(row) {
  selectedAccount.value = row || null
  auxPage.value = 1
  if (row) fetchAuxiliaries()
  else {
    auxRows.value = []
    auxTotal.value = 0
  }
}

async function fetchAuxiliaries() {
  if (!selectedAccount.value || !canQuery.value) return
  auxLoading.value = true
  try {
    const res = await accountAuxiliaryApi.getListByAccount(
      query.account_book_code,
      query.fiscal_year,
      selectedAccount.value.account_code,
      { page: auxPage.value, page_size: auxPageSize.value }
    )
    if (!res.data?.success) {
      ElMessage.error('获取辅助核算失败')
      return
    }
    auxRows.value = res.data.items || []
    auxTotal.value = res.data.total ?? 0
  } catch (e) {
    apiErr(e, '获取辅助核算失败')
  } finally {
    auxLoading.value = false
  }
}

function resetAccountForm() {
  accountFormRef.value?.resetFields?.()
  Object.assign(accountForm, {
    account_code: '',
    account_name: '',
    account_level: 1,
    account_type: '资产类',
    balance_direction: '借',
    parent_account_code: '',
    is_leaf: 0,
    is_enabled: 1,
    remark: '',
    status: 1
  })
}

async function openAccountDialog(edit) {
  if (!canQuery.value) {
    ElMessage.warning('请先选择账套与会计年度')
    return
  }
  accountDialogEdit.value = edit
  accountDialogVisible.value = true
  await nextTick()
  if (!edit) {
    resetAccountForm()
  } else if (selectedAccount.value) {
    try {
      const res = await accountApi.getDetail(
        query.account_book_code,
        query.fiscal_year,
        selectedAccount.value.account_code
      )
      if (!res.data?.success || !res.data.data) {
        ElMessage.error('获取科目详情失败')
        return
      }
      const d = res.data.data
      Object.assign(accountForm, {
        account_code: d.account_code,
        account_name: d.account_name,
        account_level: d.account_level,
        account_type: d.account_type,
        balance_direction: d.balance_direction,
        parent_account_code: d.parent_account_code || '',
        is_leaf: d.is_leaf ?? 0,
        is_enabled: d.is_enabled ?? 1,
        remark: d.remark || '',
        status: d.status ?? 1
      })
    } catch (e) {
      apiErr(e, '获取科目详情失败')
      accountDialogVisible.value = false
    }
  }
}

async function submitAccount() {
  try {
    await accountFormRef.value?.validate()
  } catch {
    return
  }
  accountSubmitting.value = true
  try {
    if (accountDialogEdit.value) {
      const code = selectedAccount.value?.account_code
      const body = {
        account_name: accountForm.account_name,
        account_level: accountForm.account_level,
        account_type: accountForm.account_type,
        balance_direction: accountForm.balance_direction,
        parent_account_code: accountForm.parent_account_code || null,
        is_leaf: accountForm.is_leaf,
        is_enabled: accountForm.is_enabled,
        remark: accountForm.remark || null,
        status: accountForm.status
      }
      const res = await accountApi.update(query.account_book_code, query.fiscal_year, code, body)
      if (!res.data?.success) {
        ElMessage.error(res.data?.message || '更新失败')
        return
      }
      ElMessage.success(res.data?.message || '更新成功')
    } else {
      const body = {
        account_book_code: query.account_book_code,
        fiscal_year: query.fiscal_year,
        account_code: accountForm.account_code,
        account_name: accountForm.account_name,
        account_level: accountForm.account_level,
        account_type: accountForm.account_type,
        balance_direction: accountForm.balance_direction,
        parent_account_code: accountForm.parent_account_code || undefined,
        is_leaf: accountForm.is_leaf,
        is_enabled: accountForm.is_enabled,
        remark: accountForm.remark || undefined,
        status: accountForm.status
      }
      const res = await accountApi.create(body)
      if (!res.data?.success) {
        ElMessage.error(res.data?.message || '创建失败')
        return
      }
      ElMessage.success(res.data?.message || '创建成功')
    }
    accountDialogVisible.value = false
    await fetchAccounts()
  } catch (e) {
    apiErr(e, '保存失败')
  } finally {
    accountSubmitting.value = false
  }
}

async function handleDeleteAccount() {
  if (!selectedAccount.value) return
  try {
    await ElMessageBox.confirm(`确定删除科目「${selectedAccount.value.account_code}」吗？`, '确认删除', {
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    const res = await accountApi.delete(
      query.account_book_code,
      query.fiscal_year,
      selectedAccount.value.account_code
    )
    if (!res.data?.success) {
      ElMessage.error(res.data?.message || '删除失败')
      return
    }
    ElMessage.success(res.data?.message || '已删除')
    selectedAccount.value = null
    await fetchAccounts()
  } catch (e) {
    apiErr(e, '删除失败')
  }
}

async function loadArchiveItemOptions() {
  if (!canQuery.value) {
    archiveItemOptions.value = []
    return
  }
  try {
    const res = await customArchiveItemApi.getListAll({
      account_book_code: query.account_book_code,
      fiscal_year: query.fiscal_year
    })
    if (res.data?.success) archiveItemOptions.value = res.data.items || []
    else archiveItemOptions.value = []
  } catch {
    archiveItemOptions.value = []
  }
}

function onAuxDialogOpen() {
  loadArchiveItemOptions()
}

function resetAuxForm() {
  auxFormRef.value?.resetFields?.()
  Object.assign(auxForm, {
    auxiliary_item_code: '',
    auxiliary_item_name: '',
    corresponding_archive: '',
    auxiliary_item_description: '',
    status: 1,
    sync_custom_archive: true,
    archive_item_name: '',
    archive_item_desc: '',
    archive_value_desc: ''
  })
}

/** 合并 2.3 节自定义档案同步字段 */
function buildAuxiliarySyncBody() {
  const body = {
    sync_custom_archive: auxForm.sync_custom_archive
  }
  if (auxForm.archive_item_name?.trim()) body.archive_item_name = auxForm.archive_item_name.trim()
  if (auxForm.archive_item_desc?.trim()) body.archive_item_desc = auxForm.archive_item_desc.trim()
  if (auxForm.archive_value_desc?.trim()) body.archive_value_desc = auxForm.archive_value_desc.trim()
  return body
}

function formatCustomArchiveSyncMessage(sync) {
  if (!sync || typeof sync !== 'object') return ''
  const parts = []
  if (sync.created_item) parts.push('档案项已新建')
  if (sync.updated_item) parts.push('档案项已更新')
  if (sync.created_value) parts.push('档案值已新建')
  if (sync.updated_value) parts.push('档案值已更新')
  return parts.length ? ` ${parts.join('，')}` : ''
}

async function openAuxDialog(edit, row) {
  if (!selectedAccount.value) return
  auxDialogEdit.value = edit
  auxDialogVisible.value = true
  await nextTick()
  if (!edit) {
    resetAuxForm()
  } else if (row) {
    try {
      const res = await accountAuxiliaryApi.getDetail(
        query.account_book_code,
        query.fiscal_year,
        selectedAccount.value.account_code,
        row.auxiliary_item_code
      )
      if (!res.data?.success || !res.data.data) {
        ElMessage.error('获取辅助项详情失败')
        return
      }
      const d = res.data.data
      Object.assign(auxForm, {
        auxiliary_item_code: d.auxiliary_item_code,
        auxiliary_item_name: d.auxiliary_item_name,
        corresponding_archive: d.corresponding_archive || '',
        auxiliary_item_description: d.auxiliary_item_description || '',
        status: d.status ?? 1,
        sync_custom_archive: d.sync_custom_archive !== false,
        archive_item_name: d.archive_item_name ?? '',
        archive_item_desc: d.archive_item_desc ?? '',
        archive_value_desc: d.archive_value_desc ?? ''
      })
    } catch (e) {
      apiErr(e, '获取辅助项详情失败')
      auxDialogVisible.value = false
    }
  }
}

async function submitAux() {
  try {
    await auxFormRef.value?.validate()
  } catch {
    return
  }
  if (!selectedAccount.value) return
  auxSubmitting.value = true
  try {
    if (auxDialogEdit.value) {
      const res = await accountAuxiliaryApi.update(
        query.account_book_code,
        query.fiscal_year,
        selectedAccount.value.account_code,
        auxForm.auxiliary_item_code,
        {
          auxiliary_item_name: auxForm.auxiliary_item_name,
          corresponding_archive: auxForm.corresponding_archive || null,
          auxiliary_item_description: auxForm.auxiliary_item_description || null,
          status: auxForm.status,
          ...buildAuxiliarySyncBody()
        }
      )
      if (!res.data?.success) {
        ElMessage.error(res.data?.message || '更新失败')
        return
      }
      const syncHint = formatCustomArchiveSyncMessage(res.data?.custom_archive_sync)
      ElMessage.success((res.data?.message || '更新成功') + syncHint)
    } else {
      const res = await accountAuxiliaryApi.createByPath(
        query.account_book_code,
        query.fiscal_year,
        selectedAccount.value.account_code,
        {
          auxiliary_item_code: auxForm.auxiliary_item_code,
          auxiliary_item_name: auxForm.auxiliary_item_name,
          corresponding_archive: auxForm.corresponding_archive || undefined,
          auxiliary_item_description: auxForm.auxiliary_item_description || undefined,
          status: auxForm.status,
          ...buildAuxiliarySyncBody()
        }
      )
      if (!res.data?.success) {
        ElMessage.error(res.data?.message || '创建失败')
        return
      }
      const syncHint = formatCustomArchiveSyncMessage(res.data?.custom_archive_sync)
      ElMessage.success((res.data?.message || '创建成功') + syncHint)
    }
    auxDialogVisible.value = false
    await fetchAuxiliaries()
  } catch (e) {
    apiErr(e, '保存失败')
  } finally {
    auxSubmitting.value = false
  }
}

async function handleDeleteAux(row) {
  if (!selectedAccount.value) return
  try {
    await ElMessageBox.confirm(`确定删除辅助项「${row.auxiliary_item_code}」吗？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    const res = await accountAuxiliaryApi.delete(
      query.account_book_code,
      query.fiscal_year,
      selectedAccount.value.account_code,
      row.auxiliary_item_code
    )
    if (!res.data?.success) {
      ElMessage.error(res.data?.message || '删除失败')
      return
    }
    ElMessage.success(res.data?.message || '已删除')
    await fetchAuxiliaries()
  } catch (e) {
    apiErr(e, '删除失败')
  }
}

onMounted(() => {
  loadAccountBooks()
})
</script>

<style scoped>
.account-archive-manage {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 20px 24px;
  box-sizing: border-box;
  background: #fafafa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.header-import-mode {
  width: 180px;
}

.header-mode-hint {
  font-size: 18px;
  color: #909399;
  cursor: help;
  flex-shrink: 0;
}

.header-left .page-title {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 600;
  color: #0d0d0d;
}

.page-subtitle {
  font-size: 13px;
  color: #7a7a7a;
}

.filter-area {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.split-panels {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  padding: 12px 16px 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.accounts-panel {
  flex: 1 1 55%;
  min-height: 280px;
}

.aux-panel {
  flex: 1 1 45%;
  min-height: 240px;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #0d0d0d;
  flex: 1;
}

.panel-title .sub {
  font-weight: 400;
  font-size: 13px;
  color: #7a7a7a;
}

.pagination-area {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0 12px;
  flex-shrink: 0;
}

.pagination-info {
  font-size: 12px;
  color: #7a7a7a;
}

.text-muted {
  color: #909399;
}

.aux-sync-hint {
  font-size: 12px;
  color: #909399;
  margin: -4px 0 8px;
  line-height: 1.5;
}

.aux-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.aux-panel :deep(.el-table),
.accounts-panel :deep(.el-table) {
  min-height: 0;
}
</style>
