import { App as AntdApp, ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import React from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import AuthDebugInfo from './components/AuthDebugInfo';
import Layout from './components/Layout';
import PublicRoute from './components/PublicRoute';
import { NotificationProvider } from './contexts/NotificationContext';
import { SimpleAuthProvider } from './contexts/SimpleAuthContext';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import AuthDebug from './pages/AuthDebug';
import Dashboard from './pages/Dashboard';
import FileManager from './pages/FileManager';
import Files from './pages/Files';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import Profile from './pages/Profile';
import ProjectDetail from './pages/ProjectDetail';
import Projects from './pages/Projects';
import Register from './pages/Register';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import UserManagement from './pages/UserManagement';
import Users from './pages/Users';

import './App.css';
import ErrorBoundary from './components/ErrorBoundary';



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
      <Route path="/debug" element={<AuthDebugInfo />} />
      <Route path="/auth-debug" element={<AuthDebug />} />

      {/* 主要路由 - 移除权限保护 */}
      <Route
        path="/"
        element={<Layout />}
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="files" element={<Files />} />
        <Route path="file-manager" element={<FileManager />} />
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
          <SimpleAuthProvider>
            <AppWithTheme>
              <Router>
                <AppRoutes />
              </Router>
            </AppWithTheme>
          </SimpleAuthProvider>
        </NotificationProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;