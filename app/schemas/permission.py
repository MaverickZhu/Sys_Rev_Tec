"""权限管理相关的Pydantic模式定义

定义权限、角色、权限组等的请求和响应模式
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from app.models.permission import ResourceType, OperationType, PermissionLevel


# 权限模式
class PermissionBase(BaseModel):
    """权限基础模式"""
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    resource_type: ResourceType = Field(..., description="资源类型")
    operation: OperationType = Field(..., description="操作类型")
    is_active: bool = Field(True, description="是否激活")


class PermissionCreate(PermissionBase):
    """创建权限模式"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限模式"""
    name: Optional[str] = Field(None, description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PermissionInDB(PermissionBase):
    """数据库中的权限模式"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Permission(PermissionInDB):
    """权限响应模式"""
    pass


# 角色模式
class RoleBase(BaseModel):
    """角色基础模式"""
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    level: int = Field(1, description="角色级别，数字越小级别越高")
    is_active: bool = Field(True, description="是否激活")


class RoleCreate(RoleBase):
    """创建角色模式"""
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色模式"""
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    level: Optional[int] = Field(None, description="角色级别")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleInDB(RoleBase):
    """数据库中的角色模式"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Role(RoleInDB):
    """角色响应模式"""
    permissions: List[Permission] = Field(default_factory=list, description="角色权限列表")


# 权限组模式
class PermissionGroupBase(BaseModel):
    """权限组基础模式"""
    code: str = Field(..., description="权限组代码")
    name: str = Field(..., description="权限组名称")
    description: Optional[str] = Field(None, description="权限组描述")
    is_active: bool = Field(True, description="是否激活")


class PermissionGroupCreate(PermissionGroupBase):
    """创建权限组模式"""
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class PermissionGroupUpdate(BaseModel):
    """更新权限组模式"""
    name: Optional[str] = Field(None, description="权限组名称")
    description: Optional[str] = Field(None, description="权限组描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class PermissionGroupInDB(PermissionGroupBase):
    """数据库中的权限组模式"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PermissionGroup(PermissionGroupInDB):
    """权限组响应模式"""
    permissions: List[Permission] = Field(default_factory=list, description="权限组权限列表")


# 资源权限模式
class ResourcePermissionBase(BaseModel):
    """资源权限基础模式"""
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    permission_level: PermissionLevel = Field(..., description="权限级别")


class ResourcePermissionCreate(ResourcePermissionBase):
    """创建资源权限模式"""
    user_id: int = Field(..., description="用户ID")


class ResourcePermissionUpdate(BaseModel):
    """更新资源权限模式"""
    permission_level: Optional[PermissionLevel] = Field(None, description="权限级别")


class ResourcePermissionInDB(ResourcePermissionBase):
    """数据库中的资源权限模式"""
    id: int
    user_id: int
    granted_by: int
    granted_at: datetime
    
    class Config:
        from_attributes = True


class ResourcePermission(ResourcePermissionInDB):
    """资源权限响应模式"""
    pass


# 用户权限相关模式
class UserPermissionSummary(BaseModel):
    """用户权限摘要"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="基础角色")
    primary_role: Optional[Role] = Field(None, description="主要角色")
    direct_permissions: List[Permission] = Field(default_factory=list, description="直接权限")
    role_permissions: List[Permission] = Field(default_factory=list, description="角色权限")
    resource_permissions: List[ResourcePermission] = Field(default_factory=list, description="资源权限")
    all_permissions: List[str] = Field(default_factory=list, description="所有权限代码")


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    permission_code: str = Field(..., description="权限代码")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    operation: Optional[str] = Field(None, description="操作类型")


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    has_permission: bool = Field(..., description="是否有权限")
    permission_source: Optional[str] = Field(None, description="权限来源")
    message: Optional[str] = Field(None, description="说明信息")


class RolePermissionRequest(BaseModel):
    """角色权限操作请求"""
    role_id: int = Field(..., description="角色ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")


class UserRoleRequest(BaseModel):
    """用户角色操作请求"""
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")


# 权限优化相关模式
class PermissionOptimizationResponse(BaseModel):
    """权限优化响应"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="响应数据")
    message: str = Field(..., description="响应消息")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "user_id": 1,
                    "permission_code": "user:read",
                    "has_permission": True,
                    "query_time_ms": 5.2
                },
                "message": "权限检查完成"
            }
        }


class BatchPermissionResult(BaseModel):
    """批量权限检查结果"""
    user_id: int = Field(..., description="用户ID")
    permissions: Dict[str, bool] = Field(..., description="权限检查结果")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "permissions": {
                    "user:read": True,
                    "user:write": False,
                    "admin:manage": False
                }
            }
        }


class PermissionUsageStats(BaseModel):
    """权限使用统计"""
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    usage_count: int = Field(..., description="使用次数")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "user:read",
                "name": "用户查看",
                "usage_count": 150
            }
        }


