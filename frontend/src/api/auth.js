import request from '@/utils/request'

// 认证API
export const authApi = {
  // 用户登录
  login(data) {
    return request({
      url: '/api/v1/auth/login',
      method: 'post',
      data
    })
  },

  // 用户登出
  logout() {
    return request({
      url: '/api/v1/auth/logout',
      method: 'post'
    })
  },

  // 刷新token
  refreshToken() {
    return request({
      url: '/api/v1/auth/refresh',
      method: 'post'
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request({
      url: '/api/v1/auth/me',
      method: 'get'
    })
  },

  // 用户注册
  register(data) {
    return request({
      url: '/api/v1/auth/register',
      method: 'post',
      data
    })
  },

  // 忘记密码
  forgotPassword(data) {
    return request({
      url: '/api/v1/auth/forgot-password',
      method: 'post',
      data
    })
  },

  // 重置密码
  resetPassword(data) {
    return request({
      url: '/api/v1/auth/reset-password',
      method: 'post',
      data
    })
  },

  // 修改密码
  changePassword(data) {
    return request({
      url: '/api/v1/auth/change-password',
      method: 'post',
      data
    })
  },

  // 更新用户资料
  updateProfile(data) {
    return request({
      url: '/api/v1/auth/profile',
      method: 'put',
      data
    })
  },

  // 验证邮箱
  verifyEmail(token) {
    return request({
      url: `/api/v1/auth/verify-email/${token}`,
      method: 'post'
    })
  },

  // 重新发送验证邮件
  resendVerificationEmail() {
    return request({
      url: '/api/v1/auth/resend-verification',
      method: 'post'
    })
  },

  // 启用两步验证
  enableTwoFactor() {
    return request({
      url: '/api/v1/auth/2fa/enable',
      method: 'post'
    })
  },

  // 禁用两步验证
  disableTwoFactor(data) {
    return request({
      url: '/api/v1/auth/2fa/disable',
      method: 'post',
      data
    })
  },

  // 验证两步验证码
  verifyTwoFactor(data) {
    return request({
      url: '/api/v1/auth/2fa/verify',
      method: 'post',
      data
    })
  },

  // 获取用户会话列表
  getUserSessions() {
    return request({
      url: '/api/v1/auth/sessions',
      method: 'get'
    })
  },

  // 终止指定会话
  terminateSession(sessionId) {
    return request({
      url: `/api/v1/auth/sessions/${sessionId}`,
      method: 'delete'
    })
  },

  // 终止所有其他会话
  terminateAllOtherSessions() {
    return request({
      url: '/api/v1/auth/sessions/terminate-others',
      method: 'post'
    })
  },

  // 获取登录历史
  getLoginHistory(params) {
    return request({
      url: '/api/v1/auth/login-history',
      method: 'get',
      params
    })
  },

  // 检查用户名是否可用
  checkUsernameAvailability(username) {
    return request({
      url: '/api/v1/auth/check-username',
      method: 'post',
      data: { username }
    })
  },

  // 检查邮箱是否可用
  checkEmailAvailability(email) {
    return request({
      url: '/api/v1/auth/check-email',
      method: 'post',
      data: { email }
    })
  }
}

export default authApi