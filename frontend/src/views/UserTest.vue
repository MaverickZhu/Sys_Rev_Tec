<template>
  <div class="user-test">
    <h1>用户管理测试页面</h1>
    <div v-if="loading">加载中...</div>
    <div v-else>
      <h2>用户列表 (共 {{ users.length }} 个用户)</h2>
      <div v-for="user in users" :key="user.id" class="user-card">
        <h3>{{ user.full_name }} ({{ user.username }})</h3>
        <p>邮箱: {{ user.email }}</p>
        <p>部门: {{ user.department }}</p>
        <p>职位: {{ user.position }}</p>
        <p>电话: {{ user.phone }}</p>
        <p>状态: <span :class="user.is_active ? 'active' : 'inactive'">{{ user.is_active ? '活跃' : '禁用' }}</span></p>
        <p>管理员: {{ user.is_superuser ? '是' : '否' }}</p>
        <p>最后登录: {{ user.last_login }}</p>
      </div>
    </div>
    <div v-if="error" class="error">
      错误: {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userAPI } from '@/api'

const loading = ref(false)
const users = ref([])
const error = ref('')

const fetchUsers = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await userAPI.getUsers()
    console.log('API响应:', response)
    users.value = response.users || response || []
  } catch (err) {
    console.error('获取用户失败:', err)
    error.value = err.message || '获取用户失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.user-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
  background: #f9f9f9;
}

.user-card h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.user-card p {
  margin: 5px 0;
  color: #666;
}

.active {
  color: green;
  font-weight: bold;
}

.inactive {
  color: red;
  font-weight: bold;
}

.error {
  color: red;
  font-weight: bold;
  padding: 10px;
  background: #ffe6e6;
  border: 1px solid #ff9999;
  border-radius: 4px;
  margin: 10px 0;
}
</style>