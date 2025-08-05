// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  name?: string; // 别名，用于兼容
  department?: string;
  position?: string;
  phone?: string;
  avatar?: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: Role[];
  permissions: Permission[];
  created_at: string;
  createdAt?: string; // 添加兼容属性
  updated_at: string;
  updatedAt?: string; // 添加兼容属性
  last_login?: string;
  lastLoginAt?: string; // 添加兼容属性
  login_count: number;
  two_factor_enabled: boolean;
  birthDate?: string; // 添加生日属性
  birth_date?: string; // 添加生日属性（后端格式）
  status?: 'active' | 'inactive' | 'pending'; // 添加状态属性
  teamCount?: number; // 团队数量
  projectCount?: number; // 项目数量
  bio?: string; // 个人简介
}

export interface Role {
  id: number;
  name: string;
  displayName?: string;
  description?: string;
  permissions: Permission[];
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: number;
  name: string;
  resource: string;
  action: string;
  description?: string;
  created_at: string;
}

// 认证相关类型
export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
  two_factor_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  requires_2fa?: boolean;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  department?: string;
  position?: string;
  phone?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

// 用户管理相关类型
export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  department?: string;
  position?: string;
  phone?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  roles?: number[];
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  full_name?: string;
  department?: string;
  position?: string;
  phone?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  roles?: number[];
}

export interface UserListResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  superusers: number;
  recent_logins: number;
  new_users_this_month: number;
}

// 项目相关类型
export interface Project {
  id: number;
  name: string;
  description?: string;
  project_type: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  progress: number;
  start_date?: string;
  end_date?: string;
  deadline?: string;
  budget?: number;
  owner: User;
  members: ProjectMember[];
  files: ProjectFile[];
  tags: ProjectTag[];
  metadata?: Record<string, any>;
  is_archived: boolean;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  last_activity_at?: string;
}

export type ProjectStatus = 
  | 'planning'
  | 'active'
  | 'on_hold'
  | 'completed'
  | 'cancelled'
  | 'archived';

export type ProjectPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface CreateProjectRequest {
  name: string;
  description?: string;
  project_type: string;
  priority?: ProjectPriority;
  start_date?: string;
  end_date?: string;
  deadline?: string;
  budget?: number;
  tags?: string[];
  members?: Array<{
    user_id: number;
    role: string;
  }>;
  metadata?: Record<string, any>;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  project_type?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
  progress?: number;
  start_date?: string;
  end_date?: string;
  deadline?: string;
  budget?: number;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  skip: number;
  limit: number;
}

export interface ProjectStats {
  total_files: number;
  total_members: number;
  total_activities: number;
  completion_rate: number;
  days_remaining?: number;
  budget_used?: number;
  recent_activity_count: number;
}

// 项目成员相关类型
export interface ProjectMember {
  id: number;
  user: User;
  project_id: number;
  role: ProjectMemberRole;
  permissions: string[];
  joined_at: string;
  last_activity_at?: string;
}

export type ProjectMemberRole = 
  | 'owner'
  | 'admin'
  | 'member'
  | 'viewer'
  | 'contributor';

// 文件相关类型
export interface ProjectFile {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  description?: string;
  tags: string[];
  project_id: number;
  uploaded_by: User;
  uploaded_at: string;
  updated_at: string;
  download_count: number;
  is_public: boolean;
  version: number;
  checksum: string;
  thumbnail_path?: string;
  preview_available: boolean;
}

export interface FileUploadResponse {
  file: ProjectFile;
  message: string;
}

export interface FilePreviewResponse {
  preview_url: string;
  preview_type: 'image' | 'pdf' | 'text' | 'video' | 'audio' | 'unsupported';
  content?: string; // 对于文本文件
  metadata?: Record<string, any>;
}

// 项目活动相关类型
export interface ProjectActivity {
  id: number;
  project_id: number;
  user: User;
  action_type: ActivityType;
  description: string;
  target_type?: string;
  target_id?: number;
  metadata?: Record<string, any>;
  created_at: string;
}

export type ActivityType =
  | 'project_created'
  | 'project_updated'
  | 'project_deleted'
  | 'member_added'
  | 'member_removed'
  | 'member_role_changed'
  | 'file_uploaded'
  | 'file_downloaded'
  | 'file_deleted'
  | 'comment_added'
  | 'comment_updated'
  | 'comment_deleted'
  | 'status_changed'
  | 'progress_updated'
  | 'tag_added'
  | 'tag_removed';

// 项目标签相关类型
export interface ProjectTag {
  id: number;
  name: string;
  color: string;
  description?: string;
  project_count: number;
  created_at: string;
}

// 审计日志相关类型
export interface AuditLog {
  id: number;
  user: User;
  action: string;
  resource_type: string;
  resource_id?: number;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

// 通知相关类型
export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: NotificationType;
  priority: NotificationPriority;
  is_read: boolean;
  action_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
  read_at?: string;
}

export type NotificationType =
  | 'info'
  | 'success'
  | 'warning'
  | 'error'
  | 'project_update'
  | 'file_upload'
  | 'member_added'
  | 'deadline_reminder';

export type NotificationPriority = 'low' | 'medium' | 'high';

// 系统设置相关类型
export interface SystemSettings {
  id: number;
  key: string;
  value: any;
  description?: string;
  category: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// API响应相关类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    total?: number;
    page?: number;
    per_page?: number;
    last_page?: number;
  };
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
  page?: number;
  per_page?: number;
}

