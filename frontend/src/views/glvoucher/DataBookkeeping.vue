<template>
  <div class="data-bookkeeping">
    <div class="page-header">
      <h2 class="page-title">数据记账</h2>
      <p class="page-desc">
        按当前账套、会计年度，根据已导入的凭证明细汇总借贷发生额，滚算期初/期末，写入科目余额表（不区分辅助项、币种等维度）；执行前会清空该账套该年度下原有科目余额数据。凭证明细为末级科目时，可填写级次规则（如 422 表示一级 4 位、二级累计 6 位、三级累计 8 位），系统会按编码前缀将余额逐级汇总到上级科目。
      </p>
    </div>

    <el-card class="form-card" shadow="never">
      <template #header>
        <span class="card-header-text">重算条件</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="bookkeeping-form"
        @submit.prevent
      >
        <el-form-item label="账套" prop="account_book_code">
          <el-select
            v-model="form.account_book_code"
            placeholder="请选择账套"
            style="width: 100%; max-width: 420px"
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

        <el-form-item label="会计年度" prop="fiscal_year">
          <el-select
            v-model="form.fiscal_year"
            placeholder="请选择会计年度"
            style="width: 100%; max-width: 320px"
            clearable
            :disabled="!form.account_book_code"
          >
            <el-option
              v-for="year in fiscalYearOptions"
              :key="year"
              :label="String(year)"
              :value="year"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="科目级次" prop="level_pattern">
          <el-input
            v-model="form.level_pattern"
            placeholder="默认 422（一级4位、二级6位、三级8位）；清空则仅按凭证明细科目出账"
            style="width: 100%; max-width: 420px"
            clearable
            maxlength="20"
          />
          <div class="form-hint">每位仅 1–9，表示该级相对上一级的编码位数增量；累计长度用于截取上级科目编码。</div>
        </el-form-item>

        <el-form-item>
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            class="warn-alert"
            title="执行后将删除该账套、该「会计年度」下 gl_account_balance 中全部行，再按凭证明细重算写入。若需保留其他来源的科目余额，请勿使用本功能。"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="submitting"
            :disabled="submitting"
            @click="handleSubmit"
          >
            从凭证重算科目余额
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="lastResult" class="result-card" shadow="never">
      <template #header>
        <span class="card-header-text">上次执行结果</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="删除行数">
          {{ lastResult.deleted_rows ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="写入行数">
          {{ lastResult.inserted_rows ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="涉及科目数">
          {{ lastResult.account_count ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="每科目滚算期间数">
          {{ lastResult.periods_emitted ?? '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="应用的级次规则">
          {{ lastResult.level_pattern_applied || '（未汇总，仅明细）' }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="lastResult.unknown_accounts && lastResult.unknown_accounts.length"
          label="未在科目表定义的科目"
        >
          <el-tag
            v-for="c in lastResult.unknown_accounts"
            :key="c"
            type="info"
            class="tag-code"
            effect="plain"
          >
            {{ c }}
          </el-tag>
          <div class="hint-muted">上述代码已按「借方」性质参与滚算，请在科目表维护后再重算以校正方向。</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { glApi } from '@/api/gl'
import { accountBookApi } from '@/api/accountBook'

const formRef = ref(null)
const submitting = ref(false)
const accountBookOptions = ref([])
const fiscalYearOptions = ref([])

const form = reactive({
  account_book_code: '',
  fiscal_year: null,
  level_pattern: '422'
})

const rules = {
  account_book_code: [{ required: true, message: '请选择账套', trigger: 'change' }],
  fiscal_year: [{ required: true, message: '请选择会计年度', trigger: 'change' }],
  level_pattern: [
    {
      validator: (_rule, value, callback) => {
        const s = (value || '').trim()
        if (!s) {
          callback()
          return
        }
        if (!/^[1-9]+$/.test(s)) {
          callback(new Error('级次规则须为数字串，每位仅 1–9，如 422'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

const lastResult = ref(null)

const fetchAccountBooks = async () => {
  try {
    const response = await accountBookApi.getList({ page_size: 1000 })
    if (response.data.success) {
      accountBookOptions.value = response.data.items || []
    } else {
      ElMessage.error(response.data.message || '获取账套列表失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('获取账套列表失败')
  }
}

const fetchFiscalYears = async (code) => {
  if (!code) {
    fiscalYearOptions.value = []
    return
  }
  try {
    const response = await accountBookApi.getFiscalYears(code)
    if (response.data.success) {
      fiscalYearOptions.value = (response.data.items || []).map((i) => i.fiscal_year)
    } else {
      fiscalYearOptions.value = []
    }
  } catch (e) {
    console.error(e)
    fiscalYearOptions.value = []
  }
}

const onAccountBookChange = (code) => {
  form.fiscal_year = null
  fetchFiscalYears(code)
}

const handleSubmit = async () => {
  const formEl = formRef.value
  if (!formEl) return
  try {
    await formEl.validate()
  } catch {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定按账套「${form.account_book_code}」、年度「${form.fiscal_year}」从凭证明细重算科目余额吗？本账套本年度的原科目余额将被清空。`,
      '确认数据记账',
      {
        type: 'warning',
        confirmButtonText: '确定执行',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  submitting.value = true
  lastResult.value = null
  try {
    const { data } = await glApi.recalculateAccountBalanceFromVouchers(
      form.account_book_code,
      form.fiscal_year,
      { level_pattern: form.level_pattern }
    )
    if (data.success) {
      lastResult.value = {
        deleted_rows: data.deleted_rows,
        inserted_rows: data.inserted_rows,
        account_count: data.account_count,
        periods_emitted: data.periods_emitted,
        unknown_accounts: data.unknown_accounts || [],
        level_pattern_applied: data.level_pattern_applied
      }
      ElMessage.success(
        `重算完成：已删除 ${data.deleted_rows ?? 0} 行，写入 ${data.inserted_rows ?? 0} 行。`
      )
    } else {
      ElMessage.error(data.message || '重算失败')
    }
  } catch (err) {
    const msg = err?.response?.data?.message || err?.message || '请求失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchAccountBooks()
})
</script>

<style scoped lang="scss">
.data-bookkeeping {
  padding: 20px 24px;
  max-width: 920px;
}

.page-header {
  margin-bottom: 20px;
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

.form-card,
.result-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.card-header-text {
  font-weight: 600;
  color: #334155;
}

.bookkeeping-form {
  max-width: 640px;
}

.warn-alert {
  max-width: 100%;
  align-items: flex-start;
}

.tag-code {
  margin: 0 6px 6px 0;
}

.hint-muted {
  margin-top: 8px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.45;
  max-width: 520px;
}
</style>
