<template>
  <div class="profile">
    <div class="page-header">
      <h1>个人资料</h1>
      <p>管理您的个人信息和账户设置</p>
    </div>

    <el-row :gutter="20">
      <!-- 个人信息 -->
      <el-col :span="16">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-button type="primary" @click="editMode = !editMode">
                {{ editMode ? '取消编辑' : '编辑资料' }}
              </el-button>
            </div>
          </template>
          
          <el-form :model="userInfo" label-width="100px" :disabled="!editMode">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input v-model="userInfo.username" disabled />
                </el-form-item>
                <el-form-item label="姓名">
                  <el-input v-model="userInfo.fullName" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="userInfo.email" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="userInfo.phone" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="部门">
                  <el-select v-model="userInfo.department" style="width: 100%">
                    <el-option label="技术部" value="tech" />
                    <el-option label="运营部" value="operations" />
                    <el-option label="安全部" value="security" />
                    <el-option label="管理部" value="management" />
                  </el-select>
                </el-form-item>
                <el-form-item label="职位">
                  <el-input v-model="userInfo.position" />
                </el-form-item>
                <el-form-item label="入职日期">
                  <el-date-picker
                    v-model="userInfo.joinDate"
                    type="date"
                    placeholder="选择日期"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="状态">
                  <el-tag :type="userInfo.status === 'active' ? 'success' : 'danger'">
                    {{ userInfo.status === 'active' ? '正常' : '禁用' }}
                  </el-tag>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="个人简介">
              <el-input
                v-model="userInfo.bio"
                type="textarea"
                :rows="4"
                placeholder="请输入个人简介"
              />
            </el-form-item>
            
            <el-form-item v-if="editMode">
              <el-button type="primary" @click="saveProfile" :loading="saving">
                保存修改
              </el-button>
              <el-button @click="editMode = false">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 密码修改 -->
        <el-card class="profile-card" style="margin-top: 20px;">
          <template #header>
            <span>密码修改</span>
          </template>
          
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="当前密码" prop="currentPassword">
                  <el-input v-model="passwordForm.currentPassword" type="password" show-password />
                </el-form-item>
                <el-form-item label="新密码" prop="newPassword">
                  <el-input v-model="passwordForm.newPassword" type="password" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirmPassword">
                  <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <div class="password-tips">
                  <h4>密码要求：</h4>
                  <ul>
                    <li>至少8个字符</li>
                    <li>包含大小写字母</li>
                    <li>包含数字</li>
                    <li>包含特殊字符</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
            
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="changingPassword">
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 侧边栏 -->
      <el-col :span="8">
        <!-- 头像上传 -->
        <el-card class="profile-card">
          <template #header>
            <span>头像</span>
          </template>
          
          <div class="avatar-section">
            <el-avatar :size="120" :src="userInfo.avatar" class="avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <el-upload
              class="avatar-uploader"
              action="#"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :on-success="handleAvatarSuccess"
            >
              <el-button type="primary" size="small" style="margin-top: 10px;">
                更换头像
              </el-button>
            </el-upload>
          </div>
        </el-card>

        <!-- 账户统计 -->
        <el-card class="profile-card" style="margin-top: 20px;">
          <template #header>
            <span>账户统计</span>
          </template>
          
          <div class="stats">
            <div class="stat-item">
              <div class="stat-value">{{ userStats.loginCount }}</div>
              <div class="stat-label">登录次数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.lastLogin }}</div>
              <div class="stat-label">最后登录</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.projectCount }}</div>
              <div class="stat-label">参与项目</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.taskCount }}</div>
              <div class="stat-label">完成任务</div>
            </div>
          </div>
        </el-card>

        <!-- 安全设置 -->
        <el-card class="profile-card" style="margin-top: 20px;">
          <template #header>
            <span>安全设置</span>
          </template>
          
          <div class="security-settings">
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">双因子认证</div>
                <div class="security-desc">增强账户安全性</div>
              </div>
              <el-switch v-model="securitySettings.twoFactor" @change="toggleTwoFactor" />
            </div>
            
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">登录通知</div>
                <div class="security-desc">新设备登录时发送邮件</div>
              </div>
              <el-switch v-model="securitySettings.loginNotification" @change="toggleLoginNotification" />
            </div>
            
            <div class="security-item">
              <div class="security-info">
                <div class="security-title">会话管理</div>
                <div class="security-desc">查看活跃会话</div>
              </div>
              <el-button size="small" @click="viewSessions">查看</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User } from '@element-plus/icons-vue'

