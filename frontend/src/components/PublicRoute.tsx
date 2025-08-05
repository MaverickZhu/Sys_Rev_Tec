import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { PageLoading } from './Loading';

interface PublicRouteProps {
  children: React.ReactNode;
  redirectIfAuthenticated?: boolean;
  redirectTo?: string;
}

const PublicRoute: React.FC<PublicRouteProps> = ({
  children,
  redirectIfAuthenticated = true,
  redirectTo = '/dashboard'
}) => {
  const { isAuthenticated, isLoading } = useSimpleAuth();
  const location = useLocation();

  // 如果正在加载认证状态，显示加载页面
  if (isLoading) {
    return <PageLoading tip="正在加载..." />;
  }

  // 如果用户已认证且需要重定向
  if (isAuthenticated && redirectIfAuthenticated) {
    // 获取原始目标路径，如果没有则使用默认重定向路径
    const from = (location.state as any)?.from?.pathname || redirectTo;
    return <Navigate to={from} replace />;
  }

  // 渲染公开路由内容
  return <>{children}</>;
};

export default PublicRoute;