<template>
  <div class="action-feedback">
    <!-- 操作确认对话框 -->
    <el-dialog
      v-model="confirmDialog.visible"
      :title="confirmDialog.title"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="confirm-content">
        <div class="confirm-icon">
          <el-icon :size="32" :color="confirmDialog.iconColor">
            <component :is="confirmDialog.icon" />
          </el-icon>
        </div>
        <div class="confirm-message">{{ confirmDialog.message }}</div>
        <div v-if="confirmDialog.details" class="confirm-details">
          {{ confirmDialog.details }}
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleConfirmCancel">取消</el-button>
          <el-button 
            :type="confirmDialog.confirmType" 
            @click="handleConfirmOk"
            :loading="confirmDialog.loading"
          >
            {{ confirmDialog.confirmText }}
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 进度对话框 -->
    <el-dialog
      v-model="progressDialog.visible"
      :title="progressDialog.title"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="progress-content">
        <div class="progress-message">{{ progressDialog.message }}</div>
        <el-progress 
          :percentage="progressDialog.percentage" 
          :status="progressDialog.status"
          :show-text="true"
        />
        <div v-if="progressDialog.details" class="progress-details">
          {{ progressDialog.details }}
        </div>
      </div>
      
      <template #footer v-if="progressDialog.showCancel">
        <div class="dialog-footer">
          <el-button @click="handleProgressCancel">取消</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 结果对话框 -->
    <el-dialog
      v-model="resultDialog.visible"
      :title="resultDialog.title"
      width="450px"
    >
      <div class="result-content">
        <div class="result-icon">
          <el-icon :size="48" :color="resultDialog.iconColor">
            <component :is="resultDialog.icon" />
          </el-icon>
        </div>
        <div class="result-message">{{ resultDialog.message }}</div>
        <div v-if="resultDialog.details" class="result-details">
          <el-scrollbar height="200px">
            <pre>{{ resultDialog.details }}</pre>
          </el-scrollbar>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleResultClose">关闭</el-button>
          <el-button 
            v-if="resultDialog.showRetry" 
            type="primary" 
            @click="handleResultRetry"
          >
            重试
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { 
  QuestionFilled, 
  WarningFilled, 
  InfoFilled, 
  SuccessFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'

// 确认对话框状态
const confirmDialog = reactive({
  visible: false,
  title: '确认操作',
  message: '',
  details: '',
  icon: QuestionFilled,
  iconColor: '#409eff',
  confirmText: '确定',
  confirmType: 'primary',
  loading: false,
  onConfirm: null,
  onCancel: null
})

// 进度对话框状态
const progressDialog = reactive({
  visible: false,
  title: '处理中',
  message: '正在处理，请稍候...',
  details: '',
  percentage: 0,
  status: '',
  showCancel: false,
  onCancel: null
})

// 结果对话框状态
const resultDialog = reactive({
  visible: false,
  title: '操作结果',
  message: '',
  details: '',
  icon: SuccessFilled,
  iconColor: '#67c23a',
  showRetry: false,
  onRetry: null,
  onClose: null
})

// 显示确认对话框
const showConfirm = (options = {}) => {
  Object.assign(confirmDialog, {
    visible: true,
    title: options.title || '确认操作',
    message: options.message || '确定要执行此操作吗？',
    details: options.details || '',
    icon: options.icon || QuestionFilled,
    iconColor: options.iconColor || '#409eff',
    confirmText: options.confirmText || '确定',
    confirmType: options.confirmType || 'primary',
    loading: false,
    onConfirm: options.onConfirm || null,
    onCancel: options.onCancel || null
  })
}

// 显示进度对话框
const showProgress = (options = {}) => {
  Object.assign(progressDialog, {
    visible: true,
    title: options.title || '处理中',
    message: options.message || '正在处理，请稍候...',
    details: options.details || '',
    percentage: options.percentage || 0,
    status: options.status || '',
    showCancel: options.showCancel || false,
    onCancel: options.onCancel || null
  })
}

// 更新进度
const updateProgress = (percentage, message = '', details = '', status = '') => {
  progressDialog.percentage = percentage
  if (message) progressDialog.message = message
  if (details) progressDialog.details = details
  if (status) progressDialog.status = status
}

// 隐藏进度对话框
const hideProgress = () => {
  progressDialog.visible = false
}

// 显示结果对话框
const showResult = (options = {}) => {
  Object.assign(resultDialog, {
    visible: true,
    title: options.title || '操作结果',
    message: options.message || '',
    details: options.details || '',
    icon: options.icon || SuccessFilled,
    iconColor: options.iconColor || '#67c23a',
    showRetry: options.showRetry || false,
    onRetry: options.onRetry || null,
    onClose: options.onClose || null
  })
}

// 显示成功结果
const showSuccess = (message, details = '') => {
  showResult({
    title: '操作成功',
    message,
    details,
    icon: SuccessFilled,
    iconColor: '#67c23a'
  })
}

// 显示错误结果
const showError = (message, details = '', showRetry = false, onRetry = null) => {
  showResult({
    title: '操作失败',
    message,
    details,
    icon: CircleCloseFilled,
    iconColor: '#f56c6c',
    showRetry,
    onRetry
  })
}

// 事件处理
const handleConfirmOk = async () => {
  if (confirmDialog.onConfirm) {
    confirmDialog.loading = true
    try {
      await confirmDialog.onConfirm()
      confirmDialog.visible = false
    } catch (error) {
      console.error('确认操作失败:', error)
    } finally {
      confirmDialog.loading = false
    }
  } else {
    confirmDialog.visible = false
  }
}

const handleConfirmCancel = () => {
  if (confirmDialog.onCancel) {
    confirmDialog.onCancel()
  }
  confirmDialog.visible = false
}

const handleProgressCancel = () => {
  if (progressDialog.onCancel) {
    progressDialog.onCancel()
  }
  progressDialog.visible = false
}

const handleResultClose = () => {
  if (resultDialog.onClose) {
    resultDialog.onClose()
  }
  resultDialog.visible = false
}

const handleResultRetry = () => {
  if (resultDialog.onRetry) {
    resultDialog.onRetry()
  }
  resultDialog.visible = false
}

// 暴露方法
defineExpose({
  showConfirm,
  showProgress,
  updateProgress,
  hideProgress,
  showResult,
  showSuccess,
  showError
})
</script>

<style scoped>
.confirm-content,
.progress-content,
.result-content {
  text-align: center;
  padding: 20px 0;
}

.confirm-icon,
.result-icon {
  margin-bottom: 16px;
}

.confirm-message,
.progress-message,
.result-message {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
  line-height: 1.5;
}

.confirm-details,
.progress-details {
  font-size: 14px;
  color: #666;
  margin-top: 12px;
  line-height: 1.4;
}

.result-details {
  margin-top: 16px;
  text-align: left;
}

.result-details pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  white-space: pre-wrap;
  word-break: break-all;
}

.dialog-footer {
  text-align: right;
}

.dialog-footer .el-button {
  margin-left: 12px;
}
</style>