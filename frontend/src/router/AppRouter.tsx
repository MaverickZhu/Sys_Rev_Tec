import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 导入页面组件
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Projects from '../pages/Projects';
import ProjectDetail from '../pages/ProjectDetail';
import Reports from '../pages/Reports';
import Users from '../pages/Users';
import UserManagement from '../pages/UserManagement';
import Settings from '../pages/Settings';
import Profile from '../pages/Profile';
import Files from '../pages/Files';
import NotFound from '../pages/NotFound';

// 导入布局组件
import Layout from '../components/Layout';

// 导入认证相关
import ProtectedRoute from '../components/ProtectedRoute';

const AppRouter: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<Login />} />
        
        {/* 受保护的路由 */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="reports" element={<Reports />} />
          <Route path="users" element={<Users />} />
          <Route path="user-management" element={<UserManagement />} />
          <Route path="files" element={<Files />} />
          <Route path="settings" element={<Settings />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        
        {/* 404 页面 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;
