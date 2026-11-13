<template>
  <div class="bx-page">
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>预算</span>
          <div class="toolbar">
            <span>年度</span>
            <el-input-number v-model="fiscalYear" :min="1000" :max="9999" :step="1" controls-position="right" />
            <el-button v-if="access.canMaintain" type="primary" @click="openCreate">新增预算</el-button>
          </div>
        </div>
      </template>
      <div class="list-body">
      <el-table class="list-table" :data="rows" v-loading="loading" height="100%">
        <el-table-column prop="dept_code" label="部门代码" width="120" />
        <el-table-column prop="dept_name" label="部门" />
        <el-table-column prop="project_code" label="项目代码" width="120" />
        <el-table-column prop="project_name" label="项目" />
        <el-table-column prop="budget_amount" label="预算金额" width="120" align="right" />
        <el-table-column prop="confirmed_amount" label="已计入" width="120" align="right" />
        <el-table-column prop="pending_amount" label="待支出" width="120" align="right" />
        <el-table-column prop="balance" label="余额" width="120" align="right" />
        <el-table-column v-if="access.canMaintain" label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="openAmount(scope.row)">改金额</el-button>
            <el-button size="small" type="danger" @click="removeRow(scope.row)">删除</el-button>
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
          @size-change="changePageSize"
        />
      </div>
      </div>
    </el-card>

    <el-dialog v-model="createVisible" title="新增预算" width="480px">
      <el-form label-width="90px">
        <el-form-item label="部门">
          <el-select v-model="createForm.dept_code" filterable style="width: 100%">
            <el-option v-for="item in leafDepartments" :key="item.dept_code" :label="item.dept_code + ' ' + item.dept_name" :value="item.dept_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="createForm.project_code" filterable style="width: 100%">
            <el-option v-for="item in leafProjects" :key="item.project_code" :label="item.project_code + ' ' + item.project_name" :value="item.project_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model="createForm.amount" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="amountVisible" title="修改预算金额" width="420px">
      <el-form label-width="90px">
        <el-form-item label="部门">{{ amountForm.dept_code }} {{ amountForm.dept_name }}</el-form-item>
        <el-form-item label="项目">{{ amountForm.project_code }} {{ amountForm.project_name }}</el-form-item>
        <el-form-item label="金额">
          <el-input v-model="amountForm.amount" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="amountVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAmount">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bxApi } from '@/api/bx'
import { bxAccess, showError, useBxYear } from './useBx'

const access = bxAccess()
const { fiscalYear } = useBxYear()
const loading = ref(false)
const rows = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const leafDepartments = ref([])
const leafProjects = ref([])
const createVisible = ref(false)
const amountVisible = ref(false)
const createForm = ref({ dept_code: '', project_code: '', amount: '' })
const amountForm = ref({})

const load = async () => {
  loading.value = true
  try {
    const [budgetRes, deptRes, projectRes] = await Promise.all([
      bxApi.listBudgets(fiscalYear.value, page.value, pageSize.value),
      bxApi.listDepartments(fiscalYear.value),
      bxApi.listProjects(fiscalYear.value)
    ])
    const items = budgetRes.data.items || []
    total.value = budgetRes.data.total || 0
    leafDepartments.value = (deptRes.data.items || []).filter((item) => item.is_leaf)
    leafProjects.value = (projectRes.data.items || []).filter((item) => item.is_leaf)
    if (!items.length && page.value > 1 && total.value > 0) {
      page.value = Math.ceil(total.value / pageSize.value)
      return
    }
    rows.value = items
  } catch (error) {
    showError(error, '加载预算失败')
  } finally {
    loading.value = false
  }
}

watch(fiscalYear, () => {
  page.value = 1
  load()
}, { immediate: true })

const changePageSize = () => {
  if (page.value !== 1) {
    page.value = 1
    return
  }
  return load()
}

const openCreate = () => {
  createForm.value = {
    dept_code: leafDepartments.value[0]?.dept_code || '',
    project_code: leafProjects.value[0]?.project_code || '',
    amount: ''
  }
  createVisible.value = true
}

const submitCreate = async () => {
  try {
    await bxApi.createBudget({ fiscal_year: fiscalYear.value, ...createForm.value })
    ElMessage.success('已保存')
    createVisible.value = false
    await load()
  } catch (error) {
    showError(error, '保存失败')
  }
}

const openAmount = (row) => {
  amountForm.value = { ...row, amount: row.budget_amount }
  amountVisible.value = true
}

const submitAmount = async () => {
  try {
    await bxApi.updateBudgetAmount({
      fiscal_year: fiscalYear.value,
      dept_code: amountForm.value.dept_code,
      project_code: amountForm.value.project_code,
      amount: amountForm.value.amount
    })
    ElMessage.success('已保存')
    amountVisible.value = false
    await load()
  } catch (error) {
    showError(error, '保存失败')
  }
}

const removeRow = async (row) => {
  try {
    await ElMessageBox.confirm(`删除预算 ${row.dept_name} / ${row.project_name}？`, '删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await bxApi.deleteBudget(fiscalYear.value, row.dept_code, row.project_code)
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    showError(error, '删除失败')
  }
}
</script>

<script>
export default { name: 'BxBudgetPage' }
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
.list-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.list-table { flex: 1; min-height: 0; }
.pager { flex: none; margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
