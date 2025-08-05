<template>
  <div class="permission-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>权限管理</h1>
      <p>管理系统权限、角色和用户权限分配</p>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" type="card" class="permission-tabs">
      <!-- 权限管理 -->
      <el-tab-pane label="权限管理" name="permissions">
        <div class="tab-content">
          <!-- 操作栏 -->
          <div class="action-bar">
            <el-button type="primary" @click="showCreatePermissionDialog">
              <el-icon><Plus /></el-icon>
              新建权限
            </el-button>
            <el-button @click="refreshPermissions">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 权限列表 -->
          <el-table 
            :data="permissions" 
            v-loading="permissionsLoading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="name" label="权限名称" width="200" />
            <el-table-column prop="code" label="权限代码" width="180" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="resource_type" label="资源类型" width="120">
              <template #default="scope">
                <el-tag :type="getResourceTypeColor(scope.row.resource_type)">
                  {{ getResourceTypeName(scope.row.resource_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="operation_type" label="操作类型" width="120">
              <template #default="scope">
                <el-tag :type="getOperationTypeColor(scope.row.operation_type)">
                  {{ getOperationTypeName(scope.row.operation_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="editPermission(scope.row)">
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deletePermission(scope.row)"
                  :disabled="scope.row.is_system"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 角色管理 -->
      <el-tab-pane label="角色管理" name="roles">
        <div class="tab-content">
          <!-- 操作栏 -->
          <div class="action-bar">
            <el-button type="primary" @click="showCreateRoleDialog">
              <el-icon><Plus /></el-icon>
              新建角色
            </el-button>
            <el-button @click="refreshRoles">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 角色列表 -->
          <el-table 
            :data="roles" 
            v-loading="rolesLoading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="name" label="角色名称" width="200" />
            <el-table-column prop="code" label="角色代码" width="150" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="level" label="级别" width="80" />
            <el-table-column label="权限数量" width="100">
              <template #default="scope">
                <el-tag>{{ scope.row.permissions?.length || 0 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewRolePermissions(scope.row)">
                  查看权限
                </el-button>
                <el-button size="small" @click="editRole(scope.row)">
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteRole(scope.row)"
                  :disabled="scope.row.is_system"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 资源权限 -->
      <el-tab-pane label="资源权限" name="resource-permissions">
        <div class="tab-content">
          <!-- 操作栏 -->
          <div class="action-bar">
            <el-button type="primary" @click="showGrantResourcePermissionDialog">
              <el-icon><Plus /></el-icon>
              授予资源权限
            </el-button>
            <el-button @click="refreshResourcePermissions">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-select
              v-model="resourcePermissionFilter.resource_type"
              placeholder="资源类型"
              style="width: 150px; margin-right: 10px;"
              clearable
              @change="filterResourcePermissions"
            >
              <el-option 
                v-for="type in resourceTypes" 
                :key="type.value" 
                :label="type.label" 
                :value="type.value"
              />
            </el-select>
            <el-input
              v-model="resourcePermissionFilter.resource_id"
              placeholder="资源ID"
              style="width: 200px; margin-right: 10px;"
              @input="filterResourcePermissions"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-input
              v-model="resourcePermissionFilter.username"
              placeholder="用户名"
              style="width: 200px; margin-right: 10px;"
              @input="filterResourcePermissions"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- 资源权限列表 -->
          <el-table 
            :data="filteredResourcePermissions" 
            v-loading="resourcePermissionsLoading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="user.username" label="用户" width="120" />
            <el-table-column prop="user.full_name" label="姓名" width="100" />
            <el-table-column prop="resource_type" label="资源类型" width="120">
              <template #default="scope">
                <el-tag :type="getResourceTypeColor(scope.row.resource_type)">
                  {{ getResourceTypeName(scope.row.resource_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_id" label="资源ID" width="150" />
            <el-table-column prop="permission_level" label="权限级别" width="120">
              <template #default="scope">
                <el-tag :type="getPermissionLevelColor(scope.row.permission_level)">
                  {{ getPermissionLevelName(scope.row.permission_level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="operations" label="操作权限" width="200">
              <template #default="scope">
                <el-tag 
                  v-for="op in scope.row.operations" 
                  :key="op" 
                  size="small" 
                  style="margin-right: 5px;"
                >
                  {{ getOperationTypeName(op) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="granted_at" label="授予时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.granted_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="expires_at" label="过期时间" width="180">
              <template #default="scope">
                <span v-if="scope.row.expires_at">
                  {{ formatDateTime(scope.row.expires_at) }}
                </span>
                <span v-else>永久</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="revokeResourcePermission(scope.row)"
                >
                  撤销
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 操作日志 -->
      <el-tab-pane label="操作日志" name="audit-logs">
        <div class="tab-content">
          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-date-picker
              v-model="auditLogFilter.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="width: 350px; margin-right: 10px;"
              @change="filterAuditLogs"
            />
            <el-select
              v-model="auditLogFilter.action_type"
              placeholder="操作类型"
              style="width: 150px; margin-right: 10px;"
              clearable
              @change="filterAuditLogs"
            >
              <el-option label="登录" value="LOGIN" />
              <el-option label="登出" value="LOGOUT" />
              <el-option label="创建" value="CREATE" />
              <el-option label="更新" value="UPDATE" />
              <el-option label="删除" value="DELETE" />
              <el-option label="查看" value="VIEW" />
              <el-option label="权限变更" value="PERMISSION_CHANGE" />
            </el-select>
            <el-select
              v-model="auditLogFilter.resource_type"
              placeholder="资源类型"
              style="width: 150px; margin-right: 10px;"
              clearable
              @change="filterAuditLogs"
            >
              <el-option 
                v-for="type in resourceTypes" 
                :key="type.value" 
                :label="type.label" 
                :value="type.value"
              />
            </el-select>
            <el-input
              v-model="auditLogFilter.username"
              placeholder="用户名"
              style="width: 150px; margin-right: 10px;"
              @input="filterAuditLogs"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-input
              v-model="auditLogFilter.ip_address"
              placeholder="IP地址"
              style="width: 150px; margin-right: 10px;"
              @input="filterAuditLogs"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="refreshAuditLogs">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="exportAuditLogs">
              导出
            </el-button>
          </div>

          <!-- 操作日志列表 -->
          <el-table 
            :data="auditLogs" 
            v-loading="auditLogsLoading"
            stripe
            border
            style="width: 100%"
            :default-sort="{prop: 'created_at', order: 'descending'}"
          >
            <el-table-column prop="created_at" label="时间" width="180" sortable>
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="user.username" label="用户" width="120" />
            <el-table-column prop="action_type" label="操作类型" width="120">
              <template #default="scope">
                <el-tag :type="getActionTypeColor(scope.row.action_type)">
                  {{ getActionTypeName(scope.row.action_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="resource_type" label="资源类型" width="120">
              <template #default="scope">
                <el-tag v-if="scope.row.resource_type" :type="getResourceTypeColor(scope.row.resource_type)">
                  {{ getResourceTypeName(scope.row.resource_type) }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="resource_id" label="资源ID" width="150">
              <template #default="scope">
                <span v-if="scope.row.resource_id">{{ scope.row.resource_id }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="操作描述" min-width="200" />
            <el-table-column prop="ip_address" label="IP地址" width="130" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'SUCCESS' ? 'success' : 'danger'">
                  {{ scope.row.status === 'SUCCESS' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewAuditLogDetail(scope.row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="auditLogPagination.page"
              v-model:page-size="auditLogPagination.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="auditLogPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleAuditLogSizeChange"
              @current-change="handleAuditLogPageChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 用户权限 -->
      <el-tab-pane label="用户权限" name="user-permissions">
        <div class="tab-content">
          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户名或邮箱"
              style="width: 300px; margin-right: 10px;"
              @input="searchUsers"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="refreshUsers">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <!-- 用户列表 -->
          <el-table 
            :data="users" 
            v-loading="usersLoading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="full_name" label="姓名" width="120" />
            <el-table-column prop="email" label="邮箱" width="200" />
            <el-table-column label="主要角色" width="150">
              <template #default="scope">
                <el-tag v-if="scope.row.primary_role">
                  {{ scope.row.primary_role.name }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="直接权限" width="100">
              <template #default="scope">
                <el-tag>{{ scope.row.direct_permissions?.length || 0 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="manageUserPermissions(scope.row)">
                  管理权限
                </el-button>
                <el-button size="small" @click="viewUserPermissions(scope.row)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 权限创建/编辑对话框 -->
    <el-dialog 
      v-model="permissionDialogVisible" 
      :title="permissionDialogTitle"
      width="600px"
    >
      <el-form 
        ref="permissionFormRef" 
        :model="permissionForm" 
        :rules="permissionRules" 
        label-width="120px"
      >
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="请输入权限名称" />
        </el-form-item>
        <el-form-item label="权限代码" prop="code">
          <el-input v-model="permissionForm.code" placeholder="请输入权限代码" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="permissionForm.description" 
            type="textarea" 
            placeholder="请输入权限描述"
          />
        </el-form-item>
        <el-form-item label="资源类型" prop="resource_type">
          <el-select v-model="permissionForm.resource_type" placeholder="请选择资源类型">
            <el-option 
              v-for="type in resourceTypes" 
              :key="type.value" 
              :label="type.label" 
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型" prop="operation_type">
          <el-select v-model="permissionForm.operation_type" placeholder="请选择操作类型">
            <el-option 
              v-for="type in operationTypes" 
              :key="type.value" 
              :label="type.label" 
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="permissionForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePermission">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 角色创建/编辑对话框 -->
    <el-dialog 
      v-model="roleDialogVisible" 
      :title="roleDialogTitle"
      width="800px"
    >
      <el-form 
        ref="roleFormRef" 
        :model="roleForm" 
        :rules="roleRules" 
        label-width="120px"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色代码" prop="code">
          <el-input v-model="roleForm.code" placeholder="请输入角色代码" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="roleForm.description" 
            type="textarea" 
            placeholder="请输入角色描述"
          />
        </el-form-item>
        <el-form-item label="级别" prop="level">
          <el-input-number v-model="roleForm.level" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="权限">
          <div class="permission-selection">
            <el-tree
              ref="permissionTreeRef"
              :data="permissionTreeData"
              :props="treeProps"
              show-checkbox
              node-key="id"
              :default-checked-keys="roleForm.permission_ids"
            />
          </div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="roleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRole">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 用户权限管理对话框 -->
    <el-dialog 
      v-model="userPermissionDialogVisible" 
      title="用户权限管理"
      width="900px"
    >
      <div v-if="selectedUser">
        <h3>{{ selectedUser.full_name }} ({{ selectedUser.username }})</h3>
        
        <el-tabs v-model="userPermissionTab">
          <el-tab-pane label="角色分配" name="roles">
            <el-form label-width="120px">
              <el-form-item label="主要角色">
                <el-select 
                  v-model="userRoleForm.primary_role_id" 
                  placeholder="请选择主要角色"
                  style="width: 100%"
                >
                  <el-option 
                    v-for="role in roles" 
                    :key="role.id" 
                    :label="role.name" 
                    :value="role.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <el-tab-pane label="直接权限" name="permissions">
            <div class="permission-assignment">
              <el-tree
                ref="userPermissionTreeRef"
                :data="permissionTreeData"
                :props="treeProps"
                show-checkbox
                node-key="id"
                :default-checked-keys="userPermissionForm.permission_ids"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userPermissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUserPermissions">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 资源权限授予对话框 -->
    <el-dialog 
      v-model="resourcePermissionDialogVisible" 
      title="授予资源权限"
      width="600px"
    >
      <el-form 
        ref="resourcePermissionFormRef" 
        :model="resourcePermissionForm" 
        :rules="resourcePermissionRules" 
        label-width="120px"
      >
        <el-form-item label="用户" prop="user_id">
          <el-select 
            v-model="resourcePermissionForm.user_id" 
            placeholder="请选择用户"
            style="width: 100%"
            filterable
          >
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="`${user.full_name} (${user.username})`" 
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资源类型" prop="resource_type">
          <el-select 
            v-model="resourcePermissionForm.resource_type" 
            placeholder="请选择资源类型"
            style="width: 100%"
          >
            <el-option 
              v-for="type in resourceTypes" 
              :key="type.value" 
              :label="type.label" 
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资源ID" prop="resource_id">
          <el-input 
            v-model="resourcePermissionForm.resource_id" 
            placeholder="请输入资源ID"
          />
        </el-form-item>
        <el-form-item label="权限级别" prop="permission_level">
          <el-select 
            v-model="resourcePermissionForm.permission_level" 
            placeholder="请选择权限级别"
            style="width: 100%"
          >
            <el-option 
              v-for="level in permissionLevels" 
              :key="level.value" 
              :label="level.label" 
              :value="level.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作权限" prop="operations">
          <el-checkbox-group v-model="resourcePermissionForm.operations">
            <el-checkbox 
              v-for="op in operationTypes" 
              :key="op.value" 
              :label="op.value"
            >
              {{ op.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="resourcePermissionForm.expires_at"
            type="datetime"
            placeholder="选择过期时间（可选）"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resourcePermissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveResourcePermission">授予</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 操作日志详情对话框 -->
    <el-dialog 
      v-model="auditLogDetailDialogVisible" 
      title="操作日志详情"
      width="800px"
    >
      <div v-if="selectedAuditLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="操作时间">
            {{ formatDateTime(selectedAuditLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ selectedAuditLog.user?.username || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getActionTypeColor(selectedAuditLog.action_type)">
              {{ getActionTypeName(selectedAuditLog.action_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedAuditLog.status === 'SUCCESS' ? 'success' : 'danger'">
              {{ selectedAuditLog.status === 'SUCCESS' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="资源类型">
            <el-tag v-if="selectedAuditLog.resource_type" :type="getResourceTypeColor(selectedAuditLog.resource_type)">
              {{ getResourceTypeName(selectedAuditLog.resource_type) }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="资源ID">
            {{ selectedAuditLog.resource_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedAuditLog.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理">
            {{ selectedAuditLog.user_agent || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求URL" :span="2">
            {{ selectedAuditLog.request_url || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作描述" :span="2">
            {{ selectedAuditLog.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAuditLog.error_message" label="错误信息" :span="2">
            <el-text type="danger">{{ selectedAuditLog.error_message }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAuditLog.session_id" label="会话ID" :span="2">
            {{ selectedAuditLog.session_id }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedAuditLog.trace_id" label="追踪ID" :span="2">
            {{ selectedAuditLog.trace_id }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedAuditLog.additional_data" style="margin-top: 20px;">
          <h4>附加数据</h4>
          <el-input
            :model-value="JSON.stringify(selectedAuditLog.additional_data, null, 2)"
            type="textarea"
            :rows="6"
            readonly
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="auditLogDetailDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { permissionApi } from '@/api/permission'
import { userApi } from '@/api/user'

// 响应式数据
const activeTab = ref('permissions')
const permissionsLoading = ref(false)
const rolesLoading = ref(false)
const usersLoading = ref(false)
const resourcePermissionsLoading = ref(false)
const auditLogsLoading = ref(false)

// 权限数据
const permissions = ref([])
const roles = ref([])
const users = ref([])
const resourcePermissions = ref([])
const auditLogs = ref([])
const userSearch = ref('')

// 对话框状态
const permissionDialogVisible = ref(false)
const roleDialogVisible = ref(false)
const userPermissionDialogVisible = ref(false)
const resourcePermissionDialogVisible = ref(false)
const auditLogDetailDialogVisible = ref(false)

// 选中的操作日志
const selectedAuditLog = ref(null)

// 资源权限过滤
const resourcePermissionFilter = reactive({
  resource_type: '',
  resource_id: '',
  username: ''
})

// 操作日志过滤
const auditLogFilter = reactive({
  dateRange: null,
  action_type: '',
  resource_type: '',
  username: '',
  ip_address: ''
})

// 操作日志分页
const auditLogPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const permissionForm = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  resource_type: '',
  operation_type: '',
  is_active: true
})

const roleForm = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  level: 1,
  permission_ids: [],
  is_active: true
})

const selectedUser = ref(null)
const userPermissionTab = ref('roles')
const userRoleForm = reactive({
  primary_role_id: null
})

const userPermissionForm = reactive({
  permission_ids: []
})

const resourcePermissionForm = reactive({
  user_id: null,
  resource_type: '',
  resource_id: '',
  permission_level: '',
  operations: [],
  expires_at: null
})

// 表单验证规则
const permissionRules = {
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入权限代码', trigger: 'blur' }],
  resource_type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  operation_type: [{ required: true, message: '请选择操作类型', trigger: 'change' }]
}

const roleRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色代码', trigger: 'blur' }],
  level: [{ required: true, message: '请输入角色级别', trigger: 'blur' }]
}

const resourcePermissionRules = {
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  resource_type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  resource_id: [{ required: true, message: '请输入资源ID', trigger: 'blur' }],
  permission_level: [{ required: true, message: '请选择权限级别', trigger: 'change' }]
}

// 选项数据
const resourceTypes = [
  { label: '用户', value: 'USER' },
  { label: '角色', value: 'ROLE' },
  { label: '权限', value: 'PERMISSION' },
  { label: '报表', value: 'REPORT' },
  { label: '系统', value: 'SYSTEM' },
  { label: '审计', value: 'AUDIT' },
  { label: '数据', value: 'DATA' }
]

const operationTypes = [
  { label: '读取', value: 'read' },
  { label: '创建', value: 'CREATE' },
  { label: '更新', value: 'UPDATE' },
  { label: '删除', value: 'DELETE' },
  { label: '执行', value: 'EXECUTE' },
  { label: '管理', value: 'MANAGE' }
]

const permissionLevels = [
  { label: '只读', value: 'READ' },
  { label: '读写', value: 'WRITE' },
  { label: '管理员', value: 'ADMIN' },
  { label: '所有者', value: 'OWNER' }
]

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 计算属性
const permissionDialogTitle = computed(() => {
  return permissionForm.id ? '编辑权限' : '新建权限'
})

const roleDialogTitle = computed(() => {
  return roleForm.id ? '编辑角色' : '新建角色'
})

const permissionTreeData = computed(() => {
  // 将权限按资源类型分组
  const groups = {}
  permissions.value.forEach(permission => {
    const type = permission.resource_type
    if (!groups[type]) {
      groups[type] = {
        id: `group_${type}`,
        name: getResourceTypeName(type),
        children: []
      }
    }
    groups[type].children.push({
      id: permission.id,
      name: permission.name,
      code: permission.code
    })
  })
  return Object.values(groups)
})

const filteredResourcePermissions = computed(() => {
  return resourcePermissions.value.filter(rp => {
    const matchType = !resourcePermissionFilter.resource_type || 
                     rp.resource_type === resourcePermissionFilter.resource_type
    const matchId = !resourcePermissionFilter.resource_id || 
                   rp.resource_id.includes(resourcePermissionFilter.resource_id)
    const matchUser = !resourcePermissionFilter.username || 
                     rp.user?.username?.includes(resourcePermissionFilter.username)
    return matchType && matchId && matchUser
  })
})

// 方法
const loadPermissions = async () => {
  permissionsLoading.value = true
  try {
    const response = await permissionApi.getPermissions()
    permissions.value = response.data
  } catch (error) {
    ElMessage.error('加载权限列表失败')
  } finally {
    permissionsLoading.value = false
  }
}

const loadRoles = async () => {
  rolesLoading.value = true
  try {
    const response = await permissionApi.getRoles()
    roles.value = response.data
  } catch (error) {
    ElMessage.error('加载角色列表失败')
  } finally {
    rolesLoading.value = false
  }
}

const loadUsers = async () => {
  usersLoading.value = true
  try {
    const response = await userApi.getUsers()
    users.value = response.data
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

const loadResourcePermissions = async () => {
  resourcePermissionsLoading.value = true
  try {
    const response = await permissionApi.getResourcePermissions()
    resourcePermissions.value = response.data
  } catch (error) {
    ElMessage.error('加载资源权限列表失败')
  } finally {
    resourcePermissionsLoading.value = false
  }
}

const loadAuditLogs = async () => {
  auditLogsLoading.value = true
  try {
    const params = {
      page: auditLogPagination.page,
      size: auditLogPagination.size,
      ...auditLogFilter
    }
    const response = await permissionApi.getAuditLogs(params)
    auditLogs.value = response.data.items
    auditLogPagination.total = response.data.total
  } catch (error) {
    ElMessage.error('加载操作日志失败')
  } finally {
    auditLogsLoading.value = false
  }
}

const refreshPermissions = () => {
  loadPermissions()
}

const refreshRoles = () => {
  loadRoles()
}

const refreshUsers = () => {
  loadUsers()
}

const refreshResourcePermissions = () => {
  loadResourcePermissions()
}

const refreshAuditLogs = () => {
  loadAuditLogs()
}

const filterAuditLogs = () => {
  auditLogPagination.page = 1
  loadAuditLogs()
}

const handleAuditLogSizeChange = (size) => {
  auditLogPagination.size = size
  auditLogPagination.page = 1
  loadAuditLogs()
}

const handleAuditLogPageChange = (page) => {
  auditLogPagination.page = page
  loadAuditLogs()
}

const viewAuditLogDetail = (auditLog) => {
  selectedAuditLog.value = auditLog
  auditLogDetailDialogVisible.value = true
}

const exportAuditLogs = async () => {
  try {
    const params = {
      ...auditLogFilter,
      export: true
    }
    await permissionApi.exportAuditLogs(params)
    ElMessage.success('导出操作日志成功')
  } catch (error) {
    ElMessage.error('导出操作日志失败')
  }
}

const getActionTypeName = (type) => {
  const typeMap = {
    'LOGIN': '登录',
    'LOGOUT': '登出',
    'CREATE': '创建',
    'UPDATE': '更新',
    'DELETE': '删除',
    'VIEW': '查看',
    'PERMISSION_CHANGE': '权限变更'
  }
  return typeMap[type] || type
}

const getActionTypeColor = (type) => {
  const colorMap = {
    'LOGIN': 'success',
    'LOGOUT': 'info',
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'VIEW': 'info',
    'PERMISSION_CHANGE': 'warning'
  }
  return colorMap[type] || ''
}

const filterResourcePermissions = () => {
  // 过滤逻辑已在计算属性中实现
}

const searchUsers = () => {
  // 实现用户搜索逻辑
  // 这里可以调用API进行搜索
}

// 权限管理方法
const showCreatePermissionDialog = () => {
  resetPermissionForm()
  permissionDialogVisible.value = true
}

const editPermission = (permission) => {
  Object.assign(permissionForm, permission)
  permissionDialogVisible.value = true
}

const resetPermissionForm = () => {
  Object.assign(permissionForm, {
    id: null,
    name: '',
    code: '',
    description: '',
    resource_type: '',
    operation_type: '',
    is_active: true
  })
}

const savePermission = async () => {
  try {
    if (permissionForm.id) {
      await permissionApi.updatePermission(permissionForm.id, permissionForm)
      ElMessage.success('权限更新成功')
    } else {
      await permissionApi.createPermission(permissionForm)
      ElMessage.success('权限创建成功')
    }
    permissionDialogVisible.value = false
    loadPermissions()
  } catch (error) {
    ElMessage.error('保存权限失败')
  }
}

const deletePermission = async (permission) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${permission.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await permissionApi.deletePermission(permission.id)
    ElMessage.success('权限删除成功')
    loadPermissions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除权限失败')
    }
  }
}

// 角色管理方法
const showCreateRoleDialog = () => {
  resetRoleForm()
  roleDialogVisible.value = true
}

const editRole = (role) => {
  Object.assign(roleForm, {
    ...role,
    permission_ids: role.permissions?.map(p => p.id) || []
  })
  roleDialogVisible.value = true
}

const resetRoleForm = () => {
  Object.assign(roleForm, {
    id: null,
    name: '',
    code: '',
    description: '',
    level: 1,
    permission_ids: [],
    is_active: true
  })
}

const saveRole = async () => {
  try {
    // 获取选中的权限ID
    const checkedKeys = permissionTreeRef.value.getCheckedKeys()
    roleForm.permission_ids = checkedKeys
    
    if (roleForm.id) {
      await permissionApi.updateRole(roleForm.id, roleForm)
      ElMessage.success('角色更新成功')
    } else {
      await permissionApi.createRole(roleForm)
      ElMessage.success('角色创建成功')
    }
    roleDialogVisible.value = false
    loadRoles()
  } catch (error) {
    ElMessage.error('保存角色失败')
  }
}

const deleteRole = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await permissionApi.deleteRole(role.id)
    ElMessage.success('角色删除成功')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败')
    }
  }
}

const viewRolePermissions = (role) => {
  // 显示角色权限详情
  ElMessage.info('查看角色权限功能待实现')
}

// 用户权限管理方法
const manageUserPermissions = (user) => {
  selectedUser.value = user
  userRoleForm.primary_role_id = user.primary_role?.id || null
  userPermissionForm.permission_ids = user.direct_permissions?.map(p => p.id) || []
  userPermissionDialogVisible.value = true
}

const viewUserPermissions = (user) => {
  // 显示用户权限详情
  ElMessage.info('查看用户权限详情功能待实现')
}

const saveUserPermissions = async () => {
  try {
    // 保存角色分配
    if (userRoleForm.primary_role_id) {
      await permissionApi.assignRoleToUser(selectedUser.value.id, {
        role_id: userRoleForm.primary_role_id
      })
    }
    
    // 保存直接权限
    const checkedKeys = userPermissionTreeRef.value.getCheckedKeys()
    await permissionApi.assignPermissionsToUser(selectedUser.value.id, {
      permission_ids: checkedKeys
    })
    
    ElMessage.success('用户权限保存成功')
    userPermissionDialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error('保存用户权限失败')
  }
}

// 辅助方法
const getResourceTypeName = (type) => {
  const typeMap = {
    'USER': '用户',
    'ROLE': '角色',
    'PERMISSION': '权限',
    'REPORT': '报表',
    'SYSTEM': '系统',
    'AUDIT': '审计',
    'DATA': '数据'
  }
  return typeMap[type] || type
}

const getResourceTypeColor = (type) => {
  const colorMap = {
    'USER': 'primary',
    'ROLE': 'success',
    'PERMISSION': 'warning',
    'REPORT': 'info',
    'SYSTEM': 'danger',
    'AUDIT': 'warning',
    'DATA': 'primary'
  }
  return colorMap[type] || ''
}

const getOperationTypeName = (type) => {
  const typeMap = {
    'READ': '读取',
    'CREATE': '创建',
    'UPDATE': '更新',
    'DELETE': '删除',
    'EXECUTE': '执行',
    'MANAGE': '管理'
  }
  return typeMap[type] || type
}

const getOperationTypeColor = (type) => {
  const colorMap = {
    'read': 'info',
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'EXECUTE': 'primary',
    'MANAGE': 'danger'
  }
  return colorMap[type] || ''
}

const getPermissionLevelName = (level) => {
  const levelMap = {
    'READ': '只读',
    'WRITE': '读写',
    'ADMIN': '管理员',
    'OWNER': '所有者'
  }
  return levelMap[level] || level
}

const getPermissionLevelColor = (level) => {
  const colorMap = {
    'READ': 'info',
    'WRITE': 'primary',
    'ADMIN': 'warning',
    'OWNER': 'danger'
  }
  return colorMap[level] || ''
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 资源权限管理方法
const showGrantResourcePermissionDialog = () => {
  resetResourcePermissionForm()
  resourcePermissionDialogVisible.value = true
}

const resetResourcePermissionForm = () => {
  Object.assign(resourcePermissionForm, {
    user_id: null,
    resource_type: '',
    resource_id: '',
    permission_level: '',
    operations: [],
    expires_at: null
  })
}

const saveResourcePermission = async () => {
  try {
    await permissionApi.grantResourcePermission(resourcePermissionForm)
    ElMessage.success('资源权限授予成功')
    resourcePermissionDialogVisible.value = false
    loadResourcePermissions()
  } catch (error) {
    ElMessage.error('授予资源权限失败')
  }
}

const revokeResourcePermission = async (resourcePermission) => {
  try {
    await ElMessageBox.confirm(
      '确定要撤销该资源权限吗？',
      '确认撤销',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await permissionApi.revokeResourcePermission(resourcePermission.id)
    ElMessage.success('资源权限撤销成功')
    loadResourcePermissions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤销资源权限失败')
    }
  }
}

// 组件引用
const permissionFormRef = ref()
const roleFormRef = ref()
const permissionTreeRef = ref()
const userPermissionTreeRef = ref()
const resourcePermissionFormRef = ref()

// 生命周期
onMounted(() => {
  loadPermissions()
  loadRoles()
  loadUsers()
  loadResourcePermissions()
  loadAuditLogs()
})
</script>

<style scoped>
.permission-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.permission-tabs {
  margin-top: 20px;
}

.tab-content {
  padding: 20px 0;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.permission-selection {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.permission-assignment {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>