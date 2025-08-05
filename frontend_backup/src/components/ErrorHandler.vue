<template>
  <div v-if="visible" class="error-overlay">
    <div class="error-content">
      <div class="error-icon">
        <el-icon :size="48" color="#f56c6c">
          <WarningFilled />
        </el-icon>
      </div>
      
      <div class="error-title">{{ title }}</div>
      
      <div class="error-message">{{ message }}</div>
      
      <div v-if="details" class="error-details">
        <el-collapse>
          <el-collapse-item title="错误详情" name="details">
            <pre>{{ details }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <div class="error-actions">
        <el-button 
          v-if="showRetry" 
          type="primary" 
          @click="handleRetry"
          :loading="retrying"
        >
          重试
        </el-button>
        
        <el-button 
          v-if="showReload" 
          type="warning" 
          @click="handleReload"
        >
          刷新页面
        </el-button>
        
        <el-button 
          v-if="showGoBack" 
          @click="handleGoBack"
        >
          返回上页
        </el-button>
        
        <el-button 
          @click="handleClose"
        >
          关闭
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { WarningFilled } from '@element-plus/icons-vue'

const router = useRouter()
const retrying = ref(false)

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '操作失败'
  },
  message: {
    type: String,
    default: '请求处理时发生错误，请稍后重试'
  },
  details: {
    type: String,
    default: null
  },
  showRetry: {
    type: Boolean,
    default: true
  },
  showReload: {
    type: Boolean,
    default: false
  },
  showGoBack: {
    type: Boolean,
    default: true
  },
  retryAction: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['close', 'retry'])

const handleRetry = async () => {
  if (props.retryAction) {
    retrying.value = true
    try {
      await props.retryAction()
      emit('close')
    } catch (error) {
      console.error('重试失败:', error)
    } finally {
      retrying.value = false
    }
  } else {
    emit('retry')
  }
}

const handleReload = () => {
  window.location.reload()
}

const handleGoBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/dashboard')
  }
}

const handleClose = () => {
  emit('close')
}
</script>

<style scoped>
.error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
  animation: fadeIn 0.3s ease;
}

.error-content {
  background: white;
  border-radius: 12px;
  padding: 40px;
  max-width: 500px;
  width: 90%;
  text-align: center;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

.error-icon {
  margin-bottom: 20px;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.error-message {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 24px;
}

.error-details {
  margin-bottom: 24px;
  text-align: left;
}

.error-details pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-content {
    padding: 30px 20px;
    width: 95%;
  }
  
  .error-title {
    font-size: 18px;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .error-actions .el-button {
    width: 100%;
  }
}
</style>