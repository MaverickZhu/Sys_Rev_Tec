/**
 * 系统评审技术平台 - 前端应用主文件
 * 提供与后端AI服务的交互功能
 */

// 应用配置
const CONFIG = {
    API_BASE: 'http://localhost:8001',
    REFRESH_INTERVAL: 30000, // 30秒
    NOTIFICATION_TIMEOUT: 5000, // 5秒
    MAX_RETRIES: 3,
    AUTH_TOKEN_KEY: 'authToken',
    USER_INFO_KEY: 'userInfo',
    TOKEN_TYPE_KEY: 'tokenType'
};

// 应用状态
const AppState = {
    isLoading: false,
    serviceStatus: 'unknown',
    isAuthenticated: false,
    currentUser: null,
    userRole: null,
    stats: {
        totalReports: 0,
        totalProjects: 0,
        totalTemplates: 4,
        systemUptime: '99.9%'
    },
    reports: [],
    templates: []
};

// 工具函数
const Utils = {
    // 显示通知
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 1.2rem; cursor: pointer; margin-left: auto;">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 显示动画
        setTimeout(() => notification.classList.add('show'), 100);
        
        // 自动隐藏
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, CONFIG.NOTIFICATION_TIMEOUT);
    },

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 重试机制
    async retry(fn, retries = CONFIG.MAX_RETRIES) {
        try {
            return await fn();
        } catch (error) {
            if (retries > 0) {
                console.log(`重试中... 剩余次数: ${retries}`);
                await new Promise(resolve => setTimeout(resolve, 1000));
                return this.retry(fn, retries - 1);
            }
            throw error;
        }
    }
};

