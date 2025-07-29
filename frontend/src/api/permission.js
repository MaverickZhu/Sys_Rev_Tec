import request from '@/utils/request'

// 权限管理API
export const permissionApi = {
  // 权限管理
  getPermissions(params) {
    return request({
      url: '/api/v1/permissions',
      method: 'get',
      params
    })
  },

  createPermission(data) {
    return request({
      url: '/api/v1/permissions',
      method: 'post',
      data
    })
  },

  getPermission(permissionId) {
    return request({
      url: `/api/v1/permissions/${permissionId}`,
      method: 'get'
    })
  },

  updatePermission(permissionId, data) {
    return request({
      url: `/api/v1/permissions/${permissionId}`,
      method: 'put',
      data
    })
  },

  deletePermission(permissionId) {
    return request({
      url: `/api/v1/permissions/${permissionId}`,
      method: 'delete'
    })
  },

  // 角色管理
  getRoles(params) {
    return request({
      url: '/api/v1/permissions/roles',
      method: 'get',
      params
    })
  },

  createRole(data) {
    return request({
      url: '/api/v1/permissions/roles',
      method: 'post',
      data
    })
  },

  getRole(roleId) {
    return request({
      url: `/api/v1/permissions/roles/${roleId}`,
      method: 'get'
    })
  },

  updateRole(roleId, data) {
    return request({
      url: `/api/v1/permissions/roles/${roleId}`,
      method: 'put',
      data
    })
  },

  deleteRole(roleId) {
    return request({
      url: `/api/v1/permissions/roles/${roleId}`,
      method: 'delete'
    })
  },

  getRolePermissions(roleId) {
    return request({
      url: `/api/v1/permissions/roles/${roleId}/permissions`,
      method: 'get'
    })
  },

  // 用户权限管理
  getUserPermissions(userId) {
    return request({
      url: `/api/v1/permissions/users/${userId}`,
      method: 'get'
    })
  },

  assignUserRole(userId, data) {
    return request({
      url: `/api/v1/permissions/users/${userId}/role`,
      method: 'post',
      data
    })
  },

  assignUserPermissions(userId, data) {
    return request({
      url: `/api/v1/permissions/users/${userId}/permissions`,
      method: 'post',
      data
    })
  },

  // 资源权限管理
  getResourcePermissions: (params) => {
    return request({
      url: '/api/v1/permissions/resource-permissions',
      method: 'get',
      params
    })
  },

  grantResourcePermission: (data) => {
    return request({
      url: '/api/v1/permissions/resource-permissions',
      method: 'post',
      data
    })
  },

  revokeResourcePermission: (data) => {
    return request({
      url: '/api/v1/permissions/resource-permissions',
      method: 'delete',
      data
    })
  },

  // 权限检查
  checkPermission(data) {
    return request({
      url: '/api/v1/permissions/check-permission',
      method: 'post',
      data
    })
  },

  // 权限统计
  getPermissionStatistics() {
    return request({
      url: '/api/v1/permissions/stats',
      method: 'get'
    })
  },

  // 初始化默认数据
  initializeDefaultData() {
    return request({
      url: '/api/v1/permissions/init-default-data',
      method: 'post'
    })
  },

  // 权限组管理
  getPermissionGroups(params) {
    return request({
      url: '/api/v1/permissions/groups',
      method: 'get',
      params
    })
  },

  createPermissionGroup(data) {
    return request({
      url: '/api/v1/permissions/groups',
      method: 'post',
      data
    })
  },

  updatePermissionGroup(groupId, data) {
    return request({
      url: `/api/v1/permissions/groups/${groupId}`,
      method: 'put',
      data
    })
  },

  deletePermissionGroup(groupId) {
    return request({
      url: `/api/v1/permissions/groups/${groupId}`,
      method: 'delete'
    })
  },

  // 批量操作
  batchAssignPermissions(data) {
    return request({
      url: '/api/v1/permissions/batch/assign',
      method: 'post',
      data
    })
  },

  batchRevokePermissions(data) {
    return request({
      url: '/api/v1/permissions/batch/revoke',
      method: 'post',
      data
    })
  },

  // 权限导入导出
  exportPermissions(params) {
    return request({
      url: '/api/v1/permissions/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  },

  importPermissions(data) {
    return request({
      url: '/api/v1/permissions/import',
      method: 'post',
      data,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 操作日志管理
  getAuditLogs(params) {
    return request({
      url: '/api/v1/security/audit-logs',
      method: 'get',
      params
    })
  },

  exportAuditLogs(params) {
    return request({
      url: '/api/v1/security/audit-logs/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  },

  getAuditLogStatistics(params) {
    return request({
      url: '/api/v1/security/audit-logs/statistics',
      method: 'get',
      params
    })
  }
}

export default permissionApi