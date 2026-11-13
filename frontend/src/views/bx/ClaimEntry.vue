<template>
  <div class="bx-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ form.id ? '修改报销单' : '报销录入' }}</span>
          <div class="toolbar">
            <span>年度</span>
            <el-input-number v-model="fiscalYear" :min="1000" :max="9999" :step="1" :disabled="!!form.id" controls-position="right" />
          </div>
        </div>
      </template>
      <el-form v-if="access.canMaintain" :inline="true" class="entry-form" label-width="68px">
        <el-form-item label="单据号">
          <el-input :model-value="form.doc_no" disabled placeholder="保存后生成" class="field-doc" />
        </el-form-item>
        <el-form-item label="报销时间">
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" :disabled-date="disableDate" class="field-date" />
        </el-form-item>
        <el-form-item label="部门" class="field-grow">
          <el-select v-model="form.dept_code" filterable>
            <el-option v-for="item in leafDepartments" :key="item.dept_code" :label="item.dept_code + ' ' + item.dept_name" :value="item.dept_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" class="field-grow">
          <el-select v-model="form.project_code" filterable>
            <el-option v-for="item in leafProjects" :key="item.project_code" :label="item.project_code + ' ' + item.project_name" :value="item.project_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="报销人">
          <el-input v-model="form.claimant" class="field-person" />
        </el-form-item>
        <el-form-item label="报销金额">
          <el-input v-model="form.amount" class="field-amount" />
        </el-form-item>
        <el-form-item label="摘要" class="field-summary">
          <el-input v-model="form.summary" />
        </el-form-item>
        <el-form-item class="field-actions">
          <el-button type="primary" @click="submit(false)">保存</el-button>
          <el-button v-if="form.id" @click="resetForm">取消修改</el-button>
        </el-form-item>
      </el-form>
      <p v-else>当前用户不能录入报销单。</p>
    </el-card>

    <el-card class="pending-card">
      <template #header>本年度待支出</template>
      <div class="pending-body">
      <el-table class="pending-table" :data="pending" v-loading="loading" height="100%">
        <el-table-column prop="doc_no" label="单据号" width="130" />
        <el-table-column prop="expense_date" label="报销时间" width="120" />
        <el-table-column prop="dept_name" label="部门" />
        <el-table-column prop="project_name" label="项目" />
        <el-table-column prop="claimant" label="报销人" width="100" />
        <el-table-column prop="summary" label="摘要" />
        <el-table-column prop="amount" label="金额" width="110" align="right" />
        <el-table-column v-if="access.canMaintain" label="操作" width="160">
          <template #default="scope">
            <el-button size="small" @click="editRow(scope.row)">修改</el-button>
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
          @current-change="showPending"
          @size-change="changePageSize"
        />
      </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bxApi } from '@/api/bx'
import { apiMessage, bxAccess, isNeedConfirm, showError, useBxYear } from './useBx'

const access = bxAccess()
const route = useRoute()
const { fiscalYear } = useBxYear()
const loading = ref(false)
const pending = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const leafDepartments = ref([])
const leafProjects = ref([])
const form = reactive({
  id: null,
  doc_no: '',
  expense_date: '',
  dept_code: '',
  project_code: '',
  claimant: '',
  summary: '',
  amount: ''
})

const disableDate = (date) => date.getFullYear() !== Number(fiscalYear.value)

const resetForm = () => {
  form.id = null
  form.doc_no = ''
  form.expense_date = `${fiscalYear.value}-01-01`
  form.dept_code = leafDepartments.value[0]?.dept_code || ''
  form.project_code = leafProjects.value[0]?.project_code || ''
  form.claimant = ''
  form.summary = ''
  form.amount = ''
}

const loadPending = async () => {
  const res = await bxApi.listClaims({
    fiscal_year: fiscalYear.value,
    status: '待支出',
    page: page.value,
    page_size: pageSize.value
  })
  const items = res.data.items || []
  total.value = res.data.total || 0
  if (!items.length && page.value > 1 && total.value > 0) {
    page.value = Math.ceil(total.value / pageSize.value)
    return
  }
  pending.value = items
}

