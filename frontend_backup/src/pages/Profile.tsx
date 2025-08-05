import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Upload,
  Avatar,
  Space,
  Divider,
  Row,
  Col,
  message,
  Tabs,
  List,
  Tag,
  Typography,
  Modal,
  Switch,
} from 'antd';
import {
  UserOutlined,
  UploadOutlined,
  EditOutlined,
  LockOutlined,
  BellOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { userService } from '../services/userService';


const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;


interface UserProfile {
  id: number;
  username: string;
  email: string;
  fullName: string;
  avatar?: string;
  phone?: string;
  department?: string;
  position?: string;
  bio?: string;
  lastLogin?: string;
  createdAt: string;
}

interface PasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  project_updates: boolean;
  system_alerts: boolean;
  weekly_digest: boolean;
}

const Profile: React.FC = () => {
  const { updateUser } = useAuth();
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [notificationForm] = Form.useForm();
  
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);

  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [activities, setActivities] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email_notifications: true,
    push_notifications: false,
    project_updates: true,
    system_alerts: true,
    weekly_digest: true,
  });

  useEffect(() => {
    loadProfile();
    loadActivities();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await userService.getCurrentUser();
      const userData = response.data;
      const profileData: UserProfile = {
        ...userData,
        fullName: userData.full_name,
        createdAt: userData.created_at,
        lastLogin: userData.last_login,
      };
      setProfile(profileData);
      form.setFieldsValue(profileData);
    } catch (error) {
      message.error('加载用户信息失败');
    } finally {
      setLoading(false);
    }
  };

  const loadActivities = async () => {
    try {
      if (profile?.id) {
        const response = await userService.getUserActivities(profile.id);
        setActivities(response.data);
      }
    } catch (error) {
      console.error('加载活动记录失败:', error);
    }
  };

  const handleProfileUpdate = async (values: any) => {
    try {
      setLoading(true);
      const response = await userService.updateCurrentUser(values);
      const userData = response.data;
      const profileData: UserProfile = {
        ...userData,
        fullName: userData.full_name,
        createdAt: userData.created_at,
        lastLogin: userData.last_login,
      };
      setProfile(profileData);
      updateUser(userData);
      message.success('个人信息更新成功');
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: PasswordForm) => {
    try {
      setLoading(true);
      await userService.changePassword(values);
      message.success('密码修改成功');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      message.error('密码修改失败，请检查当前密码是否正确');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    try {
      setLoading(true);
      const response = await userService.uploadAvatar(file);
      setProfile(prev => prev ? { ...prev, avatar: response.data.avatar_url } : null);
      message.success('头像上传成功');
    } catch (error) {
      message.error('头像上传失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationUpdate = async (values: NotificationSettings) => {
    try {
      setLoading(true);
      await userService.updateNotificationSettings(values);
      setNotifications(values);
      message.success('通知设置更新成功');
    } catch (error) {
      message.error('设置更新失败');
    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return <div>加载中...</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={24}>
        <Col span={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Avatar
                size={120}
                src={profile.avatar}
                icon={<UserOutlined />}
                style={{ marginBottom: '16px' }}
              />
              <div>
                <Title level={4}>{profile.fullName}</Title>
                <Text type="secondary">{profile.position}</Text>
                <br />
                <Text type="secondary">{profile.department}</Text>
              </div>
              <Divider />
              <Upload
                accept="image/*"
                showUploadList={false}
                beforeUpload={(file) => {
                  handleAvatarUpload(file);
                  return false;
                }}
              >
                <Button icon={<UploadOutlined />}>更换头像</Button>
              </Upload>
            </div>
          </Card>

          <Card title="账户统计" style={{ marginTop: '16px' }}>
            <List size="small">
              <List.Item>
                <Text>用户名：</Text>
                <Text strong>{profile.username}</Text>
              </List.Item>
              <List.Item>
                <Text>注册时间：</Text>
                <Text>{new Date(profile.createdAt).toLocaleDateString()}</Text>
              </List.Item>
              <List.Item>
                <Text>最后登录：</Text>
                <Text>{profile.lastLogin ? new Date(profile.lastLogin).toLocaleString() : '从未登录'}</Text>
              </List.Item>
            </List>
          </Card>
        </Col>

        <Col span={16}>
          <Card>
            <Tabs defaultActiveKey="profile">
              <TabPane tab={<span><EditOutlined />基本信息</span>} key="profile">
                <Form
                  form={form}
                  layout="vertical"
                  onFinish={handleProfileUpdate}
                  initialValues={profile}
                >
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="fullName"
                        label="姓名"
                        rules={[{ required: true, message: '请输入姓名' }]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="email"
                        label="邮箱"
                        rules={[
                          { required: true, message: '请输入邮箱' },
                          { type: 'email', message: '请输入有效的邮箱地址' },
                        ]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="phone" label="电话">
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="department" label="部门">
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item name="position" label="职位">
                    <Input />
                  </Form.Item>

                  <Form.Item name="bio" label="个人简介">
                    <TextArea rows={4} placeholder="介绍一下自己..." />
                  </Form.Item>

                  <Form.Item>
                    <Space>
                      <Button type="primary" htmlType="submit" loading={loading}>
                        保存更改
                      </Button>
                      <Button onClick={() => form.resetFields()}>
                        重置
                      </Button>
                    </Space>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab={<span><LockOutlined />安全设置</span>} key="security">
                <Card title="密码管理" size="small">
                  <p>定期更改密码可以提高账户安全性</p>
                  <Button
                    type="primary"
                    onClick={() => setPasswordModalVisible(true)}
                  >
                    修改密码
                  </Button>
                </Card>

                <Card title="登录记录" size="small" style={{ marginTop: '16px' }}>
                  <List
                    size="small"
                    dataSource={activities.filter(item => item.type === 'login').slice(0, 5)}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          title={`登录时间: ${new Date(item.createdAt).toLocaleString()}`}
                          description={`IP地址: ${item.ipAddress || '未知'}`}
                        />
                        <Tag color={item.success ? 'green' : 'red'}>
                          {item.success ? '成功' : '失败'}
                        </Tag>
                      </List.Item>
                    )}
                  />
                </Card>
              </TabPane>

              <TabPane tab={<span><BellOutlined />通知设置</span>} key="notifications">
                <Form
                  form={notificationForm}
                  layout="vertical"
                  onFinish={handleNotificationUpdate}
                  initialValues={notifications}
                >
                  <Form.Item name="email_notifications" valuePropName="checked">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>邮件通知</div>
                        <Text type="secondary">接收重要系统通知邮件</Text>
                      </div>
                      <Switch />
                    </div>
                  </Form.Item>

                  <Form.Item name="push_notifications" valuePropName="checked">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>推送通知</div>
                        <Text type="secondary">接收浏览器推送通知</Text>
                      </div>
                      <Switch />
                    </div>
                  </Form.Item>

                  <Form.Item name="system_alerts" valuePropName="checked">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>系统警报</div>
                        <Text type="secondary">接收系统重要警报通知</Text>
                      </div>
                      <Switch />
                    </div>
                  </Form.Item>

                  <Form.Item name="project_updates" valuePropName="checked">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>项目更新</div>
                        <Text type="secondary">接收项目状态变更通知</Text>
                      </div>
                      <Switch />
                    </div>
                  </Form.Item>

                  <Form.Item name="weekly_digest" valuePropName="checked">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div>周报摘要</div>
                        <Text type="secondary">接收每周活动摘要邮件</Text>
                      </div>
                      <Switch />
                    </div>
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      保存设置
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab={<span><HistoryOutlined />活动记录</span>} key="activities">
                <List
                  dataSource={activities}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={item.description}
                        description={`${new Date(item.createdAt).toLocaleString()} - ${item.ipAddress || '未知IP'}`}
                      />
                      <Tag color={getActivityColor(item.type)}>
                        {getActivityLabel(item.type)}
                      </Tag>
                    </List.Item>
                  )}
                />
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>

      {/* 修改密码模态框 */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
      >
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
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
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
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                确认修改
              </Button>
              <Button onClick={() => {
                setPasswordModalVisible(false);
                passwordForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

// 辅助函数
const getActivityColor = (type: string) => {
  switch (type) {
    case 'login': return 'green';
    case 'logout': return 'blue';
    case 'create': return 'cyan';
    case 'update': return 'orange';
    case 'delete': return 'red';
    default: return 'default';
  }
};

const getActivityLabel = (type: string) => {
  switch (type) {
    case 'login': return '登录';
    case 'logout': return '登出';
    case 'create': return '创建';
    case 'update': return '更新';
    case 'delete': return '删除';
    default: return '其他';
  }
};

export default Profile;