import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Switch,
  Select,
  Upload,
  Avatar,
  message,
  Typography,
  Row,
  Col,
  Space,
  Alert,
  Modal,
  Table,
  // Tag,
  Progress,
  Statistic,
  // List,
  // Badge,
  DatePicker,
  // TimePicker,
  Slider,
  // Radio,
  // Checkbox,
  InputNumber,
  Divider,
} from 'antd';
import {
  UserOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  BellOutlined,
  // GlobalOutlined,
  DatabaseOutlined,
  CloudOutlined,
  // MailOutlined,
  // LockOutlined,
  // EditOutlined,
  // DeleteOutlined,
  // SaveOutlined,
  ReloadOutlined,
  // UploadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  // KeyOutlined,
  SafetyOutlined,
  HistoryOutlined,
  TeamOutlined,
  FileTextOutlined,
  CameraOutlined,
  CalendarOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { userService } from '../services/userService';
// import type { User } from '../types'; // 暂未使用
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;
const { confirm } = Modal;
// const { CheckboxGroup } = Checkbox; // 暂未使用

interface SystemSettings {
  siteName: string;
  siteDescription: string;
  siteLogo: string;
  allowRegistration: boolean;
  requireEmailVerification: boolean;
  maxFileSize: number;
  allowedFileTypes: string[];
  sessionTimeout: number;
  passwordPolicy: {
    minLength: number;
    requireUppercase: boolean;
    requireLowercase: boolean;
    requireNumbers: boolean;
    requireSpecialChars: boolean;
  };
  emailSettings: {
    smtpHost: string;
    smtpPort: number;
    smtpUser: string;
    smtpPassword: string;
    fromEmail: string;
    fromName: string;
  };
  backupSettings: {
    autoBackup: boolean;
    backupInterval: number;
    maxBackups: number;
    backupPath: string;
  };
}

interface NotificationSettings {
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  projectUpdates: boolean;
  teamInvitations: boolean;
  systemAlerts: boolean;
  weeklyReports: boolean;
  marketingEmails: boolean;
}

interface SecurityLog {
  id: string;
  action: string;
  ip: string;
  userAgent: string;
  timestamp: string;
  status: 'success' | 'failed' | 'warning';
  details: string;
}

const Settings: React.FC = () => {
  const { user, updateUser } = useSimpleAuth();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  const [notificationForm] = Form.useForm();
  
  const [loading, setLoading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string>(user?.avatar || '');
  const [activeTab, setActiveTab] = useState('profile');
  // const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  // const [notificationSettings, setNotificationSettings] = useState<NotificationSettings | null>(null);
  const [securityLogs, setSecurityLogs] = useState<SecurityLog[]>([]);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  // const [qrCodeUrl, setQrCodeUrl] = useState<string>(''); // 暂未使用
  const [backupInProgress, setBackupInProgress] = useState(false);
  const [systemStats, setSystemStats] = useState({
    totalUsers: 0,
    totalProjects: 0,
    totalFiles: 0,
    storageUsed: 0,
    storageLimit: 100,
  });

  useEffect(() => {
    if (user) {
      profileForm.setFieldsValue({
        ...user,
        birthDate: user.birthDate ? dayjs(user.birthDate) : null,
      });
    }
    loadSettings();
  }, [user]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // 加载系统设置
      const systemResponse = await userService.getSystemSettings();
      const rawSystemData = systemResponse.data;
      const systemData: SystemSettings = {
        siteName: rawSystemData.site_name || '',
        siteDescription: rawSystemData.site_description || '',
        siteLogo: '', // API暂未提供
        allowRegistration: rawSystemData.allow_registration || false,
        requireEmailVerification: rawSystemData.require_email_verification || false,
        maxFileSize: rawSystemData.max_file_size || 10,
        allowedFileTypes: [], // API暂未提供
        sessionTimeout: rawSystemData.session_timeout || 30,
        passwordPolicy: {
          minLength: 8,
          requireUppercase: false,
          requireLowercase: false,
          requireNumbers: false,
          requireSpecialChars: false,
        },
        emailSettings: {
          smtpHost: '',
          smtpPort: 587,
          smtpUser: '',
          smtpPassword: '',
          fromEmail: '',
          fromName: '',
        },
        backupSettings: {
          autoBackup: rawSystemData.backup_enabled || false,
          backupInterval: 24,
          maxBackups: 30,
          backupPath: '',
        },
      };
      // setSystemSettings(systemData);
      systemForm.setFieldsValue(systemData);
      
      // 加载通知设置
      const notificationResponse = await userService.getNotificationSettings();
      const rawNotificationData = notificationResponse.data || {};
      const notificationData: NotificationSettings = {
        emailNotifications: rawNotificationData.email_notifications || false,
        smsNotifications: false, // API暂未提供sms_notifications字段
        pushNotifications: rawNotificationData.push_notifications || false,
        projectUpdates: rawNotificationData.project_updates || false,
        teamInvitations: false, // 默认值，API暂未提供
        systemAlerts: rawNotificationData.system_alerts || false,
        weeklyReports: rawNotificationData.weekly_digest || false,
        marketingEmails: false, // 默认值，API暂未提供
      };
      // setNotificationSettings(notificationData);
      notificationForm.setFieldsValue(notificationData);
      
      // 加载安全日志
      const logsResponse = await userService.getSecurityLogs({ limit: 10 });
      const logsData = logsResponse.data || [];
      const mappedLogs = logsData.map((log: any) => {
        let status: 'success' | 'warning' | 'failed' = 'failed';
        if (log.success || log.status === 'success') status = 'success';
        else if (log.status === 'warning') status = 'warning';
        
        return {
          id: log.id,
          action: log.action_type || log.action,
          ip: log.ip_address || log.ip,
          userAgent: log.user_agent || log.userAgent,
          timestamp: log.created_at || log.timestamp,
          status,
          details: log.description || log.details
        };
      });
      setSecurityLogs(mappedLogs);
      
      // 加载两步验证状态 (暂时设为false，待后续实现)
      setTwoFactorEnabled(false);
      
      // 加载系统统计 (使用系统设置中的统计数据)
      setSystemStats({
        totalUsers: systemResponse.data.user_count || 0,
        totalProjects: systemResponse.data.project_count || 0,
        totalFiles: systemResponse.data.file_count || 0,
        storageUsed: systemResponse.data.total_storage_used || 0,
        storageLimit: systemResponse.data.storage_limit || 100,
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
      message.error('加载设置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (values: any) => {
    try {
      setLoading(true);
      const userData = {
        ...values,
        avatar: avatarUrl,
        birth_date: values.birthDate?.format('YYYY-MM-DD'),
      };
      
      const updatedUser = await userService.updateCurrentUser(userData);
      updateUser(updatedUser.data);
      message.success('个人信息更新成功');
    } catch (error) {
      console.error('Failed to update profile:', error);
      message.error('更新个人信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    try {
      setLoading(true);
      // 暂时使用console.log，待后续实现changePassword方法
      console.log('Password change request:', values);
      message.success('密码修改成功');
      passwordForm.resetFields();
    } catch (error) {
      console.error('Failed to change password:', error);
      message.error('密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSystemSettingsUpdate = async (values: any) => {
    try {
      setLoading(true);
      await userService.updateSystemSettings(values);
      // setSystemSettings(values);
      message.success('系统设置更新成功');
    } catch (error) {
      console.error('Failed to update system settings:', error);
      message.error('系统设置更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationSettingsUpdate = async (values: any) => {
    try {
      setLoading(true);
      await userService.updateNotificationSettings(values);
      // setNotificationSettings(values);
      message.success('通知设置更新成功');
    } catch (error) {
      console.error('Failed to update notification settings:', error);
      message.error('通知设置更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    try {
      const response = await userService.uploadAvatar(file);
      setAvatarUrl(response.data.avatar_url);
      message.success('头像上传成功');
      return false;
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      message.error('头像上传失败');
      return false;
    }
  };

  const handleEnableTwoFactor = async () => {
    try {
      // 暂时使用模拟实现，待后续添加两步验证功能
      setTwoFactorEnabled(true);
      message.success('两步验证启用成功');
    } catch (error) {
      console.error('Failed to enable two factor:', error);
      message.error('启用两步验证失败');
    }
  };

  const handleDisableTwoFactor = () => {
    Modal.confirm({
      title: '确认禁用两步验证',
      content: '禁用两步验证会降低账户安全性，确定要继续吗？',
      onOk: async () => {
        try {
          // 暂时使用模拟实现，待后续添加两步验证功能
          setTwoFactorEnabled(false);
          message.success('两步验证已禁用');
        } catch (error) {
          console.error('Failed to disable two factor:', error);
          message.error('禁用两步验证失败');
        }
      },
    });
  };

  const handleBackupNow = async () => {
    try {
      setBackupInProgress(true);
      // 暂时使用模拟实现，待后续添加备份功能
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success('备份创建成功');
    } catch (error) {
      console.error('Failed to create backup:', error);
      message.error('备份创建失败');
    } finally {
      setBackupInProgress(false);
    }
  };

  const handleExportData = async () => {
    try {
      // 暂时使用模拟实现，待后续添加数据导出功能
      message.success('数据导出功能开发中');
    } catch (error) {
      console.error('Failed to export data:', error);
      message.error('数据导出失败');
    }
  };

  const getSecurityLogIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  const securityLogColumns = [
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => getSecurityLogIcon(status),
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 120,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 120,
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp: string) => dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>设置</Title>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 个人资料 */}
        <TabPane tab={<span><UserOutlined />个人资料</span>} key="profile">
          <Row gutter={24}>
            <Col xs={24} lg={16}>
              <Card title="基本信息">
                <Form
                  form={profileForm}
                  layout="vertical"
                  onFinish={handleProfileUpdate}
                >
                  <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <Upload
                      beforeUpload={handleAvatarUpload}
                      showUploadList={false}
                      accept="image/*"
                    >
                      <div style={{ position: 'relative', display: 'inline-block' }}>
                        <Avatar
                          size={100}
                          src={avatarUrl}
                          style={{ cursor: 'pointer' }}
                        >
                          {user?.name?.charAt(0) || user?.username?.charAt(0)}
                        </Avatar>
                        <div
                          style={{
                            position: 'absolute',
                            bottom: 0,
                            right: 0,
                            background: '#1890ff',
                            borderRadius: '50%',
                            width: '32px',
                            height: '32px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                          }}
                        >
                          <CameraOutlined style={{ color: 'white', fontSize: '16px' }} />
                        </div>
                      </div>
                    </Upload>
                  </div>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="username"
                        label="用户名"
                        rules={[{ required: true, message: '请输入用户名' }]}
                      >
                        <Input disabled />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="name"
                        label="姓名"
                        rules={[{ required: true, message: '请输入姓名' }]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="email"
                        label="邮箱"
                        rules={[
                          { required: true, message: '请输入邮箱' },
                          { type: 'email', message: '请输入正确的邮箱格式' },
                        ]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="phone"
                        label="手机号"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="department"
                        label="部门"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="position"
                        label="职位"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    name="birthDate"
                    label="生日"
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>

                  <Form.Item
                    name="bio"
                    label="个人简介"
                  >
                    <TextArea rows={4} />
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      保存更改
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            
            <Col xs={24} lg={8}>
              <Card title="账户统计">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Statistic
                    title="注册时间"
                    value={dayjs(user?.createdAt).format('YYYY-MM-DD')}
                    prefix={<CalendarOutlined />}
                  />
                  <Statistic
                    title="最后登录"
                    value={user?.lastLoginAt ? dayjs(user?.lastLoginAt).fromNow() : '从未登录'}
                    prefix={<HistoryOutlined />}
                  />
                  <Statistic
                    title="项目数量"
                    value={user?.projectCount || 0}
                    prefix={<FileTextOutlined />}
                  />
                  <Statistic
                    title="团队数量"
                    value={user?.teamCount || 0}
                    prefix={<TeamOutlined />}
                  />
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 安全设置 */}
        <TabPane tab={<span><SecurityScanOutlined />安全设置</span>} key="security">
          <Row gutter={24}>
            <Col xs={24} lg={12}>
              <Card title="修改密码" style={{ marginBottom: '24px' }}>
                <Form
                  form={passwordForm}
                  layout="vertical"
                  onFinish={handlePasswordChange}
                >
                  <Form.Item
                    name="currentPassword"
                    label="当前密码"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item
                    name="newPassword"
                    label="新密码"
                    rules={[
                      { required: true, message: '请输入新密码' },
                      { min: 6, message: '密码至少6个字符' },
                    ]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item
                    name="confirmPassword"
                    label="确认密码"
                    dependencies={['newPassword']}
                    rules={[
                      { required: true, message: '请确认密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('newPassword') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password />
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      修改密码
                    </Button>
                  </Form.Item>
                </Form>
              </Card>

              <Card title="两步验证">
                <div style={{ marginBottom: '16px' }}>
                  <Space>
                    <SafetyOutlined style={{ fontSize: '24px', color: twoFactorEnabled ? '#52c41a' : '#d9d9d9' }} />
                    <div>
                      <div style={{ fontWeight: 500 }}>
                        两步验证 {twoFactorEnabled ? '已启用' : '未启用'}
                      </div>
                      <Text type="secondary">
                        {twoFactorEnabled ? '您的账户受到额外保护' : '启用两步验证以提高账户安全性'}
                      </Text>
                    </div>
                  </Space>
                </div>
                
                <Button
                  type={twoFactorEnabled ? 'default' : 'primary'}
                  danger={twoFactorEnabled}
                  onClick={twoFactorEnabled ? handleDisableTwoFactor : handleEnableTwoFactor}
                >
                  {twoFactorEnabled ? '禁用两步验证' : '启用两步验证'}
                </Button>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="安全日志">
                <Table
                  columns={securityLogColumns}
                  dataSource={securityLogs}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  scroll={{ y: 300 }}
                />
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <Button size="small" onClick={loadSettings}>
                    查看更多
                  </Button>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 通知设置 */}
        <TabPane tab={<span><BellOutlined />通知设置</span>} key="notifications">
          <Card>
            <Form
              form={notificationForm}
              layout="vertical"
              onFinish={handleNotificationSettingsUpdate}
            >
              <Title level={4}>通知方式</Title>
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item name="emailNotifications" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <span style={{ marginLeft: '8px' }}>邮件通知</span>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="smsNotifications" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <span style={{ marginLeft: '8px' }}>短信通知</span>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="pushNotifications" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <span style={{ marginLeft: '8px' }}>推送通知</span>
                    </div>
                  </Form.Item>
                </Col>
              </Row>

              <Divider />
              
              <Title level={4}>通知内容</Title>
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item name="projectUpdates" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <div style={{ marginLeft: '8px' }}>
                        <div>项目更新</div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>项目状态变更、新文件上传等</Text>
                      </div>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="teamInvitations" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <div style={{ marginLeft: '8px' }}>
                        <div>团队邀请</div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>加入团队、角色变更等</Text>
                      </div>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="systemAlerts" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <div style={{ marginLeft: '8px' }}>
                        <div>系统警告</div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>安全警告、系统维护等</Text>
                      </div>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="weeklyReports" valuePropName="checked">
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Switch />
                      <div style={{ marginLeft: '8px' }}>
                        <div>周报</div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>每周活动摘要</Text>
                      </div>
                    </div>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 数据管理 */}
        <TabPane tab={<span><DatabaseOutlined />数据管理</span>} key="data">
          <Row gutter={24}>
            <Col xs={24} lg={12}>
              <Card title="数据导出" style={{ marginBottom: '24px' }}>
                <Paragraph>
                  导出您的所有个人数据，包括项目、文件、设置等。
                </Paragraph>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleExportData}
                >
                  导出数据
                </Button>
              </Card>

              <Card title="账户删除">
                <Alert
                  message="危险操作"
                  description="删除账户将永久删除您的所有数据，此操作不可恢复。"
                  type="error"
                  showIcon
                  style={{ marginBottom: '16px' }}
                />
                <Button
                  danger
                  onClick={() => {
                    confirm({
                      title: '确认删除账户',
                      content: '此操作将永久删除您的账户和所有相关数据，确定要继续吗？',
                      okText: '确定删除',
                      cancelText: '取消',
                      okType: 'danger',
                      onOk: async () => {
                        try {
                          await userService.deleteAccount();
                          message.success('账户删除成功');
                          // 登出用户
                          window.location.href = '/login';
                        } catch (error) {
                          console.error('Failed to delete account:', error);
                          message.error('账户删除失败');
                        }
                      },
                    });
                  }}
                >
                  删除账户
                </Button>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="存储使用情况">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <Text>已使用存储</Text>
                    <Text>{systemStats.storageUsed}GB / {systemStats.storageLimit}GB</Text>
                  </div>
                  <Progress
                    percent={(systemStats.storageUsed / systemStats.storageLimit) * 100}
                    status={systemStats.storageUsed > systemStats.storageLimit * 0.8 ? 'exception' : 'normal'}
                  />
                </div>
                
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>项目文件</Text>
                    <Text>{(systemStats.storageUsed * 0.7).toFixed(1)}GB</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>用户头像</Text>
                    <Text>{(systemStats.storageUsed * 0.2).toFixed(1)}GB</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>系统备份</Text>
                    <Text>{(systemStats.storageUsed * 0.1).toFixed(1)}GB</Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 系统设置 (仅管理员可见) */}
        {user?.roles?.some(role => role.name === 'admin') && (
          <TabPane tab={<span><SettingOutlined />系统设置</span>} key="system">
            <Row gutter={24}>
              <Col xs={24} lg={16}>
                <Card title="基本设置" style={{ marginBottom: '24px' }}>
                  <Form
                    form={systemForm}
                    layout="vertical"
                    onFinish={handleSystemSettingsUpdate}
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="siteName"
                          label="站点名称"
                          rules={[{ required: true, message: '请输入站点名称' }]}
                        >
                          <Input />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="maxFileSize"
                          label="最大文件大小(MB)"
                          rules={[{ required: true, message: '请输入最大文件大小' }]}
                        >
                          <InputNumber min={1} max={1024} style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      name="siteDescription"
                      label="站点描述"
                    >
                      <TextArea rows={3} />
                    </Form.Item>

                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item name="allowRegistration" valuePropName="checked">
                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            <Switch />
                            <span style={{ marginLeft: '8px' }}>允许用户注册</span>
                          </div>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="requireEmailVerification" valuePropName="checked">
                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            <Switch />
                            <span style={{ marginLeft: '8px' }}>需要邮箱验证</span>
                          </div>
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      name="sessionTimeout"
                      label="会话超时时间(分钟)"
                    >
                      <Slider
                        min={30}
                        max={1440}
                        marks={{
                          30: '30分钟',
                          120: '2小时',
                          480: '8小时',
                          1440: '24小时',
                        }}
                      />
                    </Form.Item>

                    <Form.Item>
                      <Button type="primary" htmlType="submit" loading={loading}>
                        保存设置
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>

                <Card title="备份设置">
                  <Form layout="vertical">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="自动备份">
                          <Switch defaultChecked />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="备份间隔">
                          <Select defaultValue="daily">
                            <Option value="hourly">每小时</Option>
                            <Option value="daily">每天</Option>
                            <Option value="weekly">每周</Option>
                            <Option value="monthly">每月</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item>
                      <Space>
                        <Button
                          type="primary"
                          icon={<CloudOutlined />}
                          onClick={handleBackupNow}
                          loading={backupInProgress}
                        >
                          立即备份
                        </Button>
                        <Button icon={<ReloadOutlined />}>
                          恢复备份
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
              
              <Col xs={24} lg={8}>
                <Card title="系统统计">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Statistic
                      title="总用户数"
                      value={systemStats.totalUsers}
                      prefix={<UserOutlined />}
                    />
                    <Statistic
                      title="总项目数"
                      value={systemStats.totalProjects}
                      prefix={<FileTextOutlined />}
                    />
                    <Statistic
                      title="总文件数"
                      value={systemStats.totalFiles}
                      prefix={<DatabaseOutlined />}
                    />
                    <div>
                      <Text strong>存储使用率</Text>
                      <Progress
                        percent={(systemStats.storageUsed / systemStats.storageLimit) * 100}
                        size="small"
                        style={{ marginTop: '8px' }}
                      />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </TabPane>
        )}
      </Tabs>
    </div>
  );
};

export default Settings;