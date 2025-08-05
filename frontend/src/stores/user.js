import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI, permissionAPI } from '@/api'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('authToken') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '[]'))
  const roles = ref(JSON.parse(localStorage.getItem('roles') || '[]'))
  
  // 计算属性
  const isLoggedIn = computed(() => {
    return !!token.value && !!userInfo.value
  })
  
  const userName = computed(() => {
    return userInfo.value?.username || ''
  })
  
  const userRole = computed(() => {
    return userInfo.value?.primary_role?.name || ''
  })
  
  const isAdmin = computed(() => {
    return roles.value.some(role => 
      role.code === 'SUPER_ADMIN' || role.code === 'SYSTEM_ADMIN'
    )
  })
  
  // 方法
  const setToken = (newToken) => {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('authToken', newToken)
    } else {
      localStorage.removeItem('authToken')
    }
  }
  
  const setUserInfo = (info) => {
    userInfo.value = info
    if (info) {
      localStorage.setItem('userInfo', JSON.stringify(info))
    } else {
      localStorage.removeItem('userInfo')
    }
  }
  
  const setPermissions = (perms) => {
    permissions.value = perms
    if (perms) {
      localStorage.setItem('permissions', JSON.stringify(perms))
    } else {
      localStorage.removeItem('permissions')
    }
  }
  
  const setRoles = (userRoles) => {
    roles.value = userRoles
    if (userRoles) {
      localStorage.setItem('roles', JSON.stringify(userRoles))
    } else {
      localStorage.removeItem('roles')
    }
  }
  
  // 登录
  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials)
      const { access_token, user } = response
      
      setToken(access_token)
      setUserInfo(user)
      
      // 获取用户权限
      await loadUserPermissions()
      
      return response
    } catch (error) {
      throw error
    }
  }
  
  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authAPI.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地数据
      setToken('')
      setUserInfo(null)
      setPermissions([])
      setRoles([])
    }
  }
  
  // 刷新token
  const refreshToken = async () => {
    try {
      const response = await authAPI.refreshToken()
      const { access_token } = response
      setToken(access_token)
      return response
    } catch (error) {
      // 刷新失败，清除登录状态
      await logout()
      throw error
    }
  }
  
  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await authAPI.getCurrentUser()
      setUserInfo(response)
      return response
    } catch (error) {
      throw error
    }
  }
  
  // 加载用户权限
  const loadUserPermissions = async () => {
    if (!userInfo.value?.id) return
    
    try {
      const response = await permissionAPI.getUserPermissions(userInfo.value.id)
      const { permissions: userPermissions, roles: userRoles } = response
      
      setPermissions(userPermissions || [])
      setRoles(userRoles || [])
    } catch (error) {
      console.error('加载用户权限失败:', error)
      setPermissions([])
      setRoles([])
    }
  }
  
  // 检查权限
  const hasPermission = (permission) => {
    if (isAdmin.value) return true
    return permissions.value.some(p => p.code === permission)
  }
  
  // 检查多个权限（任一满足）
  const hasAnyPermission = (permissionList) => {
    if (isAdmin.value) return true
    return permissionList.some(permission => hasPermission(permission))
  }
  
  // 检查多个权限（全部满足）
  const hasAllPermissions = (permissionList) => {
    if (isAdmin.value) return true
    return permissionList.every(permission => hasPermission(permission))
  }
  
  // 检查角色
  const hasRole = (roleCode) => {
    return roles.value.some(role => role.code === roleCode)
  }
  
  // 检查权限（异步，用于路由守卫）
  const checkPermissions = async (requiredPermissions) => {
    // 如果没有权限数据，尝试重新加载
    if (permissions.value.length === 0 && userInfo.value?.id) {
      await loadUserPermissions()
    }
    
    // 管理员拥有所有权限
    if (isAdmin.value) return true
    
    // 检查是否有任一所需权限
    return hasAnyPermission(requiredPermissions)
  }
  
  // 检查资源权限
  const checkResourcePermission = async (resourceType, resourceId, action) => {
    try {
      const response = await permissionAPI.checkPermission({
        resource_type: resourceType,
        resource_id: resourceId,
        action: action
      })
      return response.has_permission
    } catch (error) {
      console.error('检查资源权限失败:', error)
      return false
    }
  }
  
  // 更新用户信息
  const updateUserInfo = async (updateData) => {
    try {
      const response = await authApi.updateProfile(updateData)
      setUserInfo(response)
      ElMessage.success('用户信息更新成功')
      return response
    } catch (error) {
      throw error
    }
  }
  
  // 修改密码
  const changePassword = async (passwordData) => {
    try {
      const response = await authApi.changePassword(passwordData)
      ElMessage.success('密码修改成功')
      return response
    } catch (error) {
      throw error
    }
  }
  
  // 初始化用户状态
  const initializeUser = async () => {
    if (token.value && userInfo.value) {
      try {
        // 验证token有效性
        await getUserInfo()
        // 加载权限
        await loadUserPermissions()
      } catch (error) {
        // token无效，清除登录状态
        await logout()
      }
    }
  }
  
  return {
    // 状态
    token,
    userInfo,
    permissions,
    roles,
    
    // 计算属性
    isLoggedIn,
    userName,
    userRole,
    isAdmin,
    
    // 方法
    setToken,
    setUserInfo,
    setPermissions,
    setRoles,
    login,
    logout,
    refreshToken,
    getUserInfo,
    loadUserPermissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    checkPermissions,
    checkResourcePermission,
    updateUserInfo,
    changePassword,
    initializeUser
  }
})