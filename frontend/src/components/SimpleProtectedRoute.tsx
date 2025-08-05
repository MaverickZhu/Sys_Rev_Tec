import React from 'react';
import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';

interface SimpleProtectedRouteProps {
  children: React.ReactNode;
}

const SimpleProtectedRoute: React.FC<SimpleProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useSimpleAuth();

  // 显示加载状态
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column'
      }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>加载中...</div>
      </div>
    );
  }

  // 未认证则重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // 已认证则渲染子组件
  return <>{children}</>;
};

export default SimpleProtectedRoute;