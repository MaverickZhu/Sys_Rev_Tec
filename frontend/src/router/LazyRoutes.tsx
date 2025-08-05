import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Loading from '../components/Loading';

// 懒加载页面组�?
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Projects = lazy(() => import('../pages/Projects'));
const Reports = lazy(() => import('../pages/Reports'));
const Settings = lazy(() => import('../pages/Settings'));
const UserManagement = lazy(() => import('../pages/UserManagement'));

// 懒加载包装器
const LazyWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<Loading />}>
    {children}
  </Suspense>
);

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/dashboard" element={
        <LazyWrapper>
          <Dashboard />
        </LazyWrapper>
      } />
      <Route path="/projects" element={
        <LazyWrapper>
          <Projects />
        </LazyWrapper>
      } />
      <Route path="/reports" element={
        <LazyWrapper>
          <Reports />
        </LazyWrapper>
      } />
      <Route path="/settings" element={
        <LazyWrapper>
          <Settings />
        </LazyWrapper>
      } />
      <Route path="/users" element={
        <LazyWrapper>
          <UserManagement />
        </LazyWrapper>
      } />
    </Routes>
  );
};

export default AppRoutes;
