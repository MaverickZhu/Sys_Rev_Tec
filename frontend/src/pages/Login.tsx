import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Space,
  Divider,
  Alert,
  Checkbox,
  Row,
  Col,
  message
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  SafetyCertificateOutlined,
  LoginOutlined
} from '@ant-design/icons';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';

import styles from '../styles/Login.module.css';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
  remember: boolean;
}

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const { login, isAuthenticated } = useSimpleAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // 获取重定向路径
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  // 如果已登录，重定向到目标页面
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // 处理登录
  const handleLogin = async (values: LoginForm) => {
    try {
      setLoading(true);
      setError('');

      // 验证用户凭据（可选：如果需要与后端API验证）
      // await authService.login({
      //   username: values.username,
      //   password: values.password
      // });

      // 保存登录状态
      if (values.remember) {
        localStorage.setItem('remember_user', values.username);
      } else {
        localStorage.removeItem('remember_user');
      }

      // 调用认证上下文的登录方法
      await login(values.username, values.password);

      message.success('登录成功');
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('登录失败:', error);
      const errorMessage = error.response?.data?.detail || '登录失败，请检查用户名和密码';
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 初始化记住的用户名
  useEffect(() => {
    const rememberedUser = localStorage.getItem('remember_user');
    if (rememberedUser) {
      form.setFieldsValue({
        username: rememberedUser,
        remember: true
      });
    }
  }, [form]);

  // 处理忘记密码
  const handleForgotPassword = () => {
    message.info('请联系系统管理员重置密码');
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginBackground}>
        <div className={styles.loginContent}>
          <Row justify="center" align="middle" style={{ minHeight: '100vh' }}>
            <Col xs={22} sm={16} md={12} lg={8} xl={6}>
              <Card className={styles.loginCard}>
                <div className={styles.loginHeader}>
                  <Space direction="vertical" align="center" size="large">
                    <div className={styles.logoContainer}>
                      <SafetyCertificateOutlined className={styles.logoIcon} />
                    </div>
                    <div>
                      <Title level={2} className={styles.loginTitle}>
                        审计系统
                      </Title>
                      <Text type="secondary" className={styles.loginSubtitle}>
                        企业级审计管理平台
                      </Text>
                    </div>
                  </Space>
                </div>

                <Divider />

                {error && (
                  <Alert
                    message={error}
                    type="error"
                    showIcon
                    closable
                    onClose={() => setError('')}
                    style={{ marginBottom: '24px' }}
                  />
                )}

                <Form
                  form={form}
                  name="login"
                  onFinish={handleLogin}
                  autoComplete="off"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' },
                      { max: 50, message: '用户名不能超过50个字符' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="用户名"
                      autoComplete="username"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: '请输入密码' },
                      { min: 6, message: '密码至少6个字符' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="密码"
                      autoComplete="current-password"
                      iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Row justify="space-between" align="middle">
                      <Col>
                        <Form.Item name="remember" valuePropName="checked" noStyle>
                          <Checkbox>记住用户名</Checkbox>
                        </Form.Item>
                      </Col>
                      <Col>
                        <Button
                          type="link"
                          onClick={handleForgotPassword}
                          style={{ padding: 0 }}
                        >
                          忘记密码？
                        </Button>
                      </Col>
                    </Row>
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      icon={<LoginOutlined />}
                      className={styles.loginButton}
                    >
                      {loading ? '登录中...' : '登录'}
                    </Button>
                  </Form.Item>
                </Form>

                <Divider plain>
                  <Text type="secondary">其他选项</Text>
                </Divider>

                <div className={styles.loginFooter}>
                  <Space direction="vertical" align="center" size="small">
                    <Text type="secondary">
                      还没有账号？
                      <Link to="/register" className={styles.registerLink}>
                        立即注册
                      </Link>
                    </Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      © 2024 审计系统. 保留所有权利.
                    </Text>
                  </Space>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default Login;