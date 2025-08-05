<template>
  <div class="user-management-test">
    <div class="page-header">
      <h1>用户管理测试页面</h1>
      <p>测试权限错误提示功能</p>
    </div>

    <div class="content-card">
      <div class="test-buttons">
        <el-button type="primary" @click="testPermissionError">模拟权限错误</el-button>
        <el-button type="success" @click="testNormalLoad">模拟正常加载</el-button>
        <el-button @click="resetTest">重置测试</el-button>
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

      <!-- 加载状态 -->
      <div v-else-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 用户表格 -->
      <el-table v-else :data="users" style="width: 100%">
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
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const users = ref([])
const hasPermissionError = ref(false)

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

const testPermissionError = () => {
  loading.value = true
  hasPermissionError.value = false
  users.value = []
  
  setTimeout(() => {
    loading.value = false
    hasPermissionError.value = true
    ElMessage.error('权限不足：需要超级管理员权限才能查看用户列表')
  }, 1000)
}

const testNormalLoad = () => {
  loading.value = true
  hasPermissionError.value = false
  
  setTimeout(() => {
    loading.value = false
    users.value = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        role: 'super_admin',
        is_active: true
      },
      {
        id: 2,
        username: 'user1',
        email: 'user1@example.com', 
        role: 'user',
        is_active: true
      }
    ]
    ElMessage.success('用户列表加载成功')
  }, 1000)
}

const resetTest = () => {
  loading.value = false
  hasPermissionError.value = false
  users.value = []
}
</script>

<style scoped>
.user-management-test {
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

.test-buttons {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
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

.loading-state {
  padding: 20px;
}
</style>