import { authService } from './authService';

export interface ReportData {
  id: string;
  title: string;
  type: 'project' | 'user' | 'system' | 'audit';
  description?: string;
  data: any;
  created_at: string;
  updated_at: string;
  created_by: string;
  status: 'draft' | 'published' | 'archived';
  tags?: string[];
  file_url?: string;
  file_size?: number;
  file_type?: string;
}

export interface ReportFilter {
  type?: string;
  status?: string;
  created_by?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  search?: string;
}

export interface ReportListResponse {
  reports: ReportData[];
  total: number;
  page: number;
  limit: number;
}

export interface ReportStatistics {
  total_reports: number;
  published_reports: number;
  draft_reports: number;
  archived_reports: number;
  reports_by_type: {
    project: number;
    user: number;
    system: number;
    audit: number;
  };
  recent_reports: ReportData[];
}

export interface CreateReportRequest {
  title: string;
  type: 'project' | 'user' | 'system' | 'audit';
  description?: string;
  data: any;
  tags?: string[];
  status?: 'draft' | 'published';
}

export interface UpdateReportRequest {
  title?: string;
  description?: string;
  data?: any;
  tags?: string[];
  status?: 'draft' | 'published' | 'archived';
}

export interface ExportReportRequest {
  report_ids: string[];
  format: 'pdf' | 'excel' | 'csv' | 'json';
  include_data?: boolean;
  include_charts?: boolean;
}

class ReportService {
  private getApi() {
    return authService.getApiInstance();
  }

  // 获取报告列表
  async getReports(params: {
    skip?: number;
    limit?: number;
    filter?: ReportFilter;
  } = {}) {
    const api = this.getApi();
    const response = await api.get('/reports', { params });
    return response.data as ReportListResponse;
  }

  // 获取报告详情
  async getReport(reportId: string) {
    const api = this.getApi();
    const response = await api.get(`/reports/${reportId}`);
    return response.data as ReportData;
  }

  // 创建报告
  async createReport(data: CreateReportRequest) {
    const api = this.getApi();
    const response = await api.post('/reports', data);
    return response.data as ReportData;
  }

  // 更新报告
  async updateReport(reportId: string, data: UpdateReportRequest) {
    const api = this.getApi();
    const response = await api.put(`/reports/${reportId}`, data);
    return response.data as ReportData;
  }

  // 删除报告
  async deleteReport(reportId: string) {
    const api = this.getApi();
    await api.delete(`/reports/${reportId}`);
  }

  // 批量删除报告
  async deleteReports(reportIds: string[]) {
    const api = this.getApi();
    await api.post('/reports/batch-delete', { report_ids: reportIds });
  }

