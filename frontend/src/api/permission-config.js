import request from '@/utils/request'

/**
 * 权限配置管理API
 */

// 获取权限配置
export function getPermissionConfig(params) {
  return request({
    url: '/api/v1/permission-config/config',
    method: 'get',
    params
  })
}

// 获取配置摘要
export function getConfigSummary() {
  return request({
    url: '/api/v1/permission-config/config/summary',
    method: 'get'
  })
}

// 获取配置级别
export function getConfigLevels() {
  return request({
    url: '/api/v1/permission-config/config/levels',
    method: 'get'
  })
}

// 更新权限配置
export function updatePermissionConfig(data) {
  return request({
    url: '/api/v1/permission-config/config',
    method: 'put',
    data
  })
}

// 重新加载配置
export function reloadPermissionConfig() {
  return request({
    url: '/api/v1/permission-config/config/reload',
    method: 'post'
  })
}

// 导出权限配置
export function exportPermissionConfig(data) {
  return request({
    url: '/api/v1/permission-config/config/export',
    method: 'post',
    data
  })
}

// 导入权限配置
export function importPermissionConfig(data) {
  return request({
    url: '/api/v1/permission-config/config/import',
    method: 'post',
    data
  })
}

// 验证权限配置
export function validatePermissionConfig(configData, level = 'application') {
  return request({
    url: '/api/v1/permission-config/config/validate',
    method: 'post',
    data: configData,
    params: { level }
  })
}

// 获取配置模板
export function getConfigTemplate(level = 'application') {
  return request({
    url: '/api/v1/permission-config/config/template',
    method: 'get',
    params: { level }
  })
}