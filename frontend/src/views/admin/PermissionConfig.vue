<template>
  <div class="permission-config">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <i class="el-icon-setting"></i>
        权限配置管理
      </h1>
      <p class="page-description">管理权限系统的各级配置参数</p>
    </div>

    <!-- 配置级别选择 -->
    <el-card class="config-level-card" shadow="never">
      <div slot="header" class="card-header">
        <span>配置级别</span>
        <el-button 
          type="primary" 
          size="small" 
          @click="refreshConfig"
          :loading="loading"
        >
          <i class="el-icon-refresh"></i>
          刷新配置
        </el-button>
      </div>
      
      <el-radio-group v-model="selectedLevel" @change="handleLevelChange">
        <el-radio-button 
          v-for="level in configLevels" 
          :key="level.value" 
          :label="level.value"
        >
          {{ level.name }}
        </el-radio-button>
      </el-radio-group>
      
      <div class="level-description">
        <el-alert
          :title="currentLevelDescription"
          type="info"
          :closable="false"
          show-icon
        >
        </el-alert>
      </div>
    </el-card>

    <!-- 配置表单 -->
    <el-card class="config-form-card" shadow="never" v-loading="loading">
      <div slot="header" class="card-header">
        <span>{{ selectedLevel === 'merged' ? '合并配置' : `${selectedLevelName}配置` }}</span>
        <div class="header-actions">
          <el-button 
            size="small" 
            @click="showImportDialog = true"
            :disabled="selectedLevel === 'merged'"
          >
            <i class="el-icon-upload"></i>
            导入配置
          </el-button>
          <el-button 
            size="small" 
            @click="exportConfig"
          >
            <i class="el-icon-download"></i>
            导出配置
          </el-button>
          <el-button 
            type="primary" 
            size="small" 
            @click="saveConfig"
            :disabled="selectedLevel === 'merged' || !hasChanges"
            :loading="saving"
          >
            <i class="el-icon-check"></i>
            保存配置
          </el-button>
        </div>
      </div>

      <!-- 配置分组 -->
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 查询优化配置 -->
        <el-tab-pane label="查询优化" name="query">
          <div class="config-section">
            <h3>查询优化设置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="启用查询优化">
                <el-switch 
                  v-model="configData.enable_query_optimization"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="启用批量优化">
                <el-switch 
                  v-model="configData.enable_batch_optimization"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="启用预加载优化">
                <el-switch 
                  v-model="configData.enable_preload_optimization"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="最大批量处理大小">
                <el-input-number 
                  v-model="configData.max_batch_size"
                  :min="1"
                  :max="1000"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="预加载缓存TTL(秒)">
                <el-input-number 
                  v-model="configData.preload_cache_ttl"
                  :min="60"
                  :max="86400"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 缓存配置 -->
        <el-tab-pane label="缓存设置" name="cache">
          <div class="config-section">
            <h3>缓存配置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="启用权限缓存">
                <el-switch 
                  v-model="configData.enable_permission_cache"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="缓存TTL(秒)">
                <el-input-number 
                  v-model="configData.cache_ttl"
                  :min="60"
                  :max="86400"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="缓存最大大小">
                <el-input-number 
                  v-model="configData.cache_max_size"
                  :min="100"
                  :max="100000"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="缓存策略">
                <el-select 
                  v-model="configData.cache_strategy"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                  <el-option label="LRU (最近最少使用)" value="lru"></el-option>
                  <el-option label="LFU (最少使用频率)" value="lfu"></el-option>
                  <el-option label="FIFO (先进先出)" value="fifo"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 性能监控配置 -->
        <el-tab-pane label="性能监控" name="performance">
          <div class="config-section">
            <h3>性能监控设置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="启用性能监控">
                <el-switch 
                  v-model="configData.enable_performance_monitoring"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="慢查询阈值(秒)">
                <el-input-number 
                  v-model="configData.slow_query_threshold"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  :precision="1"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="最大历史记录大小">
                <el-input-number 
                  v-model="configData.max_history_size"
                  :min="100"
                  :max="10000"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="统计时间窗口(分钟)">
                <el-input-number 
                  v-model="configData.stats_window_minutes"
                  :min="1"
                  :max="1440"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 安全配置 -->
        <el-tab-pane label="安全设置" name="security">
          <div class="config-section">
            <h3>安全配置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="启用权限审计">
                <el-switch 
                  v-model="configData.enable_permission_audit"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="最大权限深度">
                <el-input-number 
                  v-model="configData.max_permission_depth"
                  :min="1"
                  :max="10"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="启用角色继承">
                <el-switch 
                  v-model="configData.enable_role_inheritance"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="最大角色深度">
                <el-input-number 
                  v-model="configData.max_role_depth"
                  :min="1"
                  :max="10"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="启用资源权限">
                <el-switch 
                  v-model="configData.enable_resource_permissions"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- API配置 -->
        <el-tab-pane label="API设置" name="api">
          <div class="config-section">
            <h3>API配置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="启用权限API">
                <el-switch 
                  v-model="configData.enable_permission_api"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="API速率限制(每分钟)">
                <el-input-number 
                  v-model="configData.api_rate_limit"
                  :min="10"
                  :max="10000"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
              
              <el-form-item label="启用API认证">
                <el-switch 
                  v-model="configData.enable_api_authentication"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 日志配置 -->
        <el-tab-pane label="日志设置" name="logging">
          <div class="config-section">
            <h3>日志配置</h3>
            <el-form :model="configData" label-width="200px" size="small">
              <el-form-item label="日志级别">
                <el-select 
                  v-model="configData.log_level"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                  <el-option label="DEBUG" value="DEBUG"></el-option>
                  <el-option label="INFO" value="INFO"></el-option>
                  <el-option label="WARNING" value="WARNING"></el-option>
                  <el-option label="ERROR" value="ERROR"></el-option>
                </el-select>
              </el-form-item>
              
              <el-form-item label="启用查询日志">
                <el-switch 
                  v-model="configData.enable_query_logging"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="启用性能日志">
                <el-switch 
                  v-model="configData.enable_performance_logging"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-switch>
              </el-form-item>
              
              <el-form-item label="日志保留天数">
                <el-input-number 
                  v-model="configData.log_retention_days"
                  :min="1"
                  :max="365"
                  :disabled="isReadonly"
                  @change="markChanged"
                >
                </el-input-number>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 配置摘要 -->
    <el-card class="config-summary-card" shadow="never">
      <div slot="header" class="card-header">
        <span>配置摘要</span>
        <el-button 
          size="small" 
          @click="loadConfigSummary"
          :loading="summaryLoading"
        >
          <i class="el-icon-refresh"></i>
          刷新摘要
        </el-button>
      </div>
      
      <div class="summary-content" v-loading="summaryLoading">
        <el-row :gutter="20">
          <el-col :span="6" v-for="(item, key) in configSummary" :key="key">
            <div class="summary-item">
              <div class="summary-label">{{ getSummaryLabel(key) }}</div>
              <div class="summary-value">{{ item }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 配置导入对话框 -->
    <el-dialog
      title="导入配置"
      :visible.sync="showImportDialog"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="importForm" label-width="120px">
        <el-form-item label="配置级别">
          <el-select v-model="importForm.level" placeholder="请选择配置级别">
            <el-option 
              v-for="level in configLevels.filter(l => l.value !== 'merged')" 
              :key="level.value" 
              :label="level.name" 
              :value="level.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="配置数据">
          <el-input
            type="textarea"
            v-model="importForm.configData"
            :rows="10"
            placeholder="请粘贴JSON格式的配置数据"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="importForm.validateOnly">
            仅验证不保存
          </el-checkbox>
        </el-form-item>
      </el-form>
      
      <div slot="footer" class="dialog-footer">
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="importConfig"
          :loading="importing"
        >
          {{ importForm.validateOnly ? '验证' : '导入' }}
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getPermissionConfig, updatePermissionConfig, exportPermissionConfig, importPermissionConfig, getConfigSummary, getConfigLevels, reloadPermissionConfig } from '@/api/permission-config'

