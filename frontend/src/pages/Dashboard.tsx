import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Tag,
  Avatar,
  Progress,
  Typography,
  Dropdown,
  Menu,
  Input,
  Select,
  DatePicker,
  Modal,
  Form,
  message,
  Empty,
  List,
  Timeline,
  Badge,
  Divider,
  Alert,
  Spin,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  MoreOutlined,
  ProjectOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  TeamOutlined,
  BellOutlined,
  TrendingUpOutlined,
  WarningOutlined,
  CalendarOutlined,
  UserOutlined,
  ReloadOutlined,
  SettingOutlined,
  ExportOutlined,
  ImportOutlined,
  StarOutlined,
  FilterOutlined,
  ExclamationCircleOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  SearchOutlined,
  FileOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { projectService } from '../services/projectService';

import type { Project } from '../types';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  totalFiles: number;
  recentActivity: number;
  pendingReviews: number;
  overdueProjects: number;
  thisMonthProjects: number;
  completionRate: number;
}

interface RecentActivity {
  id: number;
  type: 'create' | 'update' | 'complete' | 'review' | 'comment';
  title: string;
  description: string;
  user: {
    name: string;
    avatar?: string;
  };
  time: string;
  projectId?: number;
}

interface QuickAction {
  key: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  color: string;
}

interface Notification {
  id: number;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSimpleAuth();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    activeProjects: 0,
    completedProjects: 0,
    totalFiles: 0,
    recentActivity: 0,
    pendingReviews: 0,
    overdueProjects: 0,
    thisMonthProjects: 0,
    completionRate: 0
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [favoriteProjects, setFavoriteProjects] = useState<Project[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [createForm] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 加载数据
  useEffect(() => {
    loadDashboardData();
  }, [pagination.current, pagination.pageSize, searchText, filterStatus, filterType, dateRange]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // 并行加载项目列表和统计数据
      const [projectsResponse, statsResponse] = await Promise.all([
        projectService.getProjects({
          skip: (pagination.current - 1) * pagination.pageSize,
          limit: pagination.pageSize,
          search: searchText || undefined,
          status: filterStatus || undefined,
          project_type: filterType || undefined
        }),
        projectService.getDashboardStats()
      ]);

      const projectsData = projectsResponse.data.projects || projectsResponse.data || [];
      const totalCount = projectsResponse.data.total || projectsData.length;
      const statsData = statsResponse.data || {};

      setProjects(projectsData);
      setPagination(prev => ({
        ...prev,
        total: totalCount
      }));
      setStats({
        totalProjects: statsData.totalProjects || 0,
        activeProjects: statsData.activeProjects || 0,
        completedProjects: statsData.completedProjects || 0,
        totalFiles: statsData.totalFiles || 0,
        recentActivity: statsData.recentActivity || 0,
        pendingReviews: statsData.pendingReviews || 0,
        overdueProjects: statsData.overdueProjects || 0,
        thisMonthProjects: statsData.thisMonthProjects || 0,
        completionRate: statsData.completionRate || 0
      });

      // 加载其他数据
      await Promise.all([
        loadRecentActivities(),
        loadNotifications(),
        loadFavoriteProjects()
      ]);
    } catch (error) {
      console.error('加载仪表板数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载最近活动
  const loadRecentActivities = async () => {
    try {
      // 模拟数据，实际应该调用API
      const mockActivities: RecentActivity[] = [
        {
          id: 1,
          type: 'create',
          title: '创建了新项目',
          description: '政府办公设备采购项目',
          user: { name: '张三', avatar: undefined },
          time: '2小时前',
          projectId: 1
        },
        {
          id: 2,
          type: 'update',
          title: '更新了项目进度',
          description: '道路维修工程项目进度更新至75%',
          user: { name: '李四', avatar: undefined },
          time: '4小时前',
          projectId: 2
        },
        {
          id: 3,
          type: 'complete',
          title: '完成了项目审查',
          description: '法律咨询服务项目审查完成',
          user: { name: '王五', avatar: undefined },
          time: '1天前',
          projectId: 3
        }
      ];
      setRecentActivities(mockActivities);
    } catch (error) {
      console.error('加载最近活动失败:', error);
    }
  };

  // 加载通知
  const loadNotifications = async () => {
    try {
      // 模拟数据，实际应该调用API
      const mockNotifications: Notification[] = [
        {
          id: 1,
          type: 'warning',
          title: '项目即将到期',
          message: '政府办公设备采购项目将在3天后到期',
          time: '1小时前',
          read: false
        },
        {
          id: 2,
          type: 'info',
          title: '新的审查任务',
          message: '您有2个新的项目审查任务待处理',
          time: '2小时前',
          read: false
        },
        {
          id: 3,
          type: 'success',
          title: '项目审查完成',
          message: '法律咨询服务项目审查已完成',
          time: '1天前',
          read: true
        }
      ];
      setNotifications(mockNotifications);
    } catch (error) {
      console.error('加载通知失败:', error);
    }
  };

  // 加载收藏项目
  const loadFavoriteProjects = async () => {
    try {
      // 模拟数据，实际应该调用API
      const mockFavorites: Project[] = projects.slice(0, 2);
      setFavoriteProjects(mockFavorites);
    } catch (error) {
      console.error('加载收藏项目失败:', error);
    }
  };

  // 手动刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
    message.success('数据已刷新');
  };

  // 创建项目
  const handleCreateProject = async (values: any) => {
    try {
      await projectService.createProject(values);
      message.success('项目创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
      loadDashboardData();
    } catch (error) {
      console.error('创建项目失败:', error);
      message.error('创建项目失败');
    }
  };

  // 删除项目
  const handleDeleteProject = (projectId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个项目吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await projectService.deleteProject(projectId);
          message.success('项目删除成功');
          loadDashboardData();
        } catch (error) {
          console.error('删除项目失败:', error);
          message.error('删除项目失败');
        }
      }
    });
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      'active': { color: 'processing', text: '进行中' },
      'completed': { color: 'success', text: '已完成' },
      'paused': { color: 'warning', text: '已暂停' },
      'cancelled': { color: 'error', text: '已取消' }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取项目类型标签
  const getTypeTag = (type: string) => {
    const typeConfig = {
      'audit': { color: 'blue', text: '审计项目' },
      'compliance': { color: 'green', text: '合规检查' },
      'risk': { color: 'orange', text: '风险评估' },
      'internal': { color: 'purple', text: '内部审计' }
    };
    const config = typeConfig[type as keyof typeof typeConfig] || { color: 'default', text: type };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 项目操作菜单
  const getActionMenu = (project: Project) => (
    <Menu>
      <Menu.Item key="view" icon={<EyeOutlined />} onClick={() => navigate(`/projects/${project.id}`)}>
        查看详情
      </Menu.Item>
      <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => navigate(`/projects/${project.id}/edit`)}>
        编辑项目
      </Menu.Item>
      <Menu.Item key="members" icon={<TeamOutlined />} onClick={() => navigate(`/projects/${project.id}/members`)}>
        管理成员
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item 
        key="delete" 
        icon={<DeleteOutlined />} 
        danger
        onClick={() => handleDeleteProject(project.id)}
      >
        删除项目
      </Menu.Item>
    </Menu>
  );

