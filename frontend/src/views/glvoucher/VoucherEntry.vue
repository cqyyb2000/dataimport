<template>
  <div class="voucher-entry">
    <div class="page-header">
      <h2 class="page-title">凭证录入</h2>
      <p class="page-desc">
        按当前账套和会计年度录入记账凭证。分录记在末级科目上；科目有辅助核算时必须填写。保存时借方合计须等于贷方合计。保存后状态为「未记账」，科目余额需再到「数据记账」重算。
      </p>
    </div>

    <el-card class="form-card" shadow="never">
      <template #header>
        <span class="card-header-text">凭证头</span>
      </template>
      <el-form :model="form" label-width="96px" class="header-form">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="账套" required>
              <el-select
                v-model="form.account_book_code"
                placeholder="请选择账套"
                filterable
                style="width: 100%"
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
          </el-col>
          <el-col :span="8">
            <el-form-item label="会计年度" required>
              <el-select
                v-model="form.fiscal_year"
                placeholder="请选择年度"
                style="width: 100%"
                :disabled="!form.account_book_code"
                @change="onFiscalYearChange"
              >
                <el-option
                  v-for="year in fiscalYearOptions"
                  :key="year"
                  :label="String(year)"
                  :value="year"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="会计期间" required>
              <el-select
                v-model="form.period_number"
                placeholder="请选择期间"
                style="width: 100%"
                @change="onPeriodOrTypeChange"
              >
                <el-option
                  v-for="month in periodOptions"
                  :key="month"
                  :label="month === 13 ? '13 调整期' : `${month} 月`"
                  :value="month"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="凭证日期" required>
              <el-date-picker
                v-model="form.voucher_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="凭证类型" required>
              <el-select
                v-model="form.voucher_type_code"
                placeholder="请选择凭证类型"
                style="width: 100%"
                :disabled="!form.account_book_code || !form.fiscal_year"
                @change="onPeriodOrTypeChange"
              >
                <el-option
                  v-for="item in voucherTypeOptions"
                  :key="item.voucher_type_code"
                  :label="`${item.voucher_type_code} - ${item.voucher_type_name}`"
                  :value="item.voucher_type_code"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="凭证号" required>
              <el-input v-model="form.voucher_number" placeholder="如 JZ-01-0001" maxlength="50">
                <template #append>
                  <el-button @click="fillNextNumber">取号</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="凭证摘要" required>
              <el-input
                v-model="form.summary"
                placeholder="请输入凭证摘要"
                maxlength="500"
                @blur="fillEmptyLineSummaries"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="附单据数">
              <el-input-number
                v-model="form.attachment_count"
                :min="0"
                :precision="0"
                :controls="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="制单人">
              <el-input v-model="form.prepared_by" maxlength="50" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="lines-header">
          <span class="card-header-text">分录</span>
          <el-button type="primary" link @click="addLine">增行</el-button>
        </div>
      </template>

      <el-table :data="lines" border stripe>
        <el-table-column label="#" width="52" align="center">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>
        <el-table-column label="摘要" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.summary" maxlength="500" placeholder="默认同凭证摘要" />
          </template>
        </el-table-column>
        <el-table-column label="科目" min-width="240">
          <template #default="{ row }">
            <el-select
              v-model="row.account_code"
              filterable
              remote
              clearable
              placeholder="输入科目编码或名称"
              :remote-method="(query) => searchAccounts(query)"
              :loading="accountLoading"
              style="width: 100%"
              :disabled="!form.account_book_code || !form.fiscal_year"
              @change="() => onAccountChange(row)"
            >
              <el-option
                v-for="item in accountOptions"
                :key="item.account_code"
                :label="`${item.account_code} ${item.account_name}`"
                :value="item.account_code"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="借方金额" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.debit_amount"
              :min="0"
              :precision="2"
              :controls="false"
              style="width: 100%"
              @change="() => onDebitChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="贷方金额" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.credit_amount"
              :min="0"
              :precision="2"
              :controls="false"
              style="width: 100%"
              @change="() => onCreditChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="辅助核算" min-width="260">
          <template #default="{ row }">
            <div v-if="row.auxiliaries.length" class="aux-list">
              <div v-for="aux in row.auxiliaries" :key="aux.auxiliary_item_code" class="aux-item">
                <span class="aux-label">{{ aux.auxiliary_item_name }}</span>
                <el-select
                  v-if="aux.options.length"
                  v-model="aux.auxiliary_value"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="opt in aux.options"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-input
                  v-else
                  v-model="aux.auxiliary_value"
                  maxlength="50"
                  placeholder="填写档案值编码"
                />
              </div>
            </div>
            <span v-else class="aux-empty">无</span>
          </template>
        </el-table-column>
        <el-table-column label="" width="72" align="center">
          <template #default="{ $index }">
            <el-button type="danger" link :disabled="lines.length <= 2" @click="removeLine($index)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="totals" :class="{ unbalanced: !balanced && hasAmount }">
        <span>借方合计 {{ formatAmount(debitTotal) }}</span>
        <span>贷方合计 {{ formatAmount(creditTotal) }}</span>
        <span>差额 {{ formatAmount(difference) }}</span>
      </div>
    </el-card>

    <div class="actions">
      <el-button type="primary" :loading="submitting" @click="handleSave">保存</el-button>
      <el-button @click="resetLines">清空分录</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountBookApi } from '@/api/accountBook'
