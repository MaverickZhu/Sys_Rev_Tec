<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <!-- 移动端菜单按钮 -->
        <el-button 
          v-if="isMobile" 
          type="text" 
          @click="toggleSidebar"
          class="mobile-menu-btn"
        >
          <el-icon :size="20">
            <Menu />
          </el-icon>
        </el-button>
        
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
      <aside 
        class="sidebar" 
        :class="{ 
          collapse: isCollapse && !isMobile, 
          'mobile-show': isMobile && sidebarVisible 
        }"
      >
        <!-- 移动端遮罩层 -->
        <div 
          v-if="isMobile && sidebarVisible" 
          class="sidebar-overlay"
          @click="closeMobileSidebar"
        ></div>
        
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          :collapse="isCollapse && !isMobile"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          @select="handleMenuClick"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
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
            <el-icon><Warning /></el-icon>
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
  Odometer,
  User,
  Document,
  Lock,
  TrendCharts,
  Tools,
  Warning,
  Setting,
  ArrowDown,
  Menu
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const isMobile = ref(false)
const sidebarVisible = ref(false)

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    isCollapse.value = false
    sidebarVisible.value = false
  }
}

// 监听窗口大小变化
const handleResize = () => {
  checkMobile()
}

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
  if (isMobile.value) {
    sidebarVisible.value = !sidebarVisible.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

// 关闭移动端侧边栏
const closeMobileSidebar = () => {
  if (isMobile.value) {
    sidebarVisible.value = false
  }
}

// 处理菜单点击
const handleMenuClick = () => {
  closeMobileSidebar()
}

onMounted(() => {
  // 初始化用户信息
  if (!userStore.user) {
    userStore.getCurrentUser()
  }
  
  // 初始化移动端检测
  checkMobile()
  window.addEventListener('resize', handleResize)
})

// 清理事件监听
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
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

/* 移动端菜单按钮 */
.mobile-menu-btn {
  margin-right: 12px;
  padding: 8px;
  border-radius: 6px;
}

.mobile-menu-btn:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

/* 移动端遮罩层 */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -200px;
    top: 60px;
    height: calc(100vh - 60px);
    z-index: 999;
    transition: left 0.3s ease;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }
  
  .sidebar.mobile-show {
    left: 0;
  }
  
  .content {
    margin-left: 0;
    padding: 15px;
  }
  
  .header {
    padding: 0 15px;
  }
  
  .header-left {
    display: flex;
    align-items: center;
  }
  
  .logo h1 {
    font-size: 16px;
    margin-left: 8px;
  }
  
  .user-name {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .header {
    padding: 0 10px;
  }
  
  .logo h1 {
    font-size: 14px;
  }
  
  .content {
    padding: 10px;
  }
  
  .sidebar {
    width: 180px;
  }
  
  .sidebar.mobile-show {
    left: 0;
  }
  
  .sidebar:not(.mobile-show) {
    left: -180px;
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