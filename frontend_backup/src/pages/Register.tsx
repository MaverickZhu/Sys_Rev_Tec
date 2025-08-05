import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Space,
  Divider,
  Alert,
  Row,
  Col,
  Select,
  message,
  Progress
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  TeamOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  SafetyCertificateOutlined,
  UserAddOutlined
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import styles from '../styles/Login.module.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  phone?: string;
  department?: string;
}

const Register: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [passwordStrength, setPasswordStrength] = useState(0);
  const navigate = useNavigate();

  // 密码强度检查
  const checkPasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[a-z]/.test(password)) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;
    return Math.min(strength, 100);
  };

  // 获取密码强度颜色
  const getPasswordStrengthColor = (strength: number): string => {
    if (strength < 25) return '#ff4d4f';
    if (strength < 50) return '#faad14';
    if (strength < 75) return '#1890ff';
    return '#52c41a';
  };

  // 获取密码强度文本
  const getPasswordStrengthText = (strength: number): string => {
    if (strength < 25) return '弱';
    if (strength < 50) return '一般';
    if (strength < 75) return '良好';
    return '强';
  };

  // 处理密码变化
  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const password = e.target.value;
    setPasswordStrength(checkPasswordStrength(password));
  };

  // 处理注册
  const handleRegister = async (values: RegisterForm) => {
    try {
      setLoading(true);
      setError('');

      const registerData = {
        username: values.username,
        email: values.email,
        password: values.password,
        full_name: values.full_name,
        phone: values.phone,
        department: values.department
      };

      await authService.register(registerData);

      message.success('注册成功！请登录您的账户。');
      navigate('/login');
    } catch (error: any) {
      console.error('注册失败:', error);
      const errorMessage = error.response?.data?.detail || '注册失败，请稍后重试';
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginBackground}>
        <div className={styles.loginContent}>
          <Row justify="center" align="middle" style={{ minHeight: '100vh', padding: '20px 0' }}>
            <Col xs={22} sm={18} md={14} lg={10} xl={8}>
              <Card className={styles.loginCard}>
                <div className={styles.loginHeader}>
                  <Space direction="vertical" align="center" size="large">
                    <div className={styles.logoContainer}>
                      <SafetyCertificateOutlined className={styles.logoIcon} />
                    </div>
                    <div>
                      <Title level={2} className={styles.loginTitle}>
                        用户注册
                      </Title>
                      <Text type="secondary" className={styles.loginSubtitle}>
                        创建您的审计系统账户
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
                  name="register"
                  onFinish={handleRegister}
                  autoComplete="off"
                  layout="vertical"
                >
                  <Row gutter={16}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="username"
                        label="用户名"
                        rules={[
                          { required: true, message: '请输入用户名' },
                          { min: 3, message: '用户名至少3个字符' },
                          { max: 50, message: '用户名不能超过50个字符' },
                          { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
                        ]}
                      >
                        <Input
                          prefix={<UserOutlined />}
                          placeholder="请输入用户名"
                          autoComplete="username"
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="full_name"
                        label="姓名"
                        rules={[
                          { required: true, message: '请输入姓名' },
                          { max: 100, message: '姓名不能超过100个字符' }
                        ]}
                      >
                        <Input
                          prefix={<TeamOutlined />}
                          placeholder="请输入真实姓名"
                          autoComplete="name"
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    name="email"
                    label="邮箱地址"
                    rules={[
                      { required: true, message: '请输入邮箱地址' },
                      { type: 'email', message: '请输入有效的邮箱地址' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      placeholder="请输入邮箱地址"
                      autoComplete="email"
                    />
                  </Form.Item>

                  <Row gutter={16}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="phone"
                        label="手机号码"
                        rules={[
                          { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }
                        ]}
                      >
                        <Input
                          prefix={<PhoneOutlined />}
                          placeholder="请输入手机号码"
                          autoComplete="tel"
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="department"
                        label="部门"
                      >
                        <Select placeholder="请选择部门">
                          <Option value="audit">审计部</Option>
                          <Option value="finance">财务部</Option>
                          <Option value="hr">人力资源部</Option>
                          <Option value="it">信息技术部</Option>
                          <Option value="legal">法务部</Option>
                          <Option value="operations">运营部</Option>
                          <Option value="other">其他</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    name="password"
                    label="密码"
                    rules={[
                      { required: true, message: '请输入密码' },
                      { min: 8, message: '密码至少8个字符' },
                      { max: 128, message: '密码不能超过128个字符' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="请输入密码"
                      autoComplete="new-password"
                      onChange={handlePasswordChange}
                      iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    />
                  </Form.Item>

                  {passwordStrength > 0 && (
                    <div style={{ marginBottom: '24px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <Text type="secondary">密码强度</Text>
                        <Text style={{ color: getPasswordStrengthColor(passwordStrength) }}>
                          {getPasswordStrengthText(passwordStrength)}
                        </Text>
                      </div>
                      <Progress
                        percent={passwordStrength}
                        strokeColor={getPasswordStrengthColor(passwordStrength)}
                        showInfo={false}
                        size="small"
                      />
                    </div>
                  )}

                  <Form.Item
                    name="confirmPassword"
                    label="确认密码"
                    dependencies={['password']}
                    rules={[
                      { required: true, message: '请确认密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="请再次输入密码"
                      autoComplete="new-password"
                      iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      icon={<UserAddOutlined />}
                      className={styles.loginButton}
                      size="large"
                    >
                      {loading ? '注册中...' : '注册账户'}
                    </Button>
                  </Form.Item>
                </Form>

                <Divider plain>
                  <Text type="secondary">已有账户？</Text>
                </Divider>

                <div className={styles.loginFooter}>
                  <Space direction="vertical" align="center" size="small">
                    <Link to="/login" className={styles.registerLink}>
                      <Button type="link" size="large">
                        立即登录
                      </Button>
                    </Link>
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

export default Register;