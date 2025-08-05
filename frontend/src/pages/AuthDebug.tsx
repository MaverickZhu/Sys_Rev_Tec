import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const AuthDebug: React.FC = () => {
  const { user, token, isAuthenticated, isLoading } = useAuth();
  const [apiStatus, setApiStatus] = useState<string>('检查中...');
  const [localStorageData, setLocalStorageData] = useState<any>({});

  useEffect(() => {
    // 检查localStorage数据
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user_data');
    setLocalStorageData({
      token: storedToken,
      user: storedUser ? JSON.parse(storedUser) : null
    });

    // 检查API连接
    const checkAPI = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/auth/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer invalid_token`
          }
        });
        if (response.status === 401) {
          setApiStatus('API服务器正常运行 (返回401未授权)');
        } else {
          setApiStatus(`API响应状态: ${response.status}`);
        }
      } catch (error) {
        setApiStatus(`API连接失败: ${error}`);
      }
    };

    checkAPI();
  }, []);

  const clearAuth = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('refresh_token');
    window.location.reload();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>认证调试信息</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>AuthContext状态:</h2>
        <p>isLoading: {isLoading ? 'true' : 'false'}</p>
        <p>isAuthenticated: {isAuthenticated ? 'true' : 'false'}</p>
        <p>token: {token ? '存在' : '不存在'}</p>
        <p>user: {user ? JSON.stringify(user, null, 2) : '不存在'}</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>localStorage数据:</h2>
        <p>token: {localStorageData.token || '不存在'}</p>
        <p>user: {localStorageData.user ? JSON.stringify(localStorageData.user, null, 2) : '不存在'}</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>API状态:</h2>
        <p>{apiStatus}</p>
      </div>

      <div>
        <button onClick={clearAuth} style={{ padding: '10px', marginRight: '10px' }}>
          清除认证数据并刷新
        </button>
        <button onClick={() => window.location.href = '/login'} style={{ padding: '10px' }}>
          跳转到登录页
        </button>
      </div>
    </div>
  );
};

export default AuthDebug;