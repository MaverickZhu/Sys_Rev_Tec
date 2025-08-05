<template>
  <div class="permission-test">
    <div class="test-card">
      <h2>权限API测试</h2>
      
      <div class="test-section">
        <h3>API连接测试</h3>
        <el-button @click="testConnection" type="primary" :loading="loading.connection">
          测试连接
        </el-button>
        <p v-if="results.connection" :class="results.connection.success ? 'success' : 'error'">
          {{ results.connection.message }}
        </p>
      </div>
      
      <div class="test-section">
        <h3>登录测试</h3>
        <el-button @click="testLogin" type="success" :loading="loading.login">
          测试登录 (admin/admin123)
        </el-button>
        <p v-if="results.login" :class="results.login.success ? 'success' : 'error'">
          {{ results.login.message }}
        </p>
      </div>
      
      <div class="test-section">
        <h3>权限API测试</h3>
        <el-button @click="testPermissionAPI" type="warning" :loading="loading.permission" :disabled="!isLoggedIn">
          测试权限API
        </el-button>
        <p v-if="results.permission" :class="results.permission.success ? 'success' : 'error'">
          {{ results.permission.message }}
        </p>
        <div v-if="permissionData" class="permission-data">
          <h4>权限数据:</h4>
          <pre>{{ JSON.stringify(permissionData, null, 2) }}</pre>
        </div>
      </div>
      
      <div class="test-section">
        <h3>直接API调用测试</h3>
        <el-input v-model="testUserId" placeholder="输入用户ID" style="width: 200px; margin-right: 10px;"></el-input>
        <el-button @click="testDirectAPI" type="info" :loading="loading.direct">
          直接调用API
        </el-button>
        <p v-if="results.direct" :class="results.direct.success ? 'success' : 'error'">
          {{ results.direct.message }}
        </p>
        <div v-if="directData" class="permission-data">
          <h4>直接API数据:</h4>
          <pre>{{ JSON.stringify(directData, null, 2) }}</pre>
        </div>
      </div>
      
      <div class="test-section">
        <h3>当前状态</h3>
        <p><strong>登录状态:</strong> {{ isLoggedIn ? '已登录' : '未登录' }}</p>
        <p><strong>Token:</strong> {{ token ? '存在' : '不存在' }}</p>
        <p><strong>用户信息:</strong> {{ userInfo ? userInfo.username : '无' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const testUserId = ref('1')

const loading = ref({
  connection: false,
  login: false,
  permission: false,
  direct: false
})

const results = ref({
  connection: null,
  login: null,
  permission: null,
  direct: null
})

const permissionData = ref(null)
const directData = ref(null)

const isLoggedIn = computed(() => userStore.isLoggedIn)
const token = computed(() => userStore.token)
const userInfo = computed(() => userStore.userInfo)

const testConnection = async () => {
  loading.value.connection = true
  try {
    const response = await fetch('http://127.0.0.1:8001/api/v1/health')
    if (response.ok) {
      const data = await response.json()
      results.value.connection = {
        success: true,
        message: `连接成功: ${data.status || 'OK'}`
      }
    } else {
      results.value.connection = {
        success: false,
        message: `连接失败: ${response.status}`
      }
    }
  } catch (error) {
    results.value.connection = {
      success: false,
      message: `连接错误: ${error.message}`
    }
  } finally {
    loading.value.connection = false
  }
}

const testLogin = async () => {
  loading.value.login = true
  try {
    await userStore.login({
      username: 'admin',
      password: 'admin123'
    })
    results.value.login = {
      success: true,
      message: '登录成功'
    }
    ElMessage.success('登录成功')
  } catch (error) {
    results.value.login = {
      success: false,
      message: `登录失败: ${error.message}`
    }
    ElMessage.error('登录失败: ' + error.message)
  } finally {
    loading.value.login = false
  }
}

const testPermissionAPI = async () => {
  loading.value.permission = true
  try {
    if (!userStore.userInfo?.id) {
      throw new Error('用户信息不存在')
    }
    
    const response = await fetch(`http://127.0.0.1:8001/api/v1/permissions/users/${userStore.userInfo.id}/permissions`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      permissionData.value = data
      results.value.permission = {
        success: true,
        message: '权限API调用成功'
      }
    } else {
      const errorData = await response.json().catch(() => ({}))
      results.value.permission = {
        success: false,
        message: `API调用失败: ${response.status} - ${errorData.detail || response.statusText}`
      }
    }
  } catch (error) {
    results.value.permission = {
      success: false,
      message: `权限API错误: ${error.message}`
    }
  } finally {
    loading.value.permission = false
  }
}

const testDirectAPI = async () => {
  loading.value.direct = true
  try {
    const response = await fetch(`http://127.0.0.1:8001/api/v1/permissions/users/${testUserId.value}/permissions`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      directData.value = data
      results.value.direct = {
        success: true,
        message: '直接API调用成功'
      }
    } else {
      const errorData = await response.json().catch(() => ({}))
      results.value.direct = {
        success: false,
        message: `直接API调用失败: ${response.status} - ${errorData.detail || response.statusText}`
      }
    }
  } catch (error) {
    results.value.direct = {
      success: false,
      message: `直接API错误: ${error.message}`
    }
  } finally {
    loading.value.direct = false
  }
}
</script>

<style scoped>
.permission-test {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.test-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.test-section h3 {
  margin-top: 0;
  color: #409EFF;
  margin-bottom: 15px;
}

.test-section p {
  margin: 10px 0;
}

.success {
  color: #67C23A;
  font-weight: bold;
}

.error {
  color: #F56C6C;
  font-weight: bold;
}

.permission-data {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
}

.permission-data h4 {
  margin-top: 0;
  color: #606266;
}

pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}
</style>