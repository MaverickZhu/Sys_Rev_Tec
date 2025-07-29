<template>
  <div class="system-settings">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>管理系统配置、参数和偏好设置</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 基础设置 -->
      <el-tab-pane label="基础设置" name="basic">
        <div class="settings-section">
          <h3>系统信息</h3>
          <el-form :model="basicSettings" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="系统名称">
                  <el-input v-model="basicSettings.systemName" />
                </el-form-item>
                <el-form-item label="系统描述">
                  <el-input v-model="basicSettings.description" type="textarea" :rows="3" />
                </el-form-item>
                <el-form-item label="系统版本">
                  <el-input v-model="basicSettings.version" readonly />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="时区设置">
                  <el-select v-model="basicSettings.timezone" style="width: 100%">
                    <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                    <el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
                    <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
                    <el-option label="伦敦时间 (UTC+0)" value="Europe/London" />
                  </el-select>
                </el-form-item>
                <el-form-item label="语言设置">
                  <el-select v-model="basicSettings.language" style="width: 100%">
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                    <el-option label="日本語" value="ja-JP" />
                  </el-select>
                </el-form-item>
                <el-form-item label="主题模式">
                  <el-radio-group v-model="basicSettings.theme">
                    <el-radio label="light">浅色模式</el-radio>
                    <el-radio label="dark">深色模式</el-radio>
                    <el-radio label="auto">跟随系统</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 安全设置 -->
      <el-tab-pane label="安全设置" name="security">
        <div class="settings-section">
          <h3>密码策略</h3>
          <el-form :model="securitySettings" label-width="150px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="密码最小长度">
                  <el-input-number v-model="securitySettings.minPasswordLength" :min="6" :max="32" />
                </el-form-item>
                <el-form-item label="密码复杂度要求">
                  <el-checkbox-group v-model="securitySettings.passwordRequirements">
                    <el-checkbox label="uppercase">包含大写字母</el-checkbox>
                    <el-checkbox label="lowercase">包含小写字母</el-checkbox>
                    <el-checkbox label="numbers">包含数字</el-checkbox>
                    <el-checkbox label="symbols">包含特殊字符</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                <el-form-item label="密码有效期">
                  <el-input-number v-model="securitySettings.passwordExpiry" :min="0" :max="365" /> 天 (0表示永不过期)
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="登录失败限制">
                  <el-input-number v-model="securitySettings.maxLoginAttempts" :min="3" :max="10" />
                </el-form-item>
                <el-form-item label="账户锁定时间">
                  <el-input-number v-model="securitySettings.lockoutDuration" :min="5" :max="1440" /> 分钟
                </el-form-item>
                <el-form-item label="会话超时">
                  <el-input-number v-model="securitySettings.sessionTimeout" :min="5" :max="1440" /> 分钟
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="settings-section">
          <h3>访问控制</h3>
          <el-form :model="securitySettings" label-width="150px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="启用IP白名单">
                  <el-switch v-model="securitySettings.enableWhitelist" />
                </el-form-item>
                <el-form-item label="强制HTTPS">
                  <el-switch v-model="securitySettings.forceHttps" />
                </el-form-item>
                <el-form-item label="启用双因子认证">
                  <el-switch v-model="securitySettings.enable2FA" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="API访问限制">
                  <el-switch v-model="securitySettings.enableRateLimit" />
                </el-form-item>
                <el-form-item label="审计日志">
                  <el-switch v-model="securitySettings.enableAuditLog" />
                </el-form-item>
                <el-form-item label="安全警报">
                  <el-switch v-model="securitySettings.enableSecurityAlerts" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知设置" name="notification">
        <div class="settings-section">
          <h3>邮件通知</h3>
          <el-form :model="notificationSettings" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="SMTP服务器">
                  <el-input v-model="notificationSettings.smtpServer" />
                </el-form-item>
                <el-form-item label="SMTP端口">
                  <el-input-number v-model="notificationSettings.smtpPort" :min="1" :max="65535" />
                </el-form-item>
                <el-form-item label="发件人邮箱">
                  <el-input v-model="notificationSettings.senderEmail" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="启用SSL/TLS">
                  <el-switch v-model="notificationSettings.enableSSL" />
                </el-form-item>
                <el-form-item label="SMTP用户名">
                  <el-input v-model="notificationSettings.smtpUsername" />
                </el-form-item>
                <el-form-item label="SMTP密码">
                  <el-input v-model="notificationSettings.smtpPassword" type="password" show-password />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="settings-section">
          <h3>通知类型</h3>
          <el-form :model="notificationSettings" label-width="120px">
            <el-form-item label="通知事件">
              <el-checkbox-group v-model="notificationSettings.notificationTypes">
                <el-checkbox label="user_login">用户登录</el-checkbox>
                <el-checkbox label="user_logout">用户登出</el-checkbox>
                <el-checkbox label="security_alert">安全警报</el-checkbox>
                <el-checkbox label="system_error">系统错误</el-checkbox>
                <el-checkbox label="backup_complete">备份完成</el-checkbox>
                <el-checkbox label="maintenance">系统维护</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 存储设置 -->
      <el-tab-pane label="存储设置" name="storage">
        <div class="settings-section">
          <h3>文件存储</h3>
          <el-form :model="storageSettings" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="存储路径">
                  <el-input v-model="storageSettings.uploadPath" />
                </el-form-item>
                <el-form-item label="最大文件大小">
                  <el-input-number v-model="storageSettings.maxFileSize" :min="1" :max="1024" /> MB
                </el-form-item>
                <el-form-item label="允许的文件类型">
                  <el-input v-model="storageSettings.allowedFileTypes" placeholder="如: .pdf,.doc,.docx,.txt" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="自动清理">
                  <el-switch v-model="storageSettings.autoCleanup" />
                </el-form-item>
                <el-form-item label="文件保留期">
                  <el-input-number v-model="storageSettings.retentionDays" :min="1" :max="3650" /> 天
                </el-form-item>
                <el-form-item label="压缩存储">
                  <el-switch v-model="storageSettings.enableCompression" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="settings-section">
          <h3>数据库设置</h3>
          <el-form :model="storageSettings" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="自动备份">
                  <el-switch v-model="storageSettings.autoBackup" />
                </el-form-item>
                <el-form-item label="备份间隔">
                  <el-select v-model="storageSettings.backupInterval" style="width: 100%">
                    <el-option label="每小时" value="hourly" />
                    <el-option label="每天" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="每月" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="备份保留数量">
                  <el-input-number v-model="storageSettings.backupRetention" :min="1" :max="100" />
                </el-form-item>
                <el-form-item label="压缩备份">
                  <el-switch v-model="storageSettings.compressBackup" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <div class="settings-actions">
      <el-button @click="resetSettings">重置设置</el-button>
      <el-button type="primary" @click="saveSettings" :loading="saving">
        <el-icon><Check /></el-icon>
        保存设置
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'