import { accountApi, accountAuxiliaryApi } from '@/api/account'
import { customArchiveItemApi } from '@/api/customArchive'
import { voucherApi } from '@/api/voucher'
import { getCurrentUser } from '@/utils/auth'

const periodOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
const accountBookOptions = ref([])
const fiscalYearOptions = ref([])
const voucherTypeOptions = ref([])
const accountOptionMap = ref({})
const accountLoading = ref(false)
const submitting = ref(false)

const currentUser = getCurrentUser()
const form = reactive({
  account_book_code: '',
  fiscal_year: null,
  period_number: 1,
  voucher_date: '',
  voucher_type_code: '',
  voucher_number: '',
  summary: '',
  attachment_count: 0,
  prepared_by: currentUser && currentUser.username ? currentUser.username : ''
})

function blankLine() {
  return {
    summary: '',
    account_code: '',
    debit_amount: null,
    credit_amount: null,
    auxiliaries: []
  }
}

const lines = ref([blankLine(), blankLine()])

const accountOptions = computed(() => Object.values(accountOptionMap.value))

function amountOf(value) {
  const number = Number(value)
  if (!Number.isFinite(number) || number <= 0) return 0
  return Math.round(number * 100) / 100
}

const debitTotal = computed(() => lines.value.reduce((sum, row) => sum + amountOf(row.debit_amount), 0))
const creditTotal = computed(() => lines.value.reduce((sum, row) => sum + amountOf(row.credit_amount), 0))
const difference = computed(() => Math.round((debitTotal.value - creditTotal.value) * 100) / 100)
const hasAmount = computed(() => debitTotal.value > 0 || creditTotal.value > 0)
const balanced = computed(() => debitTotal.value > 0 && debitTotal.value === creditTotal.value)

function formatAmount(value) {
  return Number(value || 0).toFixed(2)
}

function pad(number) {
  return String(number).padStart(2, '0')
}

