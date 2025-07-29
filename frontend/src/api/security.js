import request from '@/utils/request'

// 安全监控API
export const securityApi = {
  // 获取安全仪表板数据
  getDashboardData() {
    return request({
      url: '/api/v1/security/dashboard',
      method: 'get'
    })
  },

  // 获取安全事件列表
  getSecurityEvents(params) {
    return request({
      url: '/api/v1/security/events',
      method: 'get',
      params
    })
  },

  // 解决安全事件
  resolveSecurityEvent(eventId, data) {
    return request({
      url: `/api/v1/security/events/${eventId}/resolve`,
      method: 'post',
      data
    })
  },

  // 运行威胁检测
  runThreatDetection() {
    return request({
      url: '/api/v1/security/threat-detection',
      method: 'post'
    })
  },

  // 获取威胁检测结果
  getThreatDetectionResults() {
    return request({
      url: '/api/v1/security/threat-detection/results',
      method: 'get'
    })
  },

  // 获取用户活动统计
  getUserActivities(params) {
    return request({
      url: '/api/v1/security/user-activities',
      method: 'get',
      params
    })
  },

  // 获取安全趋势数据
  getSecurityTrends(params) {
    return request({
      url: '/api/v1/security/trends',
      method: 'get',
      params
    })
  },

  // 获取安全统计数据
  getSecurityStatistics() {
    return request({
      url: '/api/v1/security/statistics',
      method: 'get'
    })
  }
}

export default securityApi