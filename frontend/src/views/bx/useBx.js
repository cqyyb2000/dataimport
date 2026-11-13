import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const YEAR_KEY = 'bx_fiscal_year'

export function useBxYear() {
  const stored = Number(localStorage.getItem(YEAR_KEY))
  const fiscalYear = ref(stored >= 1000 && stored <= 9999 ? stored : new Date().getFullYear())
  watch(fiscalYear, (value) => {
    if (value >= 1000 && value <= 9999) {
      localStorage.setItem(YEAR_KEY, String(value))
    }
  })
  return { fiscalYear }
}

export function bxAccess() {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const isAdmin = !!user.isAdmin
  return {
    isAdmin,
    role: user.role || '',
    canMaintain: isAdmin || user.role === 'accountant',
    canConfirm: isAdmin || user.role === 'cashier'
  }
}

export function apiMessage(error, fallback) {
  return error?.response?.data?.message || fallback
}

export function isNeedConfirm(error) {
  return error?.response?.status === 409 && error.response.data?.need_confirm
}

export async function askConfirm(error, confirmButtonText) {
  const data = error.response.data
  await ElMessageBox.confirm(data.message, '请确认', {
    confirmButtonText,
    cancelButtonText: '取消',
    type: 'warning'
  })
  return data
}

export function showError(error, fallback) {
  ElMessage.error(apiMessage(error, fallback))
}

export function toTree(items, codeKey, parentKey) {
  const nodes = {}
  items.forEach((item) => {
    nodes[item[codeKey]] = { ...item }
  })
  const roots = []
  items.forEach((item) => {
    const node = nodes[item[codeKey]]
    const parentCode = item[parentKey]
    if (parentCode && nodes[parentCode]) {
      if (!nodes[parentCode].children) nodes[parentCode].children = []
      nodes[parentCode].children.push(node)
    } else {
      roots.push(node)
    }
  })
  return roots
}