export default {
  name: 'PermissionConfig',
  data() {
    return {
      // 配置级别
      selectedLevel: 'application',
      configLevels: [
        { value: 'merged', name: '合并配置', description: '所有级别配置的合并结果（只读）' },
        { value: 'system', name: '系统配置', description: '核心系统设置' },
        { value: 'application', name: '应用配置', description: '应用程序设置' },
        { value: 'user', name: '用户配置', description: '用户个性化设置' },
        { value: 'runtime', name: '运行时配置', description: '动态运行时设置' }
      ],
      
      // 配置数据
      configData: {},
      originalConfigData: {},
      hasChanges: false,
      
      // 界面状态
      activeTab: 'query',
      loading: false,
      saving: false,
      
      // 配置摘要
      configSummary: {},
      summaryLoading: false,
      
      // 导入对话框
      showImportDialog: false,
      importForm: {
        level: '',
        configData: '',
        validateOnly: false
      },
      importing: false
    }
  },
  
  computed: {
    selectedLevelName() {
      const level = this.configLevels.find(l => l.value === this.selectedLevel)
      return level ? level.name : ''
    },
    
    currentLevelDescription() {
      const level = this.configLevels.find(l => l.value === this.selectedLevel)
      return level ? level.description : ''
    },
    
    isReadonly() {
      return this.selectedLevel === 'merged'
    }
  },
  
  created() {
    this.loadConfig()
    this.loadConfigSummary()
  },
  
  methods: {
    // 加载配置
    async loadConfig() {
      this.loading = true
      try {
        const response = await getPermissionConfig({
          level: this.selectedLevel === 'merged' ? null : this.selectedLevel
        })
        
        if (response.success) {
          this.configData = { ...response.data.config }
          this.originalConfigData = { ...response.data.config }
          this.hasChanges = false
        }
      } catch (error) {
        this.$message.error('加载配置失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    
    // 加载配置摘要
    async loadConfigSummary() {
      this.summaryLoading = true
      try {
        const response = await getConfigSummary()
        if (response.success) {
          this.configSummary = response.data
        }
      } catch (error) {
        console.error('加载配置摘要失败:', error)
      } finally {
        this.summaryLoading = false
      }
    },
    
    // 处理级别变化
    handleLevelChange() {
      if (this.hasChanges) {
        this.$confirm('当前有未保存的更改，切换级别将丢失这些更改，是否继续？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.loadConfig()
        }).catch(() => {
          // 恢复原来的选择
          this.$nextTick(() => {
            this.selectedLevel = Object.keys(this.originalConfigData).length > 0 ? 
              this.selectedLevel : 'application'
          })
        })
      } else {
        this.loadConfig()
      }
    },
    
    // 标记配置已更改
    markChanged() {
      this.hasChanges = true
    },
    
    // 保存配置
    async saveConfig() {
      if (this.selectedLevel === 'merged') {
        this.$message.warning('合并配置为只读，无法保存')
        return
      }
      
      this.saving = true
      try {
        // 计算更改的字段
        const updates = {}
        for (const key in this.configData) {
          if (this.configData[key] !== this.originalConfigData[key]) {
            updates[key] = this.configData[key]
          }
        }
        
        if (Object.keys(updates).length === 0) {
          this.$message.info('没有配置更改需要保存')
          return
        }
        
        const response = await updatePermissionConfig({
          level: this.selectedLevel,
          updates: updates
        })
        
        if (response.success) {
          this.$message.success('配置保存成功')
          this.originalConfigData = { ...this.configData }
          this.hasChanges = false
          this.loadConfigSummary()
        }
      } catch (error) {
        this.$message.error('保存配置失败: ' + error.message)
      } finally {
        this.saving = false
      }
    },
    
    // 导出配置
    async exportConfig() {
      try {
        const response = await exportPermissionConfig({
          level: this.selectedLevel === 'merged' ? null : this.selectedLevel,
          include_metadata: true
        })
        
        if (response.success) {
          const configJson = JSON.stringify(response.data.config_data, null, 2)
          const blob = new Blob([configJson], { type: 'application/json' })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `permission_config_${this.selectedLevel}_${new Date().toISOString().slice(0, 10)}.json`
          link.click()
          window.URL.revokeObjectURL(url)
          
          this.$message.success('配置导出成功')
        }
      } catch (error) {
        this.$message.error('导出配置失败: ' + error.message)
      }
    },
    
    // 导入配置
    async importConfig() {
      if (!this.importForm.level || !this.importForm.configData) {
        this.$message.warning('请选择配置级别并输入配置数据')
        return
      }
      
      this.importing = true
      try {
        let configData
        try {
          configData = JSON.parse(this.importForm.configData)
        } catch (error) {
          this.$message.error('配置数据格式错误，请输入有效的JSON格式')
          return
        }
        
        const response = await importPermissionConfig({
          level: this.importForm.level,
          config_data: configData,
          validate_only: this.importForm.validateOnly
        })
        
        if (response.success) {
          if (this.importForm.validateOnly) {
            this.$message.success('配置验证通过')
          } else {
            this.$message.success('配置导入成功')
            this.showImportDialog = false
            this.importForm = { level: '', configData: '', validateOnly: false }
            
            // 如果导入的是当前级别，重新加载配置
            if (this.importForm.level === this.selectedLevel) {
              this.loadConfig()
            }
            this.loadConfigSummary()
          }
        }
      } catch (error) {
        this.$message.error((this.importForm.validateOnly ? '验证' : '导入') + '配置失败: ' + error.message)
      } finally {
        this.importing = false
      }
    },
    
    // 刷新配置
    async refreshConfig() {
      if (this.hasChanges) {
        this.$confirm('当前有未保存的更改，刷新将丢失这些更改，是否继续？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.loadConfig()
        })
      } else {
        this.loadConfig()
      }
    },
    
    // 获取摘要标签
    getSummaryLabel(key) {
      const labels = {
        total_configs: '总配置数',
        active_configs: '活跃配置数',
        cache_enabled: '缓存启用',
        monitoring_enabled: '监控启用',
        optimization_enabled: '优化启用',
        last_updated: '最后更新'
      }
      return labels[key] || key
    }
  }
}
</script>

<style scoped>
.permission-config {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-title i {
  margin-right: 8px;
  color: #409EFF;
}

.page-description {
  color: #606266;
  margin: 0;
}

.config-level-card,
.config-form-card,
.config-summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.level-description {
  margin-top: 15px;
}

.config-section {
  padding: 20px;
}

.config-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 10px;
}

.summary-content {
  min-height: 80px;
}

.summary-item {
  text-align: center;
  padding: 15px;
  background: #F5F7FA;
  border-radius: 4px;
  margin-bottom: 10px;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .permission-config {
    padding: 10px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .summary-item {
    margin-bottom: 5px;
  }
}
</style>