export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SearchParams {
  search?: string;
  query?: string;
}

// 表单相关类型
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'textarea' | 'file';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ label: string; value: any }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface FormData {
  [key: string]: any;
}

// 图表相关类型
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display?: boolean;
      text?: string;
    };
  };
  scales?: {
    x?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
    y?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
  };
}

// 主题相关类型
export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  typography: {
    fontFamily: string;
    fontSize: {
      small: string;
      medium: string;
      large: string;
    };
  };
  spacing: {
    small: string;
    medium: string;
    large: string;
  };
  borderRadius: {
    small: string;
    medium: string;
    large: string;
  };
}

// 路由相关类型
export interface RouteConfig {
  path: string;
  component: React.ComponentType<any>;
  exact?: boolean;
  title?: string;
  requiresAuth?: boolean;
  requiredPermissions?: string[];
  requiredRoles?: string[];
  layout?: React.ComponentType<any>;
}

// 菜单相关类型
export interface MenuItem {
  key: string;
  label: string;
  icon?: string;
  path?: string;
  children?: MenuItem[];
  requiredPermissions?: string[];
  requiredRoles?: string[];
  disabled?: boolean;
}

// 上传相关类型
export interface UploadFile {
  uid: string;
  name: string;
  status: 'uploading' | 'done' | 'error' | 'removed';
  url?: string;
  thumbUrl?: string;
  size?: number;
  type?: string;
  percent?: number;
  originFileObj?: File;
  response?: any;
  error?: any;
}

// 表格相关类型
export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  fixed?: 'left' | 'right';
  align?: 'left' | 'center' | 'right';
  sorter?: boolean | ((a: T, b: T) => number);
  filters?: Array<{ text: string; value: any }>;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  ellipsis?: boolean;
  responsive?: string[];
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[];
  dataSource: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger?: boolean;
    showQuickJumper?: boolean;
    showTotal?: (total: number, range: [number, number]) => string;
  };
  rowSelection?: {
    selectedRowKeys: React.Key[];
    onChange: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
    type?: 'checkbox' | 'radio';
  };
  scroll?: {
    x?: number | string;
    y?: number | string;
  };
  size?: 'small' | 'middle' | 'large';
  bordered?: boolean;
  showHeader?: boolean;
  rowKey?: string | ((record: T) => string);
  expandable?: {
    expandedRowRender: (record: T) => React.ReactNode;
    rowExpandable?: (record: T) => boolean;
  };
}

// 错误相关类型
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  path?: string;
  method?: string;
  statusCode?: number;
}

// 应用状态相关类型
export interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  theme: Theme;
  language: string;
  notifications: Notification[];
  errors: AppError[];
  settings: Record<string, any>;
}

// WebSocket相关类型
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  id?: string;
}

export interface WebSocketEvent {
  event: string;
  data: any;
  room?: string;
}

// 导出/导入相关类型
export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  fields?: string[];
  filters?: Record<string, any>;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface ImportResult {
  success: boolean;
  imported_count: number;
  failed_count: number;
  errors: Array<{
    row: number;
    field: string;
    message: string;
  }>;
  warnings: Array<{
    row: number;
    field: string;
    message: string;
  }>;
}

// 缓存相关类型
export interface CacheConfig {
  key: string;
  ttl: number; // 生存时间（秒）
  version?: string;
}

export interface CacheItem<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
  version?: string;
}

// 搜索相关类型
export interface SearchResult<T = any> {
  items: T[];
  total: number;
  query: string;
  filters: Record<string, any>;
  facets?: Record<string, Array<{
    value: string;
    count: number;
  }>>;
  suggestions?: string[];
}

export interface SearchFilters {
  [key: string]: any;
}

// 统计相关类型
export interface Statistics {
  [key: string]: {
    value: number;
    change?: number;
    changeType?: 'increase' | 'decrease' | 'stable';
    trend?: number[];
  };
}

// 日期范围类型
export interface DateRange {
  start: string;
  end: string;
}

// 地理位置类型
export interface Location {
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  country?: string;
}

// 联系信息类型
export interface ContactInfo {
  email?: string;
  phone?: string;
  address?: string;
  website?: string;
  social?: {
    linkedin?: string;
    twitter?: string;
    github?: string;
  };
}

// 报告相关类型
export interface Report {
  id: string;
  title: string;
  description?: string;
  type: 'summary' | 'analysis' | 'trend' | 'detail';
  status: 'generating' | 'completed' | 'failed' | 'scheduled';
  project?: {
    id: string;
    name: string;
    color?: string;
  };
  creator?: {
    id: string;
    name?: string;
    username?: string;
    avatar?: string;
  };
  creatorId: string;
  createdAt: string;
  updatedAt?: string;
  fileUrl?: string;
  fileSize?: number;
  progress?: number;
  metadata?: Record<string, any>;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  type: 'summary' | 'analysis' | 'trend' | 'detail';
  usageCount: number;
  createdAt: string;
  updatedAt?: string;
  sections?: Array<{
    id: string;
    title: string;
    required: boolean;
  }>;
  variables?: Record<string, any>;
}

export interface ReportStats {
  totalReports: number;
  generatedToday: number;
  scheduledReports: number;
  sharedReports: number;
}