import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Modal,
  message,
  Typography,
  Row,
  Col,
  Statistic,
  Empty,
  Tooltip,
  Tag,
  Progress,
  Dropdown,
  Menu,
  DatePicker,
  TimePicker,
  Form,
  Radio,
  Checkbox,
  // Divider,
  // Alert,
  // Spin,
  // Timeline,
  // List,
  Avatar,
  // Badge,
  Tabs,
  Descriptions,
  Switch,
  // Slider,
  // TreeSelect,
} from 'antd';
import {
  FileTextOutlined,
  DownloadOutlined,
  EyeOutlined,
  PlusOutlined,
  // SearchOutlined,
  // FilterOutlined,
  MoreOutlined,
  CalendarOutlined,
  // UserOutlined,
  // ProjectOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  TableOutlined,
  // PrinterOutlined,
  ShareAltOutlined,
  // SettingOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
  // ClockCircleOutlined,
  // CheckCircleOutlined,
  // ExclamationCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  CopyOutlined,
  // SendOutlined,
  ScheduleOutlined,
  // TeamOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  // CloudDownloadOutlined,
} from '@ant-design/icons';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { reportService } from '../services/reportService';
import { projectService } from '../services/projectService';
import { userService } from '../services/userService';
import type { Report, ReportTemplate, ReportStats, Project, User } from '../types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;
const { RangePicker } = DatePicker;
// const { TabPane } = Tabs; // 已弃用，使用 items 属性
const { TextArea } = Input;

