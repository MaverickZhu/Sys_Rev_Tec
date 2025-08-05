<template>
  <div class="security-monitoring">
    <div class="page-header">
      <h1>安全监控</h1>
      <p>实时监控系统安全状态和威胁</p>
    </div>

    <!-- 安全概览 -->
    <div class="security-overview">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card threat">
            <div class="stat-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ securityStats.threats }}</div>
              <div class="stat-label">威胁检测</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card login">
            <div class="stat-icon">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ securityStats.failedLogins }}</div>
              <div class="stat-label">登录失败</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card blocked">
            <div class="stat-icon">
              <el-icon><Lock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ securityStats.blockedIPs }}</div>
              <div class="stat-label">IP封禁</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card alerts">
            <div class="stat-icon">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ securityStats.alerts }}</div>
              <div class="stat-label">安全警报</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-row :gutter="20">
      <!-- 实时威胁监控 -->
      <el-col :xs="24" :lg="12">
        <div class="content-card">
          <div class="card-header">
            <h3>实时威胁监控</h3>
            <el-button size="small" @click="refreshThreats">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div class="threat-list">
            <div v-for="threat in threats" :key="threat.id" class="threat-item">
              <div class="threat-severity" :class="threat.severity">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="threat-content">
                <div class="threat-title">{{ threat.title }}</div>
                <div class="threat-description">{{ threat.description }}</div>
                <div class="threat-time">{{ threat.timestamp }}</div>
              </div>
              <div class="threat-actions">
                <el-button size="small" type="primary" @click="handleThreat(threat)">
                  处理
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 登录监控 -->
      <el-col :xs="24" :lg="12">
        <div class="content-card">
          <div class="card-header">
            <h3>登录监控</h3>
            <el-select v-model="loginFilter" size="small" style="width: 120px">
              <el-option label="全部" value="all" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
          </div>
          
          <div class="login-list">
            <div v-for="login in filteredLogins" :key="login.id" class="login-item">
              <div class="login-status" :class="login.status">
                <el-icon v-if="login.status === 'success'"><Check /></el-icon>
                <el-icon v-else><Close /></el-icon>
              </div>
              <div class="login-content">
                <div class="login-user">{{ login.username }}</div>
                <div class="login-ip">{{ login.ip_address }}</div>
                <div class="login-time">{{ login.timestamp }}</div>
              </div>
              <div class="login-actions" v-if="login.status === 'failed'">
                <el-button size="small" type="danger" @click="blockIP(login.ip_address)">
                  封禁IP
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 安全事件日志 -->
    <div class="content-card">
      <div class="card-header">
        <h3>安全事件日志</h3>
        <div class="header-actions">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
          />
          <el-button size="small" @click="exportLogs">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>
      
      <el-table :data="securityLogs" style="width: 100%" v-loading="loading">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="event_type" label="事件类型">
          <template #default="{ row }">
            <el-tag :type="getEventTypeColor(row.event_type)">{{ row.event_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度">
          <template #default="{ row }">
            <el-tag :type="getSeverityColor(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_ip" label="来源IP" />
        <el-table-column prop="user" label="用户" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="viewLogDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="showLogDetail" title="安全事件详情" width="600px">
      <div v-if="selectedLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">{{ selectedLog.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="事件类型">{{ selectedLog.event_type }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ selectedLog.severity }}</el-descriptions-item>
          <el-descriptions-item label="来源IP">{{ selectedLog.source_ip }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ selectedLog.user || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="用户代理">{{ selectedLog.user_agent || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedLog.description }}</el-descriptions-item>
          <el-descriptions-item label="详细信息" :span="2">
            <pre>{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Warning, User, Lock, Bell, Refresh, Check, Close, Download
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const loginFilter = ref('all')
const dateRange = ref([])
const showLogDetail = ref(false)
const selectedLog = ref(null)

const securityStats = ref({
  threats: 3,
  failedLogins: 12,
  blockedIPs: 5,
  alerts: 8
})

const threats = ref([
  {
    id: 1,
    title: 'SQL注入尝试',
    description: '检测到来自IP 192.168.1.100的SQL注入攻击尝试',
    severity: 'high',
    timestamp: '2025-07-29 14:30:25'
  },
  {
    id: 2,
    title: '暴力破解攻击',
    description: '检测到来自IP 10.0.0.50的密码暴力破解攻击',
    severity: 'medium',
    timestamp: '2025-07-29 14:25:10'
  },
  {
    id: 3,
    title: '异常访问模式',
    description: '用户admin在短时间内进行了大量API调用',
    severity: 'low',
    timestamp: '2025-07-29 14:20:05'
  }
])

const logins = ref([
  {
    id: 1,
    username: 'admin',
    ip_address: '192.168.1.10',
    status: 'success',
    timestamp: '2025-07-29 14:35:00'
  },
  {
    id: 2,
    username: 'hacker',
    ip_address: '192.168.1.100',
    status: 'failed',
    timestamp: '2025-07-29 14:30:25'
  },
  {
    id: 3,
    username: 'user1',
    ip_address: '192.168.1.20',
    status: 'success',
    timestamp: '2025-07-29 14:28:15'
  },
  {
    id: 4,
    username: 'admin',
    ip_address: '10.0.0.50',
    status: 'failed',
    timestamp: '2025-07-29 14:25:10'
  }
])

const securityLogs = ref([
  {
    id: 1,
    timestamp: '2025-07-29 14:30:25',
    event_type: 'SQL注入',
    severity: '高',
    source_ip: '192.168.1.100',
    user: null,
    description: 'SQL注入攻击尝试被阻止',
    user_agent: 'Mozilla/5.0...',
    details: { query: 'SELECT * FROM users WHERE id=1 OR 1=1', blocked: true }
  },
  {
    id: 2,
    timestamp: '2025-07-29 14:25:10',
    event_type: '暴力破解',
    severity: '中',
    source_ip: '10.0.0.50',
    user: 'admin',
    description: '密码暴力破解攻击',
    user_agent: 'curl/7.68.0',
    details: { attempts: 15, duration: '5分钟' }
  },
  {
    id: 3,
    timestamp: '2025-07-29 14:20:05',
    event_type: '异常访问',
    severity: '低',
    source_ip: '192.168.1.10',
    user: 'admin',
    description: '短时间内大量API调用',
    user_agent: 'PostmanRuntime/7.28.4',
    details: { requests: 100, timeframe: '1分钟' }
  }
])

// 计算属性
const filteredLogins = computed(() => {
  if (loginFilter.value === 'all') return logins.value
  return logins.value.filter(login => login.status === loginFilter.value)
})

// 方法
const getEventTypeColor = (type) => {
  const colors = {
    'SQL注入': 'danger',
    '暴力破解': 'warning',
    '异常访问': 'info'
  }
  return colors[type] || 'info'
}

const getSeverityColor = (severity) => {
  const colors = {
    '高': 'danger',
    '中': 'warning',
    '低': 'info'
  }
  return colors[severity] || 'info'
}

const refreshThreats = async () => {
  ElMessage.info('刷新威胁数据...')
  // 模拟刷新
  await new Promise(resolve => setTimeout(resolve, 1000))
  ElMessage.success('威胁数据已更新')
}

const handleThreat = async (threat) => {
  try {
    await ElMessageBox.confirm(
      `确定要处理威胁 "${threat.title}" 吗？`,
      '确认处理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 移除威胁
    const index = threats.value.findIndex(t => t.id === threat.id)
    if (index > -1) {
      threats.value.splice(index, 1)
      securityStats.value.threats--
      ElMessage.success('威胁已处理')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('处理威胁失败: ' + error.message)
    }
  }
}

const blockIP = async (ip) => {
  try {
    await ElMessageBox.confirm(
      `确定要封禁IP地址 "${ip}" 吗？`,
      '确认封禁',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    securityStats.value.blockedIPs++
    ElMessage.success(`IP地址 ${ip} 已被封禁`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('封禁IP失败: ' + error.message)
    }
  }
}

const viewLogDetail = (log) => {
  selectedLog.value = log
  showLogDetail.value = true
}

const exportLogs = () => {
  ElMessage.success('安全日志导出已开始')
  // 这里应该实现实际的导出逻辑
}

// 生命周期
onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.security-monitoring {
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

.security-overview {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.stat-card.threat .stat-icon {
  background: #f56c6c;
}

.stat-card.login .stat-icon {
  background: #e6a23c;
}

.stat-card.blocked .stat-icon {
  background: #909399;
}

.stat-card.alerts .stat-icon {
  background: #409eff;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.content-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.threat-list, .login-list {
  max-height: 400px;
  overflow-y: auto;
}

.threat-item, .login-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 10px;
}

.threat-severity, .login-status {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: white;
}

.threat-severity.high {
  background: #f56c6c;
}

.threat-severity.medium {
  background: #e6a23c;
}

.threat-severity.low {
  background: #67c23a;
}

.login-status.success {
  background: #67c23a;
}

.login-status.failed {
  background: #f56c6c;
}

.threat-content, .login-content {
  flex: 1;
}

.threat-title, .login-user {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.threat-description, .login-ip {
  color: #606266;
  margin-bottom: 5px;
}

.threat-time, .login-time {
  color: #909399;
  font-size: 12px;
}

.threat-actions, .login-actions {
  margin-left: 15px;
}

pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .threat-item, .login-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .threat-severity, .login-status {
    margin-bottom: 10px;
  }
}
</style>