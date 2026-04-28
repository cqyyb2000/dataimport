<template>
  <div class="menu-manage">
    <div class="operation-bar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增菜单
      </el-button>
    </div>

    <!-- 菜单表格 -->
    <el-table
      :data="menuList"
      row-key="id"
      border
      default-expand-all
      :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
    >
      <el-table-column prop="name" label="菜单名称" min-width="150" />
      <el-table-column prop="path" label="路由路径" min-width="150" />
      <el-table-column prop="component" label="组件路径" min-width="150" />
      <el-table-column prop="icon" label="图标" min-width="100">
        <template #default="{ row }">
          <i :class="row.icon"></i>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button type="danger" link @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑菜单对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="菜单名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="路由路径" prop="path">
          <el-input 
            v-model="form.path" 
            placeholder="请输入路由路径（一级菜单可不填）" 
            :disabled="!form.parent_id || form.parent_id === 0"
          />
        </el-form-item>
        <el-form-item label="组件路径" prop="component">
          <el-input 
            v-model="form.component" 
            placeholder="请输入组件路径（一级菜单可不填）" 
            :disabled="!form.parent_id || form.parent_id === 0"
          />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-input v-model="form.icon" placeholder="请输入图标类名" />
        </el-form-item>
        <el-form-item label="父级菜单" prop="parent_id">
          <el-select v-model="form.parent_id" placeholder="请选择父级菜单" clearable>
            <el-option
              v-for="item in parentMenuOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { menuApi } from '@/api'

// 数据列表
const menuList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref(null)

// 表单数据
const form = ref({
  name: '',
  path: '',
  component: '',
  icon: '',
  parent_id: 0,
  sort_order: 0
})

// 表单验证规则
const rules = computed(() => {
  const isTopLevel = !form.value.parent_id || form.value.parent_id === 0
  return {
    name: [
      { required: true, message: '请输入菜单名称', trigger: 'blur' },
      { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
    ],
    path: [
      { 
        required: !isTopLevel, 
        message: '请输入路由路径', 
        trigger: 'blur' 
      }
    ],
    component: [
      { 
        required: !isTopLevel, 
        message: '请输入组件路径', 
        trigger: 'blur' 
      }
    ],
    icon: [
      { required: true, message: '请输入图标类名', trigger: 'blur' }
    ]
  }
})

// 父级菜单选项
const parentMenuOptions = computed(() => {
  return menuList.value.filter(menu => !menu.parent_id)
})

// 获取菜单列表
const fetchMenuList = async () => {
  try {
    loading.value = true
    const response = await menuApi.getAllMenus()
    if (response.data.success) {
      menuList.value = buildMenuTree(response.data.data)
    }
  } catch (error) {
    console.error('获取菜单列表失败:', error)
    ElMessage.error('获取菜单列表失败')
  } finally {
    loading.value = false
  }
}

// 构建菜单树
const buildMenuTree = (menus) => {
  const menuMap = {}
  const result = []

  // 先将所有菜单项放入 map
  menus.forEach(menu => {
    menuMap[menu.id] = { ...menu, children: [] }
  })

  // 构建树形结构
  menus.forEach(menu => {
    const node = menuMap[menu.id]
    if (menu.parent_id === 0) {
      result.push(node)
    } else {
      const parent = menuMap[menu.parent_id]
      if (parent) {
        parent.children.push(node)
      }
    }
  })

  return result
}

// 新增菜单
const handleAdd = () => {
  dialogTitle.value = '新增菜单'
  dialogVisible.value = true
}

// 编辑菜单
const handleEdit = (row) => {
  dialogTitle.value = '编辑菜单'
  form.value = { ...row }
  dialogVisible.value = true
}

// 删除菜单
const handleDelete = (row) => {
  ElMessageBox.confirm(
    '确定要删除该菜单吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await menuApi.deleteMenu(row.id)
      if (response.data.success) {
        ElMessage.success('删除成功')
        fetchMenuList()
      }
    } catch (error) {
      console.error('删除菜单失败:', error)
      ElMessage.error('删除菜单失败')
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const submitData = { ...form.value }
    
    // 如果是一级菜单，路由和组件设置为空值
    const isTopLevel = !submitData.parent_id || submitData.parent_id === 0
    if (isTopLevel) {
      submitData.path = ''
      submitData.component = ''
    }
    
    let response
    
    if (submitData.id) {
      // 编辑
      response = await menuApi.updateMenu(submitData.id, submitData)
    } else {
      // 新增
      response = await menuApi.createMenu(submitData)
    }
    
    if (response.data.success) {
      ElMessage.success(submitData.id ? '更新成功' : '创建成功')
      dialogVisible.value = false
      fetchMenuList()
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  form.value = {
    name: '',
    path: '',
    component: '',
    icon: '',
    parent_id: 0,
    sort_order: 0
  }
}

// 监听父级菜单变化，重新验证表单
watch(() => form.value.parent_id, () => {
  if (formRef.value) {
    // 清除路由和组件字段的验证错误
    formRef.value.clearValidate(['path', 'component'])
    // 如果是一级菜单，清空路由和组件字段
    const isTopLevel = !form.value.parent_id || form.value.parent_id === 0
    if (isTopLevel) {
      form.value.path = ''
      form.value.component = ''
    }
  }
})

// 页面加载时获取菜单列表
onMounted(() => {
  fetchMenuList()
})
</script>

<style scoped>
.menu-manage {
  padding: 20px;
}

.operation-bar {
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-table) {
  margin-top: 20px;
}

:deep(.el-form-item__label) {
  font-weight: bold;
}
</style> 