<template>
  <div class="auth-test">
    <div class="test-card">
      <h2>认证状态测试</h2>
      
      <div class="test-section">
        <h3>登录状态</h3>
        <p><strong>是否已登录:</strong> {{ userStore.isLoggedIn ? '是' : '否' }}</p>
        <p><strong>Token:</strong> {{ userStore.token ? '存在' : '不存在' }}</p>
      </div>
      
      <div class="test-section">
        <h3>用户信息</h3>
        <p><strong>用户名:</strong> {{ userStore.userInfo?.username || '未获取' }}</p>
        <p><strong>邮箱:</strong> {{ userStore.userInfo?.email || '未获取' }}</p>
        <p><strong>角色:</strong> {{ userStore.userRole || '未获取' }}</p>
      </div>
      
      <div class="test-section">
        <h3>权限信息</h3>
        <p><strong>权限数量:</strong> {{ userStore.permissions.length }}</p>
        <p><strong>角色数量:</strong> {{ userStore.roles.length }}</p>
        <p><strong>是否管理员:</strong> {{ userStore.isAdmin ? '是' : '否' }}</p>
      </div>
      
      <div class="test-section">
        <h3>用户管理权限检查</h3>
        <p><strong>USER_READ:</strong> {{ userStore.hasPermission('USER_READ') ? '有' : '无' }}</p>
        <p><strong>USER_MANAGE:</strong> {{ userStore.hasPermission('USER_MANAGE') ? '有' : '无' }}</p>
        <p><strong>任一权限:</strong> {{ userStore.hasAnyPermission(['USER_READ', 'USER_MANAGE']) ? '有' : '无' }}</p>
      </div>
      
      <div class="test-section">
        <h3>操作</h3>
        <el-button @click="testLogin" type="primary">测试登录</el-button>
        <el-button @click="loadPermissions" type="success">重新加载权限</el-button>
        <el-button @click="goToUsers" type="warning">跳转用户管理</el-button>
      </div>
      
      <div class="test-section">
        <h3>详细数据</h3>
        <el-collapse>
          <el-collapse-item title="用户信息详情">
            <pre>{{ JSON.stringify(userStore.userInfo, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="权限列表">
            <pre>{{ JSON.stringify(userStore.permissions, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="角色列表">
            <pre>{{ JSON.stringify(userStore.roles, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()

const testLogin = async () => {
  try {
    // 使用测试账户登录
    await userStore.login({
      username: 'admin',
      password: 'admin123'
    })
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error('登录失败: ' + error.message)
  }
}

const loadPermissions = async () => {
  try {
    await userStore.loadUserPermissions()
    ElMessage.success('权限加载成功')
  } catch (error) {
    ElMessage.error('权限加载失败: ' + error.message)
  }
}

const goToUsers = () => {
  router.push('/users')
}
</script>

<style scoped>
.auth-test {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.test-section {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.test-section h3 {
  margin-top: 0;
  color: #409EFF;
}

.test-section p {
  margin: 8px 0;
}

pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>