import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import router from '@/router'

// 用户认证状态管理
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '[]'))

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')

  // 登录
  const login = async (credentials) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        throw new Error('登录失败')
      }

      const data = await response.json()
      
      token.value = data.access_token
      user.value = data.user
      permissions.value = data.permissions || []

      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))
      localStorage.setItem('permissions', JSON.stringify(permissions.value))

      return data
    } catch (error) {
      console.error('登录错误:', error)
      throw error
    }
  }

  // 登出
  const logout = () => {
    token.value = ''
    user.value = null
    permissions.value = []
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
    
    router.push('/login')
  }

  // 检查权限
  const hasPermission = (permission) => {
    if (isSuperAdmin.value) return true
    return permissions.value.includes(permission)
  }

  // 检查多个权限（任一满足）
  const hasAnyPermission = (permissionList) => {
    if (isSuperAdmin.value) return true
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  // 检查多个权限（全部满足）
  const hasAllPermissions = (permissionList) => {
    if (isSuperAdmin.value) return true
    return permissionList.every(permission => permissions.value.includes(permission))
  }

  return {
    token,
    user,
    permissions,
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    login,
    logout,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  }
})

// 系统状态管理
export const useSystemStore = defineStore('system', () => {
  const loading = ref(false)
  const systemStats = ref({
    totalProjects: 0,
    totalDocuments: 0,
    totalUsers: 0,
    systemUptime: '0天',
  })
  
  const systemStatus = ref({
    database: 'healthy',
    cache: 'healthy',
    storage: 'healthy',
    ai_service: 'healthy',
  })

  const recentActivities = ref([])

  // 设置加载状态
  const setLoading = (state) => {
    loading.value = state
  }

  // 获取系统统计信息
  const fetchSystemStats = async () => {
    try {
      const response = await fetch('/api/v1/system/stats', {
        headers: {
          'Authorization': `Bearer ${useAuthStore().token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        systemStats.value = data
      }
    } catch (error) {
      console.error('获取系统统计信息失败:', error)
    }
  }

  // 获取系统状态
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/health', {
        headers: {
          'Authorization': `Bearer ${useAuthStore().token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        systemStatus.value = data
      }
    } catch (error) {
      console.error('获取系统状态失败:', error)
      // 设置为错误状态
      Object.keys(systemStatus.value).forEach(key => {
        systemStatus.value[key] = 'error'
      })
    }
  }

  // 获取最近活动
  const fetchRecentActivities = async () => {
    try {
      const response = await fetch('/api/v1/system/activities', {
        headers: {
          'Authorization': `Bearer ${useAuthStore().token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        recentActivities.value = data
      }
    } catch (error) {
      console.error('获取最近活动失败:', error)
    }
  }

  return {
    loading,
    systemStats,
    systemStatus,
    recentActivities,
    setLoading,
    fetchSystemStats,
    fetchSystemStatus,
    fetchRecentActivities,
  }
})