<template>
  <div class="permission-container">
    <el-card>
      <el-row :gutter="20">
        <!-- 用户列表 -->
        <el-col :span="8">
          <div class="section-title">用户列表</div>
          <el-table
            :data="users"
            @row-click="handleUserSelect"
            highlight-current-row
            style="width: 100%">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="is_admin" label="管理员" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_admin ? 'success' : 'info'">
                  {{ scope.row.is_admin ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
        <!-- 分隔线 -->
        <el-col :span="1" class="divider-col">
          <div class="vertical-divider"></div>
        </el-col>
        <!-- 菜单树 -->
        <el-col :span="15">
          <div class="tree-header">
            <span class="section-title">菜单权限</span>
            <el-button 
              type="primary" 
              size="default" 
              @click="handleSavePermissions"
              class="save-button"
              :disabled="selectedUser?.is_admin">
              <el-icon><Check /></el-icon>
              保存权限
            </el-button>
          </div>
          <el-tree
            ref="menuTreeRef"
            :data="menuTree"
            show-checkbox
            node-key="id"
            :props="defaultProps"
            :checked-keys="checkedKeys"
            @check="handleCheck"
            class="menu-tree"
            :disabled="selectedUser?.is_admin"
            default-expand-all
          />
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { permissionApi } from '@/api'
import { Check } from '@element-plus/icons-vue'

const users = ref([])
const selectedUser = ref(null)
const menuTree = ref([])
const checkedKeys = ref([])
const menuTreeRef = ref(null)
const defaultProps = { children: 'children', label: 'name' }

// 获取用户列表
const fetchUsers = async () => {
  try {
    const res = await permissionApi.getAllUsers()
    if (res.data && Array.isArray(res.data)) {
      users.value = res.data.map(user => ({
        ...user,
        is_admin: Boolean(user.is_admin) // 确保is_admin是布尔值
      }))
      console.log('用户列表数据:', users.value)
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  }
}

// 获取菜单树
const fetchMenuTree = async () => {
  try {
    const res = await permissionApi.getAllMenus()
    if (res.data && res.data.success && Array.isArray(res.data.data)) {
      console.log('菜单树数据:', res.data.data)
      menuTree.value = buildMenuTree(res.data.data)
    }
  } catch (error) {
    ElMessage.error('获取菜单列表失败')
    console.error('获取菜单列表失败:', error)
  }
}

// 构建树形结构
function buildMenuTree(menus) {
  const map = {}
  const roots = []
  
  menus.forEach(item => {
    map[item.id] = { ...item, children: [] }
  })
  
  menus.forEach(item => {
    if (item.parent_id === 0) {
      console.log('根节点:', map[item.id])
     roots.push(map[item.id])
    } else {
      const parent = map[item.parent_id]
      if (parent) {
       parent.children.push(map[item.id])
      }
    }
  })
  
  return roots
}

// 获取用户权限
const fetchUserPermissions = async (userId) => {
  try {
    const res = await permissionApi.getUserPermissions(userId)
    console.log('用户权限原始数据:', res.data)
    
    // 确保返回的是数组
    const menuIds = Array.isArray(res.data) ? res.data : 
                   (res.data && Array.isArray(res.data.menu_ids) ? res.data.menu_ids : [])
    console.log('处理后的菜单ID:', menuIds)
    
    // 将菜单ID转换为数字类型并更新选中状态
    checkedKeys.value = menuIds.map(id => Number(id))
    console.log('最终设置的选中项:', checkedKeys.value)
    
    // 更新树形控件的选中状态
    if (menuTreeRef.value) {
      menuTreeRef.value.setCheckedKeys(checkedKeys.value)
    }
  } catch (error) {
    console.error('获取用户权限失败:', error)
    ElMessage.error('获取用户权限失败')
    checkedKeys.value = []
    // 清空树形控件的选中状态
    if (menuTreeRef.value) {
      menuTreeRef.value.setCheckedKeys([])
    }
  }
}

// 选中用户时加载权限
const handleUserSelect = async (row) => {
  console.log('选中用户:', row)
  selectedUser.value = row
  
  if (row.is_admin) {
    // 如果是管理员，获取所有菜单ID并全选
    const getAllMenuIds = (tree) => {
      let ids = []
      const traverse = (nodes) => {
        nodes.forEach(node => {
          ids.push(node.id)
          if (node.children && node.children.length) {
            traverse(node.children)
          }
        })
      }
      traverse(tree)
      return ids
    }
    checkedKeys.value = getAllMenuIds(menuTree.value)
    // 更新树形控件的选中状态
    if (menuTreeRef.value) {
      menuTreeRef.value.setCheckedKeys(checkedKeys.value)
    }
    // 禁用树形控件
    menuTreeRef.value.disabled = true
  } else {
    // 如果不是管理员，获取用户特定权限
    await fetchUserPermissions(row.id)
    // 启用树形控件
    menuTreeRef.value.disabled = false
  }
}

// 监听 checkedKeys 变化
const handleCheck = (data, { checkedKeys: keys }) => {
  // 如果是管理员用户，不允许修改
  if (selectedUser.value?.is_admin) {
    return
  }
  checkedKeys.value = keys
}

// 获取所有父级菜单ID
const getAllParentIds = (tree, targetId) => {
  const parentIds = []
  
  const findParent = (nodes, targetId, parentId = null) => {
    for (const node of nodes) {
      if (node.id === targetId) {
        if (parentId) {
          parentIds.push(parentId)
        }
        return true
      }
      if (node.children && node.children.length) {
        if (findParent(node.children, targetId, node.id)) {
          if (parentId) {
            parentIds.push(parentId)
          }
          return true
        }
      }
    }
    return false
  }
  
  findParent(tree, targetId)
  return parentIds
}

// 保存权限
const handleSavePermissions = async () => {
  if (!selectedUser.value) {
    ElMessage.warning('请先选择用户')
    return
  }
  
  // 如果是管理员用户，不允许修改
  if (selectedUser.value.is_admin) {
    ElMessage.warning('管理员权限不可修改')
    return
  }
  
  try {
    // 获取选中的菜单ID
    const selectedKeys = menuTreeRef.value.getCheckedKeys()
    
    // 获取所有父级菜单ID
    const allParentIds = []
    selectedKeys.forEach(menuId => {
      const parentIds = getAllParentIds(menuTree.value, menuId)
      allParentIds.push(...parentIds)
    })
    
    // 合并选中的菜单ID和父级菜单ID，并去重
    const allMenuIds = [...new Set([...selectedKeys, ...allParentIds])]
    
    // 保存权限
    await permissionApi.updateUserPermissions(selectedUser.value.id, allMenuIds)
    ElMessage.success('权限保存成功')
  } catch (error) {
    ElMessage.error('权限保存失败')
  }
}

onMounted(() => {
  fetchUsers()
  fetchMenuTree()
})
</script>

<style scoped>
.permission-container { 
  padding: 20px; 
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 15px;
}

.tree-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 15px;
  padding: 0 4px;
}

.divider-col {
  display: flex;
  justify-content: center;
  align-items: center;
}

.vertical-divider {
  width: 1px;
  height: 100%;
  background-color: #dcdfe6;
  margin: 0 10px;
}

.menu-tree {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

:deep(.el-table) {
  border-radius: 4px;
  overflow: hidden;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-table__row.current-row) {
  background-color: #ecf5ff;
}

.save-button {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.save-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.save-button .el-icon {
  margin-right: 4px;
}
</style>