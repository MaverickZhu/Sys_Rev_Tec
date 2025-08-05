import React from 'react';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';

const AuthDebug: React.FC = () => {
  const { user, token, isAuthenticated, loading, isLoading } = useSimpleAuth();
  
  React.useEffect(() => {
    console.log('AuthDebug 组件状态', {
      user: user ? '存在' : '不存在',
      token: token ? '存在' : '不存在',
      isAuthenticated,
      loading,
      isLoading
    });
  }, [user, token, isAuthenticated, loading, isLoading]);

  return (
    <div style={{
      position: 'fixed',
      top: '50px',
      right: '10px',
      background: 'rgba(0,0,0,0.9)',
      color: 'white',
      padding: '15px',
      borderRadius: '8px',
      fontSize: '12px',
      zIndex: 10000,
      maxWidth: '300px',
      fontFamily: 'monospace'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#4CAF50' }}>🔍 认证状态调试</h4>
      <div><strong>User:</strong> {user ? `${user.username} (${user.email})` : '未登录'}</div>
      <div><strong>Token:</strong> {token ? `${token.substring(0, 20)}...` : '无'}</div>
      <div><strong>isAuthenticated:</strong> {isAuthenticated ? '是' : '否'}</div>
      <div><strong>loading:</strong> {loading ? '是' : '否'}</div>
      <div><strong>isLoading:</strong> {isLoading ? '是' : '否'}</div>
      <div style={{ marginTop: '10px', fontSize: '10px', color: '#ccc' }}>
        更新时间: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default AuthDebug;
