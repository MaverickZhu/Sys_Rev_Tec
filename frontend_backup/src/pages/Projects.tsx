import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Tag,
  Avatar,
  Progress,
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
} from 'antd';
import {
  PlusOutlined,
  // SearchOutlined,
  // FilterOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  TeamOutlined,
  FileTextOutlined,
  CalendarOutlined,
  ExportOutlined,
  // ImportOutlined,
  ReloadOutlined,
  // SettingOutlined,
  ProjectOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { projectService } from '../services/projectService';
import { userService } from '../services/userService';
import type { Project, User, ProjectMember } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

interface ProjectsPageState {
  projects: Project[];
  loading: boolean;
  selectedRowKeys: React.Key[];
  searchText: string;
  filterStatus: string;
  filterType: string;
  filterPriority: string;
  dateRange: [dayjs.Dayjs, dayjs.Dayjs] | null;
  sortField: string;
  sortOrder: 'ascend' | 'descend' | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

interface ProjectStats {
  total: number;
  active: number;
  completed: number;
  paused: number;
  cancelled: number;
  overdue: number;
}

const Projects: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [form] = Form.useForm();
  const [state, setState] = useState<ProjectsPageState>({
    projects: [],
    loading: false,
    selectedRowKeys: [],
    searchText: '',
    filterStatus: '',
    filterType: '',
    filterPriority: '',
    dateRange: null,
    sortField: 'updatedAt',
    sortOrder: 'descend',
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
    },
  });
  const [stats, setStats] = useState<ProjectStats>({
    total: 0,
    active: 0,
    completed: 0,
    paused: 0,
    cancelled: 0,
    overdue: 0,
  });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    loadProjects();
    loadUsers();
  }, [
    state.pagination.current,
    state.pagination.pageSize,
    state.searchText,
    state.filterStatus,
    state.filterType,
    state.filterPriority,
    state.dateRange,
    state.sortField,
    state.sortOrder,
  ]);

  const loadProjects = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));

      const params = {
        page: state.pagination.current,
        pageSize: state.pagination.pageSize,
        search: state.searchText || undefined,
        status: state.filterStatus || undefined,
        type: state.filterType || undefined,
        priority: state.filterPriority || undefined,
        startDate: state.dateRange?.[0]?.format('YYYY-MM-DD'),
        endDate: state.dateRange?.[1]?.format('YYYY-MM-DD'),
        sortBy: state.sortField,
        sortOrder: state.sortOrder === 'ascend' ? 'asc' : 'desc',
      };

      const response = await projectService.getProjects(params);
      const projectsData = response.data.projects || response.data || [];
      const totalCount = response.data.total || projectsData.length;
      
      const projectsWithMembers = await Promise.all(
        projectsData.map(async (project: Project) => {
          try {
            const membersResponse = await projectService.getProjectMembers(project.id);
            const members = membersResponse.data || [];
            return { ...project, members };
          } catch (error) {
            return { ...project, members: [] };
          }
        })
      );

      setState(prev => ({
        ...prev,
        projects: projectsWithMembers,
        pagination: {
          ...prev.pagination,
          total: totalCount,
        },
      }));

      // 计算统计数据
      const statsData = projectsWithMembers.reduce(
        (acc, project) => {
          acc.total++;
          acc[project.status as keyof ProjectStats]++;
          if (project.deadline && dayjs(project.deadline).isBefore(dayjs()) && project.status !== 'completed') {
            acc.overdue++;
          }
          return acc;
        },
        { total: 0, active: 0, completed: 0, paused: 0, cancelled: 0, overdue: 0 }
      );
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load projects:', error);
      message.error('加载项目列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const loadUsers = async () => {
    try {
      const response = await userService.getUsers({ skip: 0, limit: 100 });
      const usersData = response.data.users || response.data || [];
      setUsers(usersData);
    } catch (error) {
      console.error('Failed to load users:', error);
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
      sortField: sorter.field || 'updatedAt',
      sortOrder: sorter.order,
    }));
  };

  const handleCreateProject = async (values: any) => {
    try {
      const projectData = {
        ...values,
        deadline: values.deadline?.format('YYYY-MM-DD'),
        ownerId: values.ownerId || user?.id,
      };
      await projectService.createProject(projectData);
      message.success('项目创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      loadProjects();
    } catch (error) {
      console.error('Failed to create project:', error);
      message.error('创建项目失败');
    }
  };

  const handleEditProject = async (values: any) => {
    if (!editingProject) return;

    try {
      const projectData = {
        ...values,
        deadline: values.deadline?.format('YYYY-MM-DD'),
      };
      await projectService.updateProject(editingProject.id, projectData);
      message.success('项目更新成功');
      setEditModalVisible(false);
      setEditingProject(null);
      form.resetFields();
      loadProjects();
    } catch (error) {
      console.error('Failed to update project:', error);
      message.error('更新项目失败');
    }
  };

  const handleDeleteProject = (project: Project) => {
    confirm({
      title: '确认删除项目',
      content: `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await projectService.deleteProject(project.id);
          message.success('项目删除成功');
          loadProjects();
        } catch (error) {
          console.error('Failed to delete project:', error);
          message.error('删除项目失败');
        }
      },
    });
  };

  const handleBatchDelete = () => {
    if (state.selectedRowKeys.length === 0) {
      message.warning('请选择要删除的项目');
      return;
    }

    confirm({
      title: '批量删除项目',
      content: `确定要删除选中的 ${state.selectedRowKeys.length} 个项目吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await Promise.all(
            state.selectedRowKeys.map(id => projectService.deleteProject(Number(id)))
          );
          message.success('批量删除成功');
          setState(prev => ({ ...prev, selectedRowKeys: [] }));
          loadProjects();
        } catch (error) {
          console.error('Failed to batch delete projects:', error);
          message.error('批量删除失败');
        }
      },
    });
  };

  const handleExport = async () => {
    try {
      // 导出所有项目数据，这里使用第一个项目的ID作为示例
      const firstProjectId = state.projects[0]?.id || 1;
      const blob = await projectService.exportProject(firstProjectId, 'xlsx');
      
      const url = window.URL.createObjectURL(blob.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `projects_${dayjs().format('YYYY-MM-DD')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('导出成功');
    } catch (error) {
      console.error('Failed to export projects:', error);
      message.error('导出失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'processing';
      case 'completed':
        return 'success';
      case 'paused':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'paused':
        return '已暂停';
      case 'cancelled':
        return '已取消';
      default:
        return '未知';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '#ff4d4f';
      case 'high':
        return '#fa8c16';
      case 'medium':
        return '#1890ff';
      case 'low':
        return '#52c41a';
      default:
        return '#d9d9d9';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '紧急';
      case 'high':
        return '高';
      case 'medium':
        return '中';
      case 'low':
        return '低';
      default:
        return '未设置';
    }
  };

  const getActionMenu = (project: Project) => (
    <Menu>
      <Menu.Item
        key="view"
        icon={<EyeOutlined />}
        onClick={() => navigate(`/projects/${project.id}`)}
      >
        查看详情
      </Menu.Item>
      <Menu.Item
        key="edit"
        icon={<EditOutlined />}
        onClick={() => {
          setEditingProject(project);
          form.setFieldsValue({
            ...project,
            deadline: project.deadline ? dayjs(project.deadline) : null,
          });
          setEditModalVisible(true);
        }}
      >
        编辑项目
      </Menu.Item>
      <Menu.Item
        key="members"
        icon={<TeamOutlined />}
        onClick={() => navigate(`/projects/${project.id}/members`)}
      >
        管理成员
      </Menu.Item>
      <Menu.Item
        key="files"
        icon={<FileTextOutlined />}
        onClick={() => navigate(`/projects/${project.id}/files`)}
      >
        项目文件
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item
        key="delete"
        icon={<DeleteOutlined />}
        danger
        onClick={() => handleDeleteProject(project)}
      >
        删除项目
      </Menu.Item>
    </Menu>
  );

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (text: string, record: Project, _: any) => (
        <Space>
          <Avatar
            size="small"
            style={{ backgroundColor: getPriorityColor(record.priority) }}
          >
            {text.charAt(0).toUpperCase()}
          </Avatar>
          <div>
            <div style={{ fontWeight: 500, cursor: 'pointer' }}
                 onClick={() => navigate(`/projects/${record.id}`)}>
              {text}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.description?.substring(0, 40)}
              {record.description && record.description.length > 40 ? '...' : ''}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string, _: any, __: any) => (
        <Tag color="blue">{type || '未设置'}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      sorter: true,
      render: (status: string, _: any, __: any) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      sorter: true,
      render: (priority: string, _: any, __: any) => (
        <Tag color={getPriorityColor(priority)}>
          {getPriorityText(priority)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      sorter: true,
      render: (progress: number, _: any, __: any) => (
        <Progress
          percent={progress || 0}
          size="small"
          status={progress === 100 ? 'success' : 'active'}
        />
      ),
    },
    {
      title: '负责人',
      dataIndex: 'owner',
      key: 'owner',
      width: 120,
      render: (owner: User, _: any, __: any) => (
        <Space>
          <Avatar size="small" src={owner?.avatar}>
            {owner?.name?.charAt(0) || owner?.username?.charAt(0)}
          </Avatar>
          <Text>{owner?.name || owner?.username}</Text>
        </Space>
      ),
    },
    {
      title: '成员',
      dataIndex: 'members',
      key: 'members',
      width: 100,
      render: (members: ProjectMember[], _: any, __: any) => (
        <Space>
          <Avatar.Group maxCount={3} size="small">
            {members?.map(member => (
              <Tooltip key={member.id} title={member.user.name || member.user.username}>
                <Avatar size="small" src={member.user.avatar}>
                  {member.user.name?.charAt(0) || member.user.username?.charAt(0)}
                </Avatar>
              </Tooltip>
            ))}
          </Avatar.Group>
          {members && members.length > 3 && (
            <Text type="secondary">+{members.length - 3}</Text>
          )}
        </Space>
      ),
    },
    {
      title: '截止日期',
      dataIndex: 'deadline',
      key: 'deadline',
      width: 120,
      sorter: true,
      render: (deadline: string, record: Project) => {
        if (!deadline) return <Text type="secondary">未设置</Text>;
        
        const isOverdue = dayjs(deadline).isBefore(dayjs()) && record.status !== 'completed';
        return (
          <Text type={isOverdue ? 'danger' : 'secondary'}>
            {dayjs(deadline).format('YYYY-MM-DD')}
            {isOverdue && <Badge status="error" style={{ marginLeft: 4 }} />}
          </Text>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
      sorter: true,
      render: (date: string, _: any, __: any) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: Project) => (
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
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>项目管理</Title>
        <Text type="secondary">管理和跟踪所有项目的进展情况</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="总项目"
              value={stats.total}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="进行中"
              value={stats.active}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="已完成"
              value={stats.completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#13c2c2', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="已暂停"
              value={stats.paused}
              prefix={<PauseCircleOutlined />}
              valueStyle={{ color: '#faad14', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="已取消"
              value={stats.cancelled}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#f5222d', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="已逾期"
              value={stats.overdue}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#ff4d4f', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      <Card>
        {/* 工具栏 */}
        <div style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索项目名称或描述"
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterStatus', value)}
              >
                <Option value="active">进行中</Option>
                <Option value="completed">已完成</Option>
                <Option value="paused">已暂停</Option>
                <Option value="cancelled">已取消</Option>
              </Select>
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="优先级"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterPriority', value)}
              >
                <Option value="urgent">紧急</Option>
                <Option value="high">高</Option>
                <Option value="medium">中</Option>
                <Option value="low">低</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <RangePicker
                placeholder={['开始日期', '结束日期']}
                style={{ width: '100%' }}
                onChange={(dates) => handleFilterChange('dateRange', dates)}
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
              新建项目
            </Button>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadProjects}
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

        {/* 项目表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={state.projects}
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
                description="暂无项目数据"
              >
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                >
                  创建第一个项目
                </Button>
              </Empty>
            ),
          }}
        />
      </Card>

      {/* 创建项目模态框 */}
      <Modal
        title="创建新项目"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { max: 100, message: '项目名称不能超过100个字符' },
            ]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="type"
            label="项目类型"
            rules={[{ required: true, message: '请输入项目类型' }]}
          >
            <Input placeholder="请输入项目类型" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入项目描述" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                initialValue="medium"
              >
                <Select>
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                  <Option value="urgent">紧急</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ownerId" label="负责人">
                <Select
                  placeholder="选择负责人"
                  showSearch
                  optionFilterProp="children"
                >
                  {users.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.name || user.username}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="deadline" label="截止日期">
            <DatePicker
              style={{ width: '100%' }}
              placeholder="请选择截止日期"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setCreateModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建项目
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑项目模态框 */}
      <Modal
        title="编辑项目"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingProject(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { max: 100, message: '项目名称不能超过100个字符' },
            ]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="type"
            label="项目类型"
            rules={[{ required: true, message: '请输入项目类型' }]}
          >
            <Input placeholder="请输入项目类型" />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入项目描述" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="status" label="项目状态">
                <Select>
                  <Option value="active">进行中</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="paused">已暂停</Option>
                  <Option value="cancelled">已取消</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="优先级">
                <Select>
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                  <Option value="urgent">紧急</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="progress" label="项目进度">
                <Input
                  type="number"
                  min={0}
                  max={100}
                  placeholder="0-100"
                  suffix="%"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="deadline" label="截止日期">
                <DatePicker
                  style={{ width: '100%' }}
                  placeholder="请选择截止日期"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setEditModalVisible(false);
                  setEditingProject(null);
                  form.resetFields();
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
    </div>
  );
};

export default Projects;