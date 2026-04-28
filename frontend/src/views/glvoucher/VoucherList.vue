<template>
  <div class="voucher-list" ref="voucherListRef">
    <!-- 合并的头部和查询条件区域 -->
    <div class="header-filter-area" ref="headerFilterAreaRef">
      <div class="header-title">凭证列表</div>
      <el-form :model="queryForm" :inline="true" class="filter-form">
        <el-form-item label="账套">
          <el-select
            v-model="queryForm.account_book_code"
            placeholder="请选择账套"
            style="width: 200px"
            filterable
            clearable
            @change="handleAccountBookChange"
          >
            <el-option
              v-for="item in accountBookOptions"
              :key="item.account_book_code"
              :label="`${item.account_book_code} - ${item.account_book_name}`"
              :value="item.account_book_code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="年度">
          <el-select
            v-model="queryForm.fiscal_year"
            placeholder="请选择年度"
            style="width: 150px"
            clearable
            filterable
            allow-create
            default-first-option
            @change="handleFiscalYearChange"
          >
            <el-option
              v-for="year in fiscalYearOptions"
              :key="year"
              :label="year"
              :value="typeof year === 'number' ? year : parseInt(year)"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="会计月区间">
          <el-select
            v-model="queryForm.month_start"
            placeholder="起始月"
            style="width: 120px"
            clearable
            :disabled="!queryForm.account_book_code || !queryForm.fiscal_year"
          >
            <el-option
              v-for="month in monthOptions"
              :key="month"
              :label="`${month}月`"
              :value="month"
            />
          </el-select>
          <span style="margin: 0 8px">至</span>
          <el-select
            v-model="queryForm.month_end"
            placeholder="结束月"
            style="width: 120px"
            clearable
            :disabled="!queryForm.account_book_code || !queryForm.fiscal_year"
          >
            <el-option
              v-for="month in monthOptions"
              :key="month"
              :label="`${month}月`"
              :value="month"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="凭证号">
          <el-input
            v-model="queryForm.voucher_no"
            placeholder="请输入凭证号"
            clearable
            style="width: 150px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item label="摘要">
          <el-input
            v-model="queryForm.summary"
            placeholder="请输入摘要"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格区域：内层固定高度容器，避免 flex 干扰表格根高度，保证内部 100% 链完整 -->
    <div class="table-area">
      <div class="table-area-inner">
        <el-table
          v-loading="loading"
          :data="tableData"
          stripe
          border
          style="width: 100%"
          :height="'100%'"
          :empty-text="hasSearched ? '暂无数据' : '请输入查询条件后点击查询'"
          @row-dblclick="handleRowDblclick"
        >
        <el-table-column prop="account_book_code" label="账套编码" width="120" />
        <el-table-column prop="account_book_name" label="账套名称" width="180" />
        <el-table-column prop="fiscal_year" label="年度" width="80" align="center" />
        <el-table-column prop="period_number" label="会计期间" width="100" align="center" />
        <el-table-column prop="voucher_no" label="凭证号" width="120" />
        <el-table-column prop="summary" label="摘要" min-width="200" show-overflow-tooltip />
        <el-table-column label="借方金额" width="150" align="right">
          <template #default="{ row }">
            <span>{{ formatAmount(row.debit_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贷方金额" width="150" align="right">
          <template #default="{ row }">
            <span>{{ formatAmount(row.credit_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="voucher_date" label="凭证日期" width="120" align="center">
          <template #default="{ row }">
            <span>{{ formatDate(row.voucher_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="voucher_status" label="凭证状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.voucher_status" size="small" :type="getStatusType(row.voucher_status)">
              {{ row.voucher_status }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 分页区域 -->
    <div class="pagination-area" ref="paginationAreaRef">
      <template v-if="hasSearched">
        <span class="pagination-info" v-if="total > 0">
          共 {{ total }} 条记录，第 {{ currentPage }}/{{ totalPages }} 页
        </span>
        <span class="pagination-info" v-else>
          当前查询条件下没有符合条件的数据
        </span>

        <el-pagination
          v-if="total > 0"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
        <span v-else class="pagination-placeholder"></span>
      </template>
      <template v-else>
        <div class="pagination-placeholder" style="visibility:hidden; height: 50px;"></div>
      </template>
    </div>

    <!-- 凭证详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      width="1100px"
      align-center
      destroy-on-close
      class="voucher-detail-dialog"
      @closed="onDetailClosed"
    >
      <template #header>
        <div class="voucher-detail-dialog-header">
          <div class="voucher-detail-dialog-title">凭证详情</div>
          <div class="voucher-detail-nav">
            <el-button
              type="primary"
              link
              :disabled="!detailCanPrev"
              @click="handleDetailPrev"
            >
              上一张
            </el-button>
            <el-button
              type="primary"
              link
              :disabled="!detailCanNext"
              @click="handleDetailNext"
            >
              下一张
            </el-button>
          </div>
        </div>
      </template>
      <div v-loading="detailLoading" class="voucher-detail-content">
        <template v-if="detailData">
          <!-- 表头：凭证日期、凭证号、凭证类型（居中、加粗） -->
          <div class="voucher-detail-header">
            <div class="detail-header-row">
              <span class="detail-label">凭证日期：</span>
              <span class="detail-header-value">{{ formatDetailDate(detailData.voucher_date) }}</span>
            </div>
            <div class="detail-header-row">
              <span class="detail-label">凭证号：</span>
              <span class="detail-header-value">{{ detailData.voucher_number || detailData.voucher_no || '-' }}</span>
            </div>
            <div class="detail-header-row">
              <span class="detail-label">凭证类型：</span>
              <span class="detail-header-value">{{ getVoucherTypeName(detailData.voucher_type_code) || detailData.voucher_type_name || '-' }}</span>
            </div>
          </div>
          <!-- 表体：固定高度、分页、滚动 -->
          <div class="voucher-detail-body">
            <div class="voucher-detail-table-wrap">
            <el-table
              :data="detailPaginatedEntries"
              border
              stripe
              size="small"
              class="voucher-detail-table"
              height="360"
            >
              <el-table-column prop="summary" label="摘要" min-width="160" show-overflow-tooltip />
              <el-table-column label="会计科目" min-width="160">
                <template #default="{ row }">
                  {{ row.account_name || row.account_code || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="辅助项" min-width="320" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ formatAuxiliaryDetail(row) }}
                </template>
              </el-table-column>
              <el-table-column label="借方金额" width="120" align="right">
                <template #default="{ row }">
                  {{ formatAmount(row.debit_amount) }}
                </template>
              </el-table-column>
              <el-table-column label="贷方金额" width="120" align="right">
                <template #default="{ row }">
                  {{ formatAmount(row.credit_amount) }}
                </template>
              </el-table-column>
            </el-table>
            </div>
            <div class="voucher-detail-pagination">
              <el-pagination
                v-model:current-page="detailPage"
                :page-size="detailPageSize"
                :total="detailEntriesTotal"
                layout="prev, pager, next"
                small
              />
            </div>
          </div>
          <!-- 表尾：借方合计、贷方合计、制单人、审核人 -->
          <div class="voucher-detail-footer">
            <div class="detail-footer-amounts">
            <div class="detail-footer-row detail-footer-amount">
              <span class="detail-label">借方金额合计：</span>
              <span class="detail-amount-text">{{ formatAmount(detailTotalDebit) }}</span>
            </div>
            <div class="detail-footer-row detail-footer-amount">
              <span class="detail-label">贷方金额合计：</span>
              <span class="detail-amount-text">{{ formatAmount(detailTotalCredit) }}</span>
            </div>
            </div>
            <div class="detail-footer-meta">
            <div class="detail-footer-row">
              <span class="detail-label">制单人：</span>
              <span>{{ detailData.prepared_by || '-' }}</span>
            </div>
            <div class="detail-footer-row">
              <span class="detail-label">审核人：</span>
              <span>{{ detailData.reviewed_by || '-' }}</span>
            </div>
            </div>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { accountBookApi } from '@/api/accountBook'
import { voucherApi } from '@/api/voucher'

// 列表数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const hasSearched = ref(false)

// 查询表单
const queryForm = reactive({
  account_book_code: '',
  fiscal_year: null,
  month_start: null,
  month_end: null,
  voucher_no: '',
  summary: ''
})

// 选项数据
const accountBookOptions = ref([])
const fiscalYearOptions = ref([])
const monthOptions = ref([])

// 生成默认年度选项（当前年份前后10年）
const generateDefaultYears = () => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear + 10; i >= currentYear - 10; i--) {
    years.push(i)
  }
  return years
}

// 计算总页数
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

// 表格高度（动态计算）
const tableHeight = ref(null)
const voucherListRef = ref(null)
const headerFilterAreaRef = ref(null)
const paginationAreaRef = ref(null)

// 凭证详情弹窗
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const detailPage = ref(1)
const detailPageSize = 10
/** 当前查看的凭证在列表中的下标（用于上一张/下一张） */
const detailCurrentIndex = ref(-1)

/** 凭证类型列表缓存 key: 'account_book_code|fiscal_year' value: items */
const voucherTypeCache = ref({})

const detailCanPrev = computed(() => detailCurrentIndex.value > 0)
const detailCanNext = computed(() => {
  const idx = detailCurrentIndex.value
  const list = tableData.value || []
  return idx >= 0 && idx < list.length - 1
})

// 详情分录分页与合计
const detailEntriesTotal = computed(() => {
  const entries = detailData.value?.entries || []
  return entries.length
})
const detailPaginatedEntries = computed(() => {
  const entries = detailData.value?.entries || []
  const start = (detailPage.value - 1) * detailPageSize
  return entries.slice(start, start + detailPageSize)
})
const detailTotalDebit = computed(() => {
  const entries = detailData.value?.entries || []
  return entries.reduce((sum, e) => sum + (Number(e.debit_amount) || 0), 0)
})
const detailTotalCredit = computed(() => {
  const entries = detailData.value?.entries || []
  return entries.reduce((sum, e) => sum + (Number(e.credit_amount) || 0), 0)
})

// 计算表格高度：容器实际高度 - 头部高度 - 分页高度
const calculateTableHeight = () => {
  nextTick(() => {
    // 优先使用列表容器的实际高度（适配父级 tab 区域）
    let containerHeight = 0
    if (voucherListRef.value) {
      containerHeight = voucherListRef.value.clientHeight
    }
    if (!containerHeight) {
      containerHeight = window.innerHeight - 120 // 回退：减去顶栏和 tab 等
    }

    let headerHeight = 0
    if (headerFilterAreaRef.value) {
      headerHeight = headerFilterAreaRef.value.getBoundingClientRect().height + 10
    } else {
      headerHeight = 100
    }

    let paginationHeight = 0
    if (paginationAreaRef.value) {
      paginationHeight = paginationAreaRef.value.getBoundingClientRect().height
    } else {
      paginationHeight = 44
    }

    const containerPadding = 12 * 2
    const tablePadding = 10 * 2
    const tableMarginBottom = 10
    const reservedHeight = headerHeight + paginationHeight + containerPadding + tablePadding + tableMarginBottom
    const calculatedHeight = containerHeight - reservedHeight

    tableHeight.value = Math.max(200, calculatedHeight)
  })
}

// 窗口大小变化监听
const handleResize = () => {
  calculateTableHeight()
}

// 监听分页区域显示/隐藏，重新计算表格高度
watch([() => hasSearched.value, () => total.value], () => {
  nextTick(() => {
    calculateTableHeight()
  })
})

// 格式化金额（千分位，保留两位小数）
const formatAmount = (amount) => {
  if (amount === null || amount === undefined || amount === '') {
    return '-'
  }
  return Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

// 格式化日期（YYYYMMDD -> YYYY-MM-DD）
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  if (dateStr.length === 8) {
    return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
  }
  return dateStr
}

// 详情弹窗用日期格式化（支持 YYYYMMDD 或已有格式）
const formatDetailDate = (dateStr) => {
  if (!dateStr) return '-'
  const s = String(dateStr)
  if (s.length === 8 && /^\d{8}$/.test(s)) {
    return `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`
  }
  return s
}

// 辅助项展示：优先使用 auxiliary_item_values（后端返回的拼接字符串），否则用 类别**名称
const formatAuxiliaryDetail = (row) => {
  const values = row.auxiliary_item_values
  if (values != null && String(values).trim() !== '') {
    return String(values).replace(/\\/g, '；')
  }
  const name = row.auxiliary_item_name ?? row.auxiliary_item_code ?? ''
  if (name === '' || name == null) return '-'
  const category = row.auxiliary_item_type ?? row.auxiliary_item_category ?? '辅助项'
  return `${category}**${name}`
}

const onDetailClosed = () => {
  detailData.value = null
  detailPage.value = 1
  detailCurrentIndex.value = -1
}

// 凭证类型编码转名称（优先用接口返回的凭证类型列表）
const getVoucherTypeName = (code) => {
  if (code == null || code === '') return ''
  const d = detailData.value
  if (!d?.account_book_code || d?.fiscal_year == null) return ''
  const cacheKey = `${d.account_book_code}|${d.fiscal_year}`
  const list = voucherTypeCache.value[cacheKey] || []
  const item = list.find((i) => String(i.voucher_type_code) === String(code).trim())
  return item ? item.voucher_type_name : ''
}


// 获取凭证状态类型
const getStatusType = (status) => {
  const statusMap = {
    '已记账': 'success',
    '已审核': 'warning',
    '已制单': 'info'
  }
  return statusMap[status] || 'info'
}

// 获取账套列表
const fetchAccountBooks = async () => {
  try {
    const response = await accountBookApi.getList({ page_size: 1000 })
    if (response.data.success) {
      accountBookOptions.value = response.data.items || []
    } else {
      ElMessage.error(response.data.message || '获取账套列表失败')
    }
  } catch (error) {
    console.error('获取账套列表失败:', error)
    ElMessage.error('获取账套列表失败')
  }
}

// 获取会计年度列表
const fetchFiscalYears = async (accountBookCode) => {
  if (!accountBookCode) {
    fiscalYearOptions.value = []
    return
  }
  try {
    const response = await accountBookApi.getFiscalYears(accountBookCode)
    if (response.data.success) {
      fiscalYearOptions.value = (response.data.items || []).map(item => item.fiscal_year)
    } else {
      ElMessage.error(response.data.message || '获取年度列表失败')
      fiscalYearOptions.value = []
    }
  } catch (error) {
    console.error('获取年度列表失败:', error)
    ElMessage.error('获取年度列表失败')
    fiscalYearOptions.value = []
  }
}

// 获取会计月份列表
const fetchMonths = async (accountBookCode, fiscalYear) => {
  if (!accountBookCode || !fiscalYear) {
    monthOptions.value = []
    return
  }
  try {
    const response = await voucherApi.getMonths(accountBookCode, fiscalYear)
    if (response.data.success) {
      monthOptions.value = response.data.months || []
    } else {
      ElMessage.error(response.data.message || '获取月份列表失败')
      monthOptions.value = []
    }
  } catch (error) {
    console.error('获取月份列表失败:', error)
    ElMessage.error('获取月份列表失败')
    monthOptions.value = []
  }
}

// 账套选择变化
const handleAccountBookChange = (value) => {
  queryForm.month_start = null
  queryForm.month_end = null
  monthOptions.value = []
  
  if (value) {
    // 如果选择了账套，获取该账套的年度列表
    fetchFiscalYears(value)
    // 如果已经有年度选择，重新获取月份列表
    if (queryForm.fiscal_year) {
      fetchMonths(value, queryForm.fiscal_year)
    }
  } else {
    // 如果清空账套，年度列表恢复为默认年份范围
    fiscalYearOptions.value = generateDefaultYears()
    // 如果有年度但没有账套，使用1-12的月份选项
    if (queryForm.fiscal_year) {
      monthOptions.value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    }
  }
}

// 双击表格行：打开凭证详情
const handleRowDblclick = (row) => {
  if (!row.account_book_code || !row.fiscal_year || row.period_number == null || !row.voucher_no) {
    ElMessage.warning('当前行缺少账套、年度、期间或凭证号，无法查看详情')
    return
  }
  const list = tableData.value || []
  const idx = list.findIndex(
    (r) =>
      r.account_book_code === row.account_book_code &&
      r.fiscal_year === row.fiscal_year &&
      r.period_number === row.period_number &&
      r.voucher_no === row.voucher_no
  )
  detailCurrentIndex.value = idx >= 0 ? idx : -1
  detailVisible.value = true
  detailData.value = null
  fetchDetail(row)
}

// 凭证详情：上一张
const handleDetailPrev = () => {
  if (!detailCanPrev.value) return
  const list = tableData.value || []
  const row = list[detailCurrentIndex.value - 1]
  if (row) {
    detailCurrentIndex.value -= 1
    fetchDetail(row)
  }
}

// 凭证详情：下一张
const handleDetailNext = () => {
  if (!detailCanNext.value) return
  const list = tableData.value || []
  const row = list[detailCurrentIndex.value + 1]
  if (row) {
    detailCurrentIndex.value += 1
    fetchDetail(row)
  }
}

// 确保已拉取该账套+年度的凭证类型列表（带缓存）
const ensureVoucherTypes = async (accountBookCode, fiscalYear) => {
  const key = `${accountBookCode}|${fiscalYear}`
  if (voucherTypeCache.value[key]) return
  try {
    const res = await voucherApi.getVoucherTypes(accountBookCode, fiscalYear)
    const data = res?.data
    const items = data?.items ?? []
    if (data?.success !== false && Array.isArray(items)) {
      voucherTypeCache.value[key] = items
    }
  } catch (e) {
    console.warn('获取凭证类型列表失败:', e)
  }
}

// 获取凭证详情
const fetchDetail = async (row) => {
  detailLoading.value = true
  try {
    await ensureVoucherTypes(row.account_book_code, row.fiscal_year)
    const res = await voucherApi.getDetail(
      row.account_book_code,
      row.fiscal_year,
      row.period_number,
      row.voucher_no
    )
    const data = res?.data?.data ?? res?.data
    if (data) {
      detailData.value = data
      detailPage.value = 1
    } else {
      ElMessage.error('获取凭证详情失败')
      detailVisible.value = false
    }
  } catch (error) {
    console.error('获取凭证详情失败:', error)
    ElMessage.error(error?.response?.data?.message || '获取凭证详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

// 年度选择变化
const handleFiscalYearChange = (value) => {
  queryForm.month_start = null
  queryForm.month_end = null
  monthOptions.value = []
  
  // 如果账套和年度都有，则获取月份列表
  if (value && queryForm.account_book_code) {
    fetchMonths(queryForm.account_book_code, value)
  }
  
  // 如果只有年度没有账套，生成1-12的月份选项
  if (value && !queryForm.account_book_code) {
    monthOptions.value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  }
}

// 获取凭证列表
const fetchData = async () => {
  // 验证月份范围
  if (queryForm.month_start && queryForm.month_end && queryForm.month_start > queryForm.month_end) {
    ElMessage.warning('起始月不能大于结束月')
    return
  }

  // 至少需要一个查询条件
  if (!queryForm.account_book_code && !queryForm.fiscal_year && !queryForm.voucher_no && !queryForm.summary) {
    ElMessage.warning('请至少输入一个查询条件')
    return
  }

  loading.value = true
  hasSearched.value = true

  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    // 添加可选参数（只添加有值的参数）
    if (queryForm.account_book_code) {
      params.account_book_code = queryForm.account_book_code
    }
    if (queryForm.fiscal_year) {
      // 确保年度是数字类型
      params.fiscal_year = typeof queryForm.fiscal_year === 'number' 
        ? queryForm.fiscal_year 
        : parseInt(queryForm.fiscal_year)
    }
    if (queryForm.month_start) {
      params.month_start = queryForm.month_start
    }
    if (queryForm.month_end) {
      params.month_end = queryForm.month_end
    }
    if (queryForm.voucher_no) {
      params.voucher_no = queryForm.voucher_no
    }
    if (queryForm.summary) {
      params.summary = queryForm.summary
    }

    const response = await voucherApi.getList(params)
    
    if (response.data.success) {
      tableData.value = response.data.items || []
      total.value = response.data.total || 0
    } else {
      ElMessage.error(response.data.message || '获取凭证列表失败')
      tableData.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('获取凭证列表失败:', error)
    ElMessage.error('获取凭证列表失败')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 查询
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 重置
const handleReset = () => {
  queryForm.account_book_code = ''
  queryForm.fiscal_year = null
  queryForm.month_start = null
  queryForm.month_end = null
  queryForm.voucher_no = ''
  queryForm.summary = ''
  
  fiscalYearOptions.value = []
  monthOptions.value = []
  tableData.value = []
  total.value = 0
  currentPage.value = 1
  hasSearched.value = false
}

// 分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

// 页码变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchData()
}

// 初始化
onMounted(() => {
  fetchAccountBooks()
  // 初始化默认年度选项
  fiscalYearOptions.value = generateDefaultYears()
  calculateTableHeight()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
// 占满父容器（tab-content）高度，不超出屏幕
.voucher-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; // flex 子项可被压缩
  padding: 16px;
  background: linear-gradient(165deg, #f0f4f8 0%, #e8edf3 50%, #f4f6f9 100%);
  box-sizing: border-box;
  overflow: hidden;
}

// 头部 + 查询：固定高度，不参与伸缩
.voucher-list .header-filter-area {
  flex: 0 0 auto;
  padding: 18px 22px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
}

.voucher-list .header-filter-area .header-title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: #1e293b;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.voucher-list .header-filter-area .filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 12px;
}

.voucher-list .header-filter-area .filter-form :deep(.el-form-item__label) {
  padding: 0;
  font-size: 13px;
  margin-right: 6px;
}

.voucher-list .header-filter-area .filter-form :deep(.el-input),
.voucher-list .header-filter-area .filter-form :deep(.el-select) {
  font-size: 13px;
}

.voucher-list .header-filter-area .filter-form :deep(.el-button) {
  padding: 6px 14px;
  font-size: 13px;
}

// 表格区域：占据剩余空间
.voucher-list .table-area {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

/* 内层固定高度容器：用 100% 承接 table-area 高度，避免对 .el-table 用 flex 导致内部 100% 链断裂 */
.voucher-list .table-area-inner {
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

/* 不覆盖 .el-table 的 display/flex，仅保证在父容器内可收缩，高度完全由 :height="100%" 提供 */
.voucher-list .table-area-inner :deep(.el-table) {
  min-height: 0;
}

/* body-wrapper 不设 overflow:auto，滚动由内部 el-scrollbar__wrap 负责 */
.voucher-list .table-area-inner :deep(.el-table__body-wrapper) {
  overflow: hidden;
}

/* 确保 el-scrollbar 及其 wrap 获得完整高度，wrap 为唯一纵向滚动容器 */
.voucher-list .table-area-inner :deep(.el-table__body-wrapper .el-scrollbar) {
  height: 100%;
}

.voucher-list .table-area-inner :deep(.el-table__body-wrapper .el-scrollbar__wrap) {
  height: 100% !important;
  max-height: 100% !important;
  overflow-y: auto !important;
  overflow-x: auto !important;
  /* 保证滚轮和拖拽能作用在 wrap 上 */
  touch-action: pan-y pan-x;
}

// 分页区域：固定高度，始终在视口内
.voucher-list .pagination-area {
  flex: 0 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
  min-height: 44px;
}

.voucher-list .pagination-area .pagination-info {
  font-size: 13px;
  color: #606266;
}

.voucher-list .pagination-area .pagination-placeholder {
  display: inline-block;
  min-width: 200px;
}

.voucher-list .pagination-area :deep(.el-pagination) {
  flex-shrink: 0;
  font-size: 13px;
}

.voucher-list .pagination-area :deep(.el-pagination .btn-prev),
.voucher-list .pagination-area :deep(.el-pagination .btn-next),
.voucher-list .pagination-area :deep(.el-pagination .el-pager li) {
  min-width: 26px;
  height: 26px;
  line-height: 26px;
  font-size: 13px;
}

// 凭证详情弹窗：组件内层结构见同文件末「非 scoped」块（el-dialog 会 teleport 到 body）

.voucher-detail-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 16px 20px 14px 48px;
  box-sizing: border-box;
}

.voucher-detail-dialog-title {
  flex: 1;
  text-align: center;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 0.06em;
  color: #0f172a;
}

.voucher-detail-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.voucher-detail-nav :deep(.el-button) {
  font-weight: 500;
}

.voucher-detail-content {
  min-height: 120px;
  padding: 20px 24px 24px;
}

.voucher-detail-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: stretch;
  gap: 20px 32px;
  margin-bottom: 20px;
  padding: 18px 20px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  text-align: center;
  font-size: 14px;
  color: #1e293b;
}

.voucher-detail-header .detail-header-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 120px;
}

.voucher-detail-header .detail-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.02em;
  margin-right: 0;
}

.voucher-detail-header .detail-header-value {
  font-weight: 700;
  font-size: 15px;
  color: #0f172a;
  line-height: 1.35;
  word-break: break-all;
}

.voucher-detail-body {
  margin-bottom: 4px;
}

.voucher-detail-table-wrap {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 2px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.voucher-detail-table {
  font-weight: 600;
}

/* 分录表：名称列略宽、辅助项列显著加宽，表体更易读 */
.voucher-detail-table :deep(.el-table) {
  --el-table-border-color: #e2e8f0;
}

.voucher-detail-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  padding: 4px 0 2px;
}

.voucher-detail-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: flex-start;
  gap: 20px 40px;
  margin-top: 8px;
  padding: 18px 20px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  color: #1e293b;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

.voucher-detail-footer .detail-footer-amounts {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 28px;
  justify-content: center;
}

.voucher-detail-footer .detail-footer-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 28px;
  justify-content: center;
}

.voucher-detail-footer .detail-footer-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.voucher-detail-footer .detail-footer-amount {
  padding: 8px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.voucher-detail-footer .detail-amount-text {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #0f172a;
  font-size: 15px;
}

.voucher-detail-footer .detail-footer-row .detail-label {
  color: #64748b;
  font-weight: 500;
  margin-right: 0;
  white-space: nowrap;
}

// 响应式优化
@media (max-width: 1600px) {
  .voucher-list {
    .header-filter-area {
      .filter-form {
        :deep(.el-form-item) {
          margin-bottom: 8px;
        }
      }
    }
  }
}

@media (max-width: 1200px) {
  .voucher-list {
    padding: 8px;

    .header-filter-area {
      padding: 10px 12px;

      .filter-form {
        :deep(.el-form-item) {
          margin-right: 12px;
        }
      }
    }

    .table-area {
      padding: 8px;
    }

    .pagination-area {
      padding: 10px 12px;
      flex-wrap: wrap;
      gap: 8px;

      .pagination-info {
        width: 100%;
        margin-bottom: 8px;
      }
    }
  }
}
</style>

<style lang="scss">
// el-dialog 会 teleport 到 body：此处非 scoped，保证 .el-dialog 与表格内层类名命中
.voucher-detail-dialog.el-dialog {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.14);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-top: 3px solid var(--el-color-primary);
}

.voucher-detail-dialog .el-dialog__header {
  margin: 0;
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.voucher-detail-dialog .el-dialog__headerbtn {
  top: 14px;
}

.voucher-detail-dialog .el-dialog__body {
  padding: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 45%, #eef2f7 100%);
}

.voucher-detail-dialog .voucher-detail-table .el-table__header th {
  font-weight: 700;
  background: #f1f5f9 !important;
  color: #334155;
  font-size: 13px;
}

.voucher-detail-dialog .voucher-detail-table .el-table__body td {
  font-weight: 600;
  color: #1e293b;
}

.voucher-detail-dialog .voucher-detail-table .el-table__body tr.el-table__row--striped td {
  background: #fafbfc;
}

@media (max-width: 1200px) {
  .voucher-detail-dialog.el-dialog {
    width: 96% !important;
    max-width: 1100px;
  }
}
</style>
