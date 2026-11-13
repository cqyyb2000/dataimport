<template>
  <div class="bx-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>单位报销统计</span>
          <div class="toolbar">
            <span>年度</span>
            <el-input-number v-model="fiscalYear" :min="1000" :max="9999" :step="1" controls-position="right" />
            <el-radio-group v-model="groupBy">
              <el-radio-button value="department">按部门</el-radio-button>
              <el-radio-button value="project">按项目</el-radio-button>
            </el-radio-group>
            <el-button @click="exportExcel">导出 Excel</el-button>
          </div>
        </div>
      </template>
      <el-table :data="flatRows" v-loading="loading" :row-class-name="rowClass">
        <el-table-column label="代码" width="140">
          <template #default="scope">{{ scope.row.rowType === 'group' ? scope.row.code : scope.row.lineCode }}</template>
        </el-table-column>
        <el-table-column label="名称">
          <template #default="scope">{{ scope.row.rowType === 'group' ? scope.row.name + ' 小计' : scope.row.lineName }}</template>
        </el-table-column>
        <el-table-column prop="budget_amount" label="预算金额" width="130" align="right" />
        <el-table-column label="已计入" width="130" align="right">
          <template #default="scope">
            <el-button link type="primary" @click="openDetail(scope.row, '已计入')">{{ scope.row.confirmed_amount }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="待支出" width="130" align="right">
          <template #default="scope">
            <el-button link type="primary" @click="openDetail(scope.row, '待支出')">{{ scope.row.pending_amount }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="balance" label="余额" width="130" align="right" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { bxApi } from '@/api/bx'
import { downloadExcel } from './excel'
import { showError, useBxYear } from './useBx'

const router = useRouter()
const { fiscalYear } = useBxYear()
const groupBy = ref('department')
const loading = ref(false)
const groups = ref([])

const flatRows = computed(() => {
  const rows = []
  groups.value.forEach((group) => {
    rows.push({ rowType: 'group', ...group })
    group.lines.forEach((line) => {
      const byDepartment = groupBy.value === 'department'
      rows.push({
        rowType: 'line',
        ...line,
        lineCode: byDepartment ? line.project_code : line.dept_code,
        lineName: byDepartment ? line.project_name : line.dept_name
      })
    })
  })
  return rows
})

const load = async () => {
  loading.value = true
  try {
    const res = await bxApi.summary({ fiscal_year: fiscalYear.value, group_by: groupBy.value })
    groups.value = res.data.groups || []
  } catch (error) {
    showError(error, '加载统计失败')
  } finally {
    loading.value = false
  }
}

watch([fiscalYear, groupBy], load, { immediate: true })

const rowClass = ({ row }) => (row.rowType === 'group' ? 'group-row' : '')

const openDetail = (row, status) => {
  const query = { fiscal_year: fiscalYear.value, status }
  if (row.rowType === 'group') {
    if (groupBy.value === 'department') query.dept_code = row.code
    else query.project_code = row.code
  } else {
    query.dept_code = row.dept_code
    query.project_code = row.project_code
  }
  router.push({ path: '/bx/claims', query })
}

const exportExcel = () => {
  downloadExcel(
    `单位报销统计${fiscalYear.value}.xls`,
    ['代码', '名称', '预算金额', '已计入', '待支出', '余额'],
    flatRows.value.map((row) => [
      row.rowType === 'group' ? row.code : row.lineCode,
      row.rowType === 'group' ? `${row.name} 小计` : row.lineName,
      row.budget_amount,
      row.confirmed_amount,
      row.pending_amount,
      row.balance
    ])
  )
}
</script>

<style scoped>
.bx-page { padding: 20px; }
.card-header, .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
:deep(.group-row) { font-weight: 600; background: #f5f7fa; }
</style>
