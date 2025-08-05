import { useAuthStore } from '@/stores'

// API基础配置
const API_BASE_URL = 'http://127.0.0.1:8001/api/v1'

// 创建请求实例
class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  // 获取请求头
  getHeaders() {
    const authStore = useAuthStore()
    const headers = {
      'Content-Type': 'application/json',
    }
    
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    
    return headers
  }

  // 处理响应
  async handleResponse(response) {
    if (!response.ok) {
      if (response.status === 401) {
        // Token过期，自动登出
        const authStore = useAuthStore()
        authStore.logout()
        throw new Error('认证已过期，请重新登录')
      }
      
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `请求失败: ${response.status}`)
    }
    
    return response.json()
  }

  // GET请求
  async get(url, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const fullUrl = `${this.baseURL}${url}${queryString ? `?${queryString}` : ''}`
    
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: this.getHeaders(),
    })
    
    return this.handleResponse(response)
  }

  // POST请求
  async post(url, data = {}) {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    })
    
    return this.handleResponse(response)
  }

  // PUT请求
  async put(url, data = {}) {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    })
    
    return this.handleResponse(response)
  }

  // DELETE请求
  async delete(url) {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })
    
    return this.handleResponse(response)
  }

  // 文件上传
  async upload(url, formData) {
    const authStore = useAuthStore()
    const headers = {}
    
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'POST',
      headers,
      body: formData,
    })
    
    return this.handleResponse(response)
  }
}

// 创建API服务实例
const apiService = new ApiService()

// 认证相关API
export const authAPI = {
  login: (credentials) => apiService.post('/auth/login/json', credentials),
  logout: () => apiService.post('/auth/logout'),
  refreshToken: () => apiService.post('/auth/refresh'),
  getCurrentUser: () => apiService.get('/auth/me'),
  updateProfile: (data) => apiService.put('/auth/profile', data),
}

// 系统相关API
export const systemAPI = {
  getStats: () => apiService.get('/system/stats'),
  getHealth: () => apiService.get('/system/health'),
  getActivities: () => apiService.get('/system/activities'),
  getSystemInfo: () => apiService.get('/system/info'),
}

// 系统维护相关API
export const maintenanceAPI = {
  // 获取维护状态
  getStatus: () => apiService.get('/maintenance/status'),
  
  // 设置维护模式
  setMaintenanceMode: (enabled, message = '') => 
    apiService.post('/maintenance/mode', { enabled, message }),
  
  // 数据库操作
  backupDatabase: () => apiService.post('/maintenance/database/backup'),
  restoreDatabase: (backupFile) => apiService.post('/maintenance/database/restore', { backup_file: backupFile }),
  optimizeDatabase: () => apiService.post('/maintenance/database/optimize'),
  
  // 缓存操作
  clearCache: (cacheType = 'all') => apiService.post('/maintenance/cache/clear', { cache_type: cacheType }),
  getCacheStats: () => apiService.get('/maintenance/cache/stats'),
  
  // 日志管理
  getLogs: (logType = 'app', limit = 100) => 
    apiService.get('/maintenance/logs', { log_type: logType, limit }),
  clearLogs: (logType = 'app') => apiService.post('/maintenance/logs/clear', { log_type: logType }),
  downloadLogs: (logType = 'app') => apiService.get('/maintenance/logs/download', { log_type: logType }),
  
  // 系统监控
  getSystemMetrics: () => apiService.get('/maintenance/metrics'),
  getPerformanceStats: () => apiService.get('/maintenance/performance'),
  
  // 备份管理
  getBackups: () => apiService.get('/maintenance/backups'),
  deleteBackup: (backupId) => apiService.delete(`/maintenance/backups/${backupId}`),
  downloadBackup: (backupId) => apiService.get(`/maintenance/backups/${backupId}/download`),
}

// 用户管理相关API
export const userAPI = {
  getUsers: (params = {}) => apiService.get('/users', params),
  getUser: (userId) => apiService.get(`/users/${userId}`),
  createUser: (userData) => apiService.post('/users', userData),
  updateUser: (userId, userData) => apiService.put(`/users/${userId}`, userData),
  deleteUser: (userId) => apiService.delete(`/users/${userId}`),
  resetPassword: (userId) => apiService.post(`/users/${userId}/reset-password`),
}

// 权限管理相关API
export const permissionAPI = {
  getPermissions: () => apiService.get('/permissions'),
  getRoles: () => apiService.get('/roles'),
  getUserPermissions: (userId) => apiService.get(`/users/${userId}/permissions`),
  updateUserPermissions: (userId, permissions) => 
    apiService.put(`/users/${userId}/permissions`, { permissions }),
}

// 审计日志相关API
export const auditAPI = {
  getLogs: (params = {}) => apiService.get('/audit/logs', params),
  getLogDetail: (logId) => apiService.get(`/audit/logs/${logId}`),
  exportLogs: (params = {}) => apiService.get('/audit/logs/export', params),
}

// 项目管理相关API
export const projectAPI = {
  getProjects: (params = {}) => apiService.get('/projects', params),
  getProject: (projectId) => apiService.get(`/projects/${projectId}`),
  createProject: (projectData) => apiService.post('/projects', projectData),
  updateProject: (projectId, projectData) => apiService.put(`/projects/${projectId}`, projectData),
  deleteProject: (projectId) => apiService.delete(`/projects/${projectId}`),
}

// 文档管理相关API
export const documentAPI = {
  getDocuments: (params = {}) => apiService.get('/documents', params),
  getDocument: (documentId) => apiService.get(`/documents/${documentId}`),
  uploadDocument: (formData) => apiService.upload('/documents/upload', formData),
  deleteDocument: (documentId) => apiService.delete(`/documents/${documentId}`),
}

export default apiService