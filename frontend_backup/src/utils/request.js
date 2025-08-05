import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 添加认证token
    const userStore = useUserStore()
    const token = userStore.token || localStorage.getItem('token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()
    
    // 添加时间戳防止缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  error => {
    console.error('请求配置错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { data, status } = response
    
    // 处理成功响应
    if (status === 200) {
      // 检查业务状态码
      if (data.code === 0 || data.success === true || !data.hasOwnProperty('code')) {
        return data
      } else {
        // 业务错误处理
        const errorMessage = data.message || '操作失败'
        ElMessage.error(errorMessage)
        return Promise.reject(new Error(errorMessage))
      }
    }
    
    return data
  },
  error => {
    console.error('响应错误:', error)
    
    // 处理HTTP错误状态码
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转登录
          handleUnauthorized()
          break
        case 403:
          ElMessage.error('权限不足，无法访问该资源')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // 表单验证错误
          handleValidationError(data)
          break
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器内部错误，请联系管理员')
          break
        case 502:
        case 503:
        case 504:
          ElMessage.error('服务暂时不可用，请稍后再试')
          break
        default:
          const errorMessage = data?.message || `请求失败 (${status})`
          ElMessage.error(errorMessage)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败，请检查网络设置')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// 处理未授权错误
function handleUnauthorized() {
  const userStore = useUserStore()
  
  ElMessageBox.confirm(
    '登录状态已过期，请重新登录',
    '提示',
    {
      confirmButtonText: '重新登录',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 清除用户信息
    userStore.logout()
    // 跳转到登录页
    router.push('/login')
  }).catch(() => {
    // 用户取消，也清除token
    userStore.logout()
  })
}

// 处理表单验证错误
function handleValidationError(data) {
  if (data && data.errors) {
    // 显示第一个验证错误
    const firstError = Object.values(data.errors)[0]
    if (Array.isArray(firstError) && firstError.length > 0) {
      ElMessage.error(firstError[0])
    } else {
      ElMessage.error('表单验证失败')
    }
  } else {
    ElMessage.error(data?.message || '表单验证失败')
  }
}

// 生成请求ID
function generateRequestId() {
  return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

// 导出请求实例
export default request

// 导出便捷方法
export const get = (url, params = {}, config = {}) => {
  return request({
    method: 'get',
    url,
    params,
    ...config
  })
}

export const post = (url, data = {}, config = {}) => {
  return request({
    method: 'post',
    url,
    data,
    ...config
  })
}

export const put = (url, data = {}, config = {}) => {
  return request({
    method: 'put',
    url,
    data,
    ...config
  })
}

export const del = (url, config = {}) => {
  return request({
    method: 'delete',
    url,
    ...config
  })
}

// 文件上传方法
export const upload = (url, formData, config = {}) => {
  return request({
    method: 'post',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    ...config
  })
}

// 下载文件方法
export const download = (url, params = {}, filename = '') => {
  return request({
    method: 'get',
    url,
    params,
    responseType: 'blob'
  }).then(response => {
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  })
}