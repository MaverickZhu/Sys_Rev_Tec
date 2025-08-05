import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { PageLoading } from './Loading';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = []
}) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // 如果正在加载认证状态，显示加载页面
  if (loading) {
    return <PageLoading tip="正在验证用户身份..." />;
  }

  // 如果未认证，重定向到登录页面
  if (!isAuthenticated || !user) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  // 检查角色权限
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role => 
      user.roles?.some(userRole => userRole.name === role)
    );
    
    if (!hasRequiredRole) {
      return (
        <Navigate
          to="/unauthorized"
          state={{ from: location }}
          replace
        />
      );
    }
  }

  // 检查具体权限
  if (requiredPermissions.length > 0) {
    const hasRequiredPermission = requiredPermissions.some(permission => 
      user.permissions?.some(userPermission => userPermission.name === permission)
    );
    
    if (!hasRequiredPermission) {
      return (
        <Navigate
          to="/unauthorized"
          state={{ from: location }}
          replace
        />
      );
    }
  }

  // 用户已认证且有权限，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;