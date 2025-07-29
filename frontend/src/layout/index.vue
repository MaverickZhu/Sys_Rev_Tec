<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <h1>系统审查技术平台</h1>
        </div>
      </div>
      <div class="header-right">
        <div class="user-info">
          <el-dropdown @command="handleUserCommand">
            <span class="user-name">
              {{ userStore.user?.username || '用户' }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="main-container">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Dashboard /></el-icon>
            <template #title>仪表板</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/users" 
            v-if="hasPermission(['USER_READ', 'USER_MANAGE'])"
          >
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/reports" 
            v-if="hasPermission(['REPORT_READ', 'REPORT_MANAGE'])"
          >
            <el-icon><Document /></el-icon>
            <template #title>报表管理</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/permissions" 
            v-if="hasPermission(['SYSTEM_CONFIGURE', 'USER_MANAGE'])"
          >
            <el-icon><Lock /></el-icon>
            <template #title>权限管理</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/permission-optimization" 
            v-if="hasPermission(['admin:system:monitor', 'admin:system:manage'])"
          >
            <el-icon><TrendCharts /></el-icon>
            <template #title>权限查询优化</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/system-maintenance" 
            v-if="hasPermission(['admin:system:maintenance:read', 'admin:system:maintenance:write'])"
          >
            <el-icon><Tools /></el-icon>
            <template #title>系统维护</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/security" 
            v-if="hasPermission(['SYSTEM_MONITOR', 'AUDIT_READ'])"
          >
            <el-icon><Shield /></el-icon>
            <template #title>安全监控</template>
          </el-menu-item>
          
          <el-menu-item 
            index="/settings" 
            v-if="hasPermission(['SYSTEM_CONFIGURE'])"
          >
            <el-icon><Setting /></el-icon>
            <template #title>系统设置</template>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 内容区域 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import {
  Dashboard,
  User,
  Document,
  Lock,
  TrendCharts,
  Tools,
  Shield,
  Setting,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

// 权限检查
const hasPermission = (permissions) => {
  return userStore.checkPermissions(permissions)
}

// 用户操作处理
const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
      break
  }
}

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

onMounted(() => {
  // 初始化用户信息
  if (!userStore.user) {
    userStore.getCurrentUser()
  }
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  height: 60px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-name {
  cursor: pointer;
  color: #333;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 200px;
  background: #304156;
  transition: width 0.3s;
}

.sidebar.collapse {
  width: 64px;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.content {
  flex: 1;
  background: #f0f2f5;
  overflow-y: auto;
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -200px;
    top: 60px;
    height: calc(100vh - 60px);
    z-index: 999;
    transition: left 0.3s;
  }
  
  .sidebar.show {
    left: 0;
  }
  
  .content {
    margin-left: 0;
  }
  
  .header {
    padding: 0 15px;
  }
  
  .logo h1 {
    font-size: 18px;
  }
}

/* Element Plus 菜单样式覆盖 */
:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item.is-active) {
  background-color: #263445 !important;
}

:deep(.el-menu-item:hover) {
  background-color: #263445 !important;
}

:deep(.el-menu-item .el-icon) {
  margin-right: 8px;
  width: 16px;
}
</style>