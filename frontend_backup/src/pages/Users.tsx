import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Avatar,
  Dropdown,
  Menu,
  Modal,
  Form,
  message,
  Typography,
  Row,
  Col,
  Statistic,
  Empty,
  Tooltip,
  Badge,
  Upload,
  DatePicker,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UserOutlined,
  CrownOutlined,
  ExportOutlined,
  ReloadOutlined,
  MailOutlined,
  PhoneOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  UploadOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { userService } from '../services/userService';
import type { User, Role } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;
const { TextArea } = Input;

interface UsersPageState {
  users: User[];
  roles: Role[];
  loading: boolean;
  selectedRowKeys: React.Key[];
  searchText: string;
  filterRole: string;
  filterStatus: string;
  filterDepartment: string;
  sortField: string;
  sortOrder: 'ascend' | 'descend' | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

interface UserStats {
  total: number;
  active: number;
  inactive: number;
  admins: number;
  newThisMonth: number;
}

const Users: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  
  const [state, setState] = useState<UsersPageState>({
    users: [],
    roles: [],
    loading: false,
    selectedRowKeys: [],
    searchText: '',
    filterRole: '',
    filterStatus: '',
    filterDepartment: '',
    sortField: 'createdAt',
    sortOrder: 'descend',
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
    },
  });
  
  const [stats, setStats] = useState<UserStats>({
    total: 0,
    active: 0,
    inactive: 0,
    admins: 0,
    newThisMonth: 0,
  });
  
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [avatarUrl, setAvatarUrl] = useState<string>('');

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, [
    state.pagination.current,
    state.pagination.pageSize,
    state.searchText,
    state.filterRole,
    state.filterStatus,
    state.filterDepartment,
    state.sortField,
    state.sortOrder,
  ]);

  const loadUsers = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));

      const params = {
        page: state.pagination.current,
        pageSize: state.pagination.pageSize,
        search: state.searchText || undefined,
        role: state.filterRole || undefined,
        status: state.filterStatus || undefined,
        department: state.filterDepartment || undefined,
        sortBy: state.sortField,
        sortOrder: state.sortOrder === 'ascend' ? 'asc' : 'desc',
      };

      const response = await userService.getUsers(params);
      setState(prev => ({
        ...prev,
        users: response.data.users,
        pagination: {
          ...prev.pagination,
          total: response.data.total,
        },
      }));

      // 计算统计数据
      const statsData = response.data.users.reduce(
        (acc: any, user: User) => {
          acc.total++;
          if (user.status === 'active') acc.active++;
          else acc.inactive++;
          if (user.roles?.some((role: Role) => role.name === 'admin')) acc.admins++;
          if (dayjs(user.createdAt).isAfter(dayjs().subtract(1, 'month'))) {
            acc.newThisMonth++;
          }
          return acc;
        },
        { total: 0, active: 0, inactive: 0, admins: 0, newThisMonth: 0 }
      );
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load users:', error);
      message.error('加载用户列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const loadRoles = async () => {
    try {
      const response = await userService.getRoles();
      setState(prev => ({ ...prev, roles: response.data }));
    } catch (error) {
      console.error('Failed to load roles:', error);
    }
  };

  const handleSearch = (value: string) => {
    setState(prev => ({
      ...prev,
      searchText: value,
      pagination: { ...prev.pagination, current: 1 },
    }));
  };

  const handleFilterChange = (field: string, value: any) => {
    setState(prev => ({
      ...prev,
      [field]: value,
      pagination: { ...prev.pagination, current: 1 },
    }));
  };

  const handleTableChange = (pagination: any, _filters: any, sorter: any) => {
    setState(prev => ({
      ...prev,
      pagination: {
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: prev.pagination.total,
      },
      sortField: sorter.field || 'createdAt',
      sortOrder: sorter.order,
    }));
  };

  const handleCreateUser = async (values: any) => {
    try {
      const userData = {
        ...values,
        avatar: avatarUrl,
        birthDate: values.birthDate?.format('YYYY-MM-DD'),
      };
      await userService.createUser(userData);
      message.success('用户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      setAvatarUrl('');
      loadUsers();
    } catch (error) {
      console.error('Failed to create user:', error);
      message.error('创建用户失败');
    }
  };

  const handleEditUser = async (values: any) => {
    if (!editingUser) return;

    try {
      const userData = {
        ...values,
        avatar: avatarUrl || editingUser.avatar,
        birthDate: values.birthDate?.format('YYYY-MM-DD'),
      };
      await userService.updateUser(editingUser.id, userData);
      message.success('用户更新成功');
      setEditModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      setAvatarUrl('');
      loadUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
      message.error('更新用户失败');
    }
  };

  const handleDeleteUser = (user: User) => {
    confirm({
      title: '确认删除用户',
      content: `确定要删除用户 "${user.name || user.username}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await userService.deleteUser(user.id);
          message.success('用户删除成功');
          loadUsers();
        } catch (error) {
          console.error('Failed to delete user:', error);
          message.error('删除用户失败');
        }
      },
    });
  };

  const handleToggleUserStatus = async (user: User) => {
    try {
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      await userService.toggleUserStatus(user.id, newStatus === 'active');
      message.success(`用户已${newStatus === 'active' ? '启用' : '禁用'}`);
      loadUsers();
    } catch (error) {
      console.error('Failed to toggle user status:', error);
      message.error('操作失败');
    }
  };

  const handleResetPassword = async (values: any) => {
    if (!editingUser) return;

    try {
      await userService.resetUserPassword(editingUser.id, values.newPassword);
      message.success('密码重置成功');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      console.error('Failed to reset password:', error);
      message.error('密码重置失败');
    }
  };

  const handleBatchDelete = () => {
    if (state.selectedRowKeys.length === 0) {
      message.warning('请选择要删除的用户');
      return;
    }

    confirm({
      title: '批量删除用户',
      content: `确定要删除选中的 ${state.selectedRowKeys.length} 个用户吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await Promise.all(
            state.selectedRowKeys.map(id => userService.deleteUser(Number(id)))
          );
          message.success('批量删除成功');
          setState(prev => ({ ...prev, selectedRowKeys: [] }));
          loadUsers();
        } catch (error) {
          console.error('Failed to batch delete users:', error);
          message.error('批量删除失败');
        }
      },
    });
  };

  const handleExport = async () => {
    try {
      const response = await userService.exportUsers('xlsx', {
        search: state.searchText || undefined,
        role: state.filterRole || undefined,
        status: state.filterStatus || undefined,
        department: state.filterDepartment || undefined,
      });
      
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `users_${dayjs().format('YYYY-MM-DD')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('导出成功');
    } catch (error) {
      console.error('Failed to export users:', error);
      message.error('导出失败');
    }
  };

  const handleAvatarUpload = async (file: File) => {
    try {
      const userId = editingUser?.id || currentUser?.id;
      if (!userId) {
        message.error('用户ID不存在');
        return false;
      }
      const response = await userService.uploadUserAvatar(Number(userId), file);
      setAvatarUrl(response.data.avatar_url);
      message.success('头像上传成功');
      return false; // 阻止默认上传行为
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      message.error('头像上传失败');
      return false;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'active':
        return '正常';
      case 'inactive':
        return '禁用';
      case 'pending':
        return '待激活';
      default:
        return '未知';
    }
  };

  const getActionMenu = (user: User) => {
    const canEdit = currentUser?.id === user.id || currentUser?.roles?.some(role => role.name === 'admin');
    const canDelete = currentUser?.roles?.some(role => role.name === 'admin') && currentUser?.id !== user.id;
    
    return (
      <Menu>
        <Menu.Item
          key="view"
          icon={<EyeOutlined />}
          onClick={() => {
            // 查看用户详情
            Modal.info({
              title: '用户详情',
              width: 600,
              content: (
                <div style={{ marginTop: '16px' }}>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div style={{ textAlign: 'center' }}>
                      <Avatar size={80} src={user.avatar}>
                        {user.name?.charAt(0) || user.username?.charAt(0)}
                      </Avatar>
                      <div style={{ marginTop: '8px' }}>
                        <Title level={4} style={{ margin: 0 }}>
                          {user.name || user.username}
                        </Title>
                        <Text type="secondary">{user.email}</Text>
                      </div>
                    </div>
                    <Divider />
                    <Row gutter={[16, 16]}>
                      <Col span={12}>
                        <Text strong>用户名：</Text>
                        <Text>{user.username}</Text>
                      </Col>
                      <Col span={12}>
                        <Text strong>邮箱：</Text>
                        <Text>{user.email}</Text>
                      </Col>
                      <Col span={12}>
                        <Text strong>手机：</Text>
                        <Text>{user.phone || '未设置'}</Text>
                      </Col>
                      <Col span={12}>
                        <Text strong>部门：</Text>
                        <Text>{user.department || '未设置'}</Text>
                      </Col>
                      <Col span={12}>
                        <Text strong>职位：</Text>
                        <Text>{user.position || '未设置'}</Text>
                      </Col>
                      <Col span={12}>
                        <Text strong>状态：</Text>
                        <Tag color={getStatusColor(user.status)}>
                          {getStatusText(user.status)}
                        </Tag>
                      </Col>
                      <Col span={24}>
                        <Text strong>角色：</Text>
                        <Space>
                          {user.roles?.map(role => (
                            <Tag key={role.id} color="blue">
                              {role.displayName || role.name}
                            </Tag>
                          ))}
                        </Space>
                      </Col>
                      <Col span={24}>
                        <Text strong>创建时间：</Text>
                        <Text>{dayjs(user.createdAt).format('YYYY-MM-DD HH:mm:ss')}</Text>
                      </Col>
                      <Col span={24}>
                        <Text strong>最后登录：</Text>
                        <Text>{user.lastLoginAt ? dayjs(user.lastLoginAt).format('YYYY-MM-DD HH:mm:ss') : '从未登录'}</Text>
                      </Col>
                    </Row>
                  </Space>
                </div>
              ),
            });
          }}
        >
          查看详情
        </Menu.Item>
        {canEdit && (
          <Menu.Item
            key="edit"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingUser(user);
              form.setFieldsValue({
                ...user,
                roleIds: user.roles?.map(role => role.id),
                birthDate: user.birthDate ? dayjs(user.birthDate) : null,
              });
              setAvatarUrl(user.avatar || '');
              setEditModalVisible(true);
            }}
          >
            编辑用户
          </Menu.Item>
        )}
        {canEdit && (
          <Menu.Item
            key="password"
            icon={<LockOutlined />}
            onClick={() => {
              setEditingUser(user);
              setPasswordModalVisible(true);
            }}
          >
            重置密码
          </Menu.Item>
        )}
        {canEdit && (
          <Menu.Item
            key="status"
            icon={user.status === 'active' ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
            onClick={() => handleToggleUserStatus(user)}
          >
            {user.status === 'active' ? '禁用用户' : '启用用户'}
          </Menu.Item>
        )}
        {canDelete && (
          <>
            <Menu.Divider />
            <Menu.Item
              key="delete"
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDeleteUser(user)}
            >
              删除用户
            </Menu.Item>
          </>
        )}
      </Menu>
    );
  };

  const columns = [
    {
      title: '用户信息',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (_: any, record: User) => (
        <Space>
          <Avatar src={record.avatar}>
            {record.name?.charAt(0) || record.username?.charAt(0)}
          </Avatar>
          <div>
            <div style={{ fontWeight: 500 }}>
              {record.name || record.username}
              {record.id === currentUser?.id && (
                <Tag color="gold" style={{ marginLeft: '4px' }}>
                  我
                </Tag>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      sorter: true,
    },
    {
      title: '部门/职位',
      key: 'department',
      width: 150,
      render: (_: any, record: User) => (
        <div>
          <div>{record.department || '未设置'}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.position || '未设置'}
          </Text>
        </div>
      ),
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      width: 150,
      render: (roles: Role[]) => (
        <Space wrap>
          {roles?.map(role => (
            <Tag
              key={role.id}
              color={role.name === 'admin' ? 'red' : role.name === 'manager' ? 'orange' : 'blue'}
              icon={role.name === 'admin' ? <CrownOutlined /> : <UserOutlined />}
            >
              {role.displayName || role.name}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      sorter: true,
      render: (status: string) => (
        <Badge
          status={status === 'active' ? 'success' : status === 'inactive' ? 'error' : 'warning'}
          text={getStatusText(status)}
        />
      ),
    },
    {
      title: '联系方式',
      key: 'contact',
      width: 150,
      render: (_: any, record: User) => (
        <Space direction="vertical" size="small">
          {record.phone && (
            <Space size="small">
              <PhoneOutlined style={{ color: '#1890ff' }} />
              <Text style={{ fontSize: '12px' }}>{record.phone}</Text>
            </Space>
          )}
          <Space size="small">
            <MailOutlined style={{ color: '#52c41a' }} />
            <Text style={{ fontSize: '12px' }}>{record.email}</Text>
          </Space>
        </Space>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'lastLoginAt',
      key: 'lastLoginAt',
      width: 120,
      sorter: true,
      render: (date: string) => (
        <Tooltip title={date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '从未登录'}>
          <Text type="secondary">
            {date ? dayjs(date).fromNow() : '从未登录'}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
      sorter: true,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: User) => (
        <Dropdown overlay={getActionMenu(record)} trigger={['click']}>
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: state.selectedRowKeys,
    onChange: (selectedRowKeys: React.Key[]) => {
      setState(prev => ({ ...prev, selectedRowKeys }));
    },
    getCheckboxProps: (record: User) => ({
      disabled: record.id === currentUser?.id, // 不能选择自己
    }),
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>用户管理</Title>
        <Text type="secondary">管理系统用户账户和权限</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总用户数"
              value={stats.total}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="活跃用户"
              value={stats.active}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="管理员"
              value={stats.admins}
              prefix={<CrownOutlined />}
              valueStyle={{ color: '#fa8c16', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="本月新增"
              value={stats.newThisMonth}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 用户列表 */}
      <Card>
        {/* 工具栏 */}
        <div style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索用户名、邮箱或姓名"
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="角色"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterRole', value)}
              >
                {state.roles.map(role => (
                  <Option key={role.id} value={role.name}>
                    {role.displayName || role.name}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterStatus', value)}
              >
                <Option value="active">正常</Option>
                <Option value="inactive">禁用</Option>
                <Option value="pending">待激活</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="部门"
                allowClear
                onChange={(e) => handleFilterChange('filterDepartment', e.target.value)}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
        </div>

        {/* 操作按钮 */}
        <div style={{ marginBottom: '16px' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              新建用户
            </Button>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadUsers}
            >
              刷新
            </Button>
            {state.selectedRowKeys.length > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBatchDelete}
              >
                批量删除 ({state.selectedRowKeys.length})
              </Button>
            )}
          </Space>
        </div>

        {/* 用户表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={state.users}
          rowKey="id"
          loading={state.loading}
          pagination={{
            ...state.pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无用户数据"
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                >
                  创建第一个用户
                </Button>
              </Empty>
            ),
          }}
        />
      </Card>

      {/* 创建用户模态框 */}
      <Modal
        title="创建新用户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
          setAvatarUrl('');
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateUser}
        >
          <Row gutter={16}>
            <Col span={24} style={{ textAlign: 'center', marginBottom: '16px' }}>
              <Upload
                beforeUpload={handleAvatarUpload}
                showUploadList={false}
                accept="image/*"
              >
                <Avatar
                  size={80}
                  src={avatarUrl}
                  style={{ cursor: 'pointer', border: '2px dashed #d9d9d9' }}
                >
                  {avatarUrl ? null : <UploadOutlined />}
                </Avatar>
              </Upload>
              <div style={{ marginTop: '8px' }}>
                <Text type="secondary">点击上传头像</Text>
              </div>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
                ]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="姓名"
                rules={[
                  { required: true, message: '请输入姓名' },
                  { max: 50, message: '姓名不能超过50个字符' },
                ]}
              >
                <Input placeholder="请输入姓名" />
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
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                ]}
              >
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' },
                ]}
              >
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
            </Col>
            <Col span={12}>
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
                <Input.Password placeholder="请确认密码" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="department"
                label="部门"
              >
                <Input placeholder="请输入部门" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="position"
                label="职位"
              >
                <Input placeholder="请输入职位" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="roleIds"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="请选择角色"
                  optionFilterProp="children"
                >
                  {state.roles.map(role => (
                    <Option key={role.id} value={role.id}>
                      {role.displayName || role.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="birthDate"
                label="生日"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="请选择生日"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="bio"
            label="个人简介"
          >
            <TextArea rows={3} placeholder="请输入个人简介" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setCreateModalVisible(false);
                  form.resetFields();
                  setAvatarUrl('');
                }}
              >
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
          setEditingUser(null);
          form.resetFields();
          setAvatarUrl('');
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditUser}
        >
          <Row gutter={16}>
            <Col span={24} style={{ textAlign: 'center', marginBottom: '16px' }}>
              <Upload
                beforeUpload={handleAvatarUpload}
                showUploadList={false}
                accept="image/*"
              >
                <Avatar
                  size={80}
                  src={avatarUrl || editingUser?.avatar}
                  style={{ cursor: 'pointer', border: '2px dashed #d9d9d9' }}
                >
                  {(avatarUrl || editingUser?.avatar) ? null : <UploadOutlined />}
                </Avatar>
              </Upload>
              <div style={{ marginTop: '8px' }}>
                <Text type="secondary">点击更换头像</Text>
              </div>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
                ]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="姓名"
                rules={[
                  { required: true, message: '请输入姓名' },
                  { max: 50, message: '姓名不能超过50个字符' },
                ]}
              >
                <Input placeholder="请输入姓名" />
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
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                ]}
              >
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="department"
                label="部门"
              >
                <Input placeholder="请输入部门" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="position"
                label="职位"
              >
                <Input placeholder="请输入职位" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="roleIds"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="请选择角色"
                  optionFilterProp="children"
                >
                  {state.roles.map(role => (
                    <Option key={role.id} value={role.id}>
                      {role.displayName || role.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
              >
                <Select>
                  <Option value="active">正常</Option>
                  <Option value="inactive">禁用</Option>
                  <Option value="pending">待激活</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="birthDate"
            label="生日"
          >
            <DatePicker
              style={{ width: '100%' }}
              placeholder="请选择生日"
            />
          </Form.Item>

          <Form.Item
            name="bio"
            label="个人简介"
          >
            <TextArea rows={3} placeholder="请输入个人简介" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setEditModalVisible(false);
                  setEditingUser(null);
                  form.resetFields();
                  setAvatarUrl('');
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存更改
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码模态框 */}
      <Modal
        title="重置密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleResetPassword}
        >
          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
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
            <Input.Password placeholder="请确认密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setPasswordModalVisible(false);
                  passwordForm.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                重置密码
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users;