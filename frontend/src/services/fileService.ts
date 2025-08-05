import { AxiosResponse } from 'axios';
import { authService } from './authService';
import type {
  ProjectFile,
  FileUploadResponse,
  FilePreviewResponse
} from '../types';

class FileService {
  private api = authService.getApiInstance();

  // 上传文件
  async uploadFile(
    projectId: number,
    file: File,
    options?: {
      description?: string;
      tags?: string[];
      onUploadProgress?: (progressEvent: any) => void;
    }
  ): Promise<AxiosResponse<FileUploadResponse>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.description) {
      formData.append('description', options.description);
    }
    
    if (options?.tags) {
      formData.append('tags', JSON.stringify(options.tags));
    }

    return this.api.post(`/projects/${projectId}/files/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options?.onUploadProgress,
    });
  }

  // 批量上传文件
  async uploadMultipleFiles(
    projectId: number,
    files: File[],
    options?: {
      onUploadProgress?: (progressEvent: any) => void;
    }
  ): Promise<AxiosResponse<FileUploadResponse[]>> {
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append(`files`, file);
    });

    return this.api.post(`/projects/${projectId}/files/upload/batch`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options?.onUploadProgress,
    });
  }

  // 获取文件列表
  async getFiles(
    projectId: number,
    params?: {
      skip?: number;
      limit?: number;
      file_type?: string;
      search?: string;
      sort_by?: string;
      sort_order?: 'asc' | 'desc';
      tags?: string[];
    }
  ): Promise<AxiosResponse<{
    files: ProjectFile[];
    total: number;
    skip: number;
    limit: number;
  }>> {
    return this.api.get(`/projects/${projectId}/files`, { params });
  }

  // 获取单个文件信息
  async getFile(
    projectId: number,
    fileId: number
  ): Promise<AxiosResponse<ProjectFile>> {
    return this.api.get(`/projects/${projectId}/files/${fileId}`);
  }

  // 下载文件
  async downloadFile(
    projectId: number,
    fileId: number,
    filename?: string
  ): Promise<AxiosResponse<Blob>> {
    const response = await this.api.get(
      `/projects/${projectId}/files/${fileId}/download`,
      {
        responseType: 'blob',
      }
    );

    // 如果提供了文件名，创建下载链接
    if (filename) {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    }

    return response;
  }

  // 批量下载文件
  async downloadMultipleFiles(
    projectId: number,
    fileIds: number[]
  ): Promise<AxiosResponse<Blob>> {
    return this.api.post(
      `/projects/${projectId}/files/download/batch`,
      { file_ids: fileIds },
      {
        responseType: 'blob',
      }
    );
  }

  // 预览文件
  async previewFile(
    projectId: number,
    fileId: number
  ): Promise<AxiosResponse<FilePreviewResponse>> {
    return this.api.get(`/projects/${projectId}/files/${fileId}/preview`);
  }

  // 获取文件预览URL
  async getFilePreviewUrl(
    projectId: number,
    fileId: number
  ): Promise<string> {
    const token = authService.getToken();
    return `${this.api.defaults.baseURL}/projects/${projectId}/files/${fileId}/preview?token=${token}`;
  }

  // 获取文件缩略图
  async getFileThumbnail(
    projectId: number,
    fileId: number,
    size: 'small' | 'medium' | 'large' = 'medium'
  ): Promise<AxiosResponse<Blob>> {
    return this.api.get(
      `/projects/${projectId}/files/${fileId}/thumbnail`,
      {
        params: { size },
        responseType: 'blob',
      }
    );
  }

  // 获取文件缩略图URL
  async getFileThumbnailUrl(
    projectId: number,
    fileId: number,
    size: 'small' | 'medium' | 'large' = 'medium'
  ): Promise<string> {
    const token = authService.getToken();
    return `${this.api.defaults.baseURL}/projects/${projectId}/files/${fileId}/thumbnail?size=${size}&token=${token}`;
  }

  // 更新文件信息
  async updateFile(
    projectId: number,
    fileId: number,
    data: {
      filename?: string;
      description?: string;
      tags?: string[];
    }
  ): Promise<AxiosResponse<ProjectFile>> {
    return this.api.put(`/projects/${projectId}/files/${fileId}`, data);
  }

  // 删除文件
  async deleteFile(
    projectId: number,
    fileId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/files/${fileId}`);
  }

  // 批量删除文件
  async deleteMultipleFiles(
    projectId: number,
    fileIds: number[]
  ): Promise<AxiosResponse<void>> {
    return this.api.post(`/projects/${projectId}/files/delete/batch`, {
      file_ids: fileIds,
    });
  }

  // 移动文件到其他项目
  async moveFile(
    projectId: number,
    fileId: number,
    targetProjectId: number
  ): Promise<AxiosResponse<ProjectFile>> {
    return this.api.post(`/projects/${projectId}/files/${fileId}/move`, {
      target_project_id: targetProjectId,
    });
  }

  // 复制文件到其他项目
  async copyFile(
    projectId: number,
    fileId: number,
    targetProjectId: number
  ): Promise<AxiosResponse<ProjectFile>> {
    return this.api.post(`/projects/${projectId}/files/${fileId}/copy`, {
      target_project_id: targetProjectId,
    });
  }

  // 获取文件版本历史
  async getFileVersions(
    projectId: number,
    fileId: number
  ): Promise<AxiosResponse<Array<{
    id: number;
    version: number;
    filename: string;
    file_size: number;
    uploaded_by: {
      id: number;
      username: string;
      full_name: string;
    };
    uploaded_at: string;
    changes_description?: string;
  }>>> {
    return this.api.get(`/projects/${projectId}/files/${fileId}/versions`);
  }

  // 上传文件新版本
  async uploadFileVersion(
    projectId: number,
    fileId: number,
    file: File,
    changesDescription?: string
  ): Promise<AxiosResponse<ProjectFile>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (changesDescription) {
      formData.append('changes_description', changesDescription);
    }

    return this.api.post(
      `/projects/${projectId}/files/${fileId}/versions`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  }

  // 恢复文件版本
  async restoreFileVersion(
    projectId: number,
    fileId: number,
    versionId: number
  ): Promise<AxiosResponse<ProjectFile>> {
    return this.api.post(
      `/projects/${projectId}/files/${fileId}/versions/${versionId}/restore`
    );
  }

  // 获取文件共享链接
  async getFileShareLink(
    projectId: number,
    fileId: number,
    options?: {
      expires_in?: number; // 过期时间（秒）
      password?: string;
      download_limit?: number;
    }
  ): Promise<AxiosResponse<{
    share_url: string;
    expires_at?: string;
    download_count: number;
    download_limit?: number;
  }>> {
    return this.api.post(`/projects/${projectId}/files/${fileId}/share`, options);
  }

  // 取消文件共享
  async revokeFileShare(
    projectId: number,
    fileId: number
  ): Promise<AxiosResponse<void>> {
    return this.api.delete(`/projects/${projectId}/files/${fileId}/share`);
  }

  // 获取文件标签
  async getFileTags(
    projectId: number
  ): Promise<AxiosResponse<Array<{
    name: string;
    count: number;
    color?: string;
  }>>> {
    return this.api.get(`/projects/${projectId}/files/tags`);
  }

  // 搜索文件
  async searchFiles(
    projectId: number,
    query: string,
    params?: {
      file_type?: string;
      tags?: string[];
      date_from?: string;
      date_to?: string;
      size_min?: number;
      size_max?: number;
      limit?: number;
    }
  ): Promise<AxiosResponse<ProjectFile[]>> {
    return this.api.get(`/projects/${projectId}/files/search`, {
      params: { q: query, ...params },
    });
  }

  // 获取文件统计信息
  async getFileStats(
    projectId: number
  ): Promise<AxiosResponse<{
    total_files: number;
    total_size: number;
    file_types: Array<{
      type: string;
      count: number;
      size: number;
    }>;
    recent_uploads: number;
    storage_usage: {
      used: number;
      limit: number;
      percentage: number;
    };
  }>> {
    return this.api.get(`/projects/${projectId}/files/stats`);
  }

  // 检查文件权限
  async checkFilePermission(
    projectId: number,
    fileId: number,
    permission: 'view' | 'download' | 'edit' | 'delete'
  ): Promise<AxiosResponse<{ has_permission: boolean }>> {
    return this.api.get(
      `/projects/${projectId}/files/${fileId}/permissions/${permission}`
    );
  }

  // 获取支持的文件类型
  async getSupportedFileTypes(): Promise<AxiosResponse<{
    image_types: string[];
    document_types: string[];
    video_types: string[];
    audio_types: string[];
    archive_types: string[];
    max_file_size: number;
  }>> {
    return this.api.get('/files/supported-types');
  }

  // 验证文件
  async validateFile(file: File): Promise<{
    valid: boolean;
    errors: string[];
  }> {
    const errors: string[] = [];
    
    try {
      const supportedTypes = await this.getSupportedFileTypes();
      const { data } = supportedTypes;
      
      // 检查文件大小
      if (file.size > data.max_file_size) {
        errors.push(`文件大小超过限制 (${(data.max_file_size / 1024 / 1024).toFixed(1)}MB)`);
      }
      
      // 检查文件类型
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      const allSupportedTypes = [
        ...data.image_types,
        ...data.document_types,
        ...data.video_types,
        ...data.audio_types,
        ...data.archive_types,
      ];
      
      if (fileExtension && !allSupportedTypes.includes(fileExtension)) {
        errors.push(`不支持的文件类型: .${fileExtension}`);
      }
      
    } catch (error) {
      errors.push('无法验证文件类型');
    }
    
    return {
      valid: errors.length === 0,
      errors,
    };
  }

  // 格式化文件大小
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // 获取文件图标
  getFileIcon(filename: string): string {
    const extension = filename.split('.').pop()?.toLowerCase();
    
    const iconMap: Record<string, string> = {
      // 图片
      jpg: 'file-image',
      jpeg: 'file-image',
      png: 'file-image',
      gif: 'file-image',
      bmp: 'file-image',
      svg: 'file-image',
      webp: 'file-image',
      
      // 文档
      pdf: 'file-pdf',
      doc: 'file-word',
      docx: 'file-word',
      xls: 'file-excel',
      xlsx: 'file-excel',
      ppt: 'file-ppt',
      pptx: 'file-ppt',
      txt: 'file-text',
      
      // 代码
      js: 'file-text',
      ts: 'file-text',
      html: 'file-text',
      css: 'file-text',
      json: 'file-text',
      xml: 'file-text',
      py: 'file-text',
      java: 'file-text',
      cpp: 'file-text',
      c: 'file-text',
      
      // 视频
      mp4: 'video-camera',
      avi: 'video-camera',
      mov: 'video-camera',
      wmv: 'video-camera',
      flv: 'video-camera',
      
      // 音频
      mp3: 'sound',
      wav: 'sound',
      flac: 'sound',
      aac: 'sound',
      
      // 压缩包
      zip: 'file-zip',
      rar: 'file-zip',
      '7z': 'file-zip',
      tar: 'file-zip',
      gz: 'file-zip',
    };
    
    return iconMap[extension || ''] || 'file';
  }

  // 判断文件是否可预览
  isPreviewable(filename: string): boolean {
    const extension = filename.split('.').pop()?.toLowerCase();
    const previewableTypes = [
      'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
      'pdf', 'txt', 'json', 'xml', 'html', 'css', 'js', 'ts',
      'md', 'csv'
    ];
    
    return previewableTypes.includes(extension || '');
  }
}

// 创建单例实例
export const fileService = new FileService();
export default fileService;