import { AxiosResponse } from 'axios';
import { authService } from './authService';
import type {
  Project,
  ProjectFile,
  ProjectMember,
  ProjectActivity,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectListResponse,
  ProjectStats
} from '../types';

class ProjectService {
  private api = authService.getApiInstance();

  // 获取项目列表
  async getProjects(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    status?: string;
    project_type?: string;
    owner_id?: number;
    member_id?: number;
    start_date?: string;
    end_date?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<AxiosResponse<ProjectListResponse>> {
    return this.api.get('/projects', { params });
  }

  // 获取单个项目详情
  async getProject(projectId: number): Promise<AxiosResponse<Project>> {
    return this.api.get(`/projects/${projectId}`);
  }

  // 创建项目
  async createProject(projectData: CreateProjectRequest): Promise<AxiosResponse<Project>> {
    return this.api.post('/projects', projectData);
  }

  // 更新项目
  async updateProject(
    projectId: number,
    projectData: UpdateProjectRequest
  ): Promise<AxiosResponse<Project>> {
    return this.api.put(`/projects/${projectId}`, projectData);
  }

  // 删除项目
  async deleteProject(projectId: number): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}`);
  }

  // 获取项目统计数据
  async getProjectStats(projectId: number): Promise<AxiosResponse<ProjectStats>> {
    return this.api.get(`/projects/${projectId}/stats`);
  }

  // 获取仪表板统计数据
  async getDashboardStats(): Promise<AxiosResponse<{
    totalProjects: number;
    activeProjects: number;
    completedProjects: number;
    totalFiles: number;
    recentActivity: number;
  }>> {
    return this.api.get('/projects/dashboard/stats');
  }

  // 更新项目状态
  async updateProjectStatus(
    projectId: number,
    status: string
  ): Promise<AxiosResponse<Project>> {
    return this.api.patch(`/projects/${projectId}/status`, { status });
  }

  // 更新项目进度
  async updateProjectProgress(
    projectId: number,
    progress: number
  ): Promise<AxiosResponse<Project>> {
    return this.api.patch(`/projects/${projectId}/progress`, { progress });
  }

  // 获取项目文件列表
  async getProjectFiles(
    projectId: number,
    params?: {
      skip?: number;
      limit?: number;
      file_type?: string;
      search?: string;
    }
  ): Promise<AxiosResponse<ProjectFile[]>> {
    return this.api.get(`/projects/${projectId}/files`, { params });
  }

  // 获取项目成员列表
  async getProjectMembers(
    projectId: number,
    params?: {
      skip?: number;
      limit?: number;
      role?: string;
    }
  ): Promise<AxiosResponse<ProjectMember[]>> {
    return this.api.get(`/projects/${projectId}/members`, { params });
  }

  // 添加项目成员
  async addProjectMember(
    projectId: number,
    memberData: {
      user_id: number;
      role: string;
    }
  ): Promise<AxiosResponse<ProjectMember>> {
    return this.api.post(`/projects/${projectId}/members`, memberData);
  }

  // 更新项目成员角色
  async updateProjectMemberRole(
    projectId: number,
    userId: number,
    role: string
  ): Promise<AxiosResponse<ProjectMember>> {
    return this.api.put(`/projects/${projectId}/members/${userId}`, { role });
  }

  // 移除项目成员
  async removeProjectMember(
    projectId: number,
    userId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/members/${userId}`);
  }

  // 获取项目活动记录
  async getProjectActivities(
    projectId: number,
    params?: {
      skip?: number;
      limit?: number;
      action_type?: string;
      user_id?: number;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<AxiosResponse<ProjectActivity[]>> {
    return this.api.get(`/projects/${projectId}/activities`, { params });
  }

  // 添加项目活动记录
  async addProjectActivity(
    projectId: number,
    activityData: {
      action_type: string;
      description: string;
      metadata?: Record<string, any>;
    }
  ): Promise<AxiosResponse<ProjectActivity>> {
    return this.api.post(`/projects/${projectId}/activities`, activityData);
  }

  // 复制项目
  async duplicateProject(
    projectId: number,
    options?: {
      name?: string;
      copy_files?: boolean;
      copy_members?: boolean;
    }
  ): Promise<AxiosResponse<Project>> {
    return this.api.post(`/projects/${projectId}/duplicate`, options);
  }

  // 归档项目
  async archiveProject(projectId: number): Promise<AxiosResponse<Project>> {
    return this.api.patch(`/projects/${projectId}/archive`);
  }

  // 恢复项目
  async restoreProject(projectId: number): Promise<AxiosResponse<Project>> {
    return this.api.patch(`/projects/${projectId}/restore`);
  }

  // 获取项目模板
  async getProjectTemplates(): Promise<AxiosResponse<Array<{
    id: number;
    name: string;
    description: string;
    project_type: string;
    template_data: Record<string, any>;
  }>>> {
    return this.api.get('/projects/templates');
  }

  // 从模板创建项目
  async createProjectFromTemplate(
    templateId: number,
    projectData: {
      name: string;
      description?: string;
    }
  ): Promise<AxiosResponse<Project>> {
    return this.api.post(`/projects/templates/${templateId}/create`, projectData);
  }

  // 导出项目数据
  async exportProject(
    projectId: number,
    format: 'json' | 'csv' | 'xlsx'
  ): Promise<AxiosResponse<Blob>> {
    return this.api.get(`/projects/${projectId}/export`, {
      params: { format },
      responseType: 'blob'
    });
  }

  // 导入项目数据
  async importProject(file: File): Promise<AxiosResponse<Project>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.api.post('/projects/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // 获取项目权限
  async getProjectPermissions(
    projectId: number
  ): Promise<AxiosResponse<{
    can_view: boolean;
    can_edit: boolean;
    can_delete: boolean;
    can_manage_members: boolean;
    can_upload_files: boolean;
  }>> {
    return this.api.get(`/projects/${projectId}/permissions`);
  }

  // 检查项目权限
  async checkProjectPermission(
    projectId: number,
    permission: string
  ): Promise<AxiosResponse<{ has_permission: boolean }>> {
    return this.api.get(`/projects/${projectId}/permissions/${permission}`);
  }

  // 获取项目标签
  async getProjectTags(
    projectId: number
  ): Promise<AxiosResponse<Array<{
    id: number;
    name: string;
    color: string;
  }>>> {
    return this.api.get(`/projects/${projectId}/tags`);
  }

  // 添加项目标签
  async addProjectTag(
    projectId: number,
    tagData: {
      name: string;
      color?: string;
    }
  ): Promise<AxiosResponse<{
    id: number;
    name: string;
    color: string;
  }>> {
    return this.api.post(`/projects/${projectId}/tags`, tagData);
  }

  // 移除项目标签
  async removeProjectTag(
    projectId: number,
    tagId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/tags/${tagId}`);
  }

  // 获取项目评论
  async getProjectComments(
    projectId: number,
    params?: {
      skip?: number;
      limit?: number;
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    content: string;
    author: {
      id: number;
      username: string;
      full_name: string;
      avatar?: string;
    };
    created_at: string;
    updated_at: string;
  }>>> {
    return this.api.get(`/projects/${projectId}/comments`, { params });
  }

  // 添加项目评论
  async addProjectComment(
    projectId: number,
    content: string
  ): Promise<AxiosResponse<{
    id: number;
    content: string;
    author: {
      id: number;
      username: string;
      full_name: string;
      avatar?: string;
    };
    created_at: string;
  }>> {
    return this.api.post(`/projects/${projectId}/comments`, { content });
  }

  // 更新项目评论
  async updateProjectComment(
    projectId: number,
    commentId: number,
    content: string
  ): Promise<AxiosResponse<void>> {
    return this.api.put(`/projects/${projectId}/comments/${commentId}`, { content });
  }

  // 删除项目评论
  async deleteProjectComment(
    projectId: number,
    commentId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/comments/${commentId}`);
  }

  // 获取项目时间线
  async getProjectTimeline(
    projectId: number,
    params?: {
      start_date?: string;
      end_date?: string;
      event_types?: string[];
    }
  ): Promise<AxiosResponse<Array<{
    id: number;
    event_type: string;
    title: string;
    description: string;
    date: string;
    user: {
      id: number;
      username: string;
      full_name: string;
      avatar?: string;
    };
    metadata?: Record<string, any>;
  }>>> {
    return this.api.get(`/projects/${projectId}/timeline`, { params });
  }

  // 获取我的项目
  async getMyProjects(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    role?: string;
  }): Promise<AxiosResponse<ProjectListResponse>> {
    return this.api.get('/projects/my', { params });
  }

  // 获取最近访问的项目
  async getRecentProjects(
    limit: number = 10
  ): Promise<AxiosResponse<Project[]>> {
    return this.api.get('/projects/recent', { params: { limit } });
  }

  // 收藏项目
  async favoriteProject(projectId: number): Promise<AxiosResponse<void>> {
    return this.api.post(`/projects/${projectId}/favorite`);
  }

  // 取消收藏项目
  async unfavoriteProject(projectId: number): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/favorite`);
  }

  // 获取收藏的项目
  async getFavoriteProjects(): Promise<AxiosResponse<Project[]>> {
    return this.api.get('/projects/favorites');
  }

  // 搜索项目
  async searchProjects(query: string, params?: {
    project_type?: string;
    status?: string;
    limit?: number;
  }): Promise<AxiosResponse<Project[]>> {
    return this.api.get('/projects/search', {
      params: { q: query, ...params }
    });
  }
}

// 创建单例实例
export const projectService = new ProjectService();
export default projectService;