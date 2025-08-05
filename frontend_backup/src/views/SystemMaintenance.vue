<template>
  <div class="system-maintenance">
    <div class="page-header">
      <h1>系统维护</h1>
      <p>系统状态监控、数据库清理、日志管理和备份恢复</p>
    </div>

    <!-- 系统状态概览 -->
    <el-row :gutter="20" class="status-overview">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon cpu">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.system?.cpu_usage?.toFixed(1) || 0 }}%</div>
              <div class="status-label">CPU使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon memory">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.system?.memory?.percent?.toFixed(1) || 0 }}%</div>
              <div class="status-label">内存使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon disk">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.system?.disk?.percent?.toFixed(1) || 0 }}%</div>
              <div class="status-label">磁盘使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon database">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.database?.active_connections || 0 }}</div>
              <div class="status-label">数据库连接</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能选项卡 -->
    <el-tabs v-model="activeTab" class="maintenance-tabs">
      <!-- 系统监控 -->
      <el-tab-pane label="系统监控" name="monitoring">
        <div class="tab-content">
          <div class="section-header">
            <h3>系统状态监控</h3>
            <el-button type="primary" @click="refreshSystemStatus" :loading="loading.status">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-card title="系统资源">
                <template #header>
                  <span>系统资源</span>
                </template>
                <div class="resource-info">
                  <div class="resource-item">
                    <span class="label">运行时间:</span>
                    <span class="value">{{ systemStatus.system?.uptime || 'N/A' }}</span>
                  </div>
                  <div class="resource-item">
                    <span class="label">可用内存:</span>
                    <span class="value">{{ formatBytes(systemStatus.system?.memory?.available) }}</span>
                  </div>
                  <div class="resource-item">
                    <span class="label">可用磁盘:</span>
                    <span class="value">{{ formatBytes(systemStatus.system?.disk?.free) }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card title="数据库状态">
                <template #header>
                  <span>数据库状态</span>
                </template>
                <div class="resource-info">
                  <div class="resource-item">
                    <span class="label">状态:</span>
                    <el-tag :type="systemStatus.database?.status === 'healthy' ? 'success' : 'danger'">
                      {{ systemStatus.database?.status || 'unknown' }}
                    </el-tag>
                  </div>
                  <div class="resource-item">
                    <span class="label">数据库大小:</span>
                    <span class="value">{{ systemStatus.database?.size || 'N/A' }}</span>
                  </div>
                  <div class="resource-item">
                    <span class="label">活跃连接:</span>
                    <span class="value">{{ systemStatus.database?.active_connections || 0 }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 健康检查 -->
          <el-card class="health-check-card">
            <template #header>
              <div class="card-header">
                <span>健康检查</span>
                <el-button type="primary" size="small" @click="runHealthCheck" :loading="loading.health">
                  <el-icon><CircleCheck /></el-icon>
                  运行检查
                </el-button>
              </div>
            </template>
            <div v-if="healthStatus">
              <div class="health-overall">
                <el-tag :type="getHealthTagType(healthStatus.overall_status)" size="large">
                  {{ healthStatus.overall_status }}
                </el-tag>
                <span class="health-time">{{ formatTime(healthStatus.timestamp) }}</span>
              </div>
              <el-table :data="healthStatus.checks" style="width: 100%">
                <el-table-column prop="name" label="检查项" width="200" />
                <el-table-column prop="status" label="状态" width="120">
                  <template #default="scope">
                    <el-tag :type="getHealthTagType(scope.row.status)">
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="details" label="详情">
                  <template #default="scope">
                    <div v-if="scope.row.details">
                      <div v-for="(value, key) in scope.row.details" :key="key">
                        <span class="detail-key">{{ key }}:</span>
                        <span class="detail-value">{{ value }}</span>
                      </div>
                    </div>
                    <span v-else-if="scope.row.error" class="error-text">{{ scope.row.error }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 数据库维护 -->
      <el-tab-pane label="数据库维护" name="database">
        <div class="tab-content">
          <div class="section-header">
            <h3>数据库清理与维护</h3>
          </div>

          <el-card>
            <template #header>
              <span>清理配置</span>
            </template>
            <el-form :model="cleanupForm" label-width="150px">
              <el-form-item label="清理审计日志">
                <el-switch v-model="cleanupForm.cleanup_audit_logs" />
                <el-input-number 
                  v-if="cleanupForm.cleanup_audit_logs"
                  v-model="cleanupForm.audit_log_retention_days"
                  :min="1" :max="365"
                  style="margin-left: 10px; width: 120px;"
                />
                <span v-if="cleanupForm.cleanup_audit_logs" style="margin-left: 5px;">天</span>
              </el-form-item>
              <el-form-item label="清理过期会话">
                <el-switch v-model="cleanupForm.cleanup_expired_sessions" />
              </el-form-item>
              <el-form-item label="清理临时文件">
                <el-switch v-model="cleanupForm.cleanup_temp_files" />
                <el-input-number 
                  v-if="cleanupForm.cleanup_temp_files"
                  v-model="cleanupForm.temp_file_retention_days"
                  :min="1" :max="30"
                  style="margin-left: 10px; width: 120px;"
                />
                <span v-if="cleanupForm.cleanup_temp_files" style="margin-left: 5px;">天</span>
              </el-form-item>
              <el-form-item label="执行VACUUM">
                <el-switch v-model="cleanupForm.vacuum_analyze" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="cleanupDatabase" :loading="loading.cleanup">
                  <el-icon><Delete /></el-icon>
                  执行清理
                </el-button>
                <el-button @click="vacuumDatabase" :loading="loading.vacuum">
                  <el-icon><Tools /></el-icon>
                  仅执行VACUUM
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 清理结果 -->
          <el-card v-if="cleanupResult" class="result-card">
            <template #header>
              <span>清理结果</span>
            </template>
            <div class="cleanup-result">
              <div class="result-status">
                <el-tag :type="cleanupResult.status === 'success' ? 'success' : 'danger'">
                  {{ cleanupResult.status }}
                </el-tag>
                <span class="result-time">{{ formatTime(cleanupResult.timestamp) }}</span>
              </div>
              <el-table :data="cleanupResult.operations" style="width: 100%">
                <el-table-column prop="operation" label="操作" width="200" />
                <el-table-column prop="deleted_rows" label="删除行数" width="120" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'">
                      {{ scope.row.status || 'completed' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="cutoff_date" label="截止日期" />
              </el-table>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 日志管理 -->
      <el-tab-pane label="日志管理" name="logs">
        <div class="tab-content">
          <div class="section-header">
            <h3>日志轮转与管理</h3>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>日志状态</span>
                </template>
                <div class="log-status">
                  <div class="status-item">
                    <span class="label">日志文件数:</span>
                    <span class="value">{{ systemStatus.logs?.total_files || 0 }}</span>
                  </div>
                  <div class="status-item">
                    <span class="label">总大小:</span>
                    <span class="value">{{ formatBytes(systemStatus.logs?.total_size) }}</span>
                  </div>
                </div>
                <el-table :data="systemStatus.logs?.files || []" style="width: 100%">
                  <el-table-column prop="name" label="文件名" />
                  <el-table-column prop="size_human" label="大小" width="100" />
                  <el-table-column prop="lines" label="行数" width="80" />
                  <el-table-column prop="modified" label="修改时间" width="180">
                    <template #default="scope">
                      {{ formatTime(scope.row.modified) }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>轮转配置</span>
                </template>
                <el-form :model="rotationForm" label-width="120px">
                  <el-form-item label="最大文件大小">
                    <el-input-number v-model="rotationForm.max_size_mb" :min="1" :max="1000" />
                    <span style="margin-left: 5px;">MB</span>
                  </el-form-item>
                  <el-form-item label="最大文件数">
                    <el-input-number v-model="rotationForm.max_files" :min="1" :max="100" />
                  </el-form-item>
                  <el-form-item label="压缩文件">
                    <el-switch v-model="rotationForm.compress" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="rotateLogs" :loading="loading.rotation">
                      <el-icon><RefreshRight /></el-icon>
                      执行轮转
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
          </el-row>

          <!-- 轮转结果 -->
          <el-card v-if="rotationResult" class="result-card">
            <template #header>
              <span>轮转结果</span>
            </template>
            <div class="rotation-result">
              <div class="result-status">
                <el-tag :type="rotationResult.status === 'success' ? 'success' : 'danger'">
                  {{ rotationResult.status }}
                </el-tag>
                <span class="result-time">{{ formatTime(rotationResult.timestamp) }}</span>
              </div>
              <div v-if="rotationResult.rotated_files?.length">
                <h4>轮转文件:</h4>
                <el-table :data="rotationResult.rotated_files" style="width: 100%">
                  <el-table-column prop="original" label="原文件" />
                  <el-table-column prop="rotated" label="轮转后" />
                  <el-table-column prop="size" label="大小" width="120">
                    <template #default="scope">
                      {{ formatBytes(scope.row.size) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-if="rotationResult.cleaned_files?.length">
                <h4>清理文件:</h4>
                <ul>
                  <li v-for="file in rotationResult.cleaned_files" :key="file">{{ file }}</li>
                </ul>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 系统备份 -->
      <el-tab-pane label="系统备份" name="backup">
        <div class="tab-content">
          <div class="section-header">
            <h3>系统备份与恢复</h3>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>创建备份</span>
                </template>
                <el-form :model="backupForm" label-width="120px">
                  <el-form-item label="备份数据库">
                    <el-switch v-model="backupForm.backup_database" />
                  </el-form-item>
                  <el-form-item label="备份配置">
                    <el-switch v-model="backupForm.backup_config" />
                  </el-form-item>
                  <el-form-item label="备份上传文件">
                    <el-switch v-model="backupForm.backup_uploads" />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="createBackup" :loading="loading.backup">
                      <el-icon><Download /></el-icon>
                      创建备份
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>
                  <div class="card-header">
                    <span>备份列表</span>
                    <el-button type="primary" size="small" @click="loadBackups">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                </template>
                <el-table :data="backupList" style="width: 100%" max-height="400">
                  <el-table-column prop="name" label="备份名称" />
                  <el-table-column prop="size_human" label="大小" width="100" />
                  <el-table-column prop="timestamp" label="创建时间" width="180">
                    <template #default="scope">
                      {{ formatTime(scope.row.timestamp) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100">
                    <template #default="scope">
                      <el-button 
                        type="danger" 
                        size="small" 
                        @click="deleteBackup(scope.row.name)"
                        :loading="loading.deleteBackup"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>

          <!-- 备份结果 -->
          <el-card v-if="backupResult" class="result-card">
            <template #header>
              <span>备份结果</span>
            </template>
            <div class="backup-result">
              <div class="result-status">
                <el-tag :type="backupResult.status === 'success' ? 'success' : 'danger'">
                  {{ backupResult.status }}
                </el-tag>
                <span class="result-time">{{ formatTime(backupResult.timestamp) }}</span>
              </div>
              <div v-if="backupResult.status === 'success'">
                <div class="backup-info">
                  <div class="info-item">
                    <span class="label">备份名称:</span>
                    <span class="value">{{ backupResult.backup_name }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">备份路径:</span>
                    <span class="value">{{ backupResult.backup_path }}</span>
                  </div>
                </div>
                <el-table :data="backupResult.results" style="width: 100%">
                  <el-table-column prop="operation" label="操作" width="200" />
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="scope">
                      <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                        {{ scope.row.status }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="file" label="文件" />
                  <el-table-column prop="size" label="大小" width="120">
                    <template #default="scope">
                      {{ scope.row.size ? formatBytes(scope.row.size) : 'N/A' }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-else class="error-text">
                {{ backupResult.error }}
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Cpu,
  FolderOpened,
  DataBoard,
  Refresh,
  CircleCheck,
  Delete,
  Tools,
  RefreshRight,
  Download
} from '@element-plus/icons-vue'
import { systemMaintenanceApi } from '@/api/systemMaintenance'

// 响应式数据
const activeTab = ref('monitoring')
const systemStatus = ref({})
const healthStatus = ref(null)
const cleanupResult = ref(null)
const rotationResult = ref(null)
const backupResult = ref(null)
const backupList = ref([])

// 加载状态
const loading = reactive({
  status: false,
  health: false,
  cleanup: false,
  vacuum: false,
  rotation: false,
  backup: false,
  deleteBackup: false
})

// 表单数据
const cleanupForm = reactive({
  cleanup_audit_logs: true,
  audit_log_retention_days: 90,
  cleanup_expired_sessions: true,
  cleanup_temp_files: true,
  temp_file_retention_days: 7,
  vacuum_analyze: true
})

const rotationForm = reactive({
  max_size_mb: 100,
  max_files: 10,
  compress: true
})

const backupForm = reactive({
  backup_database: true,
  backup_config: true,
  backup_uploads: true
})

// 方法
const refreshSystemStatus = async () => {
  loading.status = true
  try {
    const response = await systemMaintenanceApi.getSystemStatus()
    systemStatus.value = response.data
  } catch (error) {
    ElMessage.error('获取系统状态失败: ' + error.message)
  } finally {
    loading.status = false
  }
}

const runHealthCheck = async () => {
  loading.health = true
  try {
    const response = await systemMaintenanceApi.runHealthCheck()
    healthStatus.value = response.data
    ElMessage.success('健康检查完成')
  } catch (error) {
    ElMessage.error('健康检查失败: ' + error.message)
  } finally {
    loading.health = false
  }
}

const cleanupDatabase = async () => {
  loading.cleanup = true
  try {
    const response = await systemMaintenanceApi.cleanupDatabase(cleanupForm)
    cleanupResult.value = response.data
    ElMessage.success('数据库清理完成')
  } catch (error) {
    ElMessage.error('数据库清理失败: ' + error.message)
  } finally {
    loading.cleanup = false
  }
}

const vacuumDatabase = async () => {
  loading.vacuum = true
  try {
    const response = await systemMaintenanceApi.vacuumDatabase()
    ElMessage.success('数据库VACUUM操作完成')
  } catch (error) {
    ElMessage.error('数据库VACUUM操作失败: ' + error.message)
  } finally {
    loading.vacuum = false
  }
}

const rotateLogs = async () => {
  loading.rotation = true
  try {
    const response = await systemMaintenanceApi.rotateLogs(rotationForm)
    rotationResult.value = response.data
    ElMessage.success('日志轮转完成')
    // 刷新系统状态以更新日志信息
    await refreshSystemStatus()
  } catch (error) {
    ElMessage.error('日志轮转失败: ' + error.message)
  } finally {
    loading.rotation = false
  }
}

const createBackup = async () => {
  loading.backup = true
  try {
    const response = await systemMaintenanceApi.createBackup(backupForm)
    backupResult.value = response.data
    ElMessage.success('系统备份完成')
    // 刷新备份列表
    await loadBackups()
  } catch (error) {
    ElMessage.error('系统备份失败: ' + error.message)
  } finally {
    loading.backup = false
  }
}

const loadBackups = async () => {
  try {
    const response = await systemMaintenanceApi.listBackups()
    backupList.value = response.data.backups
  } catch (error) {
    ElMessage.error('加载备份列表失败: ' + error.message)
  }
}

const deleteBackup = async (backupName) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份 "${backupName}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.deleteBackup = true
    await systemMaintenanceApi.deleteBackup(backupName)
    ElMessage.success('备份删除成功')
    await loadBackups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除备份失败: ' + error.message)
    }
  } finally {
    loading.deleteBackup = false
  }
}

// 工具函数
const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timeString) => {
  if (!timeString) return 'N/A'
  return new Date(timeString).toLocaleString('zh-CN')
}

const getHealthTagType = (status) => {
  switch (status) {
    case 'healthy':
      return 'success'
    case 'warning':
      return 'warning'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

// 生命周期
onMounted(async () => {
  await refreshSystemStatus()
  await loadBackups()
})
</script>

<style scoped>
.system-maintenance {
  padding: 20px;
}

.page-header {
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

.status-overview {
  margin-bottom: 20px;
}

.status-card {
  height: 100px;
}

.status-item {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.status-icon.cpu {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.status-icon.memory {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.status-icon.disk {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.status-icon.database {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.status-info {
  flex: 1;
}

.status-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  line-height: 1;
}

.status-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.maintenance-tabs {
  margin-top: 20px;
}

.tab-content {
  padding: 20px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.resource-info {
  padding: 10px 0;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.resource-item:last-child {
  border-bottom: none;
}

.resource-item .label {
  font-weight: 500;
  color: #666;
}

.resource-item .value {
  color: #333;
}

.health-check-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.health-overall {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.health-time {
  margin-left: 15px;
  color: #666;
  font-size: 14px;
}

.detail-key {
  font-weight: 500;
  margin-right: 8px;
}

.detail-value {
  color: #666;
}

.error-text {
  color: #f56c6c;
}

.result-card {
  margin-top: 20px;
}

.result-status {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.result-time {
  margin-left: 15px;
  color: #666;
  font-size: 14px;
}

.cleanup-result h4,
.rotation-result h4,
.backup-result h4 {
  margin: 15px 0 10px 0;
  font-size: 16px;
  font-weight: 600;
}

.log-status {
  padding: 10px 0;
  margin-bottom: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child {
  border-bottom: none;
}

.backup-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.info-item .label {
  font-weight: 500;
  margin-right: 10px;
  min-width: 80px;
}

.info-item .value {
  color: #666;
}
</style>