// 认证服务
const AuthService = {
    // 获取认证头部
    getAuthHeaders() {
        const token = localStorage.getItem(CONFIG.AUTH_TOKEN_KEY);
        const tokenType = localStorage.getItem(CONFIG.TOKEN_TYPE_KEY) || 'Bearer';
        
        if (token) {
            return {
                'Authorization': `${tokenType} ${token}`
            };
        }
        return {};
    },

    // 检查是否已认证
    isAuthenticated() {
        const token = localStorage.getItem(CONFIG.AUTH_TOKEN_KEY);
        return !!token;
    },

    // 获取当前用户信息
    getCurrentUser() {
        const userInfo = localStorage.getItem(CONFIG.USER_INFO_KEY);
        try {
            return userInfo ? JSON.parse(userInfo) : null;
        } catch {
            return null;
        }
    },

    // 登出
    logout() {
        localStorage.removeItem(CONFIG.AUTH_TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_INFO_KEY);
        localStorage.removeItem(CONFIG.TOKEN_TYPE_KEY);
        AppState.isAuthenticated = false;
        AppState.currentUser = null;
        AppState.userRole = null;
        
        // 重定向到登录页
        window.location.href = 'login.html';
    },

    // 验证token
    async verifyToken() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/api/v1/auth/verify`, {
                method: 'GET',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                AppState.isAuthenticated = true;
                AppState.currentUser = userData.user || this.getCurrentUser();
                AppState.userRole = userData.user?.role || 'user';
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Token验证失败:', error);
            return false;
        }
    },

    // 检查权限
    hasPermission(requiredRole) {
        if (!AppState.isAuthenticated) return false;
        
        const roleHierarchy = {
            'admin': 3,
            'auditor': 2,
            'user': 1
        };
        
        const userLevel = roleHierarchy[AppState.userRole] || 0;
        const requiredLevel = roleHierarchy[requiredRole] || 0;
        
        return userLevel >= requiredLevel;
    }
};

// API服务
const ApiService = {
    // 基础请求方法
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...AuthService.getAuthHeaders(),
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // 处理认证失败
            if (response.status === 401) {
                AuthService.logout();
                return;
            }
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API请求失败 [${endpoint}]:`, error);
            throw error;
        }
    },

    // 健康检查
    async checkHealth() {
        return this.request('/health');
    },

    // 获取报告列表
    async getReports(limit = 100, offset = 0) {
        return this.request(`/api/reports/list?limit=${limit}&offset=${offset}`);
    },

    // 生成报告
    async generateReport(data) {
        return this.request('/api/reports/generate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // 获取报告详情
    async getReport(reportId) {
        return this.request(`/api/reports/${reportId}`);
    },

    // 下载报告
    async downloadReport(reportId, format = 'pdf') {
        const url = `${CONFIG.API_BASE}/api/reports/${reportId}/download?format=${format}`;
        window.open(url, '_blank');
    },

    // 删除报告
    async deleteReport(reportId) {
        return this.request(`/api/reports/${reportId}`, {
            method: 'DELETE'
        });
    },

    // 获取模板列表
    async getTemplates() {
        return this.request('/api/reports/templates');
    },

    // 获取系统统计
    async getSystemStats() {
        try {
            const [reportsData, templatesData] = await Promise.all([
                this.getReports(1000),
                this.getTemplates()
            ]);
            
            return {
                totalReports: reportsData.total || 0,
                totalProjects: new Set(reportsData.reports?.map(r => r.project_id) || []).size,
                totalTemplates: templatesData.length || 4,
                systemUptime: '99.9%'
            };
        } catch (error) {
            console.error('获取系统统计失败:', error);
            return AppState.stats;
        }
    }
};

// UI控制器
const UIController = {
    // 更新服务状态
    updateServiceStatus(status, message) {
        const statusElement = document.querySelector('.status-indicator span');
        const dotElement = document.querySelector('.status-dot');
        
        if (statusElement && dotElement) {
            statusElement.textContent = message;
            
            switch (status) {
                case 'healthy':
                    dotElement.style.background = '#48bb78';
                    break;
                case 'unhealthy':
                    dotElement.style.background = '#f56565';
                    break;
                default:
                    dotElement.style.background = '#ed8936';
            }
        }
    },

    // 更新用户界面
    updateUserInterface() {
        if (AppState.isAuthenticated && AppState.currentUser) {
            this.showUserInfo();
            this.updatePermissionBasedUI();
        } else {
            this.hideUserInfo();
        }
    },

    // 显示用户信息
    showUserInfo() {
        const user = AppState.currentUser;
        const userInfoHtml = `
            <div class="user-info">
                <div class="user-avatar">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="user-details">
                    <div class="user-name">${user.username || '用户'}</div>
                    <div class="user-role">${this.getRoleDisplayName(AppState.userRole)}</div>
                </div>
                <div class="user-actions">
                    <button class="btn-icon" onclick="showUserMenu()" title="用户菜单">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn-icon" onclick="AuthService.logout()" title="退出登录">
                        <i class="fas fa-sign-out-alt"></i>
                    </button>
                </div>
            </div>
        `;
        
        // 在页面头部添加用户信息
        const header = document.querySelector('.header');
        if (header) {
            let userInfoContainer = header.querySelector('.user-info-container');
            if (!userInfoContainer) {
                userInfoContainer = document.createElement('div');
                userInfoContainer.className = 'user-info-container';
                header.appendChild(userInfoContainer);
            }
            userInfoContainer.innerHTML = userInfoHtml;
        }
    },

    // 隐藏用户信息
    hideUserInfo() {
        const userInfoContainer = document.querySelector('.user-info-container');
        if (userInfoContainer) {
            userInfoContainer.remove();
        }
    },

    // 获取角色显示名称
    getRoleDisplayName(role) {
        const roleNames = {
            'admin': '系统管理员',
            'auditor': '审计员',
            'user': '普通用户'
        };
        return roleNames[role] || '未知角色';
    },

    // 基于权限更新UI
    updatePermissionBasedUI() {
        // 管理员功能
        const adminElements = document.querySelectorAll('[data-role="admin"]');
        adminElements.forEach(el => {
            el.style.display = AuthService.hasPermission('admin') ? 'block' : 'none';
        });
        
        // 审计员功能
        const auditorElements = document.querySelectorAll('[data-role="auditor"]');
        auditorElements.forEach(el => {
            el.style.display = AuthService.hasPermission('auditor') ? 'block' : 'none';
        });
        
        // 用户功能
        const userElements = document.querySelectorAll('[data-role="user"]');
        userElements.forEach(el => {
            el.style.display = AuthService.hasPermission('user') ? 'block' : 'none';
        });
    },

    // 更新统计数据
    updateStats(stats) {
        Object.keys(stats).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = stats[key];
            }
        });
        AppState.stats = { ...AppState.stats, ...stats };
    },

    // 显示加载状态
    showLoading(element, show = true) {
        if (!element) return;
        
        if (show) {
            element.disabled = true;
            const originalText = element.textContent;
            element.dataset.originalText = originalText;
            element.innerHTML = '<span class="loading"></span> 处理中...';
        } else {
            element.disabled = false;
            element.textContent = element.dataset.originalText || element.textContent;
        }
    },

    // 打开模态框
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    },

    // 关闭模态框
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    },

    // 重置表单
    resetForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }
    }
};

