import request from '@/utils/request'

// 审计日志API
export const auditApi = {
  // 获取审计日志列表
  getAuditLogs(params) {
    return request({
      url: '/api/v1/security/audit-logs',
      method: 'get',
      params
    })
  },

  // 获取审计日志详情
  getAuditLogDetail(logId) {
    return request({
      url: `/api/v1/security/audit-logs/${logId}`,
      method: 'get'
    })
  },

  // 导出审计日志
  exportAuditLogs(params) {
    return request({
      url: '/api/v1/security/audit-logs/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  },

  // 获取审计统计数据
  getAuditStatistics(params) {
    return request({
      url: '/api/v1/security/audit-logs/statistics',
      method: 'get',
      params
    })
  },

  // 搜索审计日志
  searchAuditLogs(searchParams) {
    return request({
      url: '/api/v1/security/audit-logs/search',
      method: 'post',
      data: searchParams
    })
  },

  // 获取用户操作历史
  getUserOperationHistory(userId, params) {
    return request({
      url: `/api/v1/security/audit-logs/user/${userId}/history`,
      method: 'get',
      params
    })
  },

  // 获取资源访问日志
  getResourceAccessLogs(resourceType, resourceId, params) {
    return request({
      url: `/api/v1/security/audit-logs/resource/${resourceType}/${resourceId}`,
      method: 'get',
      params
    })
  },

  // 获取失败操作日志
  getFailedOperations(params) {
    return request({
      url: '/api/v1/security/audit-logs/failed-operations',
      method: 'get',
      params
    })
  },

  // 获取高风险操作日志
  getHighRiskOperations(params) {
    return request({
      url: '/api/v1/security/audit-logs/high-risk',
      method: 'get',
      params
    })
  }
}

export default auditApi