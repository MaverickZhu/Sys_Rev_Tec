import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Modal,
  Upload,
  message,
  Typography,
  Row,
  Col,
  Tag,
  Progress,
  Tooltip,
  Popconfirm,
  Form,
  Image,
  Descriptions,
  Divider,
  Empty
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  EditOutlined,
  FolderOutlined,
  FileOutlined,
  ReloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileZipOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { fileService } from '../services/fileService';
import { projectService } from '../services/projectService';
import type { ProjectFile, Project } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { Dragger } = Upload;
// 移除未使用的TabPane解构

interface FileManagerState {
  files: ProjectFile[];
  loading: boolean;
  uploadLoading: boolean;
  selectedRowKeys: React.Key[];
  searchText: string;
  filterType: string;
  sortField: string;
  sortOrder: 'ascend' | 'descend' | null;
  viewMode: 'list' | 'grid';
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

const FileManager: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [form] = Form.useForm();
  
  const [state, setState] = useState<FileManagerState>({
    files: [],
    loading: false,
    uploadLoading: false,
    selectedRowKeys: [],
    searchText: '',
    filterType: '',
    sortField: 'uploaded_at',
    sortOrder: 'descend',
    viewMode: 'list',
    pagination: {
      current: 1,
      pageSize: 20,
      total: 0,
    },
  });
  
