<template>
  <div class="permission-management">
    <div class="page-header">
      <h1>权限管理</h1>
      <p>管理用户角色和权限分配</p>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- 角色管理 -->
      <el-tab-pane label="角色管理" name="roles">
        <div class="content-card">
          <div class="toolbar">
            <el-button type="primary" @click="showRoleDialog = true">
              <el-icon><Plus /></el-icon>
              添加角色
            </el-button>
          </div>

          <el-table :data="roles" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="角色名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="permissions" label="权限数量">
              <template #default="{ row }">
                <el-tag>{{ row.permissions?.length || 0 }} 个权限</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_count" label="用户数量" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="editRole(row)">编辑</el-button>
                <el-button size="small" @click="managePermissions(row)">权限</el-button>
                <el-button size="small" type="danger" @click="deleteRole(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 权限列表 -->
      <el-tab-pane label="权限列表" name="permissions">
        <div class="content-card">
          <el-table :data="permissions" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="权限名称" />
            <el-table-column prop="codename" label="权限代码" />
            <el-table-column prop="module" label="模块" />
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 用户权限 -->
      <el-tab-pane label="用户权限" name="user-permissions">
        <div class="content-card">
          <div class="toolbar">
            <el-select v-model="selectedUser" placeholder="选择用户" style="width: 200px" @change="fetchUserPermissions">
              <el-option
                v-for="user in users"
                :key="user.id"
                :label="user.username"
                :value="user.id"
              />
            </el-select>
            <el-button type="primary" @click="saveUserPermissions" :disabled="!selectedUser">
              保存权限
            </el-button>
          </div>

          <div v-if="selectedUser" class="permission-tree">
            <h3>为用户分配权限</h3>
            <el-tree
              ref="permissionTree"
              :data="permissionTreeData"
              :props="treeProps"
              show-checkbox
              node-key="id"
              :default-checked-keys="userPermissions"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 角色对话框 -->
    <el-dialog v-model="showRoleDialog" :title="editingRole ? '编辑角色' : '添加角色'" width="500px">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限分配对话框 -->
    <el-dialog v-model="showPermissionDialog" title="权限分配" width="600px">
      <div v-if="currentRole">
        <h3>为角色 "{{ currentRole.name }}" 分配权限</h3>
        <el-tree
          ref="rolePermissionTree"
          :data="permissionTreeData"
          :props="treeProps"
          show-checkbox
          node-key="id"
          :default-checked-keys="currentRole.permissions || []"
        />
      </div>
      <template #footer>
        <el-button @click="showPermissionDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRolePermissions">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { permissionAPI, userAPI } from '@/api'

// 响应式数据
const loading = ref(false)
const activeTab = ref('roles')
const roles = ref([])
const permissions = ref([])
const users = ref([])
const selectedUser = ref(null)
const userPermissions = ref([])
const showRoleDialog = ref(false)
const showPermissionDialog = ref(false)
const editingRole = ref(null)
const currentRole = ref(null)
const permissionTree = ref(null)
const rolePermissionTree = ref(null)

const roleForm = ref({
  name: '',
  description: ''
})

// 树形结构配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 权限树形数据
const permissionTreeData = ref([])

// 模拟数据
const mockRoles = [
  {
    id: 1,
    name: '超级管理员',
    description: '拥有所有权限',
    permissions: [1, 2, 3, 4, 5, 6, 7, 8],
    user_count: 1
  },
  {
    id: 2,
    name: '管理员',
    description: '拥有大部分管理权限',
    permissions: [1, 2, 3, 4, 5, 6],
    user_count: 3
  },
  {
    id: 3,
    name: '普通用户',
    description: '基础用户权限',
    permissions: [1, 2],
    user_count: 15
  }
]

