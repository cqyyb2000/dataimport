<template>
  <div class="user-manage">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>
      
      <el-table :data="userList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名称" />
        <el-table-column prop="is_admin" label="是否管理员">
          <template #default="scope">
            <el-tag :type="scope.row.is_admin ? 'success' : 'info'">
              {{ scope.row.is_admin ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页控件 -->
      <div class="pagination-container">
        <div class="pagination-info">
          <span>共 {{ total }} 条记录</span>
          <span>每页 {{ pageSize }} 条</span>
          <span>当前第 {{ currentPage }}/{{ totalPages }} 页</span>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增用户' : '编辑用户'"
      width="500px"
    >
      <el-form 
        :model="userForm" 
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="用户名称" prop="username">
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" />
        </el-form-item>
        <el-form-item label="是否管理员">
          <el-switch v-model="userForm.is_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api'

const userList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref('add')
const formRef = ref(null)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const userForm = ref({
  username: '',
  password: '',
  is_admin: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 获取用户列表
const fetchUserList = async () => {
  loading.value = true
  try {
    console.log('Fetching users with params:', {
      page: currentPage.value,
      page_size: pageSize.value
    })
    const response = await userApi.getUsers({
      page: currentPage.value,
      page_size: pageSize.value
    })
    console.log('API Response:', response)
    if (response.data.success) {
      userList.value = response.data.items
      total.value = response.data.total
      console.log('Updated user list:', userList.value)
      // 如果当前页大于总页数，则跳转到最后一页
      if (currentPage.value > response.data.total_pages) {
        currentPage.value = response.data.total_pages
        await fetchUserList()
      }
    } else {
      ElMessage.error(response.data.message || '获取用户列表失败')
    }
  } catch (error) {
    console.error('Error details:', error.response || error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 处理页码改变
const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchUserList()
}

// 处理每页条数改变
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1 // 切换每页条数时重置到第一页
  fetchUserList()
}

// 新增用户
const handleAdd = () => {
  dialogType.value = 'add'
  userForm.value = {
    username: '',
    password: '',
    is_admin: false
  }
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (row) => {
  dialogType.value = 'edit'
  userForm.value = { ...row }
  dialogVisible.value = true
}

// 删除用户
const handleDelete = (row) => {
  ElMessageBox.confirm(
    '确定要删除该用户吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await userApi.deleteUser(row.id)
      ElMessage.success('删除成功')
      fetchUserList()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error('Error deleting user:', error)
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (dialogType.value === 'add') {
      await userApi.createUser({
        username: userForm.value.username,
        password: userForm.value.password,
        is_admin: userForm.value.is_admin
      })
      ElMessage.success('添加成功')
    } else {
      await userApi.updateUser(userForm.value.id, userForm.value)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchUserList()
  } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data.message || '操作失败')
    } else {
      ElMessage.error(dialogType.value === 'add' ? '添加失败' : '更新失败')
    }
    console.error('Error submitting form:', error)
  }
}

onMounted(() => {
  fetchUserList()
})
</script>

<style scoped>
.user-manage {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pagination-info {
  display: flex;
  gap: 20px;
  color: #606266;
  font-size: 14px;
}

.pagination-info span {
  display: inline-block;
}
</style> 