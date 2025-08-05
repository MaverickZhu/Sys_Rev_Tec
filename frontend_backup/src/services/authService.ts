import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios';
import type { User, LoginRequest, LoginResponse, RegisterRequest } from '../types';

class AuthService {
  private api: AxiosInstance;
  private responseInterceptorId: number | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  // 设置认证token
  setAuthToken(token: string): void {
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // 清除认证token
  clearAuthToken(): void {
    delete this.api.defaults.headers.common['Authorization'];
  }

  // 获取token
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // 设置响应拦截器
  setupResponseInterceptor(
    onUnauthorized: () => void,
    onTokenRefresh: () => Promise<boolean>
  ): number {
    this.responseInterceptorId = this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          // 尝试刷新token
          const refreshSuccess = await onTokenRefresh();
          if (refreshSuccess) {
            // 重新发送原始请求
            const token = localStorage.getItem('access_token');
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.api(originalRequest);
          } else {
            onUnauthorized();
          }
        }

        return Promise.reject(error);
      }
    );

    return this.responseInterceptorId;
  }

  // 清除响应拦截器
  clearResponseInterceptor(interceptorId: number): void {
    this.api.interceptors.response.eject(interceptorId);
  }

  // 用户登录
  async login(credentials: LoginRequest): Promise<AxiosResponse<LoginResponse>> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    return this.api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  }

  // 用户注册
  async register(userData: RegisterRequest): Promise<AxiosResponse<User>> {
    return this.api.post('/auth/register', userData);
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<AxiosResponse<User>> {
    return this.api.get('/auth/me');
  }

  // 刷新token
  async refreshToken(refreshToken: string): Promise<AxiosResponse<LoginResponse>> {
    return this.api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  // 用户登出
  async logout(): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/logout');
  }

  // 修改密码
  async changePassword(data: {
    current_password: string;
    new_password: string;
  }): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/change-password', data);
  }

  // 重置密码请求
  async requestPasswordReset(email: string): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/password-reset-request', { email });
  }

  // 重置密码确认
  async confirmPasswordReset(data: {
    token: string;
    new_password: string;
  }): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/password-reset-confirm', data);
  }

  // 验证邮箱
  async verifyEmail(token: string): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/verify-email', { token });
  }

  // 重新发送验证邮件
  async resendVerificationEmail(): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/resend-verification');
  }

  // 更新用户资料
  async updateProfile(userData: Partial<User>): Promise<AxiosResponse<User>> {
    return this.api.put('/auth/profile', userData);
  }

  // 上传头像
  async uploadAvatar(file: File): Promise<AxiosResponse<{ avatar_url: string }>> {
    const formData = new FormData();
    formData.append('avatar', file);

    return this.api.post('/auth/upload-avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 获取用户权限
  async getUserPermissions(): Promise<AxiosResponse<string[]>> {
    return this.api.get('/auth/permissions');
  }

  // 检查用户权限
  async checkPermission(permission: string): Promise<AxiosResponse<{ has_permission: boolean }>> {
    return this.api.get(`/auth/check-permission/${permission}`);
  }

  // 获取用户角色
  async getUserRoles(): Promise<AxiosResponse<string[]>> {
    return this.api.get('/auth/roles');
  }

  // 启用两步验证
  async enableTwoFactor(): Promise<AxiosResponse<{ qr_code: string; secret: string }>> {
    return this.api.post('/auth/2fa/enable');
  }

  // 确认两步验证
  async confirmTwoFactor(code: string): Promise<AxiosResponse<{ backup_codes: string[] }>> {
    return this.api.post('/auth/2fa/confirm', { code });
  }

  // 禁用两步验证
  async disableTwoFactor(password: string): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/2fa/disable', { password });
  }

  // 验证两步验证码
  async verifyTwoFactor(code: string): Promise<AxiosResponse<LoginResponse>> {
    return this.api.post('/auth/2fa/verify', { code });
  }

  // 获取登录历史
  async getLoginHistory(params?: {
    skip?: number;
    limit?: number;
  }): Promise<AxiosResponse<{
    items: Array<{
      id: number;
      ip_address: string;
      user_agent: string;
      login_time: string;
      location?: string;
    }>;
    total: number;
  }>> {
    return this.api.get('/auth/login-history', { params });
  }

  // 获取活跃会话
  async getActiveSessions(): Promise<AxiosResponse<Array<{
    id: string;
    ip_address: string;
    user_agent: string;
    created_at: string;
    last_activity: string;
    is_current: boolean;
  }>>> {
    return this.api.get('/auth/sessions');
  }

  // 撤销会话
  async revokeSession(sessionId: string): Promise<AxiosResponse<void>> {
    return this.api.delete(`/auth/sessions/${sessionId}`);
  }

  // 撤销所有其他会话
  async revokeAllOtherSessions(): Promise<AxiosResponse<void>> {
    return this.api.post('/auth/sessions/revoke-all');
  }

  // 获取API实例（用于其他服务）
  getApiInstance(): AxiosInstance {
    return this.api;
  }

  // 通用请求方法
  async request<T = any>(
    config: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.request<T>(config);
  }

  // GET请求
  async get<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.get<T>(url, config);
  }

  // POST请求
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.post<T>(url, data, config);
  }

  // PUT请求
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.put<T>(url, data, config);
  }

  // DELETE请求
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.delete<T>(url, config);
  }

  // PATCH请求
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return this.api.patch<T>(url, data, config);
  }
}

// 创建单例实例
export const authService = new AuthService();
export default authService;