class RoleUsageStats(BaseModel):
    """角色使用统计"""
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    user_count: int = Field(..., description="用户数量")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "admin",
                "name": "管理员",
                "user_count": 5
            }
        }


class QueryStats(BaseModel):
    """查询统计"""
    total_queries: int = Field(..., description="总查询次数")
    cache_hits: int = Field(..., description="缓存命中次数")
    db_queries: int = Field(..., description="数据库查询次数")
    batch_queries: int = Field(..., description="批量查询次数")
    cache_hit_rate: float = Field(..., description="缓存命中率")
    
    class Config:
        schema_extra = {
            "example": {
                "total_queries": 1000,
                "cache_hits": 800,
                "db_queries": 200,
                "batch_queries": 50,
                "cache_hit_rate": 0.8
            }
        }


class UserPermissionRequest(BaseModel):
    """用户权限操作请求"""
    user_id: int = Field(..., description="用户ID")
    permission_ids: List[int] = Field(..., description="权限ID列表")


class ResourcePermissionRequest(BaseModel):
    """资源权限操作请求"""
    user_id: int = Field(..., description="用户ID")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    permission_level: PermissionLevel = Field(..., description="权限级别")


# 权限搜索和过滤模式
class PermissionSearchRequest(BaseModel):
    """权限搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    resource_type: Optional[ResourceType] = Field(None, description="资源类型")
    operation: Optional[OperationType] = Field(None, description="操作类型")
    is_active: Optional[bool] = Field(None, description="是否激活")
    skip: int = Field(0, ge=0, description="跳过数量")
    limit: int = Field(100, ge=1, le=1000, description="限制数量")


class RoleSearchRequest(BaseModel):
    """角色搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    level_min: Optional[int] = Field(None, description="最小级别")
    level_max: Optional[int] = Field(None, description="最大级别")
    is_active: Optional[bool] = Field(None, description="是否激活")
    skip: int = Field(0, ge=0, description="跳过数量")
    limit: int = Field(100, ge=1, le=1000, description="限制数量")


class PermissionGroupSearchRequest(BaseModel):
    """权限组搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    is_active: Optional[bool] = Field(None, description="是否激活")
    skip: int = Field(0, ge=0, description="跳过数量")
    limit: int = Field(100, ge=1, le=1000, description="限制数量")


# 权限统计模式
class PermissionStats(BaseModel):
    """权限统计"""
    total_permissions: int = Field(..., description="总权限数")
    active_permissions: int = Field(..., description="激活权限数")
    total_roles: int = Field(..., description="总角色数")
    active_roles: int = Field(..., description="激活角色数")
    total_permission_groups: int = Field(..., description="总权限组数")
    active_permission_groups: int = Field(..., description="激活权限组数")
    resource_type_stats: Dict[str, int] = Field(default_factory=dict, description="资源类型统计")
    operation_type_stats: Dict[str, int] = Field(default_factory=dict, description="操作类型统计")


# 权限导入导出模式
class PermissionExportData(BaseModel):
    """权限导出数据"""
    permissions: List[Permission] = Field(default_factory=list, description="权限列表")
    roles: List[Role] = Field(default_factory=list, description="角色列表")
    permission_groups: List[PermissionGroup] = Field(default_factory=list, description="权限组列表")
    export_time: datetime = Field(..., description="导出时间")
    version: str = Field("1.0", description="数据版本")


class PermissionImportRequest(BaseModel):
    """权限导入请求"""
    data: PermissionExportData = Field(..., description="导入数据")
    overwrite_existing: bool = Field(False, description="是否覆盖已存在的数据")
    validate_only: bool = Field(False, description="仅验证不导入")


class PermissionImportResponse(BaseModel):
    """权限导入响应"""
    success: bool = Field(..., description="是否成功")
    imported_permissions: int = Field(0, description="导入权限数")
    imported_roles: int = Field(0, description="导入角色数")
    imported_permission_groups: int = Field(0, description="导入权限组数")
    skipped_items: int = Field(0, description="跳过项目数")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


# 权限审计模式
class PermissionAuditLog(BaseModel):
    """权限审计日志"""
    id: int
    action: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    user_id: int = Field(..., description="操作用户ID")
    target_user_id: Optional[int] = Field(None, description="目标用户ID")
    permission_code: Optional[str] = Field(None, description="权限代码")
    role_code: Optional[str] = Field(None, description="角色代码")
    old_value: Optional[Dict[str, Any]] = Field(None, description="旧值")
    new_value: Optional[Dict[str, Any]] = Field(None, description="新值")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class PermissionAuditSearchRequest(BaseModel):
    """权限审计搜索请求"""
    action: Optional[str] = Field(None, description="操作类型")
    resource_type: Optional[str] = Field(None, description="资源类型")
    user_id: Optional[int] = Field(None, description="操作用户ID")
    target_user_id: Optional[int] = Field(None, description="目标用户ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    skip: int = Field(0, ge=0, description="跳过数量")
    limit: int = Field(100, ge=1, le=1000, description="限制数量")