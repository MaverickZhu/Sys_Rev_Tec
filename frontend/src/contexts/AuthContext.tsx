import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import { authService } from '../services/authService';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化认证状态
  useEffect(() => {
    initializeAuth();
  }, []);

  // 初始化认证
  const initializeAuth = async () => {
    console.log('开始初始化认证...');
    try {
      const storedToken = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user_data');
      console.log('存储的token:', storedToken ? '存在' : '不存在');
      console.log('存储的用户数据:', storedUser ? '存在' : '不存在');

      if (storedToken && storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          console.log('解析用户数据成功:', userData);
          
          // 设置token以便API调用
          authService.setAuthToken(storedToken);
          
          // 验证token是否有效
          console.log('验证token有效性...');
          const response = await authService.getCurrentUser();
          console.log('token验证成功，用户数据:', response.data);
          setToken(storedToken);
          setUser(response.data);
        } catch (error) {
          console.log('token验证失败或数据解析失败，清除存储数据:', error);
          // Token无效或数据损坏，清除存储的数据
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
          localStorage.removeItem('refresh_token');
          authService.clearAuthToken();
          setToken(null);
          setUser(null);
        }
      } else {
        console.log('没有存储的认证信息，用户未登录');
        // 确保状态为空
        setToken(null);
        setUser(null);
        authService.clearAuthToken();
      }
    } catch (error) {
      console.error('初始化认证失败:', error);
      // 发生错误时确保清除状态
      setToken(null);
      setUser(null);
      authService.clearAuthToken();
    } finally {
      console.log('认证初始化完成，设置loading为false');
      setIsLoading(false);
    }
  };

  // 登录
  const login = async (accessToken: string, userData: User) => {
    try {
      setToken(accessToken);
      setUser(userData);
      
      // 存储到localStorage
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('user_data', JSON.stringify(userData));
      
      // 设置axios默认header
      authService.setAuthToken(accessToken);
      
      message.success('登录成功');
    } catch (error) {
      console.error('登录处理失败:', error);
      throw error;
    }
  };

  // 登出
  const logout = () => {
    try {
      // 清除状态
      setUser(null);
      setToken(null);
      
      // 清除localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('remember_user');
      
      // 清除axios默认header
      authService.clearAuthToken();
      
      message.success('已退出登录');
    } catch (error) {
      console.error('登出处理失败:', error);
    }
  };

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('user_data', JSON.stringify(updatedUser));
    }
  };

  // 刷新token
  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      if (!refreshTokenValue) {
        return false;
      }

      const response = await authService.refreshToken(refreshTokenValue);
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      
      authService.setAuthToken(access_token);
      
      return true;
    } catch (error) {
      console.error('刷新token失败:', error);
      logout();
      return false;
    }
  };

  // 自动刷新token
  useEffect(() => {
    if (!token) return;

    // 解析token获取过期时间
    try {
      const tokenPayload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = tokenPayload.exp * 1000; // 转换为毫秒
      const currentTime = Date.now();
      const timeUntilExpiration = expirationTime - currentTime;
      
      // 在token过期前5分钟刷新
      const refreshTime = Math.max(timeUntilExpiration - 5 * 60 * 1000, 0);
      
      if (refreshTime > 0) {
        const refreshTimer = setTimeout(() => {
          refreshToken();
        }, refreshTime);
        
        return () => clearTimeout(refreshTimer);
      } else {
        // Token已过期或即将过期，立即刷新
        refreshToken();
      }
    } catch (error) {
      console.error('解析token失败:', error);
    }
  }, [token]);

  // 监听storage变化（多标签页同步）
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token') {
        if (e.newValue === null) {
          // 其他标签页登出
          setUser(null);
          setToken(null);
          authService.clearAuthToken();
        } else if (e.newValue !== token) {
          // 其他标签页登录
          const userData = localStorage.getItem('user_data');
          if (userData) {
            setToken(e.newValue);
            setUser(JSON.parse(userData));
            authService.setAuthToken(e.newValue);
          }
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [token]);

  // 网络请求拦截器 - 处理401错误
  useEffect(() => {
    const interceptor = authService.setupResponseInterceptor(
      () => {
        // 401错误处理
        logout();
        window.location.href = '/login';
      },
      async () => {
        // 尝试刷新token
        const success = await refreshToken();
        if (!success) {
          logout();
          window.location.href = '/login';
        }
        return success;
      }
    );

    return () => {
      // 清除拦截器
      if (interceptor) {
        authService.clearResponseInterceptor(interceptor);
      }
    };
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    logout,
    updateUser,
    refreshToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook for using auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// HOC for protecting routes
export const withAuth = <P extends object>(Component: React.ComponentType<P>) => {
  return (props: P) => {
    const { isAuthenticated, isLoading } = useAuth();
    
    if (isLoading) {
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}>
          <div>加载中...</div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      window.location.href = '/login';
      return null;
    }
    
    return <Component {...props} />;
  };
};

// 不导出AuthContext，因为它不是组件
// export default AuthContext;