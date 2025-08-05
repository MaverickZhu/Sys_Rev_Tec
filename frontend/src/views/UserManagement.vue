<template>
  <div class="user-management">
    <div class="page-header">
      <h1>用户管理</h1>
      <p>管理系统用户账户和权限</p>
    </div>

    <div class="content-card">
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户..."
          style="width: 300px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 权限不足提示 -->
      <div v-if="!loading && users.length === 0 && hasPermissionError" class="permission-error">
        <el-empty description="权限不足">
          <template #image>
            <el-icon size="100" color="#909399">
              <Lock />
            </el-icon>
          </template>
          <template #description>
            <p>您没有权限查看用户列表</p>
            <p>需要超级管理员权限才能访问此功能</p>
          </template>
          <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
        </el-empty>
      </div>

      <!-- 用户表格 -->
      <el-table v-else :data="filteredUsers" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingUser ? '编辑用户' : '添加用户'"
      width="500px"
    >
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Lock } from '@element-plus/icons-vue'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const users = ref([])
const searchQuery = ref('')
const showAddDialog = ref(false)
const editingUser = ref(null)
const hasPermissionError = ref(false)
const userForm = ref({
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true
})

// 计算属性
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  return users.value.filter(user => 
    user.username.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 方法
const getRoleType = (role) => {
  const types = {
    'super_admin': 'danger',
    'admin': 'warning',
    'user': 'info'
  }
  return types[role] || 'info'
}

const getRoleLabel = (role) => {
  const labels = {
    'super_admin': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
  }
  return labels[role] || '未知'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const data = await userAPI.getUsers()
    users.value = data.users || data || []
    console.log('用户数据:', data)
  } catch (error) {
    console.error('获取用户列表错误:', error)
    if (error.message.includes('403') || error.message.includes('权限')) {
      ElMessage.error('权限不足：需要超级管理员权限才能查看用户列表')
      hasPermissionError.value = true
    } else {
      ElMessage.error('获取用户列表失败: ' + error.message)
    }
    users.value = []
  } finally {
    loading.value = false
  }
}

const editUser = (user) => {
  editingUser.value = user
  userForm.value = { ...user }
  showAddDialog.value = true
}

const saveUser = async () => {
  try {
    if (editingUser.value) {
      await userAPI.updateUser(editingUser.value.id, userForm.value)
      ElMessage.success('用户更新成功')
    } else {
      await userAPI.createUser(userForm.value)
      ElMessage.success('用户创建成功')
    }
    
    showAddDialog.value = false
    editingUser.value = null
    userForm.value = {
      username: '',
      email: '',
      password: '',
      role: 'user',
      is_active: true
    }
    
    await fetchUsers()
  } catch (error) {
    ElMessage.error('保存用户失败: ' + error.message)
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userAPI.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除用户失败: ' + error.message)
    }
  }
}

// 生命周期
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
}

.content-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 10px;
  }
}

.permission-error {
  padding: 40px 20px;
  text-align: center;
}

.permission-error .el-empty__description p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}
</style>