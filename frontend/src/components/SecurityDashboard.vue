<template>
  <div class="security-dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>安全监控仪表板</h1>
      <p>实时监控系统安全状态和威胁情况</p>
      <div class="header-actions">
        <el-button @click="refreshDashboard">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="runThreatDetection">
          <el-icon><Search /></el-icon>
          威胁扫描
        </el-button>
      </div>
    </div>

    <!-- 安全概览卡片 -->
    <div class="security-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon security-level">
                <el-icon><Shield /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value" :class="getSecurityLevelClass(dashboardData.security_level)">
                  {{ getSecurityLevelText(dashboardData.security_level) }}
                </div>
                <div class="metric-label">安全等级</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon active-threats">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ dashboardData.active_threats || 0 }}</div>
                <div class="metric-label">活跃威胁</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon failed-logins">
                <el-icon><Lock /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ dashboardData.failed_logins_24h || 0 }}</div>
                <div class="metric-label">24小时失败登录</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon system-health">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value" :class="getHealthStatusClass(dashboardData.system_health)">
                  {{ getHealthStatusText(dashboardData.system_health) }}
                </div>
                <div class="metric-label">系统健康</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧列 -->
      <el-col :span="16">
        <!-- 安全趋势图表 -->
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>安全趋势</span>
              <el-select v-model="trendPeriod" size="small" style="width: 120px">
                <el-option label="24小时" value="24h" />
                <el-option label="7天" value="7d" />
                <el-option label="30天" value="30d" />
              </el-select>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>

        <!-- 威胁检测结果 -->
        <el-card class="threat-results">
          <template #header>
            <div class="card-header">
              <span>威胁检测结果</span>
              <el-tag v-if="threatDetectionRunning" type="warning">
                <el-icon class="is-loading"><Loading /></el-icon>
                扫描中...
              </el-tag>
            </div>
          </template>
          <div v-if="threatResults.length > 0">
            <el-table :data="threatResults" stripe>
              <el-table-column prop="threat_type" label="威胁类型" width="150">
                <template #default="scope">
                  <el-tag :type="getThreatTypeColor(scope.row.threat_type)">
                    {{ getThreatTypeName(scope.row.threat_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="level" label="威胁等级" width="100">
                <template #default="scope">
                  <el-tag :type="getThreatLevelColor(scope.row.level)">
                    {{ scope.row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" />
              <el-table-column prop="affected_count" label="影响数量" width="100" />
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button size="small" @click="viewThreatDetail(scope.row)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else class="no-threats">
            <el-empty description="暂无威胁检测结果" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧列 -->
      <el-col :span="8">
        <!-- 安全警报 -->
        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <span>安全警报</span>
              <el-badge :value="securityAlerts.length" class="alert-badge" />
            </div>
          </template>
          <div class="alerts-list">
            <div 
              v-for="alert in securityAlerts" 
              :key="alert.id" 
              class="alert-item"
              :class="`alert-${alert.level.toLowerCase()}`"
            >
              <div class="alert-header">
                <el-icon class="alert-icon">
                  <Warning v-if="alert.level === 'HIGH'" />
                  <InfoFilled v-else-if="alert.level === 'MEDIUM'" />
                  <CircleCheck v-else />
                </el-icon>
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
              </div>
              <div class="alert-description">{{ alert.description }}</div>
              <div class="alert-actions">
                <el-button size="small" text @click="resolveAlert(alert)">
                  处理
                </el-button>
                <el-button size="small" text @click="viewAlertDetail(alert)">
                  详情
                </el-button>
              </div>
            </div>
          </div>
          <div v-if="securityAlerts.length === 0" class="no-alerts">
            <el-empty description="暂无安全警报" />
          </div>
        </el-card>

        <!-- 用户活动统计 -->
        <el-card class="activity-card">
          <template #header>
            <span>用户活动统计</span>
          </template>
          <div class="activity-stats">
            <div class="stat-item">
              <div class="stat-label">在线用户</div>
              <div class="stat-value">{{ userActivity.online_users || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">今日登录</div>
              <div class="stat-value">{{ userActivity.daily_logins || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">活跃会话</div>
              <div class="stat-value">{{ userActivity.active_sessions || 0 }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">异常活动</div>
              <div class="stat-value text-danger">{{ userActivity.suspicious_activities || 0 }}</div>
            </div>
          </div>
        </el-card>

        <!-- 系统状态 -->
        <el-card class="system-status-card">
          <template #header>
            <span>系统状态</span>
          </template>
          <div class="system-status">
            <div class="status-item">
              <div class="status-label">CPU使用率</div>
              <el-progress 
                :percentage="systemHealth.cpu_usage || 0" 
                :color="getProgressColor(systemHealth.cpu_usage)"
              />
            </div>
            <div class="status-item">
              <div class="status-label">内存使用率</div>
              <el-progress 
                :percentage="systemHealth.memory_usage || 0" 
                :color="getProgressColor(systemHealth.memory_usage)"
              />
            </div>
            <div class="status-item">
              <div class="status-label">磁盘使用率</div>
              <el-progress 
                :percentage="systemHealth.disk_usage || 0" 
                :color="getProgressColor(systemHealth.disk_usage)"
              />
            </div>
            <div class="status-item">
              <div class="status-label">网络延迟</div>
              <div class="status-value">{{ systemHealth.network_latency || 0 }}ms</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 审计日志表格 -->
    <el-card class="audit-logs-card">
      <template #header>
        <div class="card-header">
          <span>最近审计日志</span>
          <div class="header-actions">
            <el-input
              v-model="auditSearch"
              placeholder="搜索审计日志"
              style="width: 200px; margin-right: 10px"
              size="small"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button size="small" @click="loadAuditLogs">
              刷新
            </el-button>
            <el-button size="small" @click="exportAuditLogs">
              导出
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="auditLogs" v-loading="auditLogsLoading" stripe>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="action" label="操作" width="200" />
        <el-table-column prop="resource_type" label="资源类型" width="100" />
        <el-table-column prop="source_ip" label="IP地址" width="120" />
        <el-table-column prop="status_code" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="getStatusColor(scope.row.status_code)">
              {{ scope.row.status_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="scope">
            <el-tag :type="getRiskLevelColor(scope.row.risk_score)">
              {{ getRiskLevelText(scope.row.risk_score) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" text @click="viewAuditDetail(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="auditPagination.page"
          v-model:page-size="auditPagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="auditPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleAuditSizeChange"
          @current-change="handleAuditPageChange"
        />
      </div>
    </el-card>

    <!-- 威胁详情对话框 -->
    <el-dialog v-model="threatDetailVisible" title="威胁详情" width="800px">
      <div v-if="selectedThreat">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="威胁类型">
            <el-tag :type="getThreatTypeColor(selectedThreat.threat_type)">
              {{ getThreatTypeName(selectedThreat.threat_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="威胁等级">
            <el-tag :type="getThreatLevelColor(selectedThreat.level)">
              {{ selectedThreat.level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="影响数量">
            {{ selectedThreat.affected_count }}
          </el-descriptions-item>
          <el-descriptions-item label="检测时间">
            {{ formatDateTime(selectedThreat.detected_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedThreat.description }}
          </el-descriptions-item>
          <el-descriptions-item label="建议措施" :span="2">
            {{ selectedThreat.recommendation }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedThreat.affected_items" class="affected-items">
          <h4>受影响项目</h4>
          <el-table :data="selectedThreat.affected_items" size="small">
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="identifier" label="标识" />
            <el-table-column prop="details" label="详情" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Search, Shield, Warning, Lock, Monitor,
  Loading, InfoFilled, CircleCheck
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { securityApi } from '@/api/security'
import { auditApi } from '@/api/audit'

// 响应式数据
const dashboardData = ref({})
const securityAlerts = ref([])
const userActivity = ref({})
const systemHealth = ref({})
const threatResults = ref([])
const auditLogs = ref([])

// 加载状态
const dashboardLoading = ref(false)
const threatDetectionRunning = ref(false)
const auditLogsLoading = ref(false)

// 图表相关
const trendChartRef = ref()
const trendChart = ref(null)
const trendPeriod = ref('24h')

// 搜索和分页
const auditSearch = ref('')
const auditPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框状态
const threatDetailVisible = ref(false)
const selectedThreat = ref(null)

// 自动刷新
let refreshTimer = null
const autoRefreshInterval = 30000 // 30秒

// 方法
const loadDashboardData = async () => {
  dashboardLoading.value = true
  try {
    const response = await securityApi.getDashboardData()
    dashboardData.value = response.data.dashboard_data || {}
    securityAlerts.value = response.data.security_alerts || []
    userActivity.value = response.data.user_activity || {}
    systemHealth.value = response.data.system_health || {}
    
    // 更新趋势图表
    updateTrendChart(response.data.security_trends || [])
  } catch (error) {
    ElMessage.error('加载仪表板数据失败')
  } finally {
    dashboardLoading.value = false
  }
}

const loadAuditLogs = async () => {
  auditLogsLoading.value = true
  try {
    const params = {
      page: auditPagination.page,
      size: auditPagination.size,
      search: auditSearch.value
    }
    const response = await auditApi.getAuditLogs(params)
    auditLogs.value = response.data.items || []
    auditPagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error('加载审计日志失败')
  } finally {
    auditLogsLoading.value = false
  }
}

const runThreatDetection = async () => {
  threatDetectionRunning.value = true
  try {
    const response = await securityApi.runThreatDetection()
    ElMessage.success('威胁检测已启动')
    
    // 轮询检测结果
    const checkResults = async () => {
      try {
        const resultResponse = await securityApi.getThreatDetectionResults()
        if (resultResponse.data.status === 'completed') {
          threatResults.value = resultResponse.data.threats || []
          threatDetectionRunning.value = false
          ElMessage.success(`威胁检测完成，发现 ${threatResults.value.length} 个威胁`)
        } else {
          setTimeout(checkResults, 2000) // 2秒后再次检查
        }
      } catch (error) {
        threatDetectionRunning.value = false
        ElMessage.error('获取威胁检测结果失败')
      }
    }
    
    setTimeout(checkResults, 2000)
  } catch (error) {
    threatDetectionRunning.value = false
    ElMessage.error('启动威胁检测失败')
  }
}

const refreshDashboard = () => {
  loadDashboardData()
  loadAuditLogs()
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  trendChart.value = echarts.init(trendChartRef.value)
  
  const option = {
    title: {
      text: '安全事件趋势',
      left: 'center',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['高风险', '中风险', '低风险'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '高风险',
        type: 'line',
        data: [],
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '中风险',
        type: 'line',
        data: [],
        itemStyle: { color: '#e6a23c' }
      },
      {
        name: '低风险',
        type: 'line',
        data: [],
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  
  trendChart.value.setOption(option)
}

const updateTrendChart = (trendsData) => {
  if (!trendChart.value || !trendsData.length) return
  
  const dates = trendsData.map(item => item.date)
  const highRisk = trendsData.map(item => item.high_risk_count || 0)
  const mediumRisk = trendsData.map(item => item.medium_risk_count || 0)
  const lowRisk = trendsData.map(item => item.low_risk_count || 0)
  
  trendChart.value.setOption({
    xAxis: {
      data: dates
    },
    series: [
      { data: highRisk },
      { data: mediumRisk },
      { data: lowRisk }
    ]
  })
}

// 事件处理
const handleAuditSizeChange = (size) => {
  auditPagination.size = size
  auditPagination.page = 1
  loadAuditLogs()
}

const handleAuditPageChange = (page) => {
  auditPagination.page = page
  loadAuditLogs()
}

const viewThreatDetail = (threat) => {
  selectedThreat.value = threat
  threatDetailVisible.value = true
}

const viewAlertDetail = (alert) => {
  ElMessage.info('查看警报详情功能待实现')
}

const resolveAlert = async (alert) => {
  try {
    await securityApi.resolveSecurityEvent(alert.id)
    ElMessage.success('警报已处理')
    loadDashboardData()
  } catch (error) {
    ElMessage.error('处理警报失败')
  }
}

const viewAuditDetail = (audit) => {
  ElMessage.info('查看审计详情功能待实现')
}

const exportAuditLogs = () => {
  ElMessage.info('导出审计日志功能待实现')
}

// 辅助方法
const getSecurityLevelClass = (level) => {
  const classMap = {
    'HIGH': 'text-danger',
    'MEDIUM': 'text-warning',
    'LOW': 'text-success'
  }
  return classMap[level] || ''
}

const getSecurityLevelText = (level) => {
  const textMap = {
    'HIGH': '高风险',
    'MEDIUM': '中风险',
    'LOW': '低风险'
  }
  return textMap[level] || '未知'
}

const getHealthStatusClass = (status) => {
  const classMap = {
    'HEALTHY': 'text-success',
    'WARNING': 'text-warning',
    'CRITICAL': 'text-danger'
  }
  return classMap[status] || ''
}

const getHealthStatusText = (status) => {
  const textMap = {
    'HEALTHY': '健康',
    'WARNING': '警告',
    'CRITICAL': '严重'
  }
  return textMap[status] || '未知'
}

const getThreatTypeColor = (type) => {
  const colorMap = {
    'BRUTE_FORCE': 'danger',
    'SUSPICIOUS_LOGIN': 'warning',
    'PRIVILEGE_ESCALATION': 'danger',
    'DATA_EXFILTRATION': 'danger',
    'API_ABUSE': 'warning',
    'INJECTION_ATTACK': 'danger'
  }
  return colorMap[type] || 'info'
}

const getThreatTypeName = (type) => {
  const nameMap = {
    'BRUTE_FORCE': '暴力破解',
    'SUSPICIOUS_LOGIN': '可疑登录',
    'PRIVILEGE_ESCALATION': '权限提升',
    'DATA_EXFILTRATION': '数据泄露',
    'API_ABUSE': 'API滥用',
    'INJECTION_ATTACK': '注入攻击'
  }
  return nameMap[type] || type
}

const getThreatLevelColor = (level) => {
  const colorMap = {
    'HIGH': 'danger',
    'MEDIUM': 'warning',
    'LOW': 'success'
  }
  return colorMap[level] || 'info'
}

const getStatusColor = (status) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'info'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'danger'
  return 'info'
}

const getRiskLevelColor = (score) => {
  if (score >= 8) return 'danger'
  if (score >= 5) return 'warning'
  if (score >= 3) return 'info'
  return 'success'
}

const getRiskLevelText = (score) => {
  if (score >= 8) return '高风险'
  if (score >= 5) return '中风险'
  if (score >= 3) return '低风险'
  return '安全'
}

const getProgressColor = (percentage) => {
  if (percentage >= 80) return '#f56c6c'
  if (percentage >= 60) return '#e6a23c'
  return '#67c23a'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString()
}

const formatDateTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp * 1000)
  return date.toLocaleString()
}

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadDashboardData()
  }, autoRefreshInterval)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(async () => {
  await loadDashboardData()
  await loadAuditLogs()
  
  await nextTick()
  initTrendChart()
  
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  if (trendChart.value) {
    trendChart.value.dispose()
  }
})
</script>

<style scoped>
.security-dashboard {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.security-overview {
  margin-bottom: 20px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.metric-icon {
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

.metric-icon.security-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-icon.active-threats {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-icon.failed-logins {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-icon.system-health {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
}

.metric-label {
  color: #666;
  font-size: 14px;
}

.text-danger {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}

.text-success {
  color: #67c23a;
}

.main-content {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.threat-results {
  margin-bottom: 20px;
}

.no-threats {
  text-align: center;
  padding: 40px 0;
}

.alerts-card {
  margin-bottom: 20px;
}

.alert-badge {
  margin-left: 10px;
}

.alerts-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 12px;
  border-left: 4px solid #ddd;
  margin-bottom: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.alert-item.alert-high {
  border-left-color: #f56c6c;
}

.alert-item.alert-medium {
  border-left-color: #e6a23c;
}

.alert-item.alert-low {
  border-left-color: #67c23a;
}

.alert-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.alert-icon {
  margin-right: 8px;
  font-size: 16px;
}

.alert-title {
  flex: 1;
  font-weight: 600;
}

.alert-time {
  font-size: 12px;
  color: #999;
}

.alert-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.alert-actions {
  display: flex;
  gap: 10px;
}

.no-alerts {
  text-align: center;
  padding: 40px 0;
}

.activity-card {
  margin-bottom: 20px;
}

.activity-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.system-status-card {
  margin-bottom: 20px;
}

.system-status {
  space-y: 15px;
}

.status-item {
  margin-bottom: 15px;
}

.status-label {
  font-size: 14px;
  margin-bottom: 8px;
}

.status-value {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.audit-logs-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.affected-items {
  margin-top: 20px;
}

.affected-items h4 {
  margin-bottom: 10px;
}
</style>