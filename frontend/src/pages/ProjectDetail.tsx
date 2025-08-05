import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Button,
  Space,
  Tabs,
  Table,
  Upload,
  Progress,
  Avatar,
  Descriptions,
  Timeline,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  message,
  Spin,
  Empty,
  Popconfirm,
  // Tooltip,
  // Badge,
  Statistic
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  UserAddOutlined,
  TeamOutlined,
  FileTextOutlined,
  // ClockCircleOutlined,
  CheckCircleOutlined,
  // ExclamationCircleOutlined,
  PlusOutlined,
  // SettingOutlined,
  HistoryOutlined,
  CommentOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext';
import { projectService } from '../services/projectService';
import { fileService } from '../services/fileService';
import { userService } from '../services/userService';
import type { Project, ProjectFile, User, ProjectMember, ProjectActivity } from '../types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  // const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [activities, setActivities] = useState<ProjectActivity[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [memberModalVisible, setMemberModalVisible] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [editForm] = Form.useForm();
  const [memberForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('overview');
  const [uploadLoading, setUploadLoading] = useState(false);

  // 加载项目数据
  useEffect(() => {
    if (id) {
      loadProjectData();
    }
  }, [id]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      const [projectRes, filesRes, membersRes, activitiesRes] = await Promise.all([
        projectService.getProject(parseInt(id!)),
        projectService.getProjectFiles(parseInt(id!)),
        projectService.getProjectMembers(parseInt(id!)),
        projectService.getProjectActivities(parseInt(id!))
      ]);

      setProject(projectRes.data);
      setFiles(filesRes.data);
      setMembers(membersRes.data);
      setActivities(activitiesRes.data);
    } catch (error) {
      console.error('加载项目数据失败:', error);
      message.error('加载项目数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载可用用户列表
  const loadAvailableUsers = async () => {
    try {
      const response = await userService.getUsers({ limit: 100 });
      setAvailableUsers(response.data.users);
    } catch (error) {
      console.error('加载用户列表失败:', error);
    }
  };

  // 编辑项目
  const handleEditProject = async (values: any) => {
    try {
      await projectService.updateProject(parseInt(id!), values);
      message.success('项目更新成功');
      setEditModalVisible(false);
      loadProjectData();
    } catch (error) {
      console.error('更新项目失败:', error);
      message.error('更新项目失败');
    }
  };

  // 删除项目
  const handleDeleteProject = async () => {
    try {
      await projectService.deleteProject(parseInt(id!));
      message.success('项目删除成功');
      navigate('/dashboard');
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error('删除项目失败');
    }
  };

  // 添加成员
  const handleAddMember = async (values: any) => {
    try {
      await projectService.addProjectMember(parseInt(id!), {
        user_id: values.user_id,
        role: values.role
      });
      message.success('成员添加成功');
      setMemberModalVisible(false);
      memberForm.resetFields();
      loadProjectData();
    } catch (error) {
      console.error('添加成员失败:', error);
      message.error('添加成员失败');
    }
  };

  // 移除成员
  const handleRemoveMember = async (userId: number) => {
    try {
      await projectService.removeProjectMember(parseInt(id!), userId);
      message.success('成员移除成功');
      loadProjectData();
    } catch (error) {
      console.error('移除成员失败:', error);
      message.error('移除成员失败');
    }
  };

  // 文件上传
  const handleFileUpload = async (file: File) => {
    try {
      setUploadLoading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', id!);
      
      await fileService.uploadFile(Number(id), file);
      message.success('文件上传成功');
      loadProjectData();
    } catch (error) {
      console.error('文件上传失败:', error);
      message.error('文件上传失败');
    } finally {
      setUploadLoading(false);
    }
  };

  // 文件下载
  const handleFileDownload = async (fileId: number, fileName: string) => {
    try {
      const response = await fileService.downloadFile(Number(id), fileId, fileName);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('文件下载失败:', error);
      message.error('文件下载失败');
    }
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

  // 获取优先级标签
  const getPriorityTag = (priority: string) => {
    const priorityConfig = {
      'low': { color: 'default', text: '低' },
      'medium': { color: 'blue', text: '中' },
      'high': { color: 'orange', text: '高' },
      'urgent': { color: 'red', text: '紧急' }
    };
    const config = priorityConfig[priority as keyof typeof priorityConfig] || { color: 'default', text: priority };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 文件表格列
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string, _record: ProjectFile) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => {
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
      }
    },
    {
      title: '上传者',
      dataIndex: 'uploader',
      key: 'uploader',
      render: (uploader: User) => (
        <Space>
          <Avatar size="small" src={uploader?.avatar}>
            {uploader?.full_name?.charAt(0) || uploader?.username?.charAt(0)}
          </Avatar>
          <span>{uploader?.full_name || uploader?.username}</span>
        </Space>
      )
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: ProjectFile) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => window.open(`/api/files/${record.id}/preview`, '_blank')}
          >
            预览
          </Button>
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleFileDownload(record.id, record.filename)}
          >
            下载
          </Button>
        </Space>
      )
    }
  ];

  // 成员表格列
  const memberColumns = [
    {
      title: '成员',
      dataIndex: 'user',
      key: 'user',
      render: (user: User) => (
        <Space>
          <Avatar src={user?.avatar}>
            {user?.full_name?.charAt(0) || user?.username?.charAt(0)}
          </Avatar>
          <div>
            <div>{user?.full_name || user?.username}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {user?.email}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleConfig = {
          'owner': { color: 'red', text: '项目负责人' },
          'manager': { color: 'blue', text: '项目经理' },
          'member': { color: 'green', text: '项目成员' },
          'viewer': { color: 'default', text: '查看者' }
        };
        const config = roleConfig[role as keyof typeof roleConfig] || { color: 'default', text: role };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '加入时间',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD')
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: ProjectMember) => (
        <Popconfirm
          title="确定要移除这个成员吗？"
          onConfirm={() => handleRemoveMember(record.user.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />}>
            移除
          </Button>
        </Popconfirm>
      )
    }
  ];

  if (loading) {
    return (
      <Layout.Content style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </Layout.Content>
    );
  }

  if (!project) {
    return (
      <Layout.Content style={{ padding: '24px', textAlign: 'center' }}>
        <Empty description="项目不存在" />
      </Layout.Content>
    );
  }

  return (
    <Layout.Content style={{ padding: '24px' }}>
      {/* 项目头部 */}
      <div style={{ marginBottom: '24px' }}>
        <Space style={{ marginBottom: '16px' }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/dashboard')}
          >
            返回
          </Button>
        </Space>
        
        <Row justify="space-between" align="middle">
          <Col>
            <Space direction="vertical" size="small">
              <Title level={2} style={{ margin: 0 }}>
                {project.name}
              </Title>
              <Space>
                {getStatusTag(project.status)}
                {getPriorityTag(project.priority)}
                <Tag>{project.project_type}</Tag>
              </Space>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<EditOutlined />}
                onClick={() => {
                  setEditModalVisible(true);
                  editForm.setFieldsValue({
                    ...project,
                    deadline: project.deadline ? dayjs(project.deadline) : null
                  });
                }}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定要删除这个项目吗？"
                description="此操作不可恢复，请谨慎操作。"
                onConfirm={handleDeleteProject}
                okText="确定"
                cancelText="取消"
                okType="danger"
              >
                <Button danger icon={<DeleteOutlined />}>
                  删除
                </Button>
              </Popconfirm>
            </Space>
          </Col>
        </Row>
      </div>

      {/* 项目统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="项目进度"
              value={project.progress || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
            />
            <Progress percent={project.progress || 0} showInfo={false} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="团队成员"
              value={members.length}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="项目文件"
              value={files.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="活动记录"
              value={activities.length}
              prefix={<HistoryOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 项目详情标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="项目概览" key="overview">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="项目名称">{project.name}</Descriptions.Item>
              <Descriptions.Item label="项目类型">{project.project_type}</Descriptions.Item>
              <Descriptions.Item label="项目状态">{getStatusTag(project.status)}</Descriptions.Item>
              <Descriptions.Item label="优先级">{getPriorityTag(project.priority)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(project.created_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="截止时间">
                {project.deadline ? dayjs(project.deadline).format('YYYY-MM-DD') : '未设置'}
              </Descriptions.Item>
              <Descriptions.Item label="项目描述" span={2}>
                <Paragraph>{project.description || '暂无描述'}</Paragraph>
              </Descriptions.Item>
            </Descriptions>
          </TabPane>

          <TabPane tab={`文件管理 (${files.length})`} key="files">
            <div style={{ marginBottom: '16px' }}>
              <Upload
                beforeUpload={(file) => {
                  handleFileUpload(file);
                  return false;
                }}
                showUploadList={false}
              >
                <Button icon={<UploadOutlined />} loading={uploadLoading}>
                  上传文件
                </Button>
              </Upload>
            </div>
            <Table
              columns={fileColumns}
              dataSource={files}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab={`团队成员 (${members.length})`} key="members">
            <div style={{ marginBottom: '16px' }}>
              <Button
                type="primary"
                icon={<UserAddOutlined />}
                onClick={() => {
                  setMemberModalVisible(true);
                  loadAvailableUsers();
                }}
              >
                添加成员
              </Button>
            </div>
            <Table
              columns={memberColumns}
              dataSource={members}
              rowKey={(record) => `${record.user.id}-${record.role}`}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane tab={`活动记录 (${activities.length})`} key="activities">
            <Timeline>
              {activities.map((activity, index) => (
                <Timeline.Item
                  key={index}
                  dot={
                    activity.action_type === 'project_created' ? <PlusOutlined /> :
                    activity.action_type === 'project_updated' ? <EditOutlined /> :
                    activity.action_type === 'project_deleted' ? <DeleteOutlined /> :
                    <CommentOutlined />
                  }
                >
                  <div>
                    <Text strong>{activity.user?.full_name || activity.user?.username}</Text>
                    <Text> {activity.description}</Text>
                    <br />
                    <Text type="secondary">
                      {dayjs(activity.created_at).format('YYYY-MM-DD HH:mm:ss')}
                    </Text>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </TabPane>
        </Tabs>
      </Card>

      {/* 编辑项目模态框 */}
      <Modal
        title="编辑项目"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditProject}
        >
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="项目状态"
            rules={[{ required: true, message: '请选择项目状态' }]}
          >
            <Select>
              <Option value="active">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="paused">已暂停</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
          >
            <Select>
              <Option value="low">低</Option>
              <Option value="medium">中</Option>
              <Option value="high">高</Option>
              <Option value="urgent">紧急</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="progress"
            label="项目进度"
          >
            <Input type="number" min={0} max={100} suffix="%" />
          </Form.Item>

          <Form.Item
            name="deadline"
            label="截止时间"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="description"
            label="项目描述"
          >
            <TextArea rows={4} />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加成员模态框 */}
      <Modal
        title="添加项目成员"
        open={memberModalVisible}
        onCancel={() => setMemberModalVisible(false)}
        footer={null}
      >
        <Form
          form={memberForm}
          layout="vertical"
          onFinish={handleAddMember}
        >
          <Form.Item
            name="user_id"
            label="选择用户"
            rules={[{ required: true, message: '请选择用户' }]}
          >
            <Select
              showSearch
              placeholder="搜索并选择用户"
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {availableUsers.map(user => (
                <Option key={user.id} value={user.id}>
                  {user.full_name || user.username} ({user.email})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
            initialValue="member"
          >
            <Select>
              <Option value="manager">项目经理</Option>
              <Option value="member">项目成员</Option>
              <Option value="viewer">查看者</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setMemberModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout.Content>
  );
};

export default ProjectDetail;