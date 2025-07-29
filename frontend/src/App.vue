<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

// 应用初始化
onMounted(async () => {
  // 检查用户认证状态
  const token = localStorage.getItem('authToken')
  if (token) {
    try {
      await userStore.getCurrentUser()
      // 如果当前在登录页面且已认证，重定向到仪表板
      if (router.currentRoute.value.path === '/login') {
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('用户认证失败:', error)
      // 清除无效token
      localStorage.removeItem('authToken')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('tokenType')
      // 重定向到登录页面
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
  } else {
    // 未认证用户重定向到登录页面
    if (router.currentRoute.value.path !== '/login') {
      router.push('/login')
    }
  }
})
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f0f2f5;
  color: #333;
}

#app {
  height: 100vh;
  overflow: hidden;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Element Plus 样式覆盖 */
.el-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-button {
  border-radius: 6px;
}

.el-input__wrapper {
  border-radius: 6px;
}

.el-select .el-input__wrapper {
  border-radius: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-card {
    margin: 10px;
  }
  
  .el-table {
    font-size: 12px;
  }
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(-100%);
}

.slide-leave-to {
  transform: translateX(100%);
}

/* 工具类 */
.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.text-left {
  text-align: left;
}

.mb-10 {
  margin-bottom: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}

.mt-10 {
  margin-top: 10px;
}

.mt-20 {
  margin-top: 20px;
}

.p-10 {
  padding: 10px;
}

.p-20 {
  padding: 20px;
}

.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-1 {
  flex: 1;
}

/* 状态颜色 */
.status-success {
  color: #67c23a;
}

.status-warning {
  color: #e6a23c;
}

.status-danger {
  color: #f56c6c;
}

.status-info {
  color: #909399;
}

/* 加载状态 */
.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  flex-direction: column;
  gap: 10px;
}

.loading-text {
  color: #909399;
  font-size: 14px;
}

/* 空状态 */
.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  flex-direction: column;
  gap: 10px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  color: #dcdfe6;
}

.empty-text {
  font-size: 14px;
}
</style>