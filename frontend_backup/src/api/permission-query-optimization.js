/**
 * 权限查询性能优化API客户端
 */

import request from '@/utils/request'

export const permissionQueryOptimizationApi = {
  /**
   * 批量权限检查
   * @param {Object} data - 批量检查请求数据
   * @param {Array} data.user_ids - 用户ID列表
   * @param {Array} data.permission_codes - 权限代码列表
   * @param {string} data.mode - 检查模式 (fast/accurate/balanced)
   * @param {string} data.strategy - 检查策略 (parallel/sequential/batch_optimized)
   * @param {boolean} data.use_cache - 是否使用缓存
   * @param {boolean} data.preload_missing - 是否预加载缺失数据
   * @returns {Promise}
   */
  batchCheckPermissions(data) {
    return request({
      url: '/api/v1/permission-query-optimization/batch-check',
      method: 'post',
      data
    })
  },

  /**
   * 批量资源权限检查
   * @param {Object} data - 批量资源检查请求数据
   * @param {Array} data.user_ids - 用户ID列表
   * @param {Array} data.resource_checks - 资源检查列表
   * @param {string} data.mode - 检查模式
   * @returns {Promise}
   */
  batchCheckResourcePermissions(data) {
    return request({
      url: '/api/v1/permission-query-optimization/batch-check-resources',
      method: 'post',
      data
    })
  },

  /**
   * 请求权限预加载
   * @param {Object} data - 预加载请求数据
   * @param {Array} data.user_ids - 用户ID列表
   * @param {Array} data.permission_codes - 权限代码列表（可选）
   * @param {number} data.priority - 优先级 (1-5)
   * @returns {Promise}
   */
  requestPreload(data) {
    return request({
      url: '/api/v1/permission-query-optimization/preload',
      method: 'post',
      data
    })
  },

  /**
   * 自动预加载（基于访问模式）
   * @returns {Promise}
   */
  autoPreload() {
    return request({
      url: '/api/v1/permission-query-optimization/auto-preload',
      method: 'post'
    })
  },

  /**
   * 获取预加载统计信息
   * @returns {Promise}
   */
  getPreloadStats() {
    return request({
      url: '/api/v1/permission-query-optimization/preload/stats',
      method: 'get'
    })
  },

  /**
   * 获取访问模式分析
   * @returns {Promise}
   */
  getAccessPatterns() {
    return request({
      url: '/api/v1/permission-query-optimization/preload/patterns',
      method: 'get'
    })
  },

  /**
   * 获取批量检查统计信息
   * @returns {Promise}
   */
  getBatchCheckStats() {
    return request({
      url: '/api/v1/permission-query-optimization/batch-check/stats',
      method: 'get'
    })
  },

  /**
   * 获取查询优化器统计信息
   * @returns {Promise}
   */
  getQueryOptimizerStats() {
    return request({
      url: '/api/v1/permission-query-optimization/query-optimizer/stats',
      method: 'get'
    })
  },

  /**
   * 权限使用分析
   * @param {number} days - 分析天数
   * @returns {Promise}
   */
  getUsageAnalysis(days = 30) {
    return request({
      url: '/api/v1/permission-query-optimization/usage-analysis',
      method: 'get',
      params: { days }
    })
  },

  /**
   * 获取索引优化建议
   * @returns {Promise}
   */
  getIndexSuggestions() {
    return request({
      url: '/api/v1/permission-query-optimization/index-suggestions',
      method: 'get'
    })
  },

  /**
   * 应用索引优化
   * @returns {Promise}
   */
  applyIndexOptimizations() {
    return request({
      url: '/api/v1/permission-query-optimization/apply-index-optimizations',
      method: 'post'
    })
  },

  /**
   * 更新优化配置
   * @param {Object} config - 配置数据
   * @param {number} config.max_batch_size - 最大批量大小
   * @param {number} config.max_users_per_batch - 每批最大用户数
   * @param {number} config.max_permissions_per_batch - 每批最大权限数
   * @param {number} config.cache_ttl - 缓存TTL
   * @param {boolean} config.enable_preloading - 启用预加载
   * @param {number} config.parallel_threshold - 并行处理阈值
   * @param {number} config.optimization_level - 优化级别
   * @returns {Promise}
   */
  updateConfig(config) {
    return request({
      url: '/api/v1/permission-query-optimization/config',
      method: 'put',
      data: config
    })
  },

  /**
   * 重置统计信息
   * @returns {Promise}
   */
  resetStats() {
    return request({
      url: '/api/v1/permission-query-optimization/reset-stats',
      method: 'post'
    })
  },

  /**
   * 获取用户权限摘要
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  getUserPermissionSummary(userId) {
    return request({
      url: `/api/v1/permission-query-optimization/user/${userId}/summary`,
      method: 'get'
    })
  },

  /**
   * 优化系统健康检查
   * @returns {Promise}
   */
  getHealthStatus() {
    return request({
      url: '/api/v1/permission-query-optimization/health',
      method: 'get'
    })
  },

  // 便捷方法

  /**
   * 检查单个用户的多个权限
   * @param {number} userId - 用户ID
   * @param {Array} permissionCodes - 权限代码列表
   * @param {Object} options - 检查选项
   * @returns {Promise}
   */
  checkUserPermissions(userId, permissionCodes, options = {}) {
    return this.batchCheckPermissions({
      user_ids: [userId],
      permission_codes: permissionCodes,
      mode: options.mode || 'balanced',
      strategy: options.strategy || 'batch_optimized',
      use_cache: options.use_cache !== false,
      preload_missing: options.preload_missing !== false
    })
  },

  /**
   * 检查多个用户的单个权限
   * @param {Array} userIds - 用户ID列表
   * @param {string} permissionCode - 权限代码
   * @param {Object} options - 检查选项
   * @returns {Promise}
   */
  checkUsersPermission(userIds, permissionCode, options = {}) {
    return this.batchCheckPermissions({
      user_ids: userIds,
      permission_codes: [permissionCode],
      mode: options.mode || 'balanced',
      strategy: options.strategy || 'batch_optimized',
      use_cache: options.use_cache !== false,
      preload_missing: options.preload_missing !== false
    })
  },

  /**
   * 预加载用户权限
   * @param {number} userId - 用户ID
   * @param {number} priority - 优先级
   * @returns {Promise}
   */
  preloadUserPermissions(userId, priority = 3) {
    return this.requestPreload({
      user_ids: [userId],
      priority
    })
  },

  /**
   * 批量预加载用户权限
   * @param {Array} userIds - 用户ID列表
   * @param {Array} permissionCodes - 权限代码列表（可选）
   * @param {number} priority - 优先级
   * @returns {Promise}
   */
  batchPreloadPermissions(userIds, permissionCodes = null, priority = 3) {
    return this.requestPreload({
      user_ids: userIds,
      permission_codes: permissionCodes,
      priority
    })
  },

  /**
   * 获取完整的性能报告
   * @param {number} days - 分析天数
   * @returns {Promise}
   */
  async getPerformanceReport(days = 30) {
    try {
      const [healthStatus, batchStats, preloadStats, optimizerStats, usageAnalysis] = await Promise.all([
        this.getHealthStatus(),
        this.getBatchCheckStats(),
        this.getPreloadStats(),
        this.getQueryOptimizerStats(),
        this.getUsageAnalysis(days)
      ])

      return {
        success: true,
        data: {
          health: healthStatus.data,
          batch_check: batchStats.data,
          preload: preloadStats.data,
          query_optimizer: optimizerStats.data,
          usage_analysis: usageAnalysis.data,
          generated_at: new Date().toISOString()
        }
      }
    } catch (error) {
      console.error('获取性能报告失败:', error)
      return {
        success: false,
        error: error.message
      }
    }
  },

  /**
   * 执行完整的系统优化
   * @param {Object} options - 优化选项
   * @returns {Promise}
   */
  async performFullOptimization(options = {}) {
    try {
      const results = []

      // 1. 自动预加载
      if (options.autoPreload !== false) {
        const preloadResult = await this.autoPreload()
        results.push({ step: 'auto_preload', result: preloadResult })
      }

      // 2. 应用索引优化（如果启用）
      if (options.applyIndexOptimizations === true) {
        const indexResult = await this.applyIndexOptimizations()
        results.push({ step: 'index_optimization', result: indexResult })
      }

      // 3. 更新配置（如果提供）
      if (options.config) {
        const configResult = await this.updateConfig(options.config)
        results.push({ step: 'config_update', result: configResult })
      }

      return {
        success: true,
        data: {
          optimization_steps: results,
          completed_at: new Date().toISOString()
        }
      }
    } catch (error) {
      console.error('系统优化失败:', error)
      return {
        success: false,
        error: error.message
      }
    }
  }
}

export default permissionQueryOptimizationApi