// 报告管理器
const ReportManager = {
    // 生成报告
    async generateReport() {
        const form = document.getElementById('reportForm');
        const submitBtn = form.querySelector('button[type="button"]');
        
        // 获取表单数据
        const formData = {
            template_type: document.getElementById('reportType').value,
            project_id: parseInt(document.getElementById('projectId').value),
            output_format: document.getElementById('outputFormat').value,
            data: {
                project_name: document.getElementById('projectName')?.value || `项目 ${document.getElementById('projectId').value}`,
                author: document.getElementById('author')?.value || '系统管理员',
                generated_at: new Date().toISOString(),
                description: document.getElementById('description')?.value || '自动生成的报告'
            }
        };

        // 验证表单
        if (!formData.project_id || isNaN(formData.project_id)) {
            Utils.showNotification('请输入有效的项目ID', 'error');
            return;
        }

        try {
            UIController.showLoading(submitBtn, true);
            
            const result = await Utils.retry(() => ApiService.generateReport(formData));
            
            Utils.showNotification(`报告生成成功！报告ID: ${result.report_id}`, 'success');
            UIController.closeModal('reportModal');
            UIController.resetForm('reportForm');
            
            // 刷新统计数据
            await this.refreshStats();
            
            // 询问是否下载报告
            if (confirm('报告已生成，是否立即下载？')) {
                await ApiService.downloadReport(result.report_id, formData.output_format);
            }
            
        } catch (error) {
            Utils.showNotification(`报告生成失败: ${error.message}`, 'error');
        } finally {
            UIController.showLoading(submitBtn, false);
        }
    },

    // 快速生成报告
    async quickGenerate(templateType) {
        const projectId = prompt('请输入项目ID:');
        if (!projectId || isNaN(parseInt(projectId))) {
            Utils.showNotification('请输入有效的项目ID', 'error');
            return;
        }

        const formData = {
            template_type: templateType,
            project_id: parseInt(projectId),
            output_format: 'html',
            data: {
                project_name: `项目 ${projectId}`,
                author: '系统管理员',
                generated_at: new Date().toISOString(),
                description: `快速生成的${this.getTemplateDisplayName(templateType)}`
            }
        };

        try {
            const result = await Utils.retry(() => ApiService.generateReport(formData));
            Utils.showNotification(`${this.getTemplateDisplayName(templateType)}生成成功！`, 'success');
            await this.refreshStats();
        } catch (error) {
            Utils.showNotification(`生成失败: ${error.message}`, 'error');
        }
    },

    // 获取模板显示名称
    getTemplateDisplayName(templateType) {
        const names = {
            'risk_assessment': '风险评估报告',
            'compliance_check': '合规性检查报告',
            'comprehensive': '综合分析报告',
            'executive_summary': '执行摘要报告'
        };
        return names[templateType] || templateType;
    },

    // 刷新统计数据
    async refreshStats() {
        try {
            const stats = await ApiService.getSystemStats();
            UIController.updateStats(stats);
        } catch (error) {
            console.error('刷新统计数据失败:', error);
        }
    }
};

