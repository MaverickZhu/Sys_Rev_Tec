import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Upload,
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
  Image,
  Breadcrumb,
  Avatar,
  Divider,
  Drawer,
  Form,
  Alert,
  Radio,
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  FolderOutlined,
  FileOutlined,
  MoreOutlined,
  ShareAltOutlined,
  CopyOutlined,
  ScissorOutlined,
  FolderAddOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  FileImageOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileZipOutlined,
  FileUnknownOutlined,
  HomeOutlined,
  DatabaseOutlined,

  StarOutlined,
  StarFilled,


  UnorderedListOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { fileService } from '../services/fileService';
// TODO: 定义FileItem和FileStats类型
interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  created_at: string;
  updated_at: string;
  path: string;
  isFavorite?: boolean;
  isDirectory?: boolean;
  uploaderId?: string;
  uploader?: { name: string };
  description?: string;
  url?: string;
}

interface FileStats {
  totalFiles: number;
  totalSize: number;
  imageCount: number;
  documentCount: number;
  videoCount: number;
  otherCount: number;
}
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;
const { Dragger } = Upload;
const { TextArea } = Input;

interface FilesPageState {
  files: FileItem[];
  loading: boolean;
  selectedRowKeys: React.Key[];
  searchText: string;
  filterType: string;
  filterProject: string;
  sortField: string;
  sortOrder: 'ascend' | 'descend' | null;
  currentPath: string[];
  viewMode: 'table' | 'grid';
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

interface FilePreview {
  visible: boolean;
  file: FileItem | null;
  loading: boolean;
}

const Files: React.FC = () => {
  const { user } = useAuth();
  const [form] = Form.useForm();
  
  // 假设从URL或context获取项目ID，这里先用默认值
  const projectId = 1; // TODO: 从实际来源获取项目ID
  
  const [state, setState] = useState<FilesPageState>({
    files: [],
    loading: false,
    selectedRowKeys: [],
    searchText: '',
    filterType: '',
    filterProject: '',
    sortField: 'updated_at',
    sortOrder: 'descend',
    currentPath: [],
    viewMode: 'table',
    pagination: {
      current: 1,
      pageSize: 20,
      total: 0,
    },
  });
  
  const [stats, setStats] = useState<FileStats>({
    totalFiles: 0,
    totalSize: 0,
    imageCount: 0,
    documentCount: 0,
    videoCount: 0,
    otherCount: 0,
  });
  
  const [preview, setPreview] = useState<FilePreview>({
    visible: false,
    file: null,
    loading: false,
  });
  
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [createFolderModalVisible, setCreateFolderModalVisible] = useState(false);
  const [shareModalVisible, setShareModalVisible] = useState(false);
  const [propertiesDrawerVisible, setPropertiesDrawerVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);

  const [clipboard, setClipboard] = useState<{ files: FileItem[]; action: 'copy' | 'cut' | null }>({ files: [], action: null });

  useEffect(() => {
    loadFiles();
    loadStats();
  }, [
    state.pagination.current,
    state.pagination.pageSize,
    state.searchText,
    state.filterType,
    state.filterProject,
    state.sortField,
    state.sortOrder,
    state.currentPath,
  ]);

  const loadFiles = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));

      const params = {
        skip: (state.pagination.current - 1) * state.pagination.pageSize,
        limit: state.pagination.pageSize,
        search: state.searchText || undefined,
        file_type: state.filterType || undefined,
        sort_by: state.sortField,
        sort_order: (state.sortOrder === 'ascend' ? 'asc' : 'desc') as 'asc' | 'desc',
      };

      const response = await fileService.getFiles(projectId, params);
      setState(prev => ({
        ...prev,
        files: response.data.files as unknown as FileItem[],
        pagination: {
          ...prev.pagination,
          total: response.data.total,
        },
      }));
    } catch (error) {
      console.error('Failed to load files:', error);
      message.error('加载文件列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const loadStats = async () => {
    try {
      const response = await fileService.getFileStats(projectId);
      setStats({
        totalFiles: response.data.total_files,
        totalSize: response.data.total_size,
        imageCount: response.data.file_types.find(t => t.type.startsWith('image/'))?.count || 0,
        documentCount: response.data.file_types.find(t => t.type.includes('document'))?.count || 0,
        videoCount: response.data.file_types.find(t => t.type.startsWith('video/'))?.count || 0,
        otherCount: response.data.file_types.filter(t => !t.type.startsWith('image/') && !t.type.includes('document') && !t.type.startsWith('video/')).reduce((sum, t) => sum + t.count, 0),
      });
    } catch (error) {
      console.error('Failed to load file stats:', error);
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
      sortField: sorter.field || 'updated_at',
      sortOrder: sorter.order,
    }));
  };

  const handleUpload = async (options: any) => {
    const { file, onProgress, onSuccess, onError } = options;
    
    try {
      const response = await fileService.uploadFile(Number(projectId), file, {
        onUploadProgress: (progressEvent: any) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress({ percent });
        },
      });
      
      onSuccess(response.data);
      message.success(`${file.name} 上传成功`);
      loadFiles();
      loadStats();
    } catch (error) {
      console.error('Upload failed:', error);
      onError(error);
      message.error(`${file.name} 上传失败`);
    } finally {
      // Upload progress cleanup is handled by the upload component
    }
  };

  const handleDownload = async (file: FileItem) => {
    try {
      await fileService.downloadFile(Number(projectId), Number(file.id), file.name);
      message.success('文件下载成功');
    } catch (error) {
      console.error('Download failed:', error);
      message.error('文件下载失败');
    }
  };

  const handleDelete = (files: FileItem[]) => {
    const fileNames = files.map(f => f.name).join('、');
    confirm({
      title: '确认删除文件',
      content: `确定要删除 "${fileNames}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await Promise.all(files.map(file => fileService.deleteFile(Number(projectId), Number(file.id))));
          message.success('文件删除成功');
          setState(prev => ({ ...prev, selectedRowKeys: [] }));
          loadFiles();
          loadStats();
        } catch (error) {
          console.error('Delete failed:', error);
          message.error('文件删除失败');
        }
      },
    });
  };

  const handlePreview = async (file: FileItem) => {
    setPreview({ visible: true, file, loading: true });
    
    try {
      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        const url = await fileService.getFilePreviewUrl(Number(projectId), Number(file.id));
        setPreview(prev => ({ ...prev, file: { ...file, url }, loading: false }));
      } else {
        // 对于其他类型的文件，显示基本信息
        setPreview(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      console.error('Preview failed:', error);
      message.error('预览失败');
      setPreview(prev => ({ ...prev, loading: false }));
    }
  };

  const handleCreateFolder = async (_values: any) => {
    try {
      // TODO: 实现文件夹创建功能
      message.info('文件夹创建功能暂未实现');
      setCreateFolderModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Create folder failed:', error);
      message.error('文件夹创建失败');
    }
  };

  const handleNavigate = (path: string[]) => {
    setState(prev => ({
      ...prev,
      currentPath: path,
      pagination: { ...prev.pagination, current: 1 },
    }));
  };

  const handleCopy = (files: FileItem[]) => {
    setClipboard({ files, action: 'copy' });
    message.success(`已复制 ${files.length} 个文件`);
  };

  const handleCut = (files: FileItem[]) => {
    setClipboard({ files, action: 'cut' });
    message.success(`已剪切 ${files.length} 个文件`);
  };

  const handlePaste = async () => {
    if (clipboard.files.length === 0) {
      message.warning('剪贴板为空');
      return;
    }

    try {
      if (clipboard.action === 'copy') {
        await Promise.all(
          clipboard.files.map(file => 
            fileService.copyFile(Number(projectId), Number(file.id), Number(projectId))
          )
        );
        message.success('文件复制成功');
      } else if (clipboard.action === 'cut') {
        await Promise.all(
          clipboard.files.map(file => 
            fileService.moveFile(Number(projectId), Number(file.id), Number(projectId))
          )
        );
        message.success('文件移动成功');
        setClipboard({ files: [], action: null });
      }
      
      loadFiles();
    } catch (error) {
      console.error('Paste failed:', error);
      message.error('操作失败');
    }
  };

  const handleToggleFavorite = async (_file: FileItem) => {
    try {
      // TODO: 实现收藏功能
      message.info('收藏功能暂未实现');
    } catch (error) {
      console.error('Toggle favorite failed:', error);
      message.error('操作失败');
    }
  };

  const getFileIcon = (file: FileItem) => {
    if (file.isDirectory) {
      return <FolderOutlined style={{ fontSize: '24px', color: '#1890ff' }} />;
    }
    
    const { type } = file;
    if (type.startsWith('image/')) {
      return <FileImageOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
    } else if (type === 'application/pdf') {
      return <FilePdfOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />;
    } else if (type.includes('word')) {
      return <FileWordOutlined style={{ fontSize: '24px', color: '#1890ff' }} />;
    } else if (type.includes('excel') || type.includes('spreadsheet')) {
      return <FileExcelOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
    } else if (type.includes('powerpoint') || type.includes('presentation')) {
      return <FilePptOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />;
    } else if (type.includes('zip') || type.includes('rar') || type.includes('7z')) {
      return <FileZipOutlined style={{ fontSize: '24px', color: '#722ed1' }} />;
    } else if (type.startsWith('text/')) {
      return <FileTextOutlined style={{ fontSize: '24px', color: '#13c2c2' }} />;
    } else {
      return <FileUnknownOutlined style={{ fontSize: '24px', color: '#8c8c8c' }} />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getActionMenu = (file: FileItem) => {
    const canEdit = file.uploaderId === user?.id || user?.roles?.some(role => role.name === 'admin');
    
    return (
      <Menu>
        <Menu.Item
          key="preview"
          icon={<EyeOutlined />}
          onClick={() => handlePreview(file)}
        >
          预览
        </Menu.Item>
        <Menu.Item
          key="download"
          icon={<DownloadOutlined />}
          onClick={() => handleDownload(file)}
        >
          下载
        </Menu.Item>
        <Menu.Item
          key="favorite"
          icon={file.isFavorite ? <StarFilled /> : <StarOutlined />}
          onClick={() => handleToggleFavorite(file)}
        >
          {file.isFavorite ? '取消收藏' : '收藏'}
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item
          key="copy"
          icon={<CopyOutlined />}
          onClick={() => handleCopy([file])}
        >
          复制
        </Menu.Item>
        {canEdit && (
          <Menu.Item
            key="cut"
            icon={<ScissorOutlined />}
            onClick={() => handleCut([file])}
          >
            剪切
          </Menu.Item>
        )}
        <Menu.Item
          key="share"
          icon={<ShareAltOutlined />}
          onClick={() => {
            setSelectedFile(file);
            setShareModalVisible(true);
          }}
        >
          分享
        </Menu.Item>
        <Menu.Item
          key="properties"
          icon={<FileOutlined />}
          onClick={() => {
            setSelectedFile(file);
            setPropertiesDrawerVisible(true);
          }}
        >
          属性
        </Menu.Item>
        {canEdit && (
          <>
            <Menu.Divider />
            <Menu.Item
              key="delete"
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDelete([file])}
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
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
      render: (_text: string, record: FileItem) => (
        <Space>
          {getFileIcon(record)}
          <div>
            <div
              style={{
                fontWeight: 500,
                cursor: record.isDirectory ? 'pointer' : 'default',
                color: record.isDirectory ? '#1890ff' : 'inherit',
              }}
              onClick={() => {
                if (record.isDirectory) {
                  handleNavigate([...state.currentPath, record.name]);
                }
              }}
            >
              {record.name}
              {record.isFavorite && (
                <StarFilled style={{ color: '#faad14', marginLeft: '4px' }} />
              )}
            </div>
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
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      sorter: true,
      render: (size: number, record: FileItem) => (
        record.isDirectory ? '-' : formatFileSize(size)
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string, record: FileItem) => {
        if (record.isDirectory) {
          return <Tag color="blue">文件夹</Tag>;
        }
        
        const typeMap: { [key: string]: { label: string; color: string } } = {
          'image/': { label: '图片', color: 'green' },
          'application/pdf': { label: 'PDF', color: 'red' },
          'text/': { label: '文本', color: 'cyan' },
          'application/zip': { label: '压缩包', color: 'purple' },
          'application/msword': { label: 'Word', color: 'blue' },
          'application/vnd.ms-excel': { label: 'Excel', color: 'green' },
        };
        
        const matchedType = Object.keys(typeMap).find(key => type.includes(key));
        const typeInfo = matchedType ? typeMap[matchedType] : { label: '其他', color: 'default' };
        
        return <Tag color={typeInfo.color}>{typeInfo.label}</Tag>;
      },
    },
    {
      title: '上传者',
      dataIndex: 'uploader',
      key: 'uploader',
      width: 120,
      render: (uploader: any) => (
        <Space>
          <Avatar size="small" src={uploader?.avatar}>
            {uploader?.name?.charAt(0) || uploader?.username?.charAt(0)}
          </Avatar>
          <Text>{uploader?.name || uploader?.username}</Text>
        </Space>
      ),
    },
    {
      title: '修改时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 150,
      sorter: true,
      render: (date: string) => (
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
      render: (_: any, record: FileItem) => (
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

  const breadcrumbItems = [
    {
      title: <HomeOutlined />,
      onClick: () => handleNavigate([]),
    },
    ...state.currentPath.map((path, index) => ({
      title: path,
      onClick: () => handleNavigate(state.currentPath.slice(0, index + 1)),
    })),
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>文件管理</Title>
        <Text type="secondary">管理和组织您的文件</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总文件数"
              value={stats.totalFiles}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="总大小"
              value={formatFileSize(stats.totalSize)}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="图片文件"
              value={stats.imageCount}
              prefix={<FileImageOutlined />}
              valueStyle={{ color: '#fa8c16', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="文档文件"
              value={stats.documentCount}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 文件列表 */}
      <Card>
        {/* 面包屑导航 */}
        <div style={{ marginBottom: '16px' }}>
          <Breadcrumb>
            {breadcrumbItems.map((item, index) => (
              <Breadcrumb.Item key={index}>
                <Button
                  type="link"
                  size="small"
                  onClick={item.onClick}
                  style={{ padding: 0, height: 'auto' }}
                >
                  {item.title}
                </Button>
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>
        </div>

        {/* 工具栏 */}
        <div style={{ marginBottom: '16px' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索文件名"
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="文件类型"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterType', value)}
              >
                <Option value="image">图片</Option>
                <Option value="document">文档</Option>
                <Option value="video">视频</Option>
                <Option value="audio">音频</Option>
                <Option value="archive">压缩包</Option>
              </Select>
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="项目"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('filterProject', value)}
              >
                {/* 这里应该从API获取项目列表 */}
                <Option value="project1">项目1</Option>
                <Option value="project2">项目2</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Button
                  type="text"
                  icon={state.viewMode === 'table' ? <UnorderedListOutlined /> : <AppstoreOutlined />}
                  onClick={() => setState(prev => ({
                    ...prev,
                    viewMode: prev.viewMode === 'table' ? 'grid' : 'table'
                  }))}
                />
              </Space>
            </Col>
          </Row>
        </div>

        {/* 操作按钮 */}
        <div style={{ marginBottom: '16px' }}>
          <Space>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传文件
            </Button>
            <Button
              icon={<FolderAddOutlined />}
              onClick={() => setCreateFolderModalVisible(true)}
            >
              新建文件夹
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadFiles}
            >
              刷新
            </Button>
            {clipboard.files.length > 0 && (
              <Button
                icon={<CopyOutlined />}
                onClick={handlePaste}
              >
                粘贴 ({clipboard.files.length})
              </Button>
            )}
            {state.selectedRowKeys.length > 0 && (
              <>
                <Button
                  icon={<CopyOutlined />}
                  onClick={() => {
                    const selectedFiles = state.files.filter(f => state.selectedRowKeys.includes(f.id));
                    handleCopy(selectedFiles);
                  }}
                >
                  复制 ({state.selectedRowKeys.length})
                </Button>
                <Button
                  icon={<ScissorOutlined />}
                  onClick={() => {
                    const selectedFiles = state.files.filter(f => state.selectedRowKeys.includes(f.id));
                    handleCut(selectedFiles);
                  }}
                >
                  剪切 ({state.selectedRowKeys.length})
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    const selectedFiles = state.files.filter(f => state.selectedRowKeys.includes(f.id));
                    handleDelete(selectedFiles);
                  }}
                >
                  删除 ({state.selectedRowKeys.length})
                </Button>
              </>
            )}
          </Space>
        </div>

        {/* 文件表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={state.files}
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
                description="暂无文件"
              >
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传第一个文件
                </Button>
              </Empty>
            ),
          }}
        />
      </Card>

      {/* 上传文件模态框 */}
      <Modal
        title="上传文件"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Dragger
          multiple
          customRequest={handleUpload}
          showUploadList={{
            showRemoveIcon: true,
          }}
        >
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。严禁上传公司数据或其他敏感文件。
          </p>
        </Dragger>
      </Modal>

      {/* 新建文件夹模态框 */}
      <Modal
        title="新建文件夹"
        open={createFolderModalVisible}
        onCancel={() => {
          setCreateFolderModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateFolder}
        >
          <Form.Item
            name="name"
            label="文件夹名称"
            rules={[
              { required: true, message: '请输入文件夹名称' },
              { max: 50, message: '名称不能超过50个字符' },
            ]}
          >
            <Input placeholder="请输入文件夹名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入描述（可选）" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setCreateFolderModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 文件预览模态框 */}
      <Modal
        title={preview.file?.name}
        open={preview.visible}
        onCancel={() => setPreview({ visible: false, file: null, loading: false })}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={() => preview.file && handleDownload(preview.file)}>
            下载
          </Button>,
          <Button key="close" onClick={() => setPreview({ visible: false, file: null, loading: false })}>
            关闭
          </Button>,
        ]}
        width={800}
        centered
      >
        {preview.loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Progress type="circle" />
          </div>
        ) : preview.file ? (
          <div style={{ textAlign: 'center' }}>
            {preview.file.type.startsWith('image/') ? (
              <Image
                src={preview.file.url}
                alt={preview.file.name}
                style={{ maxWidth: '100%', maxHeight: '500px' }}
              />
            ) : preview.file.type === 'application/pdf' ? (
              <iframe
                src={preview.file.url}
                style={{ width: '100%', height: '500px', border: 'none' }}
                title={preview.file.name}
              />
            ) : (
              <div style={{ padding: '50px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>
                  {getFileIcon(preview.file)}
                </div>
                <Title level={4}>{preview.file.name}</Title>
                <Space direction="vertical">
                  <Text>文件大小: {formatFileSize(preview.file.size)}</Text>
                  <Text>文件类型: {preview.file.type}</Text>
                  <Text>上传时间: {dayjs(preview.file.created_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
                </Space>
              </div>
            )}
          </div>
        ) : null}
      </Modal>

      {/* 文件属性抽屉 */}
      <Drawer
        title="文件属性"
        placement="right"
        onClose={() => setPropertiesDrawerVisible(false)}
        open={propertiesDrawerVisible}
        width={400}
      >
        {selectedFile && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <div style={{ fontSize: '48px', marginBottom: '8px' }}>
                {getFileIcon(selectedFile)}
              </div>
              <Title level={4} style={{ margin: 0 }}>{selectedFile.name}</Title>
            </div>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>文件大小</Text>
                <div>{formatFileSize(selectedFile.size)}</div>
              </div>
              
              <div>
                <Text strong>文件类型</Text>
                <div>{selectedFile.type}</div>
              </div>
              
              <div>
                <Text strong>上传者</Text>
                <div>
                  <Space>
                    <Avatar size="small" style={{ backgroundColor: '#1890ff' }}>
                      {selectedFile.uploader?.name?.charAt(0)}
                    </Avatar>
                    {selectedFile.uploader?.name}
                  </Space>
                </div>
              </div>
              
              <div>
                <Text strong>创建时间</Text>
                <div>{dayjs(selectedFile.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
              </div>
              
              <div>
                <Text strong>修改时间</Text>
                <div>{dayjs(selectedFile.updated_at).format('YYYY-MM-DD HH:mm:ss')}</div>
              </div>
              
              {selectedFile.description && (
                <div>
                  <Text strong>描述</Text>
                  <div>{selectedFile.description}</div>
                </div>
              )}
              
              <div>
                <Text strong>文件路径</Text>
                <div style={{ wordBreak: 'break-all' }}>
                  /{state.currentPath.join('/')}/{selectedFile.name}
                </div>
              </div>
            </Space>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => handleDownload(selectedFile)}
                block
              >
                下载文件
              </Button>
              
              <Button
                icon={selectedFile.isFavorite ? <StarFilled /> : <StarOutlined />}
                onClick={() => handleToggleFavorite(selectedFile)}
                block
              >
                {selectedFile.isFavorite ? '取消收藏' : '添加收藏'}
              </Button>
              
              <Button
                icon={<ShareAltOutlined />}
                onClick={() => {
                  setShareModalVisible(true);
                  setPropertiesDrawerVisible(false);
                }}
                block
              >
                分享文件
              </Button>
            </Space>
          </div>
        )}
      </Drawer>

      {/* 分享文件模态框 */}
      <Modal
        title="分享文件"
        open={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        footer={null}
      >
        {selectedFile && (
          <div>
            <Alert
              message="文件分享"
              description={`您正在分享文件: ${selectedFile.name}`}
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            
            <Form layout="vertical">
              <Form.Item label="分享链接">
                <Input.Group compact>
                  <Input
                    value={`${window.location.origin}/share/${selectedFile.id}`}
                    readOnly
                    style={{ width: 'calc(100% - 80px)' }}
                  />
                  <Button
                    icon={<CopyOutlined />}
                    onClick={() => {
                      navigator.clipboard.writeText(`${window.location.origin}/share/${selectedFile.id}`);
                      message.success('链接已复制到剪贴板');
                    }}
                  >
                    复制
                  </Button>
                </Input.Group>
              </Form.Item>
              
              <Form.Item label="访问权限">
                <Radio.Group defaultValue="view">
                  <Radio value="view">仅查看</Radio>
                  <Radio value="download">可下载</Radio>
                </Radio.Group>
              </Form.Item>
              
              <Form.Item label="有效期">
                <Select defaultValue="7" style={{ width: '100%' }}>
                  <Option value="1">1天</Option>
                  <Option value="7">7天</Option>
                  <Option value="30">30天</Option>
                  <Option value="0">永久</Option>
                </Select>
              </Form.Item>
              
              <Form.Item label="访问密码">
                <Input.Password placeholder="可选，留空则无需密码" />
              </Form.Item>
            </Form>
            
            <div style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setShareModalVisible(false)}>
                  取消
                </Button>
                <Button type="primary">
                  创建分享链接
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Files;