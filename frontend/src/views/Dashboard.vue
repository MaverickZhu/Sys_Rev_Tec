<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">仪表板</h1>
      <p class="page-subtitle">欢迎回到系统审查技术平台</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon projects">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-number">{{ stats.totalProjects }}</h3>
            <p class="stat-label">项目总数</p>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon documents">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-number">{{ stats.totalDocuments }}</h3>
            <p class="stat-label">文档总数</p>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon users">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-number">{{ stats.totalUsers }}</h3>
            <p class="stat-label">用户总数</p>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon uptime">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-number">{{ stats.systemUptime }}</h3>
            <p class="stat-label">系统运行时间</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主要功能区域 -->
    <div class="main-content">
      <!-- 快速操作 -->
      <el-card class="quick-actions" shadow="hover">
        <template #header>
          <div class="card-header">
            <h3>快速操作</h3>
          </div>
        </template>
        <div class="actions-grid">
          <div 
            class="action-item" 
            @click="navigateTo('/users')"
            v-if="hasPermission(['USER_READ', 'USER_MANAGE'])"
          >
            <el-icon class="action-icon"><User /></el-icon>
            <span class="action-label">用户管理</span>
          </div>
          
          <div 
            class="action-item" 
            @click="navigateTo('/reports')"
            v-if="hasPermission(['REPORT_READ', 'REPORT_MANAGE'])"
          >
            <el-icon class="action-icon"><Document /></el-icon>
            <span class="action-label">报表管理</span>
          </div>
          
          <div 
            class="action-item" 
            @click="navigateTo('/permissions')"
            v-if="hasPermission(['SYSTEM_CONFIGURE', 'USER_MANAGE'])"
          >
            <el-icon class="action-icon"><Lock /></el-icon>
            <span class="action-label">权限管理</span>
          </div>
          
          <div 
            class="action-item" 
            @click="navigateTo('/system-maintenance')"
            v-if="hasPermission(['admin:system:maintenance:read', 'admin:system:maintenance:write'])"
          >
            <el-icon class="action-icon"><Tools /></el-icon>
            <span class="action-label">系统维护</span>
          </div>
          
          <div 
            class="action-item" 
            @click="navigateTo('/security')"
            v-if="hasPermission(['SYSTEM_MONITOR', 'AUDIT_READ'])"
          >
            <el-icon class="action-icon"><Shield /></el-icon>
            <span class="action-label">安全监控</span>
          </div>
          
          <div 
            class="action-item" 
            @click="navigateTo('/settings')"
            v-if="hasPermission(['SYSTEM_CONFIGURE'])"
          >
            <el-icon class="action-icon"><Setting /></el-icon>
            <span class="action-label">系统设置</span>
          </div>
        </div>
      </el-card>

      <!-- 系统状态 -->
      <el-card class="system-status" shadow="hover">
        <template #header>
          <div class="card-header">
            <h3>系统状态</h3>
            <el-button 
              type="primary" 
              size="small" 
              @click="refreshSystemStatus"
              :loading="statusLoading"
            >
              刷新
            </el-button>
          </div>
        </template>
        <div class="status-list">
          <div class="status-item">
            <span class="status-label">数据库连接</span>
            <el-tag 
              :type="systemStatus.database === 'healthy' ? 'success' : 'danger'"
              size="small"
            >
              {{ systemStatus.database === 'healthy' ? '正常' : '异常' }}
            </el-tag>
          </div>
          
          <div class="status-item">
            <span class="status-label">缓存服务</span>
            <el-tag 
              :type="systemStatus.cache === 'healthy' ? 'success' : 'danger'"
              size="small"
            >
              {{ systemStatus.cache === 'healthy' ? '正常' : '异常' }}
            </el-tag>
          </div>
          
          <div class="status-item">
            <span class="status-label">文件存储</span>
            <el-tag 
              :type="systemStatus.storage === 'healthy' ? 'success' : 'danger'"
              size="small"
            >
              {{ systemStatus.storage === 'healthy' ? '正常' : '异常' }}
            </el-tag>
          </div>
          
          <div class="status-item">
            <span class="status-label">AI服务</span>
            <el-tag 
              :type="systemStatus.ai_service === 'healthy' ? 'success' : 'danger'"
              size="small"
            >
              {{ systemStatus.ai_service === 'healthy' ? '正常' : '异常' }}
            </el-tag>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 最近活动 -->
    <el-card class="recent-activities" shadow="hover">
      <template #header>
        <div class="card-header">
          <h3>最近活动</h3>
        </div>
      </template>
      <div class="activities-list" v-loading="activitiesLoading">
        <div 
          v-for="activity in recentActivities" 
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="activity-content">
            <p class="activity-text">{{ activity.description }}</p>
            <span class="activity-time">{{ formatTime(activity.created_at) }}</span>
          </div>
        </div>
        
        <div v-if="recentActivities.length === 0" class="empty-activities">
          <el-empty description="暂无活动记录" :image-size="80" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import {
  Folder,
  Document,
  User,
  TrendCharts,
  Lock,
  Tools,
  Shield,
  Setting,
  Bell
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const stats = reactive({
  totalProjects: 0,
  totalDocuments: 0,
  totalUsers: 0,
  systemUptime: '99.9%'
})

const systemStatus = reactive({
  database: 'healthy',
  cache: 'healthy',
  storage: 'healthy',
  ai_service: 'healthy'
})

const recentActivities = ref([])
const statusLoading = ref(false)
const activitiesLoading = ref(false)

// 计算属性
const hasPermission = computed(() => {
  return (permissions) => {
    return userStore.checkPermissions(permissions)
  }
})

// 方法
const navigateTo = (path) => {
  router.push(path)
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const loadStats = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await api.getSystemStats()
    // Object.assign(stats, response.data)
    
    // 模拟数据
    stats.totalProjects = 156
    stats.totalDocuments = 2340
    stats.totalUsers = 89
    stats.systemUptime = '99.9%'
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

const refreshSystemStatus = async () => {
  statusLoading.value = true
  try {
    // 这里应该调用实际的API
    // const response = await api.getSystemStatus()
    // Object.assign(systemStatus, response.data)
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('系统状态已刷新')
  } catch (error) {
    console.error('刷新系统状态失败:', error)
    ElMessage.error('刷新系统状态失败')
  } finally {
    statusLoading.value = false
  }
}

const loadRecentActivities = async () => {
  activitiesLoading.value = true
  try {
    // 这里应该调用实际的API
    // const response = await api.getRecentActivities()
    // recentActivities.value = response.data
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    recentActivities.value = [
      {
        id: 1,
        description: '用户 admin 登录系统',
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        description: '系统执行了定期维护任务',
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 3,
        description: '新增了 5 个用户账户',
        created_at: new Date(Date.now() - 7200000).toISOString()
      }
    ]
  } catch (error) {
    console.error('加载最近活动失败:', error)
  } finally {
    activitiesLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadStats()
  loadRecentActivities()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  border-radius: 12px;
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.projects {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.documents {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.users {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.uptime {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  margin: 0 0 4px 0;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.action-icon {
  font-size: 24px;
  color: #667eea;
}

.action-label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.status-label {
  font-size: 14px;
  color: #333;
}

.recent-activities {
  border-radius: 12px;
}

.activities-list {
  min-height: 200px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
}

.activity-text {
  font-size: 14px;
  color: #333;
  margin: 0 0 4px 0;
}

.activity-time {
  font-size: 12px;
  color: #999;
}

.empty-activities {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 15px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .main-content {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .stat-number {
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .action-item {
    padding: 15px;
  }
}
</style>