// 响应式数据
const editMode = ref(false)
const saving = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref()

const userInfo = reactive({
  username: 'admin',
  fullName: '系统管理员',
  email: 'admin@example.com',
  phone: '13800138000',
  department: 'tech',
  position: '系统架构师',
  joinDate: new Date('2023-01-01'),
  status: 'active',
  bio: '负责系统架构设计和技术决策，具有丰富的系统开发和管理经验。',
  avatar: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const userStats = reactive({
  loginCount: 1234,
  lastLogin: '2024-01-15 14:30',
  projectCount: 15,
  taskCount: 89
})

const securitySettings = reactive({
  twoFactor: false,
  loginNotification: true
})

// 表单验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      message: '密码必须包含大小写字母、数字和特殊字符',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const saveProfile = async () => {
  try {
    saving.value = true
    
    // 模拟保存用户信息
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    editMode.value = false
    ElMessage.success('个人资料保存成功')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    
    changingPassword.value = true
    
    // 模拟修改密码
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    resetPasswordForm()
    ElMessage.success('密码修改成功')
  } catch (error) {
    if (error !== false) {
      ElMessage.error('密码修改失败: ' + error.message)
    }
  } finally {
    changingPassword.value = false
  }
}

const resetPasswordForm = () => {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

const beforeAvatarUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('头像只能是 JPG/PNG 格式!')
  }
  if (!isLt2M) {
    ElMessage.error('头像大小不能超过 2MB!')
  }
  return isJPG && isLt2M
}

const handleAvatarSuccess = (response, file) => {
  userInfo.avatar = URL.createObjectURL(file.raw)
  ElMessage.success('头像上传成功')
}

const toggleTwoFactor = (value) => {
  if (value) {
    ElMessageBox.confirm(
      '启用双因子认证将增强您的账户安全性，是否继续？',
      '确认启用',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    ).then(() => {
      ElMessage.success('双因子认证已启用')
    }).catch(() => {
      securitySettings.twoFactor = false
    })
  } else {
    ElMessage.info('双因子认证已关闭')
  }
}

const toggleLoginNotification = (value) => {
  ElMessage.success(value ? '登录通知已开启' : '登录通知已关闭')
}

const viewSessions = () => {
  ElMessageBox.alert(
    '当前活跃会话：\n1. Chrome - 192.168.1.100 (当前)\n2. Firefox - 192.168.1.101 (2小时前)',
    '会话管理',
    {
      confirmButtonText: '确定',
    }
  )
}

// 生命周期
onMounted(() => {
  // 加载用户数据
})
</script>

<style scoped>
.profile {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
}

.profile-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.avatar-section {
  text-align: center;
}

.avatar {
  margin-bottom: 10px;
}

.stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.security-settings {
  space-y: 16px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.security-item:last-child {
  border-bottom: none;
}

.security-info {
  flex: 1;
}

.security-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.security-desc {
  font-size: 12px;
  color: #909399;
}

.password-tips {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid #409EFF;
}

.password-tips h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
}

.password-tips ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
}

.password-tips li {
  margin-bottom: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}

@media (max-width: 768px) {
  .profile {
    padding: 10px;
  }
  
  .stats {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  :deep(.el-col) {
    margin-bottom: 20px;
  }
}
</style>