interface ReportsPageState {
  reports: Report[];
  templates: ReportTemplate[];
  loading: boolean;
  selectedRowKeys: React.Key[];
  searchText: string;
  filterStatus: string;
  filterType: string;
  filterProject: string;
  dateRange: [dayjs.Dayjs, dayjs.Dayjs] | null;
  sortField: string;
  sortOrder: 'ascend' | 'descend' | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

interface ReportGeneration {
  visible: boolean;
  loading: boolean;
  progress: number;
  currentStep: string;
  template: ReportTemplate | null;
}

const Reports: React.FC = () => {
  const { user } = useSimpleAuth();
  const [form] = Form.useForm();
  const [templateForm] = Form.useForm();
  
  const [state, setState] = useState<ReportsPageState>({
    reports: [],
    templates: [],
    loading: false,
    selectedRowKeys: [],
    searchText: '',
    filterStatus: '',
    filterType: '',
    filterProject: '',
    dateRange: null,
    sortField: 'createdAt',
    sortOrder: 'descend',
    pagination: {
      current: 1,
      pageSize: 20,
      total: 0,
    },
  });
  
  const [stats, setStats] = useState<ReportStats>({
    totalReports: 0,
    generatedToday: 0,
    scheduledReports: 0,
    sharedReports: 0,
  });
  
  const [generation, setGeneration] = useState<ReportGeneration>({
    visible: false,
    loading: false,
    progress: 0,
    currentStep: '',
    template: null,
  });
  
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [activeTab, setActiveTab] = useState('reports');

  useEffect(() => {
    loadReports();
    loadTemplates();
    loadStats();
    loadProjects();
    loadUsers();
  }, [
    state.pagination.current,
    state.pagination.pageSize,
    state.searchText,
    state.filterStatus,
    state.filterType,
    state.filterProject,
    state.dateRange,
    state.sortField,
    state.sortOrder,
  ]);

  const loadReports = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));

      const params = {
        skip: (state.pagination.current - 1) * state.pagination.pageSize,
        limit: state.pagination.pageSize,
        filter: {
          search: state.searchText || undefined,
          status: state.filterStatus || undefined,
          type: state.filterType || undefined,
          projectId: state.filterProject || undefined,
          startDate: state.dateRange?.[0]?.format('YYYY-MM-DD'),
          endDate: state.dateRange?.[1]?.format('YYYY-MM-DD'),
          sortBy: state.sortField,
          sortOrder: state.sortOrder === 'ascend' ? 'asc' : 'desc',
        }
      };

      const response = await reportService.getReports(params);
      const reportsData = (response.reports || []).map((report: any) => ({
        ...report,
        creatorId: report.creatorId || report.creator_id || '',
        createdAt: report.createdAt || report.created_at || new Date().toISOString()
      }));
      const totalCount = response.total || reportsData.length;
      setState(prev => ({
        ...prev,
        reports: reportsData,
        pagination: {
          ...prev.pagination,
          total: totalCount,
        },
      }));
    } catch (error) {
      console.error('Failed to load reports:', error);
      message.error('加载报告列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await reportService.getReportTemplates();
      const templatesData = response.data.templates || response.data || [];
      setState(prev => ({ ...prev, templates: templatesData }));
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadStats = async () => {
    try {
      // const response = await reportService.getReportTags();
      const statsData = {
         totalReports: 0,
         generatedToday: 0,
         scheduledReports: 0,
         sharedReports: 0,
       };
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load report stats:', error);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await projectService.getProjects({ limit: 1000 });
      const projectsData = response.data.projects || response.data || [];
      setProjects(projectsData);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await userService.getUsers({ skip: 0, limit: 1000 });
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
      sortField: sorter.field || 'createdAt',
      sortOrder: sorter.order,
    }));
  };

  const handleGenerateReport = async (values: any) => {
    try {
      setGeneration({
        visible: true,
        loading: true,
        progress: 0,
        currentStep: '准备生成报告...',
        template: state.templates.find(t => t.id === values.templateId) || null,
      });

      // 模拟报告生成过程
      const steps = [
        { step: '收集数据...', progress: 20 },
        { step: '分析数据...', progress: 40 },
        { step: '生成图表...', progress: 60 },
        { step: '渲染报告...', progress: 80 },
        { step: '完成生成', progress: 100 },
      ];

      for (const { step, progress } of steps) {
        setGeneration(prev => ({ ...prev, currentStep: step, progress }));
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // const response = await reportService.generateReport(values);
      
      message.success('报告生成成功');
      setCreateModalVisible(false);
      setGeneration(prev => ({ ...prev, visible: false, loading: false }));
      form.resetFields();
      loadReports();
      loadStats();
    } catch (error) {
      console.error('Generate report failed:', error);
      message.error('报告生成失败');
      setGeneration(prev => ({ ...prev, visible: false, loading: false }));
    }
  };

  const handleDownloadReport = async (report: Report, format: 'pdf' | 'excel' | 'word' = 'pdf') => {
    try {
      const blob = await reportService.downloadReport(report.id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('报告下载成功');
    } catch (error) {
      console.error('Download failed:', error);
      message.error('报告下载失败');
    }
  };

  const handlePreviewReport = async (report: Report) => {
    try {
      setSelectedReport(report);
      setPreviewModalVisible(true);
    } catch (error) {
      console.error('Preview failed:', error);
      message.error('预览失败');
    }
  };

  const handleDeleteReport = (reports: Report[]) => {
    const reportTitles = reports.map(r => r.title).join('、');
    confirm({
      title: '确认删除报告',
      content: `确定要删除 "${reportTitles}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await Promise.all(reports.map(report => reportService.deleteReport(report.id)));
          message.success('报告删除成功');
          setState(prev => ({ ...prev, selectedRowKeys: [] }));
          loadReports();
          loadStats();
        } catch (error) {
          console.error('Delete failed:', error);
          message.error('报告删除失败');
        }
      },
    });
  };

  const handleScheduleReport = async (values: any) => {
    try {
      await reportService.scheduleReport({
        ...values,
        reportId: selectedReport?.id,
      });
      message.success('报告定时任务设置成功');
      setScheduleModalVisible(false);
      loadReports();
    } catch (error) {
      console.error('Schedule failed:', error);
      message.error('设置定时任务失败');
    }
  };

  const handleCreateTemplate = async (values: any) => {
    try {
      await reportService.createTemplate(values);
      message.success('模板创建成功');
      setTemplateModalVisible(false);
      templateForm.resetFields();
      loadTemplates();
    } catch (error) {
      console.error('Create template failed:', error);
      message.error('模板创建失败');
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap = {
      generating: { color: 'processing', text: '生成中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '生成失败' },
      scheduled: { color: 'warning', text: '已调度' },
    };
    const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getTypeIcon = (type: string) => {
    const iconMap = {
      summary: <BarChartOutlined />,
      analysis: <PieChartOutlined />,
      trend: <LineChartOutlined />,
      detail: <TableOutlined />,
    };
    return iconMap[type as keyof typeof iconMap] || <FileTextOutlined />;
  };

  const getActionMenu = (report: Report) => {
    const canEdit = String(report.creatorId) === String(user?.id) || user?.roles?.some(role => role.name === 'admin');
    
    return (
      <Menu>
        <Menu.Item
          key="preview"
          icon={<EyeOutlined />}
          onClick={() => handlePreviewReport(report)}
        >
          预览
        </Menu.Item>
        <Menu.Item key="download">
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item
                  key="pdf"
                  icon={<FilePdfOutlined />}
                  onClick={() => handleDownloadReport(report, 'pdf')}
                >
                  下载PDF
                </Menu.Item>
                <Menu.Item
                  key="excel"
                  icon={<FileExcelOutlined />}
                  onClick={() => handleDownloadReport(report, 'excel')}
                >
                  下载Excel
                </Menu.Item>
                <Menu.Item
                  key="word"
                  icon={<FileWordOutlined />}
                  onClick={() => handleDownloadReport(report, 'word')}
                >
                  下载Word
                </Menu.Item>
              </Menu>
            }
            placement="topRight"
          >
            <span>
              <DownloadOutlined /> 下载
            </span>
          </Dropdown>
        </Menu.Item>
        <Menu.Item
          key="share"
          icon={<ShareAltOutlined />}
          onClick={() => {
            // 实现分享功能
            message.info('分享功能开发中');
          }}
        >
          分享
        </Menu.Item>
        <Menu.Divider />
        {canEdit && (
          <Menu.Item
            key="schedule"
            icon={<ScheduleOutlined />}
            onClick={() => {
              setSelectedReport(report);
              setScheduleModalVisible(true);
            }}
          >
            定时生成
          </Menu.Item>
        )}
        <Menu.Item
          key="copy"
          icon={<CopyOutlined />}
          onClick={() => {
            // 实现复制功能
            message.info('复制功能开发中');
          }}
        >
          复制
        </Menu.Item>
        {canEdit && (
          <>
            <Menu.Divider />
            <Menu.Item
              key="delete"
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDeleteReport([report])}
            >
              删除
            </Menu.Item>
          </>
        )}
      </Menu>
    );
  };

  const columns = [
    {
      title: '报告名称',
      dataIndex: 'title',
      key: 'title',
      sorter: true,
      render: (text: string, record: Report, _: any) => (
        <Space>
          {getTypeIcon(record.type)}
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            {record.description && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.description}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string, _: any) => {
        const typeMap = {
          summary: { color: 'blue', text: '汇总报告' },
          analysis: { color: 'green', text: '分析报告' },
          trend: { color: 'orange', text: '趋势报告' },
          detail: { color: 'purple', text: '详细报告' },
        };
        const config = typeMap[type as keyof typeof typeMap] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string, _: any) => getStatusTag(status),
    },
    {
      title: '项目',
      dataIndex: 'project',
      key: 'project',
      width: 120,
      render: (project: any, _: any) => (
        project ? (
          <Space>
            <Avatar size="small" style={{ backgroundColor: project.color }}>
              {project.name.charAt(0)}
            </Avatar>
            <Text>{project.name}</Text>
          </Space>
        ) : (
          <Text type="secondary">全部项目</Text>
        )
      ),
    },
    {
      title: '创建者',
      dataIndex: 'creator',
      key: 'creator',
      width: 120,
      render: (creator: any, _: any) => (
        <Space>
          <Avatar size="small" src={creator?.avatar}>
            {creator?.name?.charAt(0) || creator?.username?.charAt(0)}
          </Avatar>
          <Text>{creator?.name || creator?.username}</Text>
        </Space>
      ),
    },
    {
      title: '生成时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      sorter: true,
      render: (date: string, _: any) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          <Text type="secondary">{dayjs(date).fromNow()}</Text>
        </Tooltip>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: Report) => (
        <Dropdown overlay={getActionMenu(record)} trigger={['click']}>
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  const templateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ReportTemplate, _: any) => (
        <Space>
          {getTypeIcon(record.type)}
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            {record.description && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.description}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string, _: any) => {
        const typeMap = {
          summary: { color: 'blue', text: '汇总报告' },
          analysis: { color: 'green', text: '分析报告' },
          trend: { color: 'orange', text: '趋势报告' },
          detail: { color: 'purple', text: '详细报告' },
        };
        const config = typeMap[type as keyof typeof typeMap] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '使用次数',
      dataIndex: 'usageCount',
      key: 'usageCount',
      width: 100,
      sorter: true,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      sorter: true,
      render: (date: string, _: any) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: ReportTemplate) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              // 预览模板
              message.info('模板预览功能开发中');
            }}
          />
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              // 编辑模板
              message.info('模板编辑功能开发中');
            }}
          />
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => {
              // 删除模板
              confirm({
                title: '确认删除模板',
                content: `确定要删除模板 "${record.name}" 吗？`,
                onOk: async () => {
                  try {
                    await reportService.deleteTemplate(record.id);
                    message.success('模板删除成功');
                    loadTemplates();
                  } catch (error) {
                    message.error('模板删除失败');
                  }
                },
              });
            }}
          />
        </Space>
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
        <Title level={2}>报告管理</Title>
        <Text type="secondary">生成和管理各类项目报告</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总报告数"
              value={stats.totalReports}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="今日生成"
              value={stats.generatedToday}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="定时报告"
              value={stats.scheduledReports}
              prefix={<ScheduleOutlined />}
              valueStyle={{ color: '#fa8c16', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="共享报告"
              value={stats.sharedReports}
              prefix={<ShareAltOutlined />}
              valueStyle={{ color: '#722ed1', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'reports',
              label: '报告列表',
              children: (
                <div>
            {/* 工具栏 */}
            <div style={{ marginBottom: '16px' }}>
              <Row gutter={[16, 16]} align="middle">
                <Col xs={24} sm={12} md={6}>
                  <Search
                    placeholder="搜索报告名称"
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
                    <Option value="generating">生成中</Option>
                    <Option value="completed">已完成</Option>
                    <Option value="failed">生成失败</Option>
                    <Option value="scheduled">已调度</Option>
                  </Select>
                </Col>
                <Col xs={12} sm={6} md={4}>
                  <Select
                    placeholder="类型"
                    allowClear
                    style={{ width: '100%' }}
                    onChange={(value) => handleFilterChange('filterType', value)}
                  >
                    <Option value="summary">汇总报告</Option>
                    <Option value="analysis">分析报告</Option>
                    <Option value="trend">趋势报告</Option>
                    <Option value="detail">详细报告</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <RangePicker
                    style={{ width: '100%' }}
                    onChange={(dates) => handleFilterChange('dateRange', dates)}
                    placeholder={['开始日期', '结束日期']}
                  />
                </Col>
                <Col xs={24} sm={12} md={4}>
                  <Space>
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={loadReports}
                    >
                      刷新
                    </Button>
                  </Space>
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
                  生成报告
                </Button>
                <Button
                  icon={<ImportOutlined />}
                  onClick={() => message.info('批量导入功能开发中')}
                >
                  批量导入
                </Button>
                {state.selectedRowKeys.length > 0 && (
                  <>
                    <Button
                      icon={<ExportOutlined />}
                      onClick={() => {
                        // 批量导出
                        message.info('批量导出功能开发中');
                      }}
                    >
                      批量导出 ({state.selectedRowKeys.length})
                    </Button>
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => {
                        const selectedReports = state.reports.filter(r => state.selectedRowKeys.includes(r.id));
                        handleDeleteReport(selectedReports);
                      }}
                    >
                      批量删除 ({state.selectedRowKeys.length})
                    </Button>
                  </>
                )}
              </Space>
            </div>

            {/* 报告表格 */}
            <Table
              rowSelection={rowSelection}
              columns={columns}
              dataSource={state.reports}
              rowKey="id"
              loading={state.loading}
              pagination={{
                ...state.pagination,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
              onChange={handleTableChange}
              scroll={{ x: 1000 }}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="暂无报告"
                  >
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setCreateModalVisible(true)}
                    >
                      生成第一个报告
                    </Button>
                  </Empty>
                ),
              }}
            />
                </div>
              ),
            },
            {
              key: 'templates',
              label: '报告模板',
              children: (
                <div>
            <div style={{ marginBottom: '16px' }}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setTemplateModalVisible(true)}
                >
                  创建模板
                </Button>
                <Button
                  icon={<ImportOutlined />}
                  onClick={() => message.info('导入模板功能开发中')}
                >
                  导入模板
                </Button>
              </Space>
            </div>

            <Table
              columns={templateColumns}
              dataSource={state.templates}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="暂无模板"
                  >
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setTemplateModalVisible(true)}
                    >
                      创建第一个模板
                    </Button>
                  </Empty>
                ),
              }}
            />
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* 生成报告模态框 */}
      <Modal
        title="生成报告"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerateReport}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="title"
                label="报告标题"
                rules={[
                  { required: true, message: '请输入报告标题' },
                  { max: 100, message: '标题不能超过100个字符' },
                ]}
              >
                <Input placeholder="请输入报告标题" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="templateId"
                label="报告模板"
                rules={[{ required: true, message: '请选择报告模板' }]}
              >
                <Select placeholder="请选择报告模板">
                  {state.templates.map(template => (
                    <Option key={template.id} value={template.id}>
                      {template.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="报告描述"
          >
            <TextArea rows={3} placeholder="请输入报告描述（可选）" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="projectIds"
                label="包含项目"
              >
                <Select
                  mode="multiple"
                  placeholder="选择项目（留空表示所有项目）"
                  allowClear
                >
                  {projects.map(project => (
                    <Option key={project.id} value={project.id}>
                      {project.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="dateRange"
                label="数据时间范围"
                rules={[{ required: true, message: '请选择数据时间范围' }]}
              >
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="includeCharts"
            label="报告选项"
          >
            <Checkbox.Group>
              <Row>
                <Col span={8}>
                  <Checkbox value="charts">包含图表</Checkbox>
                </Col>
                <Col span={8}>
                  <Checkbox value="summary">包含摘要</Checkbox>
                </Col>
                <Col span={8}>
                  <Checkbox value="details">包含详细数据</Checkbox>
                </Col>
                <Col span={8}>
                  <Checkbox value="trends">包含趋势分析</Checkbox>
                </Col>
                <Col span={8}>
                  <Checkbox value="recommendations">包含建议</Checkbox>
                </Col>
              </Row>
            </Checkbox.Group>
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
                生成报告
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 报告生成进度模态框 */}
      <Modal
        title="正在生成报告"
        open={generation.visible}
        closable={false}
        footer={null}
        centered
      >
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Progress
            type="circle"
            percent={generation.progress}
            status={generation.loading ? 'active' : 'success'}
            style={{ marginBottom: '20px' }}
          />
          <div style={{ marginBottom: '10px' }}>
            <Text strong>{generation.currentStep}</Text>
          </div>
          {generation.template && (
            <Text type="secondary">
              使用模板: {generation.template.name}
            </Text>
          )}
        </div>
      </Modal>

      {/* 创建模板模态框 */}
      <Modal
        title="创建报告模板"
        open={templateModalVisible}
        onCancel={() => {
          setTemplateModalVisible(false);
          templateForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={templateForm}
          layout="vertical"
          onFinish={handleCreateTemplate}
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[
              { required: true, message: '请输入模板名称' },
              { max: 50, message: '名称不能超过50个字符' },
            ]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>

          <Form.Item
            name="type"
            label="模板类型"
            rules={[{ required: true, message: '请选择模板类型' }]}
          >
            <Radio.Group>
              <Radio value="summary">汇总报告</Radio>
              <Radio value="analysis">分析报告</Radio>
              <Radio value="trend">趋势报告</Radio>
              <Radio value="detail">详细报告</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="description"
            label="模板描述"
          >
            <TextArea rows={3} placeholder="请输入模板描述" />
          </Form.Item>

          <Form.Item
            name="config"
            label="模板配置"
          >
            <TextArea
              rows={6}
              placeholder="请输入模板配置（JSON格式）"
              defaultValue={JSON.stringify({
                sections: [
                  { type: 'summary', title: '概要' },
                  { type: 'charts', title: '图表分析' },
                  { type: 'data', title: '详细数据' },
                ],
                charts: ['bar', 'line', 'pie'],
                filters: ['project', 'date', 'status'],
              }, null, 2)}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setTemplateModalVisible(false);
                  templateForm.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建模板
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 报告预览模态框 */}
      <Modal
        title={selectedReport?.title}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => selectedReport && handleDownloadReport(selectedReport)}
          >
            下载报告
          </Button>,
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={1000}
        centered
      >
        {selectedReport && (
          <div>
            <Descriptions bordered column={2} style={{ marginBottom: '20px' }}>
              <Descriptions.Item label="报告类型">
                {getTypeIcon(selectedReport.type)} {selectedReport.type}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(selectedReport.status)}
              </Descriptions.Item>
              <Descriptions.Item label="创建者">
                <Space>
                  <Avatar size="small" src={selectedReport.creator?.avatar}>
                    {selectedReport.creator?.name?.charAt(0)}
                  </Avatar>
                  {selectedReport.creator?.name}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="生成时间">
                {dayjs(selectedReport.createdAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedReport.description || '无描述'}
              </Descriptions.Item>
            </Descriptions>

            <div style={{ 
              border: '1px solid #d9d9d9',
              borderRadius: '6px',
              padding: '20px',
              backgroundColor: '#fafafa',
              minHeight: '400px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px', color: '#8c8c8c' }}>
                <FileTextOutlined />
              </div>
              <Title level={4} type="secondary">报告预览</Title>
              <Paragraph type="secondary">
                报告内容预览功能正在开发中...
              </Paragraph>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => handleDownloadReport(selectedReport)}
              >
                下载完整报告
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 定时报告模态框 */}
      <Modal
        title="设置定时报告"
        open={scheduleModalVisible}
        onCancel={() => setScheduleModalVisible(false)}
        footer={null}
      >
        <Form
          layout="vertical"
          onFinish={handleScheduleReport}
        >
          <Form.Item
            name="frequency"
            label="生成频率"
            rules={[{ required: true, message: '请选择生成频率' }]}
          >
            <Radio.Group>
              <Radio value="daily">每日</Radio>
              <Radio value="weekly">每周</Radio>
              <Radio value="monthly">每月</Radio>
              <Radio value="quarterly">每季度</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="time"
            label="生成时间"
            rules={[{ required: true, message: '请选择生成时间' }]}
          >
            <TimePicker style={{ width: '100%' }} format="HH:mm" />
          </Form.Item>

          <Form.Item
            name="recipients"
            label="接收人"
          >
            <Select
              mode="multiple"
              placeholder="选择接收人"
              allowClear
            >
              {users.map(user => (
                <Option key={user.id} value={user.id}>
                  {user.name || user.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="autoSend"
            label="自动发送"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setScheduleModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                设置定时任务
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Reports;