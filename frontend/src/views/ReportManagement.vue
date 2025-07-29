<template>
  <div class="report-management">
    <div class="page-header">
      <h1>报表管理</h1>
      <p>生成和管理系统报表</p>
    </div>

    <div class="content-card">
      <div class="toolbar">
        <el-button type="primary" @click="generateReport">
          <el-icon><Document /></el-icon>
          生成报表
        </el-button>
        <el-select v-model="reportType" placeholder="选择报表类型" style="width: 200px">
          <el-option label="用户活动报表" value="user_activity" />
          <el-option label="系统性能报表" value="system_performance" />
          <el-option label="安全审计报表" value="security_audit" />
          <el-option label="项目统计报表" value="project_stats" />
        </el-select>
      </div>

      <el-table :data="reports" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="报表名称" />
        <el-table-column prop="type" label="类型">
          <template #default="{ row }">
            <el-tag>{{ getReportTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column prop="file_size" label="文件大小" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="downloadReport(row)" :disabled="row.status !== 'completed'">
              下载
            </el-button>
            <el-button size="small" type="danger" @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const reports = ref([])
const reportType = ref('user_activity')

// 模拟数据
const mockReports = [
  {
    id: 1,
    name: '用户活动报表_2025-07-29',
    type: 'user_activity',
    status: 'completed',
    created_at: '2025-07-29 10:30:00',
    file_size: '2.5MB'
  },
  {
    id: 2,
    name: '系统性能报表_2025-07-28',
    type: 'system_performance',
    status: 'generating',
    created_at: '2025-07-28 15:20:00',
    file_size: '-'
  },
  {
    id: 3,
    name: '安全审计报表_2025-07-27',
    type: 'security_audit',
    status: 'completed',
    created_at: '2025-07-27 09:15:00',
    file_size: '1.8MB'
  }
]

// 方法
const getReportTypeLabel = (type) => {
  const labels = {
    'user_activity': '用户活动',
    'system_performance': '系统性能',
    'security_audit': '安全审计',
    'project_stats': '项目统计'
  }
  return labels[type] || '未知'
}

const getStatusType = (status) => {
  const types = {
    'completed': 'success',
    'generating': 'warning',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    'completed': '已完成',
    'generating': '生成中',
    'failed': '失败'
  }
  return labels[status] || '未知'
}

const fetchReports = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    reports.value = mockReports
  } catch (error) {
    ElMessage.error('获取报表列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const generateReport = async () => {
  try {
    ElMessage.info('开始生成报表...')
    // 模拟生成报表
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const newReport = {
      id: reports.value.length + 1,
      name: `${getReportTypeLabel(reportType.value)}_${new Date().toISOString().split('T')[0]}`,
      type: reportType.value,
      status: 'completed',
      created_at: new Date().toLocaleString(),
      file_size: '1.2MB'
    }
    
    reports.value.unshift(newReport)
    ElMessage.success('报表生成成功')
  } catch (error) {
    ElMessage.error('生成报表失败: ' + error.message)
  }
}

const downloadReport = (report) => {
  ElMessage.success(`开始下载报表: ${report.name}`)
  // 这里应该实现实际的下载逻辑
}

const deleteReport = async (report) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除报表 "${report.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const index = reports.value.findIndex(r => r.id === report.id)
    if (index > -1) {
      reports.value.splice(index, 1)
      ElMessage.success('报表删除成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除报表失败: ' + error.message)
    }
  }
}

// 生命周期
onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.report-management {
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
</style>