function todayText() {
  const now = new Date()
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`
}

function syncDateWithPeriod() {
  const year = form.fiscal_year
  if (!year) return
  const month = form.period_number === 13 ? 12 : form.period_number
  const current = form.voucher_date
  let day = '01'
  if (current && current.length === 8) {
    day = current.slice(6, 8)
  }
  const probe = new Date(year, month, 0).getDate()
  const safeDay = Math.min(Number(day) || 1, probe)
  form.voucher_date = `${year}${pad(month)}${pad(safeDay)}`
}

async function fetchAccountBooks() {
  try {
    const response = await accountBookApi.getList({ page: 1, page_size: 100 })
    if (response.data.success) {
      accountBookOptions.value = response.data.items || []
    }
  } catch {
    ElMessage.error('获取账套列表失败')
  }
}

async function fetchFiscalYears(code) {
  fiscalYearOptions.value = []
  if (!code) return
  try {
    const response = await accountBookApi.getFiscalYears(code)
    if (response.data.success) {
      fiscalYearOptions.value = (response.data.items || []).map((item) => item.fiscal_year)
    }
  } catch {
    fiscalYearOptions.value = []
  }
}

async function fetchVoucherTypes() {
  voucherTypeOptions.value = []
  form.voucher_type_code = ''
  if (!form.account_book_code || !form.fiscal_year) return
  try {
    const response = await voucherApi.getVoucherTypes(form.account_book_code, form.fiscal_year)
    if (response.data.success) {
      voucherTypeOptions.value = response.data.items || response.data.data || []
      if (voucherTypeOptions.value.length === 1) {
        form.voucher_type_code = voucherTypeOptions.value[0].voucher_type_code
        fillNextNumber()
      }
    }
  } catch {
    voucherTypeOptions.value = []
  }
}

function onAccountBookChange(code) {
  form.fiscal_year = null
  form.voucher_number = ''
  accountOptionMap.value = {}
  resetLines()
  fetchFiscalYears(code)
  fetchVoucherTypes()
}

function onFiscalYearChange() {
  form.voucher_number = ''
  accountOptionMap.value = {}
  lines.value.forEach((row) => {
    row.account_code = ''
    row.auxiliaries = []
  })
  syncDateWithPeriod()
  fetchVoucherTypes()
  searchAccounts('')
}

function onPeriodOrTypeChange() {
  syncDateWithPeriod()
  if (!form.voucher_number && form.voucher_type_code) {
    fillNextNumber()
  }
}

function fillEmptyLineSummaries() {
  const summary = (form.summary || '').trim()
  if (!summary) return
  lines.value.forEach((row) => {
    if (!row.summary) row.summary = summary
  })
}

async function fillNextNumber() {
  if (!form.account_book_code || !form.fiscal_year || !form.period_number || !form.voucher_type_code) {
    ElMessage.warning('请先选择账套、年度、期间和凭证类型')
    return
  }
  try {
    const response = await voucherApi.nextNumber(
      form.account_book_code,
      form.fiscal_year,
      form.period_number,
      form.voucher_type_code
    )
    if (response.data.success) {
      form.voucher_number = response.data.voucher_number
    } else {
      ElMessage.error(response.data.message || '取号失败')
    }
  } catch (error) {
    const message = error?.response?.data?.message || '取号失败'
    ElMessage.error(message)
  }
}

async function searchAccounts(query) {
  if (!form.account_book_code || !form.fiscal_year) return
  const keyword = (query || '').trim()
  accountLoading.value = true
  try {
    const base = {
      account_book_code: form.account_book_code,
      fiscal_year: form.fiscal_year,
      is_leaf: 1,
      is_enabled: 1,
      page: 1,
      page_size: 50
    }
    const requests = []
    if (!keyword) {
      requests.push(accountApi.getList(base))
    } else {
      requests.push(accountApi.getList({ ...base, account_code: keyword }))
      requests.push(accountApi.getList({ ...base, account_name: keyword }))
    }
    const responses = await Promise.all(requests)
    const next = { ...accountOptionMap.value }
    responses.forEach((response) => {
      const items = response.data && response.data.items ? response.data.items : []
      items.forEach((item) => {
        if (item.is_leaf === 1 && item.is_enabled !== 0 && item.status !== 0) {
          next[item.account_code] = item
        }
      })
    })
    accountOptionMap.value = next
  } catch {
    ElMessage.error('查询科目失败')
  } finally {
    accountLoading.value = false
  }
}

async function loadArchiveOptions(definition) {
  const keys = [definition.corresponding_archive, definition.auxiliary_item_name].filter(Boolean)
  const seen = new Set()
  for (const key of keys) {
    if (seen.has(key)) continue
    seen.add(key)
    try {
      const response = await customArchiveItemApi.getValues(
        form.account_book_code,
        form.fiscal_year,
        key,
        false
      )
      if (response.data && response.data.success) {
        return (response.data.items || [])
          .filter((item) => item.status !== 0)
          .map((item) => ({
            value: item.archive_value_code,
            label: `${item.archive_value_code} ${item.archive_value_name || ''}`.trim()
          }))
      }
    } catch {
      // 编码对不上时再按档案名称找
    }
  }
  try {
    const response = await customArchiveItemApi.getListAll({
      account_book_code: form.account_book_code,
      fiscal_year: form.fiscal_year,
      status: 1
    })
    const items = response.data && response.data.items ? response.data.items : []
    const found = items.find((item) => keys.includes(item.archive_item_code) || keys.includes(item.archive_item_name))
    if (!found) return []
    const values = await customArchiveItemApi.getValues(
      form.account_book_code,
      form.fiscal_year,
      found.archive_item_code,
      false
    )
    if (values.data && values.data.success) {
      return (values.data.items || [])
        .filter((item) => item.status !== 0)
        .map((item) => ({
          value: item.archive_value_code,
          label: `${item.archive_value_code} ${item.archive_value_name || ''}`.trim()
        }))
    }
  } catch {
    return []
  }
  return []
}

async function onAccountChange(row) {
  row.auxiliaries = []
  if (!row.account_code) return
  try {
    const response = await accountAuxiliaryApi.getListByAccount(
      form.account_book_code,
      form.fiscal_year,
      row.account_code,
      { status: 1, page: 1, page_size: 100 }
    )
    const defs = ((response.data && response.data.items) || []).filter((item) => item.status !== 0)
    const auxiliaries = []
    for (const definition of defs) {
      auxiliaries.push({
        auxiliary_item_code: definition.auxiliary_item_code,
        auxiliary_item_name: definition.auxiliary_item_name || definition.auxiliary_item_code,
        auxiliary_value: '',
        options: await loadArchiveOptions(definition)
      })
    }
    row.auxiliaries = auxiliaries
  } catch {
    ElMessage.error('读取科目辅助核算失败')
  }
}

function onDebitChange(row) {
  if (amountOf(row.debit_amount) > 0) row.credit_amount = null
}

function onCreditChange(row) {
  if (amountOf(row.credit_amount) > 0) row.debit_amount = null
}

function addLine() {
  const row = blankLine()
  row.summary = (form.summary || '').trim()
  lines.value.push(row)
}

function removeLine(index) {
  if (lines.value.length <= 2) return
  lines.value.splice(index, 1)
}

function resetLines() {
  lines.value = [blankLine(), blankLine()]
  fillEmptyLineSummaries()
}

function clientErrors() {
  const errors = []
  if (!form.account_book_code) errors.push('请选择账套')
  if (!form.fiscal_year) errors.push('请选择会计年度')
  if (!form.period_number) errors.push('请选择会计期间')
  if (!form.voucher_date) errors.push('请选择凭证日期')
  if (!form.voucher_type_code) errors.push('请选择凭证类型')
  if (!(form.voucher_number || '').trim()) errors.push('请填写凭证号')
  if (!(form.summary || '').trim()) errors.push('请填写凭证摘要')
  const active = lines.value.filter((row) => row.account_code || amountOf(row.debit_amount) || amountOf(row.credit_amount))
  if (!active.length) errors.push('请录入分录')
  lines.value.forEach((row, index) => {
    const touched = row.account_code || amountOf(row.debit_amount) || amountOf(row.credit_amount)
    if (!touched) return
    const lineNo = index + 1
    if (!row.account_code) errors.push(`第 ${lineNo} 行请选择科目`)
    const debit = amountOf(row.debit_amount)
    const credit = amountOf(row.credit_amount)
    if (debit > 0 && credit > 0) errors.push(`第 ${lineNo} 行不能同时填写借方和贷方金额`)
    if (debit === 0 && credit === 0) errors.push(`第 ${lineNo} 行请填写借方或贷方金额`)
    row.auxiliaries.forEach((aux) => {
      if (!(aux.auxiliary_value || '').trim()) {
        errors.push(`第 ${lineNo} 行请填写辅助核算「${aux.auxiliary_item_name}」`)
      }
    })
  })
  const debit = active.reduce((sum, row) => sum + amountOf(row.debit_amount), 0)
  const credit = active.reduce((sum, row) => sum + amountOf(row.credit_amount), 0)
  if (active.length && (debit <= 0 || credit <= 0 || Math.round((debit - credit) * 100) !== 0)) {
    errors.push(`借贷不平衡：借方合计 ${debit.toFixed(2)}，贷方合计 ${credit.toFixed(2)}`)
  }
  return errors
}

async function handleSave() {
  fillEmptyLineSummaries()
  const errors = clientErrors()
  if (errors.length) {
    ElMessage.error(errors[0])
    return
  }
  const payload = {
    account_book_code: form.account_book_code,
    fiscal_year: form.fiscal_year,
    period_number: form.period_number,
    voucher_date: form.voucher_date,
    voucher_type_code: form.voucher_type_code,
    voucher_number: form.voucher_number.trim(),
    summary: form.summary.trim(),
    attachment_count: form.attachment_count,
    prepared_by: (form.prepared_by || '').trim(),
    entries: lines.value
      .filter((row) => row.account_code)
      .map((row) => ({
        summary: (row.summary || '').trim(),
        account_code: row.account_code,
        debit_amount: amountOf(row.debit_amount),
        credit_amount: amountOf(row.credit_amount),
        auxiliaries: row.auxiliaries.map((aux) => ({
          auxiliary_item_code: aux.auxiliary_item_code,
          auxiliary_value: (aux.auxiliary_value || '').trim()
        }))
      }))
  }
  submitting.value = true
  try {
    const response = await voucherApi.create(payload)
    if (response.data.success) {
      ElMessage.success(response.data.message || '凭证保存成功')
      try {
        await ElMessageBox.confirm('凭证已保存。是否继续录入下一张？', '保存成功', {
          confirmButtonText: '继续录入',
          cancelButtonText: '留在本张',
          type: 'success'
        })
        form.voucher_number = ''
        form.summary = ''
        resetLines()
        await fillNextNumber()
      } catch {
        // 留在当前凭证
      }
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    const data = error?.response?.data
    const message = (data && data.errors && data.errors.length) ? data.errors[0] : (data && data.message) || '保存失败'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  form.voucher_date = todayText()
  form.period_number = new Date().getMonth() + 1
  fetchAccountBooks()
})
</script>

<style scoped lang="scss">
.voucher-entry {
  padding: 20px 24px 32px;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 8px;
}

.page-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #64748b;
}

.form-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.card-header-text {
  font-weight: 600;
  color: #334155;
}

.lines-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.aux-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.aux-item {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 6px;
  align-items: center;
}

.aux-label {
  font-size: 12px;
  color: #475569;
}

.aux-empty {
  color: #94a3b8;
}

.totals {
  display: flex;
  gap: 24px;
  justify-content: flex-end;
  margin-top: 12px;
  font-size: 14px;
  color: #334155;
}

.totals.unbalanced {
  color: #b91c1c;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 12px;
}
</style>
