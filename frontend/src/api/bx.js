import api from './index'

export const bxApi = {
  listDepartments: (fiscalYear) => api.get('/bx/departments', { params: { fiscal_year: fiscalYear } }),
  createDepartment: (data) => api.post('/bx/departments', data),
  renameDepartment: (data) => api.put('/bx/departments/name', data),
  moveDepartment: (data) => api.put('/bx/departments/parent', data),
  deleteDepartment: (fiscalYear, deptCode) => api.delete('/bx/departments', {
    params: { fiscal_year: fiscalYear, dept_code: deptCode }
  }),

  listProjects: (fiscalYear) => api.get('/bx/projects', { params: { fiscal_year: fiscalYear } }),
  createProject: (data) => api.post('/bx/projects', data),
  renameProject: (data) => api.put('/bx/projects/name', data),
  moveProject: (data) => api.put('/bx/projects/parent', data),
  deleteProject: (fiscalYear, projectCode) => api.delete('/bx/projects', {
    params: { fiscal_year: fiscalYear, project_code: projectCode }
  }),

  copyYear: (data) => api.post('/bx/copy-year', data),

  listBudgets: (fiscalYear, page = 1, pageSize = 10) => api.get('/bx/budgets', {
    params: { fiscal_year: fiscalYear, page, page_size: pageSize }
  }),
  createBudget: (data) => api.post('/bx/budgets', data),
  updateBudgetAmount: (data) => api.put('/bx/budgets/amount', data),
  deleteBudget: (fiscalYear, deptCode, projectCode) => api.delete('/bx/budgets', {
    params: { fiscal_year: fiscalYear, dept_code: deptCode, project_code: projectCode }
  }),

  listClaims: (params) => api.get('/bx/claims', { params }),
  createClaim: (data) => api.post('/bx/claims', data),
  updateClaim: (id, data) => api.put(`/bx/claims/${id}`, data),
  deleteClaim: (id) => api.delete(`/bx/claims/${id}`),
  confirmClaim: (id, data) => api.post(`/bx/claims/${id}/confirm`, data || {}),
  cancelConfirmClaim: (id) => api.post(`/bx/claims/${id}/cancel-confirm`, {}),

  summary: (params) => api.get('/bx/summary', { params })
}
