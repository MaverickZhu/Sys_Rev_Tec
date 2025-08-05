import React from 'react';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { Card, Typography, Space, Tag } from 'antd';

const { Text } = Typography;

const AuthDebugInfo: React.FC = () => {
  const { user, token, isAuthenticated, isLoading } = useSimpleAuth();

  return (
    <Card title="认证调试信息" style={{ margin: '20px', maxWidth: '600px' }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Text strong>加载状态: </Text>
          <Tag color={isLoading ? 'orange' : 'green'}>
            {isLoading ? '加载中' : '加载完成'}
          </Tag>
        </div>
        
        <div>
          <Text strong>认证状态: </Text>
          <Tag color={isAuthenticated ? 'green' : 'red'}>
            {isAuthenticated ? '已认证' : '未认证'}
          </Tag>
        </div>
        
        <div>
          <Text strong>Token: </Text>
          <Text code>{token ? `${token.substring(0, 20)}...` : '无'}</Text>
        </div>
        
        <div>
          <Text strong>用户信息: </Text>
          {user ? (
            <div style={{ marginLeft: '10px' }}>
              <div><Text>用户名: {user.username}</Text></div>
              <div><Text>邮箱: {user.email}</Text></div>
              <div><Text>角色: {user.roles?.map(r => r.name).join(', ') || '无'}</Text></div>
            </div>
          ) : (
            <Text type="secondary">无用户信息</Text>
          )}
        </div>
        
        <div>
          <Text strong>localStorage数据: </Text>
          <div style={{ marginLeft: '10px' }}>
            <div><Text>access_token: {localStorage.getItem('access_token') ? '存在' : '不存在'}</Text></div>
            <div><Text>user_data: {localStorage.getItem('user_data') ? '存在' : '不存在'}</Text></div>
          </div>
        </div>
      </Space>
    </Card>
  );
};

export default AuthDebugInfo;