  // 复制报告
  async duplicateReport(reportId: string, title?: string) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/duplicate`, {
      title: title || undefined
    });
    return response.data as ReportData;
  }

  // 发布报告
  async publishReport(reportId: string) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/publish`);
    return response.data as ReportData;
  }

  // 归档报告
  async archiveReport(reportId: string) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/archive`);
    return response.data as ReportData;
  }

  // 恢复报告
  async restoreReport(reportId: string) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/restore`);
    return response.data as ReportData;
  }

  // 获取报告统计信息
  async getReportStatistics() {
    const api = this.getApi();
    const response = await api.get('/reports/statistics');
    return response.data as ReportStatistics;
  }

  // 搜索报告
  async searchReports(query: string, filters?: ReportFilter) {
    const api = this.getApi();
    const response = await api.get('/reports/search', {
      params: { q: query, ...filters }
    });
    return response.data as ReportListResponse;
  }

  // 获取报告模板
  async getReportTemplates() {
    const api = this.getApi();
    const response = await api.get('/reports/templates');
    return response.data;
  }

  // 创建报告模板
  async createTemplate(data: {
    name: string;
    type: string;
    description?: string;
    config: any;
  }) {
    const api = this.getApi();
    const response = await api.post('/reports/templates', data);
    return response.data;
  }

  // 删除报告模板
  async deleteTemplate(templateId: string) {
    const api = this.getApi();
    await api.delete(`/reports/templates/${templateId}`);
  }

  // 生成报告
  async generateReport(params: any) {
    const api = this.getApi();
    const response = await api.post('/reports/generate', params);
    return response.data;
  }

  // 下载报告
  async downloadReport(reportId: string, format: string) {
    const api = this.getApi();
    const response = await api.get(`/reports/${reportId}/download`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  // 从模板创建报告
  async createReportFromTemplate(templateId: string, data: {
    title: string;
    description?: string;
    parameters?: any;
  }) {
    const api = this.getApi();
    const response = await api.post(`/reports/templates/${templateId}/create`, data);
    return response.data as ReportData;
  }

  // 导出报告
  async exportReports(data: ExportReportRequest) {
    const api = this.getApi();
    const response = await api.post('/reports/export', data, {
      responseType: 'blob'
    });
    return response.data;
  }

  // 导出单个报告
  async exportReport(reportId: string, format: 'pdf' | 'excel' | 'csv' | 'json') {
    const api = this.getApi();
    const response = await api.get(`/reports/${reportId}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }

  // 生成报告预览
  async generateReportPreview(data: CreateReportRequest) {
    const api = this.getApi();
    const response = await api.post('/reports/preview', data);
    return response.data;
  }

  // 获取报告标签
  async getReportTags() {
    const api = this.getApi();
    const response = await api.get('/reports/tags');
    return response.data as string[];
  }

  // 获取我的报告
  async getMyReports(params: {
    skip?: number;
    limit?: number;
    status?: string;
  } = {}) {
    const api = this.getApi();
    const response = await api.get('/reports/my', { params });
    return response.data as ReportListResponse;
  }

  // 获取最近的报告
  async getRecentReports(limit: number = 10) {
    const api = this.getApi();
    const response = await api.get('/reports/recent', {
      params: { limit }
    });
    return response.data as ReportData[];
  }

  // 获取热门报告
  async getPopularReports(limit: number = 10) {
    const api = this.getApi();
    const response = await api.get('/reports/popular', {
      params: { limit }
    });
    return response.data as ReportData[];
  }

  // 分享报告
  async shareReport(reportId: string, data: {
    share_type: 'public' | 'private';
    expires_at?: string;
    password?: string;
    allowed_users?: string[];
  }) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/share`, data);
    return response.data;
  }

  // 取消分享报告
  async unshareReport(reportId: string) {
    const api = this.getApi();
    await api.delete(`/reports/${reportId}/share`);
  }

  // 获取分享的报告
  async getSharedReport(shareToken: string, password?: string) {
    const api = this.getApi();
    const response = await api.get(`/reports/shared/${shareToken}`, {
      params: password ? { password } : undefined
    });
    return response.data as ReportData;
  }

  // 添加报告评论
  async addReportComment(reportId: string, content: string) {
    const api = this.getApi();
    const response = await api.post(`/reports/${reportId}/comments`, {
      content
    });
    return response.data;
  }

  // 获取报告评论
  async getReportComments(reportId: string) {
    const api = this.getApi();
    const response = await api.get(`/reports/${reportId}/comments`);
    return response.data;
  }

  // 删除报告评论
  async deleteReportComment(reportId: string, commentId: string) {
    const api = this.getApi();
    await api.delete(`/reports/${reportId}/comments/${commentId}`);
  }

  // 生成项目报告
  async generateProjectReport(projectId: string, options: {
    include_files?: boolean;
    include_activities?: boolean;
    include_members?: boolean;
    date_range?: {
      start_date: string;
      end_date: string;
    };
  } = {}) {
    const api = this.getApi();
    const response = await api.post(`/reports/generate/project/${projectId}`, options);
    return response.data as ReportData;
  }

  // 生成用户活动报告
  async generateUserActivityReport(userId?: string, options: {
    date_range?: {
      start_date: string;
      end_date: string;
    };
    include_projects?: boolean;
    include_files?: boolean;
  } = {}) {
    const api = this.getApi();
    const response = await api.post('/reports/generate/user-activity', {
      user_id: userId,
      ...options
    });
    return response.data as ReportData;
  }

  // 生成系统使用报告
  async generateSystemUsageReport(options: {
    date_range?: {
      start_date: string;
      end_date: string;
    };
    include_storage?: boolean;
    include_performance?: boolean;
  } = {}) {
    const api = this.getApi();
    const response = await api.post('/reports/generate/system-usage', options);
    return response.data as ReportData;
  }

  // 生成审计报告
  async generateAuditReport(options: {
    date_range?: {
      start_date: string;
      end_date: string;
    };
    audit_type?: string;
    user_id?: string;
    project_id?: string;
  } = {}) {
    const api = this.getApi();
    const response = await api.post('/reports/generate/audit', options);
    return response.data as ReportData;
  }

  // 计划报告生成
  async scheduleReport(data: {
    report_type: 'project' | 'user' | 'system' | 'audit';
    title: string;
    schedule: {
      frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
      time: string; // HH:MM format
      day_of_week?: number; // 0-6, for weekly
      day_of_month?: number; // 1-31, for monthly
    };
    recipients: string[]; // email addresses
    parameters: any;
  }) {
    const api = this.getApi();
    const response = await api.post('/reports/schedule', data);
    return response.data;
  }

  // 获取计划报告列表
  async getScheduledReports() {
    const api = this.getApi();
    const response = await api.get('/reports/scheduled');
    return response.data;
  }

  // 删除计划报告
  async deleteScheduledReport(scheduleId: string) {
    const api = this.getApi();
    await api.delete(`/reports/scheduled/${scheduleId}`);
  }

  // 启用/禁用计划报告
  async toggleScheduledReport(scheduleId: string, enabled: boolean) {
    const api = this.getApi();
    const response = await api.patch(`/reports/scheduled/${scheduleId}`, {
      enabled
    });
    return response.data;
  }
}

export const reportService = new ReportService();