import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'

export const useUIStore = defineStore('ui', () => {
  // 全局加载状态
  const globalLoading = ref(false)
  const loadingText = ref('加载中...')
  const loadingProgress = ref(null)
  
  // 错误处理状态
  const errorState = reactive({
    visible: false,
    title: '操作失败',
    message: '请求处理时发生错误，请稍后重试',
    details: null,
    showRetry: true,
    showReload: false,
    showGoBack: true,
    retryAction: null
  })
  
  // 页面加载状态管理
  const pageLoadingStates = reactive({})
  
  // 设置全局加载状态
  const setGlobalLoading = (loading, text = '加载中...', progress = null) => {
    globalLoading.value = loading
    loadingText.value = text
    loadingProgress.value = progress
  }
  
  // 显示错误
  const showError = (options = {}) => {
    Object.assign(errorState, {
      visible: true,
      title: options.title || '操作失败',
      message: options.message || '请求处理时发生错误，请稍后重试',
      details: options.details || null,
      showRetry: options.showRetry !== false,
      showReload: options.showReload || false,
      showGoBack: options.showGoBack !== false,
      retryAction: options.retryAction || null
    })
  }
  
  // 隐藏错误
  const hideError = () => {
    errorState.visible = false
  }
  
  // 设置页面加载状态
  const setPageLoading = (page, loading) => {
    pageLoadingStates[page] = loading
  }
  
  // 获取页面加载状态
  const getPageLoading = (page) => {
    return pageLoadingStates[page] || false
  }
  
  // 显示成功消息
  const showSuccess = (message, options = {}) => {
    if (options.type === 'notification') {
      ElNotification({
        title: '成功',
        message,
        type: 'success',
        duration: options.duration || 3000,
        ...options
      })
    } else {
      ElMessage({
        message,
        type: 'success',
        duration: options.duration || 3000,
        ...options
      })
    }
  }
  
  // 显示警告消息
  const showWarning = (message, options = {}) => {
    if (options.type === 'notification') {
      ElNotification({
        title: '警告',
        message,
        type: 'warning',
        duration: options.duration || 4000,
        ...options
      })
    } else {
      ElMessage({
        message,
        type: 'warning',
        duration: options.duration || 4000,
        ...options
      })
    }
  }
  
  // 显示错误消息
  const showErrorMessage = (message, options = {}) => {
    if (options.type === 'notification') {
      ElNotification({
        title: '错误',
        message,
        type: 'error',
        duration: options.duration || 5000,
        ...options
      })
    } else {
      ElMessage({
        message,
        type: 'error',
        duration: options.duration || 5000,
        ...options
      })
    }
  }
  
  // 显示信息消息
  const showInfo = (message, options = {}) => {
    if (options.type === 'notification') {
      ElNotification({
        title: '提示',
        message,
        type: 'info',
        duration: options.duration || 3000,
        ...options
      })
    } else {
      ElMessage({
        message,
        type: 'info',
        duration: options.duration || 3000,
        ...options
      })
    }
  }
  
  // 处理API错误
  const handleApiError = (error, options = {}) => {
    console.error('API错误:', error)
    
    let message = '请求处理时发生错误，请稍后重试'
    let details = null
    
    if (error.response) {
      // 服务器响应错误
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          message = data?.message || '请求参数错误'
          break
        case 401:
          message = '身份验证失败，请重新登录'
          break
        case 403:
          message = '权限不足，无法执行此操作'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = data?.message || '数据验证失败'
          if (data?.errors) {
            details = JSON.stringify(data.errors, null, 2)
          }
          break
        case 500:
          message = '服务器内部错误，请稍后重试'
          break
        default:
          message = data?.message || `请求失败 (${status})`
      }
      
      if (data?.detail && typeof data.detail === 'string') {
        details = data.detail
      }
    } else if (error.request) {
      // 网络错误
      message = '网络连接失败，请检查网络设置'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }
    
    if (options.showModal) {
      showError({
        title: options.title || '请求失败',
        message,
        details,
        ...options
      })
    } else {
      showErrorMessage(message, options)
    }
  }
  
  // 异步操作包装器
  const withLoading = async (asyncFn, loadingText = '处理中...', showGlobalLoading = false) => {
    try {
      if (showGlobalLoading) {
        setGlobalLoading(true, loadingText)
      }
      
      const result = await asyncFn()
      return result
    } catch (error) {
      handleApiError(error)
      throw error
    } finally {
      if (showGlobalLoading) {
        setGlobalLoading(false)
      }
    }
  }
  
  return {
    // 状态
    globalLoading,
    loadingText,
    loadingProgress,
    errorState,
    pageLoadingStates,
    
    // 方法
    setGlobalLoading,
    showError,
    hideError,
    setPageLoading,
    getPageLoading,
    showSuccess,
    showWarning,
    showErrorMessage,
    showInfo,
    handleApiError,
    withLoading
  }
})