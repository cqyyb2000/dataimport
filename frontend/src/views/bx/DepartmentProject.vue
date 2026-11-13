<template>
  <div class="bx-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>部门与项目</span>
          <div class="toolbar">
            <span>年度</span>
            <el-input-number v-model="fiscalYear" :min="1000" :max="9999" :step="1" controls-position="right" />
            <el-button v-if="access.canMaintain" @click="openCopy">从其他年度复制</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <section class="archive-panel archive-panel-dept">
          <div class="block-title">
            <span class="block-name">部门</span>
            <el-button v-if="access.canMaintain" type="primary" @click="openCreate('department')">新增部门</el-button>
          </div>
          <el-table
            :data="departmentTree"
            row-key="dept_code"
            default-expand-all
            :tree-props="{ children: 'children' }"
            v-loading="loading"
          >
            <el-table-column prop="dept_code" label="代码" width="120" />
            <el-table-column prop="dept_name" label="名称" />
            <el-table-column prop="level_no" label="级次" width="70" />
            <el-table-column label="最明细" width="80">
              <template #default="scope">{{ scope.row.is_leaf ? '是' : '' }}</template>
            </el-table-column>
            <el-table-column v-if="access.canMaintain" label="操作" width="250">
              <template #default="scope">
                <el-button size="small" @click="openRename('department', scope.row)">改名</el-button>
                <el-button size="small" @click="openMove('department', scope.row)">调整上级</el-button>
                <el-button size="small" type="danger" @click="removeRow('department', scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          </section>
        </el-col>
        <el-col :span="12">
          <section class="archive-panel archive-panel-project">
          <div class="block-title">
            <span class="block-name">项目</span>
            <el-button v-if="access.canMaintain" type="success" @click="openCreate('project')">新增项目</el-button>
          </div>
          <el-table
            :data="projectTree"
            row-key="project_code"
            default-expand-all
            :tree-props="{ children: 'children' }"
            v-loading="loading"
          >
            <el-table-column prop="project_code" label="代码" width="120" />
            <el-table-column prop="project_name" label="名称" />
            <el-table-column prop="level_no" label="级次" width="70" />
            <el-table-column label="最明细" width="80">
              <template #default="scope">{{ scope.row.is_leaf ? '是' : '' }}</template>
            </el-table-column>
            <el-table-column v-if="access.canMaintain" label="操作" width="250">
              <template #default="scope">
                <el-button size="small" @click="openRename('project', scope.row)">改名</el-button>
                <el-button size="small" @click="openMove('project', scope.row)">调整上级</el-button>
                <el-button size="small" type="danger" @click="removeRow('project', scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          </section>
        </el-col>
      </el-row>
    </el-card>

    <el-dialog v-model="editVisible" :title="editTitle" width="480px">
      <el-form label-width="90px">
        <el-form-item :label="kindLabel + '代码'">
          <el-input v-model="editForm.code" :disabled="editMode !== 'create'" />
        </el-form-item>
        <el-form-item v-if="editMode !== 'move'" :label="kindLabel + '名称'">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item v-if="editMode !== 'rename'" label="上级">
          <el-select v-model="editForm.parentCode" clearable placeholder="无上级则为第一级" style="width: 100%">
            <el-option
              v-for="item in parentOptions"
              :key="item.code"
              :label="item.code + ' ' + item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="copyVisible" title="从其他年度复制" width="420px">
      <el-form label-width="90px">
        <el-form-item label="来源年度">
          <el-input-number v-model="sourceYear" :min="1000" :max="9999" :step="1" />
        </el-form-item>
        <el-form-item label="目标年度">
          <span>{{ fiscalYear }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCopy(false)">复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bxApi } from '@/api/bx'
import { apiMessage, bxAccess, isNeedConfirm, showError, toTree, useBxYear } from './useBx'

const access = bxAccess()
const { fiscalYear } = useBxYear()
const loading = ref(false)
const departments = ref([])
const projects = ref([])
const editVisible = ref(false)
const editMode = ref('create')
const editKind = ref('department')
const editForm = ref({ code: '', name: '', parentCode: null })
const copyVisible = ref(false)
const sourceYear = ref(new Date().getFullYear() - 1)

const departmentTree = computed(() => toTree(departments.value, 'dept_code', 'parent_dept_code'))
const projectTree = computed(() => toTree(projects.value, 'project_code', 'parent_project_code'))
const kindLabel = computed(() => (editKind.value === 'department' ? '部门' : '项目'))
const editTitle = computed(() => {
  const action = { create: '新增', rename: '修改名称', move: '调整上级' }[editMode.value]
  return action + kindLabel.value
})
const parentOptions = computed(() => {
  const codeKey = editKind.value === 'department' ? 'dept_code' : 'project_code'
  const nameKey = editKind.value === 'department' ? 'dept_name' : 'project_name'
  const rows = editKind.value === 'department' ? departments.value : projects.value
  return rows
    .filter((item) => item[codeKey] !== editForm.value.code)
    .map((item) => ({ code: item[codeKey], name: item[nameKey] }))
})

const load = async () => {
  if (!fiscalYear.value) return
  loading.value = true
  try {
    const [deptRes, projectRes] = await Promise.all([
      bxApi.listDepartments(fiscalYear.value),
      bxApi.listProjects(fiscalYear.value)
    ])
    departments.value = deptRes.data.items || []
    projects.value = projectRes.data.items || []
  } catch (error) {
    showError(error, '加载档案失败')
  } finally {
    loading.value = false
  }
}

watch(fiscalYear, load, { immediate: true })

const openCreate = (kind) => {
  editKind.value = kind
  editMode.value = 'create'
  editForm.value = { code: '', name: '', parentCode: null }
  editVisible.value = true
}

const openRename = (kind, row) => {
  editKind.value = kind
  editMode.value = 'rename'
  editForm.value = {
    code: kind === 'department' ? row.dept_code : row.project_code,
    name: kind === 'department' ? row.dept_name : row.project_name,
    parentCode: null
  }
  editVisible.value = true
}

const openMove = (kind, row) => {
  editKind.value = kind
  editMode.value = 'move'
  editForm.value = {
    code: kind === 'department' ? row.dept_code : row.project_code,
    name: kind === 'department' ? row.dept_name : row.project_name,
    parentCode: kind === 'department' ? row.parent_dept_code : row.parent_project_code
  }
  editVisible.value = true
}

const submitEdit = async () => {
  const year = fiscalYear.value
  const code = (editForm.value.code || '').trim()
  const name = (editForm.value.name || '').trim()
  const parent = editForm.value.parentCode || null
  try {
    if (editKind.value === 'department') {
      if (editMode.value === 'create') {
        await bxApi.createDepartment({ fiscal_year: year, dept_code: code, dept_name: name, parent_dept_code: parent })
      } else if (editMode.value === 'rename') {
        await bxApi.renameDepartment({ fiscal_year: year, dept_code: code, dept_name: name })
      } else {
        await bxApi.moveDepartment({ fiscal_year: year, dept_code: code, parent_dept_code: parent })
      }
    } else if (editMode.value === 'create') {
      await bxApi.createProject({ fiscal_year: year, project_code: code, project_name: name, parent_project_code: parent })
    } else if (editMode.value === 'rename') {
      await bxApi.renameProject({ fiscal_year: year, project_code: code, project_name: name })
    } else {
      await bxApi.moveProject({ fiscal_year: year, project_code: code, parent_project_code: parent })
    }
    ElMessage.success('已保存')
    editVisible.value = false
    await load()
  } catch (error) {
    showError(error, '保存失败')
  }
}

const removeRow = async (kind, row) => {
  const code = kind === 'department' ? row.dept_code : row.project_code
  const name = kind === 'department' ? row.dept_name : row.project_name
  try {
    await ElMessageBox.confirm(`删除${kind === 'department' ? '部门' : '项目'} ${code} ${name}？`, '删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    if (kind === 'department') await bxApi.deleteDepartment(fiscalYear.value, code)
    else await bxApi.deleteProject(fiscalYear.value, code)
    ElMessage.success('已删除')
    await load()
  } catch (error) {
    showError(error, '删除失败')
  }
}

const openCopy = () => {
  sourceYear.value = fiscalYear.value - 1
  copyVisible.value = true
}

const submitCopy = async (confirmed) => {
  try {
    await bxApi.copyYear({
      source_year: sourceYear.value,
      target_year: fiscalYear.value,
      confirmed
    })
    ElMessage.success('复制完成')
    copyVisible.value = false
    await load()
  } catch (error) {
    if (!confirmed && isNeedConfirm(error)) {
      const data = error.response.data
      try {
        await ElMessageBox.confirm(
          `${data.message}。将删除部门 ${data.department_count} 个、项目 ${data.project_count} 个、预算 ${data.budget_count} 条。`,
          '复制提醒',
          { confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning' }
        )
      } catch {
        return
      }
      await submitCopy(true)
      return
    }
    ElMessage.error(apiMessage(error, '复制失败'))
  }
}
</script>

<style scoped>
.bx-page { padding: 20px; }
.card-header, .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.toolbar { font-weight: 400; }
.archive-panel { border: 1px solid #e4e7ed; border-radius: 6px; overflow: hidden; min-width: 0; }
.archive-panel-dept { border-top: 3px solid #409eff; }
.archive-panel-project { border-top: 3px solid #67c23a; }
.block-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; }
.archive-panel-dept .block-title { background: #ecf5ff; }
.archive-panel-project .block-title { background: #f0f9eb; }
.block-name { font-size: 15px; font-weight: 600; }
</style>