// 系统监控器
const SystemMonitor = {
    // 检查服务状态
    async checkServiceStatus() {
        try {
            const health = await ApiService.checkHealth();
            
            if (health.status === 'healthy') {
                UIController.updateServiceStatus('healthy', 'AI服务运行中');
                AppState.serviceStatus = 'healthy';
            } else {
                UIController.updateServiceStatus('unhealthy', 'AI服务异常');
                AppState.serviceStatus = 'unhealthy';
            }
        } catch (error) {
            UIController.updateServiceStatus('offline', 'AI服务离线');
            AppState.serviceStatus = 'offline';
            console.error('服务状态检查失败:', error);
        }
    },

    // 开始监控
    startMonitoring() {
        // 立即检查一次
        this.checkServiceStatus();
        
        // 定期检查
        setInterval(() => {
            this.checkServiceStatus();
        }, CONFIG.REFRESH_INTERVAL);
    }
};

// 应用初始化
const App = {
    // 初始化应用
    async init() {
        console.log('系统评审技术平台启动中...');
        
        try {
            // 检查认证状态
            if (!AuthService.isAuthenticated()) {
                // 未认证，重定向到登录页面
                window.location.href = 'login.html';
                return;
            }
            
            // 验证token有效性
            const isValid = await AuthService.verifyToken();
            if (!isValid) {
                AuthService.logout();
                return;
            }
            
            // 更新用户界面
            UIController.updateUserInterface();
            
            // 绑定事件监听器
            this.bindEventListeners();
            
            // 启动系统监控
            SystemMonitor.startMonitoring();
            
            // 加载初始数据
            await this.loadInitialData();
            
            console.log('应用初始化完成');
            Utils.showNotification('系统已就绪', 'success');
            
        } catch (error) {
            console.error('应用初始化失败:', error);
            Utils.showNotification('系统初始化失败', 'error');
        }
    },

    // 绑定事件监听器
    bindEventListeners() {
        // 模态框外部点击关闭
        window.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                UIController.closeModal(event.target.id);
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const openModal = document.querySelector('.modal[style*="block"]');
                if (openModal) {
                    UIController.closeModal(openModal.id);
                }
            }
        });

        // 表单提交防止页面刷新
        document.addEventListener('submit', (event) => {
            event.preventDefault();
        });
    },

    // 加载初始数据
    async loadInitialData() {
        try {
            // 加载统计数据
            const stats = await ApiService.getSystemStats();
            UIController.updateStats(stats);
            
            // 加载模板数据
            const templates = await ApiService.getTemplates();
            AppState.templates = templates;
            
        } catch (error) {
            console.error('加载初始数据失败:', error);
        }
    }
};

// 全局函数（供HTML调用）
window.openReportGenerator = () => UIController.openModal('reportModal');
window.closeModal = (modalId) => UIController.closeModal(modalId);
window.generateReport = () => ReportManager.generateReport();
window.quickAction = (type) => ReportManager.quickGenerate(type);

window.openAnalytics = () => {
    Utils.showNotification('数据分析功能开发中...', 'info');
};

window.openTemplates = () => {
    window.open(`${CONFIG.API_BASE}/api/reports/templates`, '_blank');
};

window.openSettings = () => {
    Utils.showNotification('系统设置功能开发中...', 'info');
};

// 全局函数
function showUserMenu() {
    // 显示用户菜单
    const menu = document.createElement('div');
    menu.className = 'user-menu';
    menu.innerHTML = `
        <div class="menu-item" onclick="showUserProfile()">
            <i class="fas fa-user"></i> 个人资料
        </div>
        <div class="menu-item" onclick="showSettings()">
            <i class="fas fa-cog"></i> 设置
        </div>
        <div class="menu-item" onclick="AuthService.logout()">
            <i class="fas fa-sign-out-alt"></i> 退出登录
        </div>
    `;
    
    // 添加到页面并显示
    document.body.appendChild(menu);
    
    // 点击外部关闭菜单
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 100);
}

function showUserProfile() {
    // 显示用户资料页面
    Utils.showNotification('用户资料功能开发中...', 'info');
}

function showSettings() {
    // 显示设置页面
    Utils.showNotification('设置功能开发中...', 'info');
}

// 权限检查函数
function requirePermission(permission, callback) {
    if (AuthService.hasPermission(permission)) {
        callback();
    } else {
        Utils.showNotification('您没有执行此操作的权限', 'error');
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// 导出模块（如果需要）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        App,
        ApiService,
        UIController,
        ReportManager,
        SystemMonitor,
        Utils,
        CONFIG
    };
}