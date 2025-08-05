import { AxiosResponse } from 'axios';
import { authService } from './authService';
import type {
  User,
  Role,
  Permission,
  CreateUserRequest,
  UpdateUserRequest,
  UserListResponse,
  UserStats
} from '../types';

class UserService {
  private api = authService.getApiInstance();

  // 获取用户列表
  async getUsers(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    department?: string;
    role?: string;
    is_active?: boolean;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<AxiosResponse<UserListResponse>> {
    return this.api.get('/users', { params });
  }

  // 获取单个用户详情
  async getUser(userId: number): Promise<AxiosResponse<User>> {
    return this.api.get(`/users/${userId}`);
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<AxiosResponse<User>> {
    return this.api.get('/users/me');
  }

  // 创建用户
  async createUser(userData: CreateUserRequest): Promise<AxiosResponse<User>> {
    return this.api.post('/users', userData);
  }

  // 更新用户信息
  async updateUser(
    userId: number,
    userData: UpdateUserRequest
  ): Promise<AxiosResponse<User>> {
    return this.api.put(`/users/${userId}`, userData);
  }

  // 更新当前用户信息
  async updateCurrentUser(userData: UpdateUserRequest): Promise<AxiosResponse<User>> {
    return this.api.put('/users/me', userData);
  }

  // 删除用户
  async deleteUser(userId: number): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}`);
  }

  // 激活/停用用户
  async toggleUserStatus(
    userId: number,
    isActive: boolean
  ): Promise<AxiosResponse<User>> {
    return this.api.patch(`/users/${userId}/status`, { is_active: isActive });
  }

  // 重置用户密码
  async resetUserPassword(
    userId: number,
    newPassword: string
  ): Promise<AxiosResponse<void>> {
    return this.api.post(`/users/${userId}/reset-password`, {
      new_password: newPassword,
    });
  }

  // 批量操作用户
  async batchUpdateUsers(
    userIds: number[],
    operation: 'activate' | 'deactivate' | 'delete',
    data?: any
  ): Promise<AxiosResponse<{ success_count: number; failed_count: number }>> {
    return this.api.post('/users/batch', {
      user_ids: userIds,
      operation,
      data,
    });
  }

  // 获取用户角色列表
  async getUserRoles(userId: number): Promise<AxiosResponse<Role[]>> {
    return this.api.get(`/users/${userId}/roles`);
  }

  // 获取所有角色列表
  async getRoles(): Promise<AxiosResponse<Role[]>> {
    return this.api.get('/permissions/roles');
  }

  // 分配角色给用户
  async assignRoleToUser(
    userId: number,
    roleId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.post(`/users/${userId}/roles`, { role_id: roleId });
  }

  // 移除用户角色
  async removeRoleFromUser(
    userId: number,
    roleId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/roles/${roleId}`);
  }

  // 获取用户权限列表
  async getUserPermissions(userId: number): Promise<AxiosResponse<Permission[]>> {
    return this.api.get(`/users/${userId}/permissions`);
  }

  // 检查用户权限
  async checkUserPermission(
    userId: number,
    permission: string
  ): Promise<AxiosResponse<{ has_permission: boolean }>> {
    return this.api.get(`/users/${userId}/permissions/${permission}`);
  }

  // 获取用户统计信息
  async getUserStats(userId: number): Promise<AxiosResponse<UserStats>> {
    return this.api.get(`/users/${userId}/stats`);
  }

  // 获取用户活动记录
  async getUserActivities(
    userId: number,
    params?: {
      skip?: number;
      limit?: number;
      action_type?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    action_type: string;
    description: string;
    resource_type?: string;
    resource_id?: number;
    ip_address: string;
    user_agent: string;
    created_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/activities`, { params });
  }

  // 获取用户项目列表
  async getUserProjects(
    userId: number,
    params?: {
      skip?: number;
      limit?: number;
      role?: string;
      status?: string;
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    name: string;
    description?: string;
    status: string;
    role: string;
    joined_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/projects`, { params });
  }

  // 上传指定用户头像
  async uploadUserAvatar(
    userId: number,
    file: File
  ): Promise<AxiosResponse<{ avatar_url: string }>> {
    const formData = new FormData();
    formData.append('avatar', file);

    return this.api.post(`/users/${userId}/avatar`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 删除用户头像
  async deleteAvatar(userId: number): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/avatar`);
  }

  // 获取用户偏好设置
  async getUserPreferences(
    userId: number
  ): Promise<AxiosResponse<Record<string, any>>> {
    return this.api.get(`/users/${userId}/preferences`);
  }

  // 更新用户偏好设置
  async updateUserPreferences(
    userId: number,
    preferences: Record<string, any>
  ): Promise<AxiosResponse<Record<string, any>>> {
    return this.api.put(`/users/${userId}/preferences`, preferences);
  }

  // 获取用户通知设置
  async getUserNotificationSettings(
    userId: number
  ): Promise<AxiosResponse<{
    email_notifications: boolean;
    push_notifications: boolean;
    sms_notifications: boolean;
    notification_types: Record<string, boolean>;
  }>> {
    return this.api.get(`/users/${userId}/notification-settings`);
  }

  // 更新用户通知设置
  async updateUserNotificationSettings(
    userId: number,
    settings: {
      email_notifications?: boolean;
      push_notifications?: boolean;
      sms_notifications?: boolean;
      notification_types?: Record<string, boolean>;
    }
  ): Promise<AxiosResponse<void>> {
    return this.api.put(`/users/${userId}/notification-settings`, settings);
  }

  // 获取用户会话列表
  async getUserSessions(
    userId: number
  ): Promise<AxiosResponse<Array<{
    id: string;
    ip_address: string;
    user_agent: string;
    location?: string;
    is_current: boolean;
    created_at: string;
    last_activity_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/sessions`);
  }

  // 终止用户会话
  async terminateUserSession(
    userId: number,
    sessionId: string
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/sessions/${sessionId}`);
  }

  // 终止用户所有会话
  async terminateAllUserSessions(userId: number): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/sessions`);
  }

  // 启用/禁用用户两步验证
  async toggleTwoFactorAuth(
    userId: number,
    enabled: boolean,
    secret?: string
  ): Promise<AxiosResponse<{
    enabled: boolean;
    secret?: string;
    qr_code?: string;
    backup_codes?: string[];
  }>> {
    return this.api.post(`/users/${userId}/2fa`, {
      enabled,
      secret,
    });
  }

  // 验证两步验证码
  async verifyTwoFactorCode(
    userId: number,
    code: string
  ): Promise<AxiosResponse<{ valid: boolean }>> {
    return this.api.post(`/users/${userId}/2fa/verify`, { code });
  }

  // 生成两步验证备用码
  async generateBackupCodes(
    userId: number
  ): Promise<AxiosResponse<{ backup_codes: string[] }>> {
    return this.api.post(`/users/${userId}/2fa/backup-codes`);
  }

  // 搜索用户
  async searchUsers(
    query: string,
    params?: {
      department?: string;
      role?: string;
      is_active?: boolean;
      limit?: number;
    }
  ): Promise<AxiosResponse<User[]>> {
    return this.api.get('/users/search', {
      params: { q: query, ...params },
    });
  }

  // 获取部门列表
  async getDepartments(): Promise<AxiosResponse<Array<{
    name: string;
    user_count: number;
  }>>> {
    return this.api.get('/users/departments');
  }

  // 获取职位列表
  async getPositions(): Promise<AxiosResponse<Array<{
    name: string;
    user_count: number;
  }>>> {
    return this.api.get('/users/positions');
  }

  // 导出用户数据
  async exportUsers(
    format: 'csv' | 'xlsx' | 'json',
    filters?: Record<string, any>
  ): Promise<AxiosResponse<Blob>> {
    return this.api.get('/users/export', {
      params: { format, ...filters },
      responseType: 'blob',
    });
  }

  // 导入用户数据
  async importUsers(file: File): Promise<AxiosResponse<{
    success_count: number;
    failed_count: number;
    errors: Array<{
      row: number;
      field: string;
      message: string;
    }>;
  }>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.api.post('/users/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 获取用户登录历史
  async getUserLoginHistory(
    userId: number,
    params?: {
      skip?: number;
      limit?: number;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    ip_address: string;
    user_agent: string;
    location?: string;
    success: boolean;
    failure_reason?: string;
    created_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/login-history`, { params });
  }

  // 锁定用户账户
  async lockUser(
    userId: number,
    reason?: string,
    duration?: number
  ): Promise<AxiosResponse<void>> {
    return this.api.post(`/users/${userId}/lock`, {
      reason,
      duration,
    });
  }

  // 解锁用户账户
  async unlockUser(userId: number): Promise<AxiosResponse<void>> {
    return this.api.post(`/users/${userId}/unlock`);
  }

  // 获取用户安全日志
  async getUserSecurityLogs(
    userId: number,
    params?: {
      skip?: number;
      limit?: number;
      event_type?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    event_type: string;
    description: string;
    ip_address: string;
    user_agent: string;
    risk_level: 'low' | 'medium' | 'high';
    created_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/security-logs`, { params });
  }

  // 发送用户通知
  async sendUserNotification(
    userId: number,
    notification: {
      title: string;
      message: string;
      type: 'info' | 'success' | 'warning' | 'error';
      action_url?: string;
    }
  ): Promise<AxiosResponse<void>> {
    return this.api.post(`/users/${userId}/notifications`, notification);
  }

  // 批量发送通知
  async sendBulkNotification(
    userIds: number[],
    notification: {
      title: string;
      message: string;
      type: 'info' | 'success' | 'warning' | 'error';
      action_url?: string;
    }
  ): Promise<AxiosResponse<{ sent_count: number; failed_count: number }>> {
    return this.api.post('/users/notifications/bulk', {
      user_ids: userIds,
      ...notification,
    });
  }

  // 获取用户标签
  async getUserTags(
    userId: number
  ): Promise<AxiosResponse<Array<{
    id: number;
    name: string;
    color: string;
  }>>> {
    return this.api.get(`/users/${userId}/tags`);
  }

  // 添加用户标签
  async addUserTag(
    userId: number,
    tagData: {
      name: string;
      color?: string;
    }
  ): Promise<AxiosResponse<{
    id: number;
    name: string;
    color: string;
  }>> {
    return this.api.post(`/users/${userId}/tags`, tagData);
  }

  // 移除用户标签
  async removeUserTag(
    userId: number,
    tagId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/tags/${tagId}`);
  }

  // 获取用户备注
  async getUserNotes(
    userId: number
  ): Promise<AxiosResponse<Array<{
    id: number;
    content: string;
    author: {
      id: number;
      username: string;
      full_name: string;
    };
    created_at: string;
    updated_at: string;
  }>>> {
    return this.api.get(`/users/${userId}/notes`);
  }

  // 添加用户备注
  async addUserNote(
    userId: number,
    content: string
  ): Promise<AxiosResponse<{
    id: number;
    content: string;
    author: {
      id: number;
      username: string;
      full_name: string;
    };
    created_at: string;
  }>> {
    return this.api.post(`/users/${userId}/notes`, { content });
  }

  // 更新用户备注
  async updateUserNote(
    userId: number,
    noteId: number,
    content: string
  ): Promise<AxiosResponse<void>> {
    return this.api.put(`/users/${userId}/notes/${noteId}`, { content });
  }

  // 删除用户备注
  async deleteUserNote(
    userId: number,
    noteId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/users/${userId}/notes/${noteId}`);
  }

  // 获取在线用户列表
  async getOnlineUsers(): Promise<AxiosResponse<Array<{
    id: number;
    username: string;
    full_name: string;
    avatar?: string;
    last_activity_at: string;
    status: 'online' | 'away' | 'busy';
  }>>> {
    return this.api.get('/users/online');
  }

  // 更新用户在线状态
  async updateUserStatus(
    status: 'online' | 'away' | 'busy' | 'offline'
  ): Promise<AxiosResponse<void>> {
    return this.api.post('/users/me/status', { status });
  }

  // 获取用户仪表板数据
  async getUserDashboard(
    userId: number
  ): Promise<AxiosResponse<{
    project_count: number;
    active_projects: number;
    completed_projects: number;
    total_files: number;
    recent_activities: Array<{
      id: number;
      action_type: string;
      description: string;
      created_at: string;
    }>;
    upcoming_deadlines: Array<{
      project_id: number;
      project_name: string;
      deadline: string;
      days_remaining: number;
    }>;
  }>> {
    return this.api.get(`/users/${userId}/dashboard`);
  }

  // 验证用户名是否可用
  async checkUsernameAvailability(
    username: string
  ): Promise<AxiosResponse<{ available: boolean }>> {
    return this.api.get('/users/check-username', {
      params: { username },
    });
  }

  // 验证邮箱是否可用
  async checkEmailAvailability(
    email: string
  ): Promise<AxiosResponse<{ available: boolean }>> {
    return this.api.get('/users/check-email', {
      params: { email },
    });
  }

  // 格式化用户显示名称
  formatUserDisplayName(user: User): string {
    if (user.full_name) {
      return `${user.full_name} (${user.username})`;
    }
    return user.username;
  }

  // 获取用户头像URL
  getUserAvatarUrl(user: User): string {
    if (user.avatar) {
      return user.avatar.startsWith('http') 
        ? user.avatar 
        : `${this.api.defaults.baseURL}/static/avatars/${user.avatar}`;
    }
    
    // 返回默认头像
    return `${this.api.defaults.baseURL}/static/avatars/default.png`;
  }

  // 获取用户状态颜色
  getUserStatusColor(user: User): string {
    if (!user.is_active) return '#ff4d4f'; // 红色 - 未激活
    return '#52c41a'; // 绿色 - 激活
  }

  // 获取用户角色标签颜色
  getRoleTagColor(roleName: string): string {
    const colorMap: Record<string, string> = {
      admin: '#f50',
      manager: '#2db7f5',
      member: '#87d068',
      viewer: '#108ee9',
      guest: '#999',
    };
    
    return colorMap[roleName.toLowerCase()] || '#108ee9';
  }

  // 检查用户是否在线
  isUserOnline(lastActivityAt: string): boolean {
    const lastActivity = new Date(lastActivityAt);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastActivity.getTime()) / (1000 * 60);
    
    return diffMinutes <= 5; // 5分钟内有活动认为在线
  }

  // 计算用户加入天数
  getUserJoinedDays(createdAt: string): number {
    const joinDate = new Date(createdAt);
    const now = new Date();
    const diffTime = now.getTime() - joinDate.getTime();
    
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
  }

  // 删除当前用户账户
  async deleteAccount(): Promise<AxiosResponse<void>> {
    return this.api.delete('/users/me');
  }

  // 获取系统设置
  async getSystemSettings(): Promise<AxiosResponse<{
    site_name: string;
    site_description: string;
    max_file_size: number;
    allow_registration: boolean;
    require_email_verification: boolean;
    session_timeout: number;
    backup_enabled: boolean;
    backup_schedule: string;
    storage_limit: number;
    user_count: number;
    project_count: number;
    file_count: number;
    total_storage_used: number;
  }>> {
    return this.api.get('/system/settings');
  }

  // 更新系统设置
  async updateSystemSettings(settings: {
    site_name?: string;
    site_description?: string;
    max_file_size?: number;
    allow_registration?: boolean;
    require_email_verification?: boolean;
    session_timeout?: number;
    backup_enabled?: boolean;
    backup_schedule?: string;
    storage_limit?: number;
  }): Promise<AxiosResponse<void>> {
    return this.api.put('/system/settings', settings);
  }

  // 获取通知设置
  async getNotificationSettings(): Promise<AxiosResponse<{
    email_notifications: boolean;
    push_notifications: boolean;
    project_updates: boolean;
    system_alerts: boolean;
    weekly_digest: boolean;
  }>> {
    return this.api.get('/users/me/notification-settings');
  }

  // 更新通知设置
  async updateNotificationSettings(settings: {
    email_notifications?: boolean;
    push_notifications?: boolean;
    project_updates?: boolean;
    system_alerts?: boolean;
    weekly_digest?: boolean;
  }): Promise<AxiosResponse<void>> {
    return this.api.put('/users/me/notification-settings', settings);
  }

  // 获取安全日志
  async getSecurityLogs(params?: {
    skip?: number;
    limit?: number;
    action_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AxiosResponse<Array<{
    id: number;
    action_type: string;
    description: string;
    ip_address: string;
    user_agent: string;
    success: boolean;
    created_at: string;
  }>>> {
    return this.api.get('/users/me/security-logs', { params });
  }

  // 获取存储使用情况
  async getStorageUsage(): Promise<AxiosResponse<{
    total_used: number;
    total_limit: number;
    breakdown: {
      documents: number;
      images: number;
      videos: number;
      others: number;
    };
  }>> {
    return this.api.get('/users/me/storage-usage');
  }

  // 修改密码
  async changePassword(data: {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
  }): Promise<AxiosResponse<void>> {
    return this.api.post('/users/me/change-password', {
      current_password: data.currentPassword,
      new_password: data.newPassword,
      confirm_password: data.confirmPassword,
    });
  }

  // 上传当前用户头像
  async uploadAvatar(file: File): Promise<AxiosResponse<{ avatar_url: string }>> {
    const formData = new FormData();
    formData.append('avatar', file);

    return this.api.post('/users/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}

// 创建单例实例
export const userService = new UserService();
export default userService;