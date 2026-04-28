<template>
  <div class="account-balance-report" ref="rootRef">
    <div class="header-filter-area" ref="headerRef">
      <div class="header-title">科目余额表</div>
      <el-form :model="queryForm" :inline="true" class="filter-form" @submit.prevent>
        <el-form-item label="账套" required>
          <el-select
            v-model="queryForm.account_book_code"
            placeholder="请选择账套"
            style="width: 220px"
            filterable
            clearable
            @change="onAccountBookChange"
          >
            <el-option
              v-for="item in accountBookOptions"
              :key="item.account_book_code"
              :label="`${item.account_book_code} - ${item.account_book_name}`"
              :value="item.account_book_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="年度" required>
          <el-select
            v-model="queryForm.fiscal_year"
            placeholder="会计年度"
            style="width: 120px"
            clearable
            :disabled="!queryForm.account_book_code"
          >
            <el-option
              v-for="y in fiscalYearOptions"
              :key="y"
              :label="String(y)"
              :value="y"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="会计月" required>
          <el-select
            v-model="queryForm.period_month"
            placeholder="1～12 月"
            style="width: 120px"
            clearable
            :disabled="!queryForm.account_book_code || !queryForm.fiscal_year"
          >
            <el-option
              v-for="m in monthOptions"
              :key="m"
              :label="`${m} 月`"
              :value="m"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="科目">
          <el-input
            v-model="queryForm.account_code"
            placeholder="科目编号（模糊，可选）"
            clearable
            style="width: 160px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button
            :disabled="!canExport"
            :loading="exporting"
            @click="handleExport"
          >
            导出 Excel
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <div v-if="hasSearched" class="tree-hint">
        按会计月展示树形科目：点击行首展开加载下级（懒加载）。不区分币种筛选，导出为当前月全部匹配行。
      </div>
    </div>

    <div class="table-area">
      <el-table
        v-loading="loading"
        :data="tableData"
        row-key="id"
        stripe
        border
        style="width: 100%"
        :height="tableHeight"
        :empty-text="emptyText"
        lazy
        :load="loadChildren"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column prop="account_code" label="科目编号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="account_name" label="科目名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="parent_code" label="父级科目" min-width="110" show-overflow-tooltip />
        <el-table-column prop="period_number" label="期间" width="72" align="center" />
        <el-table-column label="期初余额" min-width="120" align="right">
          <template #default="{ row }">
            {{ formatBalance(row, 'open') }}
          </template>
        </el-table-column>
        <el-table-column label="本期借方" min-width="110" align="right">
          <template #default="{ row }">
            {{ formatNum(row.current_period_debit_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="本期贷方" min-width="110" align="right">
          <template #default="{ row }">
            {{ formatNum(row.current_period_credit_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="期末余额" min-width="120" align="right">
          <template #default="{ row }">
            {{ formatBalance(row, 'close') }}
          </template>
        </el-table-column>
        <el-table-column prop="currency_code" label="币种" width="80" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { glApi } from '@/api/gl'
import { accountBookApi } from '@/api/accountBook'

const rootRef = ref(null)
const headerRef = ref(null)
const loading = ref(false)
const exporting = ref(false)
const tableData = ref([])
const hasSearched = ref(false)
const tableHeight = ref(420)
const monthOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

const accountBookOptions = ref([])
const fiscalYearOptions = ref([])

const queryForm = reactive({
  account_book_code: '',
  fiscal_year: null,
  period_month: null,
  account_code: ''
})

const canExport = computed(
  () =>
    !!(
      queryForm.account_book_code &&
      queryForm.fiscal_year != null &&
      queryForm.fiscal_year !== '' &&
      queryForm.period_month != null
    )
)

const emptyText = computed(() => {
  if (!hasSearched.value) return '请选择账套、年度、会计月后点击查询'
  return '暂无数据'
})

const buildLazyParams = (parentKey) => {
  const p = {
    lazy_tree: 'true',
    period_number: queryForm.period_month
  }
  if (parentKey != null && parentKey !== '') {
    p.parent_key = parentKey
  } else {
    p.parent_key = '__root__'
  }
  const code = (queryForm.account_code || '').trim()
  if (code) p.account_code = code
  return p
}

const mapRows = (items) =>
  (items || []).map((r) => ({
    ...r,
    hasChildren: r.has_children === true
  }))

const fetchRoot = async () => {
  if (!queryForm.account_book_code || queryForm.fiscal_year == null || queryForm.fiscal_year === '') {
    ElMessage.warning('请选择账套与年度')
    return
  }
  if (queryForm.period_month == null || queryForm.period_month < 1 || queryForm.period_month > 12) {
    ElMessage.warning('请选择会计月（1～12）')
    return
  }
  loading.value = true
  hasSearched.value = true
  tableData.value = []
  try {
    const { data } = await glApi.listAccountBalance(
      queryForm.account_book_code,
      queryForm.fiscal_year,
      buildLazyParams(null)
    )
    if (data.success) {
      tableData.value = mapRows(data.items)
    } else {
      ElMessage.error(data.message || '查询失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '请求失败')
  } finally {
    loading.value = false
    nextTick(() => calcTableHeight())
  }
}

const loadChildren = async (row, _treeNode, resolve) => {
  try {
    const { data } = await glApi.listAccountBalance(
      queryForm.account_book_code,
      queryForm.fiscal_year,
      buildLazyParams(row.account_code)
    )
    if (data.success) {
      resolve(mapRows(data.items))
    } else {
      resolve([])
    }
  } catch {
    resolve([])
  }
}

const buildExportParams = () => {
  const p = {
    period_number: queryForm.period_month
  }
  const code = (queryForm.account_code || '').trim()
  if (code) p.account_code = code
  return p
}

const formatNum = (v) => {
  if (v === null || v === undefined || v === '') return '—'
  return Number(v).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatBalance = (row, which) => {
  const amt = which === 'open' ? row.opening_balance : row.closing_balance
  const dir = which === 'open' ? row.opening_balance_direction : row.closing_balance_direction
  if (amt === null || amt === undefined) return '—'
  const n = formatNum(amt)
  return dir ? `${n}（${dir}）` : n
}

const handleSearch = async () => {
  await fetchRoot()
}

const handleReset = () => {
  queryForm.account_code = ''
  queryForm.period_month = null
  tableData.value = []
  hasSearched.value = false
}

const handleExport = async () => {
  if (!canExport.value) {
    ElMessage.warning('请选择账套、年度与会计月')
    return
  }
  exporting.value = true
  try {
    const res = await glApi.exportAccountBalanceBlob(
      queryForm.account_book_code,
      queryForm.fiscal_year,
      buildExportParams()
    )
    const blob = res.data
    const ct = (res.headers && (res.headers['content-type'] || res.headers['Content-Type'])) || ''
    if (ct.includes('application/json') || (blob && blob.size < 2000)) {
      const text = await blob.text()
      try {
        const j = JSON.parse(text)
        if (j.message) {
          ElMessage.error(j.message)
          return
        }
      } catch {
        /* not json */
      }
    }
    const dispo = res.headers && (res.headers['content-disposition'] || res.headers['Content-Disposition'] || '')
    let filename = '科目余额表.xlsx'
    const m =
      /filename\*=UTF-8''([^;\r\n]+)/i.exec(dispo) ||
      /filename="([^"]+)"/i.exec(dispo) ||
      /filename=([^;\r\n]+)/i.exec(dispo)
    if (m) {
      try {
        filename = decodeURIComponent(m[1].replace(/['"]/g, '').trim())
      } catch {
        filename = m[1].replace(/['"]/g, '').trim()
      }
    }
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出已触发下载')
  } catch (e) {
    const data = e?.response?.data
    if (data instanceof Blob) {
      const text = await data.text()
      try {
        const j = JSON.parse(text)
        ElMessage.error(j.message || '导出失败')
        return
      } catch {
        /* ignore */
      }
    }
    ElMessage.error(e?.response?.data?.message || e?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

const onAccountBookChange = (code) => {
  queryForm.fiscal_year = null
  if (code) {
    loadFiscalYears(code)
  } else {
    fiscalYearOptions.value = []
  }
}

const loadAccountBooks = async () => {
  try {
    const { data } = await accountBookApi.getList({ page_size: 1000 })
    if (data.success) {
      accountBookOptions.value = data.items || []
    }
  } catch {
    /* ignore */
  }
}

const loadFiscalYears = async (code) => {
  try {
    const { data } = await accountBookApi.getFiscalYears(code)
    if (data.success) {
      fiscalYearOptions.value = (data.items || []).map((i) => i.fiscal_year)
    } else {
      fiscalYearOptions.value = []
    }
  } catch {
    fiscalYearOptions.value = []
  }
}

const calcTableHeight = () => {
  nextTick(() => {
    const h = window.innerHeight
    const top = headerRef.value ? headerRef.value.getBoundingClientRect().height : 200
    const rest = 80
    tableHeight.value = Math.max(280, h - top - rest)
  })
}

onMounted(() => {
  loadAccountBooks()
  calcTableHeight()
  window.addEventListener('resize', calcTableHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', calcTableHeight)
})

watch(
  [() => queryForm.account_book_code, () => queryForm.fiscal_year],
  () => {
    nextTick(calcTableHeight)
  }
)
</script>

<style scoped lang="scss">
.account-balance-report {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 16px 20px;
  box-sizing: border-box;
  background: #f8fafc;
}

.header-filter-area {
  flex-shrink: 0;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 16px 18px 8px;
  margin-bottom: 12px;
}

.tree-hint {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  padding: 0 0 8px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12px;
}

.filter-form {
  :deep(.el-form-item) {
    margin-bottom: 8px;
  }
}

.table-area {
  flex: 1;
  min-height: 0;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 10px 12px;
  overflow: hidden;
}
</style>