  // 表格列定义
  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Project, _: any) => (
        <Space>
          <Avatar icon={<ProjectOutlined />} size="small" />
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.description?.substring(0, 50)}{record.description && record.description.length > 50 ? '...' : ''}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'project_type',
      key: 'project_type',
      width: 120,
      render: (type: string, _: any, __: any) => getTypeTag(type)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string, _: any, __: any) => getStatusTag(status)
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress: number, _: any, __: any) => (
        <Progress 
          percent={progress || 0} 
          size="small" 
          status={progress === 100 ? 'success' : 'active'}
        />
      )
    },
    {
      title: '负责人',
      dataIndex: 'owner',
      key: 'owner',
      width: 120,
      render: (owner: any, _: any, __: any) => (
        <Space>
          <Avatar size="small" src={owner?.avatar}>
            {owner?.full_name?.charAt(0) || owner?.username?.charAt(0)}
          </Avatar>
          <Text>{owner?.full_name || owner?.username}</Text>
        </Space>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string, _: any, __: any) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: any, record: Project) => (
        <Dropdown overlay={getActionMenu(record)} trigger={['click']}>
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      )
    }
  ];

  return (
    <Layout.Content style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>项目仪表板</Title>
        <Text type="secondary">欢迎回来，{user?.full_name || user?.username}！</Text>
      </div>

      {/* 页面头部 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>项目仪表盘</h2>
            <p style={{ margin: '4px 0 0 0', color: '#666' }}>欢迎回来，这里是您的项目概览</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button 
              icon={<BellOutlined />} 
              onClick={() => setShowQuickActions(!showQuickActions)}
            >
              通知 {notifications.filter(n => !n.read).length > 0 && (
                <Badge count={notifications.filter(n => !n.read).length} size="small" />
              )}
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              loading={refreshing}
              onClick={handleRefresh}
            >
              刷新
            </Button>
          </div>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card hoverable>
              <Statistic
                title="总项目数"
                value={stats.totalProjects}
                prefix={<ProjectOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff', fontSize: 28, fontWeight: 'bold' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                本月新增 {stats.thisMonthProjects} 个
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card hoverable>
              <Statistic
                title="进行中"
                value={stats.activeProjects}
                prefix={<ClockCircleOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontSize: 28, fontWeight: 'bold' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                完成率 {stats.completionRate}%
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card hoverable>
              <Statistic
                title="已完成"
                value={stats.completedProjects}
                prefix={<CheckCircleOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14', fontSize: 28, fontWeight: 'bold' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                待审查 {stats.pendingReviews} 个
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card hoverable>
              <Statistic
                title="逾期项目"
                value={stats.overdueProjects}
                prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
                valueStyle={{ color: '#ff4d4f', fontSize: 28, fontWeight: 'bold' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                需要关注
              </div>
            </Card>
          </Col>
        </Row>

      {/* 快捷操作和最近活动 */}
      {showQuickActions && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={16}>
            <Card title="快捷操作" size="small">
              <Row gutter={[8, 8]}>
                <Col span={6}>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />} 
                    block 
                    onClick={() => setCreateModalVisible(true)}
                  >
                    新建项目
                  </Button>
                </Col>
                <Col span={6}>
                  <Button icon={<ImportOutlined />} block>
                    导入项目
                  </Button>
                </Col>
                <Col span={6}>
                  <Button icon={<ExportOutlined />} block>
                    导出数据
                  </Button>
                </Col>
                <Col span={6}>
                  <Button icon={<SettingOutlined />} block>
                    系统设置
                  </Button>
                </Col>
              </Row>
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="通知中心" size="small" extra={
              <Badge count={notifications.filter(n => !n.read).length} size="small" />
            }>
              <List
                size="small"
                dataSource={notifications.slice(0, 3)}
                renderItem={(item) => (
                  <List.Item style={{ padding: '8px 0' }}>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ 
                          fontSize: 12, 
                          fontWeight: item.read ? 'normal' : 'bold',
                          color: item.read ? '#666' : '#000'
                        }}>
                          {item.title}
                        </span>
                        <span style={{ fontSize: 10, color: '#999' }}>{item.time}</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>
                        {item.message}
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 最近活动和收藏项目 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="最近活动" size="small">
            <Timeline 
               size="small"
               items={recentActivities.map((activity) => ({
                 key: activity.id,
                 color: activity.type === 'create' ? 'green' : activity.type === 'update' ? 'blue' : 'orange',
                 children: (
                   <div style={{ fontSize: 12 }}>
                     <div style={{ fontWeight: 500 }}>{activity.title}</div>
                     <div style={{ color: '#666', margin: '2px 0' }}>{activity.description}</div>
                     <div style={{ color: '#999', fontSize: 11 }}>
                       {activity.user.name} · {activity.time}
                     </div>
                   </div>
                 )
               }))}
             />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="收藏项目" size="small">
            <List
              size="small"
              dataSource={favoriteProjects}
              renderItem={(project) => (
                <List.Item 
                  actions={[
                    <Button type="link" size="small" onClick={() => navigate(`/projects/${project.id}`)}>
                      查看
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={<span style={{ fontSize: 13 }}>{project.name}</span>}
                    description={
                      <div style={{ fontSize: 11 }}>
                        {getStatusTag(project.status)}
                        <span style={{ marginLeft: 8, color: '#666' }}>
                          {project.owner?.full_name || project.owner?.username}
                        </span>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目列表 */}
      <Card 
        title="项目列表" 
        extra={
          <Space>
             <Space.Compact>
               <Button 
                 type={viewMode === 'list' ? 'primary' : 'default'}
                 icon={<UnorderedListOutlined />}
                 onClick={() => setViewMode('list')}
               />
               <Button 
                 type={viewMode === 'grid' ? 'primary' : 'default'}
                 icon={<AppstoreOutlined />}
                 onClick={() => setViewMode('grid')}
               />
             </Space.Compact>
             <Button 
               type="primary" 
               icon={<PlusOutlined />}
               onClick={() => setCreateModalVisible(true)}
             >
               新建项目
             </Button>
           </Space>
        }
      >
        {/* 搜索和过滤 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索项目名称或描述"
              allowClear
              onSearch={setSearchText}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="项目状态"
              allowClear
              style={{ width: '100%' }}
              onChange={setFilterStatus}
            >
              <Option value="active">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="paused">已暂停</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="项目类型"
              allowClear
              style={{ width: '100%' }}
              onChange={setFilterType}
            >
              <Option value="audit">审计项目</Option>
              <Option value="compliance">合规检查</Option>
              <Option value="risk">风险评估</Option>
              <Option value="internal">内部审计</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              placeholder={['开始日期', '结束日期']}
              style={{ width: '100%' }}
              onChange={(dates) => setDateRange(dates)}
            />
          </Col>
        </Row>

        {/* 项目列表/网格 */}
        {viewMode === 'list' ? (
          <Table
            columns={columns}
            dataSource={projects}
            rowKey="id"
            loading={loading}
            pagination={{
              ...pagination,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              onChange: (page, pageSize) => {
                setPagination(prev => ({
                  ...prev,
                  current: page,
                  pageSize: pageSize || 10
                }));
              }
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无项目数据"
                >
                  <Button type="primary" onClick={() => setCreateModalVisible(true)}>
                    创建第一个项目
                  </Button>
                </Empty>
              )
            }}
          />
        ) : (
          <div>
            <Row gutter={[16, 16]}>
              {projects.map((project) => (
                <Col xs={24} sm={12} lg={8} xl={6} key={project.id}>
                  <Card
                    hoverable
                    size="small"
                    actions={[
                      <EyeOutlined key="view" onClick={() => navigate(`/projects/${project.id}`)} />,
                      <EditOutlined key="edit" onClick={() => navigate(`/projects/${project.id}/edit`)} />,
                      <DeleteOutlined key="delete" onClick={() => handleDeleteProject(project.id)} style={{ color: '#ff4d4f' }} />
                    ]}
                  >
                    <Card.Meta
                      title={
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: 14, fontWeight: 600 }}>{project.name}</span>
                          {getStatusTag(project.status)}
                        </div>
                      }
                      description={
                        <div>
                          <div style={{ marginBottom: 8 }}>
                            {getTypeTag(project.project_type)}
                            <span style={{ marginLeft: 8, fontSize: 12, color: '#666' }}>
                              {project.owner?.full_name || project.owner?.username}
                            </span>
                          </div>
                          <div style={{ marginBottom: 8 }}>
                            <Progress 
                              percent={project.progress || 0} 
                              size="small" 
                              status={project.status === 'completed' ? 'success' : 'active'}
                            />
                          </div>
                          <div style={{ fontSize: 11, color: '#999' }}>
                            创建时间: {new Date(project.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      }
                    />
                  </Card>
                </Col>
              ))}
            </Row>
            {projects.length === 0 && (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无项目数据"
              >
                <Button type="primary" onClick={() => setCreateModalVisible(true)}>
                  创建第一个项目
                </Button>
              </Empty>
            )}
          </div>
        )}
      </Card>

      {/* 创建项目模态框 */}
      <Modal
        title="创建新项目"
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
          onFinish={handleCreateProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[
              { required: true, message: '请输入项目名称' },
              { max: 100, message: '项目名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="project_type"
            label="项目类型"
            rules={[{ required: true, message: '请选择项目类型' }]}
          >
            <Select placeholder="请选择项目类型">
              <Option value="audit">审计项目</Option>
              <Option value="compliance">合规检查</Option>
              <Option value="risk">风险评估</Option>
              <Option value="internal">内部审计</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea
              rows={4}
              placeholder="请输入项目描述"
            />
          </Form.Item>

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

          <Form.Item
            name="deadline"
            label="截止日期"
          >
            <DatePicker
              style={{ width: '100%' }}
              placeholder="请选择截止日期"
            />
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
                创建项目
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout.Content>
  );
};

export default Dashboard;