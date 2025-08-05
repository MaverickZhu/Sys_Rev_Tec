import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

// 导入组件
const Login = () => import('@/views/Login.vue')
const Layout = () => import('@/layout/index.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const UserManagement = () => import('@/views/UserManagement.vue')
const ReportManagement = () => import('@/views/ReportManagement.vue')
const SystemSettings = () => import('@/views/SystemSettings.vue')
const PermissionManagement = () => import('@/components/PermissionManagement.vue')
const SecurityDashboard = () => import('@/components/SecurityDashboard.vue')
const PermissionQueryOptimization = () => import('@/components/PermissionQueryOptimization.vue')
const SystemMaintenance = () => import('@/views/SystemMaintenance.vue')
const Profile = () => import('@/views/Profile.vue')

// 基础路由
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
          title: '仪表板',
          icon: 'Odometer',
          requiresAuth: true
        }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: {
          title: '用户管理',
          icon: 'User',
          requiresAuth: true,
          permissions: ['USER_READ', 'USER_MANAGE']
        }
      },
      {
        path: 'reports',
        name: 'ReportManagement',
        component: ReportManagement,
        meta: {
          title: '报表管理',
          icon: 'Document',
          requiresAuth: true,
          permissions: ['REPORT_READ', 'REPORT_MANAGE']
        }
      },
      {
        path: 'permissions',
        name: 'PermissionManagement',
        component: PermissionManagement,
        meta: {
          title: '权限管理',
          icon: 'Lock',
          requiresAuth: true,
          permissions: ['SYSTEM_CONFIGURE', 'USER_MANAGE']
        }
      },
      {
        path: 'permission-optimization',
        name: 'PermissionQueryOptimization',
        component: PermissionQueryOptimization,
        meta: {
          title: '权限查询优化',
          icon: 'TrendCharts',
          requiresAuth: true,
          permissions: ['admin:system:monitor', 'admin:system:manage']
        }
      },
      {
        path: 'security',
        name: 'SecurityDashboard',
        component: SecurityDashboard,
        meta: {
          title: '安全监控',
          icon: 'Warning',
          requiresAuth: true,
          permissions: ['SYSTEM_MONITOR', 'AUDIT_READ']
        }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: SystemSettings,
        meta: {
          title: '系统设置',
          icon: 'Setting',
          requiresAuth: true,
          permissions: ['SYSTEM_CONFIGURE']
        }
      },
      {
        path: 'system-maintenance',
        name: 'SystemMaintenance',
        component: SystemMaintenance,
        meta: {
          title: '系统维护',
          icon: 'Tools',
          requiresAuth: true,
          permissions: ['admin:system:maintenance:read', 'admin:system:maintenance:write']
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: {
          title: '个人资料',
          icon: 'UserFilled',
          requiresAuth: true,
          hideInMenu: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 系统审查技术平台`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      // 未登录，重定向到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 检查权限
    if (to.meta.permissions && to.meta.permissions.length > 0) {
      const hasPermission = await userStore.checkPermissions(to.meta.permissions)
      if (!hasPermission) {
        ElMessage.error('您没有访问此页面的权限')
        next({ path: '/dashboard' })
        return
      }
    }
  }
  
  // 已登录用户访问登录页，重定向到仪表板
  if (to.path === '/login' && userStore.isLoggedIn) {
    next({ path: '/dashboard' })
    return
  }
  
  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('页面加载失败，请重试')
})

export default router