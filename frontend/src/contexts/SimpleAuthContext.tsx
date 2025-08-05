import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { message } from 'antd';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  name?: string;
  department?: string;
  position?: string;
  phone?: string;
  avatar?: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: Array<{id: number; name: string; displayName?: string; description?: string}>;
  permissions: Array<{id: number; name: string; resource: string; action: string; description?: string}>;
  created_at: string;
  createdAt?: string;
  updated_at: string;
  updatedAt?: string;
  last_login?: string;
  lastLoginAt?: string;
  login_count: number;
  two_factor_enabled: boolean;
  birthDate?: string;
  birth_date?: string;
  status?: 'active' | 'inactive' | 'pending';
  teamCount?: number;
  projectCount?: number;
  bio?: string;
}

interface SimpleAuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loading?: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  autoLogin: () => void;
}

const SimpleAuthContext = createContext<SimpleAuthContextType | undefined>(undefined);

interface SimpleAuthProviderProps {
  children: ReactNode;
}

// 默认用户数据（个人使用）
const DEFAULT_USER: User = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  full_name: '系统管理员',
  name: '系统管理员',
  department: 'IT部门',
  position: '系统管理员',
  phone: '13800138000',
  avatar: '',
  is_active: true,
  is_superuser: true,
  roles: [{
    id: 1,
    name: 'admin',
    displayName: '管理员',
    description: '系统管理员角色'
  }],
  permissions: [{
    id: 1,
    name: 'all',
    resource: '*',
    action: '*',
    description: '所有权限'
  }],
  created_at: new Date().toISOString(),
  createdAt: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  last_login: new Date().toISOString(),
  lastLoginAt: new Date().toISOString(),
  login_count: 1,
  two_factor_enabled: false,
  birthDate: '',
  birth_date: '',
  status: 'active',
  teamCount: 0,
  projectCount: 0,
  bio: '系统管理员账户'
};

// 简单的用户名密码（您可以修改这些）
const SIMPLE_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

export const SimpleAuthProvider: React.FC<SimpleAuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化 - 检查是否已登录
  useEffect(() => {
    const savedUser = localStorage.getItem('simple_user');
    const savedToken = localStorage.getItem('access_token');
    if (savedUser && savedToken) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
      } catch (error) {
        console.error('解析用户数据失败:', error);
        localStorage.removeItem('simple_user');
        localStorage.removeItem('access_token');
      }
    }
    setIsLoading(false);
  }, []);

  // 简单登录
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      // 验证用户名密码
      if (username === SIMPLE_CREDENTIALS.username && password === SIMPLE_CREDENTIALS.password) {
        const accessToken = 'simple_token_' + Date.now();
        setToken(accessToken);
        setUser(DEFAULT_USER);
        
        // 存储到localStorage
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('simple_user', JSON.stringify(DEFAULT_USER));
        
        message.success('登录成功');
        return true;
      } else {
        message.error('用户名或密码错误');
        return false;
      }
    } catch (error) {
      console.error('登录处理失败:', error);
      return false;
    }
  };

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('simple_user', JSON.stringify(updatedUser));
    }
  };

  // 自动登录（跳过验证）
  const autoLogin = () => {
    const defaultToken = 'simple_token_' + Date.now();
    setUser(DEFAULT_USER);
    setToken(defaultToken);
    localStorage.setItem('simple_user', JSON.stringify(DEFAULT_USER));
    localStorage.setItem('access_token', defaultToken);
    message.success('自动登录成功！');
  };

  // 登出
  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('simple_user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('remember_user');
    message.success('已退出登录');
  };

  const value: SimpleAuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    loading: isLoading,
    login,
    logout,
    updateUser,
    autoLogin
  };

  return (
    <SimpleAuthContext.Provider value={value}>
      {children}
    </SimpleAuthContext.Provider>
  );
};

// Hook for using simple auth context
export const useSimpleAuth = (): SimpleAuthContextType => {
  const context = useContext(SimpleAuthContext);
  if (context === undefined) {
    throw new Error('useSimpleAuth must be used within a SimpleAuthProvider');
  }
  return context;
};