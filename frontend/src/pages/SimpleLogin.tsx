import React, { useState } from 'react';
import { Form, Input, Button, Card, Space, Divider, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

const SimpleLogin: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const { login, autoLogin } = useSimpleAuth();
  const navigate = useNavigate();

  // 处理表单提交
  const handleSubmit = async (values: LoginForm) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (success) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('登录失败:', error);
      message.error('登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 一键自动登录
  const handleAutoLogin = () => {
    autoLogin();
    navigate('/dashboard');
  };

  // 填充默认账号密码
  const fillDefaultCredentials = () => {
    form.setFieldsValue({
      username: 'admin',
      password: 'admin123'
    });
    message.info('已填充默认账号密码');
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          borderRadius: 12
        }}
        styles={{ body: { padding: '32px' } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ margin: 0, color: '#1890ff' }}>
            系统登录
          </Title>
          <Text type="secondary">个人使用版 - 简化登录</Text>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名 (默认: admin)"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码 (默认: admin123)"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              icon={<LoginOutlined />}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider>或者</Divider>

        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Button
            type="dashed"
            block
            icon={<ThunderboltOutlined />}
            onClick={handleAutoLogin}
            style={{ color: '#52c41a', borderColor: '#52c41a' }}
          >
            一键自动登录（跳过验证）
          </Button>
          
          <Button
            type="link"
            block
            onClick={fillDefaultCredentials}
            style={{ color: '#666' }}
          >
            填充默认账号密码
          </Button>
        </Space>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            提示：这是个人使用的简化版本
            <br />
            默认账号: admin / admin123
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default SimpleLogin;