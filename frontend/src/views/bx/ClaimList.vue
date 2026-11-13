<template>
  <div class="bx-page">
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>报销明细</span>
          <div class="toolbar">
            <span>年度</span>
            <el-input-number v-model="fiscalYear" :min="1000" :max="9999" :step="1" controls-position="right" />
            <el-button @click="exportExcel">导出 Excel</el-button>
          </div>
        </div>
      </template>
      <el-form :inline="true" class="filters">
        <el-form-item label="开始日期"><el-date-picker v-model="filters.date_from" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="filters.date_to" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.dept_code" clearable filterable style="width: 160px">
            <el-option v-for="item in departments" :key="item.dept_code" :label="item.dept_name" :value="item.dept_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="filters.project_code" clearable filterable style="width: 160px">
            <el-option v-for="item in projects" :key="item.project_code" :label="item.project_name" :value="item.project_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="报销人"><el-input v-model="filters.claimant" clearable /></el-form-item>
        <el-form-item label="摘要"><el-input v-model="filters.summary" clearable /></el-form-item>
        <el-form-item label="单据号"><el-input v-model="filters.doc_no" clearable /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable style="width: 120px">
            <el-option label="待支出" value="待支出" />
            <el-option label="已计入" value="已计入" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
        </el-form-item>
      </el-form>
      <div class="totals">支出总额 {{ confirmedTotal }}<span class="gap"></span>待支出合计 {{ pendingTotal }}</div>
      <div class="list-body">
      <el-table class="list-table" :data="rows" v-loading="loading" height="100%">
        <el-table-column prop="doc_no" label="单据号" width="130" />
        <el-table-column prop="expense_date" label="报销时间" width="120" />
        <el-table-column prop="dept_name" label="部门" />
        <el-table-column prop="project_name" label="项目" />
        <el-table-column prop="claimant" label="报销人" width="100" />
        <el-table-column prop="summary" label="摘要" />
        <el-table-column prop="amount" label="报销金额" width="110" align="right" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column label="操作" width="220">
          <template #default="scope">
            <el-button v-if="access.canMaintain && scope.row.status === '待支出'" size="small" @click="editRow(scope.row)">修改</el-button>
            <el-button v-if="access.canMaintain && scope.row.status === '待支出'" size="small" type="danger" @click="removeRow(scope.row)">删除</el-button>
            <el-button v-if="access.canConfirm && scope.row.status === '待支出'" size="small" type="primary" @click="confirmRow(scope.row, false)">确认</el-button>
            <el-button v-if="access.canConfirm && scope.row.status === '已计入'" size="small" @click="cancelRow(scope.row)">取消确认</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="search"
        />
      </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bxApi } from '@/api/bx'
import { downloadExcel } from './excel'
import { apiMessage, bxAccess, isNeedConfirm, showError, useBxYear } from './useBx'

const access = bxAccess()
const route = useRoute()
const router = useRouter()
const { fiscalYear } = useBxYear()
const loading = ref(false)
const rows = ref([])
const departments = ref([])
const projects = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const confirmedTotal = ref('0.00')
const pendingTotal = ref('0.00')
const filters = reactive({
  date_from: '',
  date_to: '',
  dept_code: '',
  project_code: '',
  claimant: '',
  summary: '',
  doc_no: '',
  status: ''
})

const params = () => {
  const query = { fiscal_year: fiscalYear.value, page: page.value, page_size: pageSize.value }
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query[key] = value
  })
  return query
}

const load = async () => {
  loading.value = true
  try {
    const [claimRes, deptRes, projectRes] = await Promise.all([
      bxApi.listClaims(params()),
      bxApi.listDepartments(fiscalYear.value),
      bxApi.listProjects(fiscalYear.value)
    ])
    rows.value = claimRes.data.items || []
    total.value = claimRes.data.total || 0
    confirmedTotal.value = claimRes.data.confirmed_total || '0.00'
    pendingTotal.value = claimRes.data.pending_total || '0.00'
    departments.value = deptRes.data.items || []
    projects.value = projectRes.data.items || []
  } catch (error) {
    showError(error, '加载明细失败')
  } finally {
    loading.value = false
  }
}

watch(() => route.fullPath, () => {
  if (route.path !== '/bx/claims') return
  if (route.query.fiscal_year && Number(route.query.fiscal_year) !== Number(fiscalYear.value)) {
    fiscalYear.value = Number(route.query.fiscal_year)
  }
  filters.dept_code = route.query.dept_code || ''
  filters.project_code = route.query.project_code || ''
  filters.status = route.query.status || ''
  filters.doc_no = route.query.doc_no || ''
  page.value = 1
  load()
}, { immediate: true })

watch(fiscalYear, (value, oldValue) => {
  if (oldValue === undefined) return
  if (route.query.fiscal_year && Number(route.query.fiscal_year) === Number(value)) return
  page.value = 1
  load()
})

const search = () => {
  page.value = 1
  load()
}

const editRow = (row) => {
  router.push({ path: '/bx/entry', query: { fiscal_year: fiscalYear.value, doc_no: row.doc_no } })
}

const removeRow = async (row) => {
  try {
    await ElMessageBox.confirm(`删除报销单 ${row.doc_no}？`, '删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
  } catch {
    return
  }
  try {
    await bxApi.deleteClaim(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    showError(error, '删除失败')
  }
}

const confirmRow = async (row, allowOverspend) => {
  try {
    await bxApi.confirmClaim(row.id, { allow_overspend: allowOverspend })
    ElMessage.success('已计入')
    await load()
  } catch (error) {
    if (!allowOverspend && isNeedConfirm(error)) {
      try {
        await ElMessageBox.confirm(error.response.data.message, '超支提醒', {
          confirmButtonText: '保存', cancelButtonText: '取消', type: 'warning'
        })
      } catch {
        return
      }
      await confirmRow(row, true)
      return
    }
    ElMessage.error(apiMessage(error, '确认失败'))
  }
}

const cancelRow = async (row) => {
  try {
    await bxApi.cancelConfirmClaim(row.id)
    ElMessage.success('已取消确认')
    await load()
  } catch (error) {
    showError(error, '取消确认失败')
  }
}

const exportExcel = async () => {
  const items = []
  let current = 1
  let count = 0
  try {
    do {
      const res = await bxApi.listClaims({ ...params(), page: current, page_size: 100 })
      items.push(...(res.data.items || []))
      count = res.data.total || 0
      current += 1
    } while (items.length < count)
    downloadExcel(
      `报销明细${fiscalYear.value}.xls`,
      ['单据号', '报销时间', '部门', '项目', '报销人', '摘要', '报销金额', '状态'],
      items.map((row) => [row.doc_no, row.expense_date, row.dept_name, row.project_name, row.claimant, row.summary, row.amount, row.status])
    )
  } catch (error) {
    showError(error, '导出失败')
  }
}
</script>

<style scoped>
.bx-page {
  height: 100%;
  box-sizing: border-box;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.list-card { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.list-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.card-header, .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.filters { margin-bottom: 8px; flex: none; }
.totals { margin-bottom: 12px; font-weight: 600; flex: none; }
.gap { display: inline-block; width: 24px; }
.list-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.list-table { flex: 1; min-height: 0; }
.pager { flex: none; margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