// 响应式数据
const activeTab = ref('basic')
const saving = ref(false)

const basicSettings = ref({
  systemName: '系统审查技术平台',
  description: '基于AI的系统审查和技术分析平台',
  version: '1.0.0',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  theme: 'light'
})

const securitySettings = ref({
  minPasswordLength: 8,
  passwordRequirements: ['lowercase', 'numbers'],
  passwordExpiry: 90,
  maxLoginAttempts: 5,
  lockoutDuration: 30,
  sessionTimeout: 30,
  enableWhitelist: false,
  forceHttps: true,
  enable2FA: false,
  enableRateLimit: true,
  enableAuditLog: true,
  enableSecurityAlerts: true
})

const notificationSettings = ref({
  smtpServer: 'smtp.example.com',
  smtpPort: 587,
  senderEmail: 'noreply@example.com',
  enableSSL: true,
  smtpUsername: '',
  smtpPassword: '',
  notificationTypes: ['security_alert', 'system_error']
})

const storageSettings = ref({
  uploadPath: '/uploads',
  maxFileSize: 100,
  allowedFileTypes: '.pdf,.doc,.docx,.txt,.jpg,.png',
  autoCleanup: true,
  retentionDays: 365,
  enableCompression: true,
  autoBackup: true,
  backupInterval: 'daily',
  backupRetention: 30,
  compressBackup: true
})

// 方法
const saveSettings = async () => {
  try {
    saving.value = true
    
    // 模拟保存设置
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存设置失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置到默认值吗？此操作不可恢复。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 重置到默认值
    basicSettings.value = {
      systemName: '系统审查技术平台',
      description: '基于AI的系统审查和技术分析平台',
      version: '1.0.0',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      theme: 'light'
    }
    
    securitySettings.value = {
      minPasswordLength: 8,
      passwordRequirements: ['lowercase', 'numbers'],
      passwordExpiry: 90,
      maxLoginAttempts: 5,
      lockoutDuration: 30,
      sessionTimeout: 30,
      enableWhitelist: false,
      forceHttps: true,
      enable2FA: false,
      enableRateLimit: true,
      enableAuditLog: true,
      enableSecurityAlerts: true
    }
    
    ElMessage.success('设置已重置为默认值')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置设置失败: ' + error.message)
    }
  }
}

// 生命周期
onMounted(() => {
  // 加载设置数据
})
</script>

<style scoped>
.system-settings {
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

.settings-tabs {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.settings-section {
  margin-bottom: 30px;
}

.settings-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 18px;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 10px;
}

.settings-actions {
  text-align: right;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.settings-actions .el-button {
  margin-left: 10px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 20px;
}

:deep(.el-tabs__content) {
  padding-top: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}

@media (max-width: 768px) {
  .system-settings {
    padding: 10px;
  }
  
  .settings-tabs {
    padding: 15px;
  }
  
  :deep(.el-tabs__item) {
    font-size: 14px;
    padding: 0 10px;
  }
  
  :deep(.el-form-item__label) {
    font-size: 14px;
  }
  
  .settings-actions {
    text-align: center;
  }
  
  .settings-actions .el-button {
    margin: 5px;
    width: 120px;
  }
}
</style>