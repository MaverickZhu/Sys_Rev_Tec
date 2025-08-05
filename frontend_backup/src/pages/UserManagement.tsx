import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Table,
  Button,
  Space,
  Tag,
  Avatar,
  Typography,
  Dropdown,
  Menu,
  Input,
  Select,
  Modal,
  Form,
  message,
  Switch,
  Row,
  Col,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  MoreOutlined,
  LockOutlined,
  UnlockOutlined,
  MailOutlined,
  PhoneOutlined,
  TeamOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { userService } from '../services/userService';
import type { User } from '../types';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface UserManagementState {
  users: User[];
  loading: boolean;
  searchText: string;
  filterDepartment: string;
  filterRole: string;
  filterStatus: string;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [state, setState] = useState<UserManagementState>({
    users: [],
    loading: true,
    searchText: '',
    filterDepartment: '',
    filterRole: '',
    filterStatus: '',
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0
    }
  });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  // 加载用户数据
  useEffect(() => {
    loadUsers();
  }, [state.pagination.current, state.pagination.pageSize, state.searchText, state.filterDepartment, state.filterRole, state.filterStatus]);

  const loadUsers = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const response = await userService.getUsers({
        skip: (state.pagination.current - 1) * state.pagination.pageSize,
        limit: state.pagination.pageSize,
        search: state.searchText || undefined,
        department: state.filterDepartment || undefined,
        role: state.filterRole || undefined,
        is_active: state.filterStatus ? state.filterStatus === 'active' : undefined
      });

      setState(prev => ({
        ...prev,
        users: response.data.users,
        pagination: {
          ...prev.pagination,
          total: response.data.total
        },
        loading: false
      }));
    } catch (error) {
      console.error('加载用户数据失败:', error);
      message.error('加载用户数据失败');
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  // 创建用户
  const handleCreateUser = async (values: any) => {
    try {
      await userService.createUser(values);
      message.success('用户创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
      loadUsers();
    } catch (error) {
      console.error('创建用户失败:', error);
      message.error('创建用户失败');
    }
  };

  // 更新用户
  const handleUpdateUser = async (values: any) => {
    if (!selectedUser) return;
    
    try {
      await userService.updateUser(selectedUser.id, values);
      message.success('用户更新成功');
      setEditModalVisible(false);
      setSelectedUser(null);
      editForm.resetFields();
      loadUsers();
    } catch (error) {
      console.error('更新用户失败:', error);
      message.error('更新用户失败');
    }
  };

  // 删除用户
  const handleDeleteUser = (user: User) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 "${user.full_name || user.username}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await userService.deleteUser(user.id);
          message.success('用户删除成功');
          loadUsers();
        } catch (error) {
          console.error('删除用户失败:', error);
          message.error('删除用户失败');
        }
      }
    });
  };

  // 切换用户状态
  const handleToggleUserStatus = async (user: User, isActive: boolean) => {
    try {
      await userService.toggleUserStatus(user.id, isActive);
      message.success(`用户${isActive ? '激活' : '停用'}成功`);
      loadUsers();
    } catch (error) {
      console.error('切换用户状态失败:', error);
      message.error('操作失败');
    }
  };

  // 重置密码
  const handleResetPassword = (user: User) => {
    Modal.confirm({
      title: '重置密码',
      content: `确定要重置用户 "${user.full_name || user.username}" 的密码吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const newPassword = Math.random().toString(36).slice(-8);
          await userService.resetUserPassword(user.id, newPassword);
          Modal.info({
            title: '密码重置成功',
            content: `新密码：${newPassword}\n请告知用户并要求其首次登录后修改密码。`,
            okText: '确定'
          });
        } catch (error) {
          console.error('重置密码失败:', error);
          message.error('重置密码失败');
        }
      }
    });
  };

  // 编辑用户
  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    editForm.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      phone: user.phone,
      department: user.department,
      is_active: user.is_active
    });
    setEditModalVisible(true);
  };

  // 获取状态标签
  const getStatusTag = (isActive: boolean) => {
    return isActive ? (
      <Tag color="success">激活</Tag>
    ) : (
      <Tag color="error">停用</Tag>
    );
  };

  // 用户操作菜单
  const getUserActionMenu = (user: User) => (
    <Menu>
      <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => handleEditUser(user)}>
        编辑用户
      </Menu.Item>
      <Menu.Item 
        key="toggle" 
        icon={user.is_active ? <LockOutlined /> : <UnlockOutlined />}
        onClick={() => handleToggleUserStatus(user, !user.is_active)}
      >
        {user.is_active ? '停用用户' : '激活用户'}
      </Menu.Item>
      <Menu.Item key="reset" icon={<SafetyCertificateOutlined />} onClick={() => handleResetPassword(user)}>
        重置密码
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item 
        key="delete" 
        icon={<DeleteOutlined />} 
        danger
        onClick={() => handleDeleteUser(user)}
        disabled={user.id === currentUser?.id}
      >
        删除用户
      </Menu.Item>
    </Menu>
  );

  // 表格列定义
  const columns = [
    {
      title: '用户信息',
      key: 'user_info',
      render: (_: any, record: User) => (
        <Space>
          <Badge dot={record.is_active} color={record.is_active ? 'green' : 'red'}>
            <Avatar src={record.avatar} size="large">
              {record.full_name?.charAt(0) || record.username.charAt(0)}
            </Avatar>
          </Badge>
          <div>
            <div style={{ fontWeight: 500 }}>{record.full_name || record.username}</div>
            <Text type="secondary">@{record.username}</Text>
          </div>
        </Space>
      )
    },
    {
      title: '联系方式',
      key: 'contact',
      render: (_: any, record: User) => (
        <Space direction="vertical" size="small">
          <Space>
            <MailOutlined />
            <Text>{record.email}</Text>
          </Space>
          {record.phone && (
            <Space>
              <PhoneOutlined />
              <Text>{record.phone}</Text>
            </Space>
          )}
        </Space>
      )
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (department: string) => (
        <Tag icon={<TeamOutlined />}>{department || '未设置'}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => getStatusTag(isActive)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: any, record: User) => (
        <Dropdown overlay={getUserActionMenu(record)} trigger={['click']}>
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      )
    }
  ];

  return (
    <Layout.Content style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>用户管理</Title>
        <Text type="secondary">管理系统用户账户和权限</Text>
      </div>

      <Card 
        title="用户列表" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建用户
          </Button>
        }
      >
        {/* 搜索和过滤 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索用户名、姓名或邮箱"
              allowClear
              onSearch={(value) => setState(prev => ({ ...prev, searchText: value }))}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="部门"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setState(prev => ({ ...prev, filterDepartment: value || '' }))}
            >
              <Option value="audit">审计部</Option>
              <Option value="finance">财务部</Option>
              <Option value="hr">人力资源部</Option>
              <Option value="it">信息技术部</Option>
              <Option value="legal">法务部</Option>
              <Option value="operations">运营部</Option>
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setState(prev => ({ ...prev, filterStatus: value || '' }))}
            >
              <Option value="active">激活</Option>
              <Option value="inactive">停用</Option>
            </Select>
          </Col>
        </Row>

        {/* 用户表格 */}
        <Table
          columns={columns}
          dataSource={state.users}
          rowKey="id"
          loading={state.loading}
          pagination={{
            ...state.pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, pageSize) => {
              setState(prev => ({
                ...prev,
                pagination: {
                  ...prev.pagination,
                  current: page,
                  pageSize: pageSize || 10
                }
              }));
            }
          }}
        />
      </Card>

      {/* 创建用户模态框 */}
      <Modal
        title="创建新用户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateUser}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
                ]}
              >
                <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="full_name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input prefix={<TeamOutlined />} placeholder="请输入真实姓名" />
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
            <Input prefix={<MailOutlined />} placeholder="请输入邮箱地址" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号码"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }
                ]}
              >
                <Input prefix={<PhoneOutlined />} placeholder="请输入手机号码" />
              </Form.Item>
            </Col>
            <Col span={12}>
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
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="password"
            label="初始密码"
            rules={[
              { required: true, message: '请输入初始密码' },
              { min: 8, message: '密码至少8个字符' }
            ]}
          >
            <Input.Password placeholder="请输入初始密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建用户
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户模态框 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedUser(null);
          editForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateUser}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' }
                ]}
              >
                <Input prefix={<UserOutlined />} disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="full_name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input prefix={<TeamOutlined />} placeholder="请输入真实姓名" />
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
            <Input prefix={<MailOutlined />} placeholder="请输入邮箱地址" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号码"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }
                ]}
              >
                <Input prefix={<PhoneOutlined />} placeholder="请输入手机号码" />
              </Form.Item>
            </Col>
            <Col span={12}>
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
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="is_active"
            label="账户状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="激活" unCheckedChildren="停用" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false);
                setSelectedUser(null);
                editForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                更新用户
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout.Content>
  );
};

export default UserManagement;