  const [project, setProject] = useState<Project | null>(null);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<ProjectFile | null>(null);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});

  useEffect(() => {
    if (projectId) {
      loadProject();
      loadFiles();
    }
  }, [
    projectId,
    state.pagination.current,
    state.pagination.pageSize,
    state.searchText,
    state.filterType,
    state.sortField,
    state.sortOrder,
  ]);

  const loadProject = async () => {
    try {
      const response = await projectService.getProject(parseInt(projectId!));
      setProject(response.data);
    } catch (error) {
      console.error('加载项目信息失败:', error);
      message.error('加载项目信息失败');
    }
  };

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

      const response = await fileService.getFiles(parseInt(projectId!), params);
      
      setState(prev => ({
        ...prev,
        files: response.data.files,
        pagination: {
          ...prev.pagination,
          total: response.data.total,
        },
      }));
    } catch (error) {
      console.error('加载文件列表失败:', error);
      message.error('加载文件列表失败');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  // 获取文件图标
  const getFileIcon = (fileType: string, size: number = 16) => {
    const iconProps = { style: { fontSize: size } };
    
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return <FilePdfOutlined {...iconProps} style={{ ...iconProps.style, color: '#ff4d4f' }} />;
      case 'doc':
      case 'docx':
        return <FileWordOutlined {...iconProps} style={{ ...iconProps.style, color: '#1890ff' }} />;
      case 'xls':
      case 'xlsx':
        return <FileExcelOutlined {...iconProps} style={{ ...iconProps.style, color: '#52c41a' }} />;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'svg':
        return <FileImageOutlined {...iconProps} style={{ ...iconProps.style, color: '#722ed1' }} />;
      case 'mp4':
      case 'avi':
      case 'mov':
      case 'wmv':
        return <VideoCameraOutlined {...iconProps} style={{ ...iconProps.style, color: '#fa8c16' }} />;
      case 'mp3':
      case 'wav':
      case 'flac':
        return <AudioOutlined {...iconProps} style={{ ...iconProps.style, color: '#eb2f96' }} />;
      case 'zip':
      case 'rar':
      case '7z':
        return <FileZipOutlined {...iconProps} style={{ ...iconProps.style, color: '#faad14' }} />;
      case 'txt':
      case 'md':
        return <FileTextOutlined {...iconProps} />;
      default:
        return <FileOutlined {...iconProps} />;
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 文件上传处理
  const handleUpload = async (file: File) => {
    try {
      setState(prev => ({ ...prev, uploadLoading: true }));
      
      await fileService.uploadFile(parseInt(projectId!), file, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
        },
      });
      
      message.success(`文件 ${file.name} 上传成功`);
      loadFiles();
      setUploadModalVisible(false);
    } catch (error) {
      console.error('文件上传失败:', error);
      message.error(`文件 ${file.name} 上传失败`);
    } finally {
      setState(prev => ({ ...prev, uploadLoading: false }));
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[file.name];
        return newProgress;
      });
    }
  };

  // 批量上传处理
  const handleBatchUpload = async (files: File[]) => {
    try {
      setState(prev => ({ ...prev, uploadLoading: true }));
      
      await fileService.uploadMultipleFiles(parseInt(projectId!), files, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          files.forEach(file => {
            setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
          });
        },
      });
      
      message.success(`成功上传 ${files.length} 个文件`);
      loadFiles();
      setUploadModalVisible(false);
    } catch (error) {
      console.error('批量上传失败:', error);
      message.error('批量上传失败');
    } finally {
      setState(prev => ({ ...prev, uploadLoading: false }));
      setUploadProgress({});
    }
  };

  // 文件下载
  const handleDownload = async (file: ProjectFile) => {
    try {
      await fileService.downloadFile(parseInt(projectId!), file.id, file.filename);
      message.success('文件下载成功');
    } catch (error) {
      console.error('文件下载失败:', error);
      message.error('文件下载失败');
    }
  };

  // 文件预览
  const handlePreview = async (file: ProjectFile) => {
    try {
      setSelectedFile(file);
      
      if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(file.file_type.toLowerCase())) {
        // 图片文件直接显示
        const previewUrl = await fileService.getFilePreviewUrl(parseInt(projectId!), file.id);
        setPreviewContent(previewUrl);
      } else if (['txt', 'md', 'json', 'xml', 'csv'].includes(file.file_type.toLowerCase())) {
        // 文本文件获取内容
        const response = await fileService.previewFile(parseInt(projectId!), file.id);
        setPreviewContent(response.data.content || '');
      } else {
        // 其他文件类型显示基本信息
        setPreviewContent('');
      }
      
      setPreviewModalVisible(true);
    } catch (error) {
      console.error('文件预览失败:', error);
      message.error('文件预览失败');
    }
  };

  // 文件删除
  const handleDelete = async (file: ProjectFile) => {
    try {
      await fileService.deleteFile(parseInt(projectId!), file.id);
      message.success('文件删除成功');
      loadFiles();
    } catch (error) {
      console.error('文件删除失败:', error);
      message.error('文件删除失败');
    }
  };

  // 批量删除
  const handleBatchDelete = async () => {
    try {
      const fileIds = state.selectedRowKeys.map(key => parseInt(key.toString()));
      await fileService.deleteMultipleFiles(parseInt(projectId!), fileIds);
      message.success(`成功删除 ${fileIds.length} 个文件`);
      setState(prev => ({ ...prev, selectedRowKeys: [] }));
      loadFiles();
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error('批量删除失败');
    }
  };

  // 文件编辑
  const handleEdit = async (values: any) => {
    try {
      if (!selectedFile) return;
      
      await fileService.updateFile(parseInt(projectId!), selectedFile.id, {
        filename: values.filename,
        description: values.description,
        tags: values.tags ? values.tags.split(',').map((tag: string) => tag.trim()) : [],
      });
      
      message.success('文件信息更新成功');
      setEditModalVisible(false);
      loadFiles();
    } catch (error) {
      console.error('文件信息更新失败:', error);
      message.error('文件信息更新失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string, record: ProjectFile) => (
        <Space>
          {getFileIcon(record.file_type)}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 80,
      render: (text: string) => (
        <Tag color="blue">{text.toUpperCase()}</Tag>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: ProjectFile) => (
        <Space>
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedFile(record);
                form.setFieldsValue({
                  filename: record.filename,
                  description: record.description,
                  tags: record.tags?.join(', ') || '',
                });
                setEditModalVisible(true);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个文件吗？"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Layout.Content style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3}>
                <FolderOutlined /> 文件管理
                {project && (
                  <Text type="secondary" style={{ marginLeft: 8, fontSize: 16, fontWeight: 'normal' }}>
                    - {project.name}
                  </Text>
                )}
              </Title>
            </Col>
            <Col>
              <Space>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传文件
                </Button>
                {state.selectedRowKeys.length > 0 && (
                  <Popconfirm
                    title={`确定要删除选中的 ${state.selectedRowKeys.length} 个文件吗？`}
                    onConfirm={handleBatchDelete}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button danger icon={<DeleteOutlined />}>
                      批量删除
                    </Button>
                  </Popconfirm>
                )}
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadFiles}
                >
                  刷新
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <div style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Search
                placeholder="搜索文件名"
                value={state.searchText}
                onChange={(e) => setState(prev => ({ ...prev, searchText: e.target.value }))}
                onSearch={loadFiles}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="文件类型"
                value={state.filterType}
                onChange={(value) => setState(prev => ({ ...prev, filterType: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="pdf">PDF</Option>
                <Option value="doc">Word</Option>
                <Option value="xls">Excel</Option>
                <Option value="jpg">图片</Option>
                <Option value="txt">文本</Option>
              </Select>
            </Col>
          </Row>
        </div>

        <Table
          columns={columns}
          dataSource={state.files}
          rowKey="id"
          loading={state.loading}
          rowSelection={{
            selectedRowKeys: state.selectedRowKeys,
            onChange: (selectedRowKeys) => {
              setState(prev => ({ ...prev, selectedRowKeys }));
            },
          }}
          pagination={{
            current: state.pagination.current,
            pageSize: state.pagination.pageSize,
            total: state.pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, pageSize) => {
              setState(prev => ({
                ...prev,
                pagination: {
                  ...prev.pagination,
                  current: page,
                  pageSize: pageSize || prev.pagination.pageSize,
                },
              }));
            },
          }}
          onChange={(_pagination, _filters, sorter: any) => {
            setState(prev => ({
              ...prev,
              sortField: sorter.field || 'uploaded_at',
              sortOrder: sorter.order,
            }));
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
          name="files"
          multiple
          beforeUpload={(file, fileList) => {
            if (fileList.length === 1) {
              handleUpload(file);
            } else {
              handleBatchUpload(fileList);
            }
            return false;
          }}
          disabled={state.uploadLoading}
        >
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。支持 PDF、Word、Excel、图片等多种格式。
          </p>
        </Dragger>
        
        {Object.keys(uploadProgress).length > 0 && (
          <div style={{ marginTop: 16 }}>
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename} style={{ marginBottom: 8 }}>
                <Text>{filename}</Text>
                <Progress percent={progress} size="small" />
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* 文件预览模态框 */}
      <Modal
        title={`预览 - ${selectedFile?.filename}`}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={() => selectedFile && handleDownload(selectedFile)}>
            下载
          </Button>,
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedFile && (
          <div>
            <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="文件名">{selectedFile.filename}</Descriptions.Item>
              <Descriptions.Item label="文件类型">{selectedFile.file_type.toUpperCase()}</Descriptions.Item>
              <Descriptions.Item label="文件大小">{formatFileSize(selectedFile.file_size)}</Descriptions.Item>
              <Descriptions.Item label="上传时间">
                {dayjs(selectedFile.uploaded_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>
            
            <Divider />
            
            {['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(selectedFile.file_type.toLowerCase()) ? (
              <div style={{ textAlign: 'center' }}>
                <Image
                  src={previewContent}
                  alt={selectedFile.filename}
                  style={{ maxWidth: '100%', maxHeight: 400 }}
                />
              </div>
            ) : ['txt', 'md', 'json', 'xml', 'csv'].includes(selectedFile.file_type.toLowerCase()) ? (
              <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4, maxHeight: 400, overflow: 'auto' }}>
                {previewContent}
              </pre>
            ) : (
              <Empty
                image={getFileIcon(selectedFile.file_type, 48)}
                description="此文件类型不支持预览"
              />
            )}
          </div>
        )}
      </Modal>

      {/* 编辑文件模态框 */}
      <Modal
        title="编辑文件信息"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={() => form.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEdit}
        >
          <Form.Item
            name="filename"
            label="文件名"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item
            name="tags"
            label="标签"
            help="多个标签用逗号分隔"
          >
            <Input placeholder="例如：重要,审查,合同" />
          </Form.Item>
        </Form>
      </Modal>
    </Layout.Content>
  );
};

export default FileManager;