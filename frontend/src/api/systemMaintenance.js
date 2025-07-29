import request from '@/utils/request'

/**
 * 系统维护API接口
 */
export const systemMaintenanceApi = {
  /**
   * 获取系统状态
   */
  getSystemStatus() {
    return request({
      url: '/api/v1/system-maintenance/status',
      method: 'get'
    })
  },

  /**
   * 运行健康检查
   */
  runHealthCheck() {
    return request({
      url: '/api/v1/system-maintenance/health',
      method: 'get'
    })
  },

  /**
   * 数据库清理
   * @param {Object} params - 清理参数
   * @param {boolean} params.cleanup_audit_logs - 是否清理审计日志
   * @param {number} params.audit_log_retention_days - 审计日志保留天数
   * @param {boolean} params.cleanup_expired_sessions - 是否清理过期会话
   * @param {boolean} params.cleanup_temp_files - 是否清理临时文件
   * @param {number} params.temp_file_retention_days - 临时文件保留天数
   * @param {boolean} params.vacuum_analyze - 是否执行VACUUM ANALYZE
   */
  cleanupDatabase(params) {
    return request({
      url: '/api/v1/system-maintenance/database/cleanup',
      method: 'post',
      data: params
    })
  },

  /**
   * 执行数据库VACUUM操作
   */
  vacuumDatabase() {
    return request({
      url: '/api/v1/system-maintenance/database/vacuum',
      method: 'post'
    })
  },

  /**
   * 获取数据库状态
   */
  getDatabaseStatus() {
    return request({
      url: '/api/v1/system-maintenance/database/status',
      method: 'get'
    })
  },

  /**
   * 日志轮转
   * @param {Object} params - 轮转参数
   * @param {number} params.max_size_mb - 最大文件大小(MB)
   * @param {number} params.max_files - 最大文件数
   * @param {boolean} params.compress - 是否压缩
   */
  rotateLogs(params) {
    return request({
      url: '/api/v1/system-maintenance/logs/rotate',
      method: 'post',
      data: params
    })
  },

  /**
   * 获取日志状态
   */
  getLogsStatus() {
    return request({
      url: '/api/v1/system-maintenance/logs/status',
      method: 'get'
    })
  },

  /**
   * 创建系统备份
   * @param {Object} params - 备份参数
   * @param {boolean} params.backup_database - 是否备份数据库
   * @param {boolean} params.backup_config - 是否备份配置
   * @param {boolean} params.backup_uploads - 是否备份上传文件
   */
  createBackup(params) {
    return request({
      url: '/api/v1/system-maintenance/backup',
      method: 'post',
      data: params
    })
  },

  /**
   * 获取备份列表
   */
  listBackups() {
    return request({
      url: '/api/v1/system-maintenance/backups/list',
      method: 'get'
    })
  },

  /**
   * 删除备份
   * @param {string} backupName - 备份名称
   */
  deleteBackup(backupName) {
    return request({
      url: `/api/v1/system-maintenance/backups/${backupName}`,
      method: 'delete'
    })
  },

  /**
   * 获取存储状态
   */
  getStorageStatus() {
    return request({
      url: '/api/v1/system-maintenance/storage/status',
      method: 'get'
    })
  },

  /**
   * 获取系统资源信息
   */
  getSystemResources() {
    return request({
      url: '/api/v1/system-maintenance/system/resources',
      method: 'get'
    })
  },

  /**
   * 获取维护指标
   */
  getMaintenanceMetrics() {
    return request({
      url: '/api/v1/system-maintenance/metrics',
      method: 'get'
    })
  },

  /**
   * 获取维护计划
   */
  getMaintenanceSchedule() {
    return request({
      url: '/api/v1/system-maintenance/schedule',
      method: 'get'
    })
  },

  /**
   * 更新维护计划
   * @param {Object} schedule - 计划配置
   */
  updateMaintenanceSchedule(schedule) {
    return request({
      url: '/api/v1/system-maintenance/schedule',
      method: 'put',
      data: schedule
    })
  },

  /**
   * 启用维护计划
   */
  enableMaintenanceSchedule() {
    return request({
      url: '/api/v1/system-maintenance/schedule/enable',
      method: 'post'
    })
  },

  /**
   * 禁用维护计划
   */
  disableMaintenanceSchedule() {
    return request({
      url: '/api/v1/system-maintenance/schedule/disable',
      method: 'post'
    })
  }
}

export default systemMaintenanceApi