const showPending = async () => {
  try {
    await loadPending()
  } catch (error) {
    showError(error, '加载待支出失败')
  }
}

const changePageSize = () => {
  if (page.value !== 1) {
    page.value = 1
    return
  }
  return showPending()
}

const loadArchives = async () => {
  const [deptRes, projectRes] = await Promise.all([
    bxApi.listDepartments(fiscalYear.value),
    bxApi.listProjects(fiscalYear.value)
  ])
  leafDepartments.value = (deptRes.data.items || []).filter((item) => item.is_leaf)
  leafProjects.value = (projectRes.data.items || []).filter((item) => item.is_leaf)
}

const loadEdited = async () => {
  const docNo = route.query.doc_no
  if (!docNo) return
  if (route.query.fiscal_year) fiscalYear.value = Number(route.query.fiscal_year)
  const res = await bxApi.listClaims({
    fiscal_year: fiscalYear.value,
    doc_no: docNo,
    page: 1,
    page_size: 10
  })
  const row = (res.data.items || [])[0]
  if (row && row.status === '待支出') editRow(row)
}

const load = async () => {
  loading.value = true
  try {
    await loadArchives()
    await loadPending()
    if (!form.id) resetForm()
    await loadEdited()
  } catch (error) {
    showError(error, '加载录入数据失败')
  } finally {
    loading.value = false
  }
}

watch(fiscalYear, () => {
  form.id = null
  page.value = 1
  load()
}, { immediate: true })

watch(() => route.query.doc_no, async (docNo) => {
  if (!docNo) return
  if (route.query.fiscal_year) fiscalYear.value = Number(route.query.fiscal_year)
  try {
    await loadEdited()
  } catch (error) {
    showError(error, '加载报销单失败')
  }
})

const editRow = (row) => {
  form.id = row.id
  form.doc_no = row.doc_no
  form.expense_date = row.expense_date
  form.dept_code = row.dept_code
  form.project_code = row.project_code
  form.claimant = row.claimant
  form.summary = row.summary
  form.amount = row.amount
}

const submit = async (allowOverspend) => {
  const payload = {
    fiscal_year: fiscalYear.value,
    expense_date: form.expense_date,
    dept_code: form.dept_code,
    project_code: form.project_code,
    claimant: form.claimant,
    summary: form.summary,
    amount: form.amount,
    allow_overspend: allowOverspend
  }
  try {
    if (form.id) await bxApi.updateClaim(form.id, payload)
    else await bxApi.createClaim(payload)
    ElMessage.success('已保存，状态为待支出')
    form.id = null
    await load()
  } catch (error) {
    if (!allowOverspend && isNeedConfirm(error)) {
      try {
        await ElMessageBox.confirm(error.response.data.message, '超支提醒', {
          confirmButtonText: '保存',
          cancelButtonText: '取消',
          type: 'warning'
        })
      } catch {
        return
      }
      await submit(true)
      return
    }
    ElMessage.error(apiMessage(error, '保存失败'))
  }
}

const removeRow = async (row) => {
  try {
    await ElMessageBox.confirm(`删除报销单 ${row.doc_no}？`, '删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await bxApi.deleteClaim(row.id)
    if (form.id === row.id) form.id = null
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    showError(error, '删除失败')
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
  gap: 12px;
  overflow: hidden;
}
.card-header, .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.entry-form { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; }
.entry-form :deep(.el-form-item) { margin: 0; }
.entry-form :deep(.el-select),
.entry-form :deep(.el-input),
.entry-form :deep(.el-date-editor) { width: 100%; }
.field-doc { width: 132px; }
.field-date { width: 150px; }
.field-person { width: 120px; }
.field-amount { width: 110px; }
.field-grow { flex: 1 1 180px; }
.field-summary { flex: 1.4 1 220px; }
.field-grow :deep(.el-form-item__content),
.field-summary :deep(.el-form-item__content) { flex: 1; }
.pending-card { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.pending-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.pending-body { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.pending-table { flex: 1; min-height: 0; }
.pager { flex: none; margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
