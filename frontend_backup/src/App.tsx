import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Files from './pages/Files';
import Reports from './pages/Reports';
import Users from './pages/Users';
import UserManagement from './pages/UserManagement';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';

import ErrorBoundary from './components/ErrorBoundary';
import './App.css';



// 应用路由组件
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 公共路由 */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* 受保护的路由 */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="files" element={<Files />} />
        <Route path="reports" element={<Reports />} />
        <Route path="users" element={<Users />} />
        <Route path="user-management" element={<UserManagement />} />
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* 404 页面 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

// 主题配置组件
const AppWithTheme: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isDarkMode } = useTheme();

  // 主题配置
  const themeConfig = {
    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      colorSuccess: '#52c41a',
      colorWarning: '#faad14',
      colorError: '#ff4d4f',
      colorInfo: '#1890ff',
      borderRadius: 6,
      wireframe: false,
    },
    components: {
      Layout: {
        headerBg: isDarkMode ? '#001529' : '#ffffff',
        siderBg: isDarkMode ? '#001529' : '#ffffff',
        bodyBg: isDarkMode ? '#141414' : '#f0f2f5',
      },
      Menu: {
        darkItemBg: '#001529',
        darkSubMenuItemBg: '#000c17',
        darkItemSelectedBg: '#1890ff',
      },
      Card: {
        headerBg: isDarkMode ? '#1f1f1f' : '#fafafa',
      },
      Table: {
        headerBg: isDarkMode ? '#1f1f1f' : '#fafafa',
      },
    },
  };





  return (
    <ConfigProvider
      locale={zhCN}
      theme={themeConfig}
      componentSize="middle"
    >
      <AntdApp>
        <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
          {children}
        </div>
      </AntdApp>
    </ConfigProvider>
  );
};

// 主应用组件
const App: React.FC = () => {
  // 全局错误处理
  const handleError = React.useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    console.error('应用错误:', error, errorInfo);
    // 这里可以添加错误上报逻辑
  }, []);

  return (
    <ErrorBoundary onError={handleError}>
      <ThemeProvider>
        <NotificationProvider>
          <AppWithTheme>
            <AuthProvider>
              <Router>
                <AppRoutes />
              </Router>
            </AuthProvider>
          </AppWithTheme>
        </NotificationProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;