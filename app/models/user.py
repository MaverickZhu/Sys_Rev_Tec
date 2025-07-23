from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    full_name = Column(String(100), comment="姓名")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    
    # 用户详细信息
    employee_id = Column(String(50), unique=True, comment="工号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    phone = Column(String(20), comment="电话")
    
    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    
    # 角色权限
    role_id = Column(Integer, ForeignKey("roles.id"), comment="角色ID")
    permissions = Column(Text, comment="额外权限(JSON格式)")
    
    # 审查相关
    reviewer_level = Column(String(20), comment="审查员级别：junior/senior/expert/chief")
    specialties = Column(Text, comment="专业领域(JSON格式)")
    certification = Column(String(100), comment="资质证书")
    
    # 登录信息
    last_login = Column(DateTime(timezone=True), comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(DateTime(timezone=True), comment="锁定到期时间")
    
    # 密码管理
    password_changed_at = Column(DateTime(timezone=True), comment="密码修改时间")
    password_reset_token = Column(String(255), comment="密码重置令牌")
    password_reset_expires = Column(DateTime(timezone=True), comment="重置令牌过期时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    role = relationship("Role", back_populates="users")
    projects = relationship("Project", back_populates="owner")
    user_sessions = relationship("UserSession", back_populates="user")


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 角色基本信息
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    display_name = Column(String(100), comment="显示名称")
    description = Column(Text, comment="角色描述")
    
    # 角色权限
    permissions = Column(Text, nullable=False, comment="权限列表(JSON格式)")
    
    # 角色状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统角色")
    
    # 层级关系
    parent_role_id = Column(Integer, ForeignKey("roles.id"), comment="父角色ID")
    level = Column(Integer, default=1, comment="角色层级")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    users = relationship("User", back_populates="role")
    parent_role = relationship("Role", remote_side=[id])
    child_roles = relationship("Role", overlaps="parent_role")


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 会话信息
    session_token = Column(String(255), unique=True, nullable=False, comment="会话令牌")
    refresh_token = Column(String(255), unique=True, comment="刷新令牌")
    
    # 会话状态
    is_active = Column(Boolean, default=True, comment="是否活跃")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    
    # 客户端信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    device_info = Column(Text, comment="设备信息")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="user_sessions")


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), comment="操作用户ID")
    
    # 操作信息
    action = Column(String(50), nullable=False, comment="操作类型")
    resource_type = Column(String(50), comment="资源类型")
    resource_id = Column(String(50), comment="资源ID")
    
    # 操作详情
    description = Column(Text, comment="操作描述")
    old_values = Column(Text, comment="修改前的值(JSON格式)")
    new_values = Column(Text, comment="修改后的值(JSON格式)")
    
    # 请求信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    request_id = Column(String(100), comment="请求ID")
    
    # 结果信息
    status = Column(String(20), comment="操作状态：success/failure/error")
    error_message = Column(Text, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    user = relationship("User")