const mockPermissions = [
  { id: 1, name: '查看仪表板', codename: 'view_dashboard', module: '仪表板', description: '查看系统仪表板' },
  { id: 2, name: '查看项目', codename: 'view_project', module: '项目管理', description: '查看项目列表' },
  { id: 3, name: '创建项目', codename: 'create_project', module: '项目管理', description: '创建新项目' },
  { id: 4, name: '编辑项目', codename: 'edit_project', module: '项目管理', description: '编辑项目信息' },
  { id: 5, name: '删除项目', codename: 'delete_project', module: '项目管理', description: '删除项目' },
  { id: 6, name: '用户管理', codename: 'manage_users', module: '用户管理', description: '管理系统用户' },
  { id: 7, name: '权限管理', codename: 'manage_permissions', module: '权限管理', description: '管理用户权限' },
  { id: 8, name: '系统维护', codename: 'system_maintenance', module: '系统维护', description: '系统维护操作' }
]

const mockUsers = [
  { id: 1, username: 'admin', email: 'admin@example.com' },
  { id: 2, username: 'user1', email: 'user1@example.com' },
  { id: 3, username: 'user2', email: 'user2@example.com' }
]

// 方法
const fetchRoles = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    roles.value = mockRoles
  } catch (error) {
    ElMessage.error('获取角色列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const fetchPermissions = async () => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    permissions.value = mockPermissions
    
    // 构建权限树形结构
    const modules = {}
    mockPermissions.forEach(permission => {
      if (!modules[permission.module]) {
        modules[permission.module] = {
          id: `module_${permission.module}`,
          name: permission.module,
          children: []
        }
      }
      modules[permission.module].children.push({
        id: permission.id,
        name: permission.name,
        codename: permission.codename
      })
    })
    
    permissionTreeData.value = Object.values(modules)
  } catch (error) {
    ElMessage.error('获取权限列表失败: ' + error.message)
  }
}

const fetchUsers = async () => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    users.value = mockUsers
  } catch (error) {
    ElMessage.error('获取用户列表失败: ' + error.message)
  }
}

const fetchUserPermissions = async () => {
  if (!selectedUser.value) return
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    // 模拟用户权限
    userPermissions.value = [1, 2, 3]
  } catch (error) {
    ElMessage.error('获取用户权限失败: ' + error.message)
  }
}

const editRole = (role) => {
  editingRole.value = role
  roleForm.value = { ...role }
  showRoleDialog.value = true
}

const saveRole = async () => {
  try {
    if (editingRole.value) {
      // 更新角色
      const index = roles.value.findIndex(r => r.id === editingRole.value.id)
      if (index > -1) {
        roles.value[index] = { ...roles.value[index], ...roleForm.value }
      }
      ElMessage.success('角色更新成功')
    } else {
      // 创建角色
      const newRole = {
        id: roles.value.length + 1,
        ...roleForm.value,
        permissions: [],
        user_count: 0
      }
      roles.value.push(newRole)
      ElMessage.success('角色创建成功')
    }
    
    showRoleDialog.value = false
    editingRole.value = null
    roleForm.value = { name: '', description: '' }
  } catch (error) {
    ElMessage.error('保存角色失败: ' + error.message)
  }
}

const deleteRole = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const index = roles.value.findIndex(r => r.id === role.id)
    if (index > -1) {
      roles.value.splice(index, 1)
      ElMessage.success('角色删除成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败: ' + error.message)
    }
  }
}

const managePermissions = (role) => {
  currentRole.value = role
  showPermissionDialog.value = true
}

const saveRolePermissions = async () => {
  try {
    const checkedKeys = rolePermissionTree.value.getCheckedKeys()
    const leafKeys = checkedKeys.filter(key => typeof key === 'number')
    
    currentRole.value.permissions = leafKeys
    ElMessage.success('权限分配成功')
    showPermissionDialog.value = false
  } catch (error) {
    ElMessage.error('保存权限失败: ' + error.message)
  }
}

const saveUserPermissions = async () => {
  try {
    const checkedKeys = permissionTree.value.getCheckedKeys()
    const leafKeys = checkedKeys.filter(key => typeof key === 'number')
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('用户权限保存成功')
  } catch (error) {
    ElMessage.error('保存用户权限失败: ' + error.message)
  }
}

// 生命周期
onMounted(() => {
  fetchRoles()
  fetchPermissions()
  fetchUsers()
})
</script>

<style scoped>
.permission-management {
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

.permission-tree {
  margin-top: 20px;
}

.permission-tree h3 {
  margin-bottom: 15px;
  color: #303133;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 10px;
  }
}
</style>