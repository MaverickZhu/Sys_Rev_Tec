from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class Project(Base):
    """政府采购项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    
    # 项目基本信息
    project_code = Column(String(50), unique=True, nullable=False, index=True, comment="项目编号")
    name = Column(String(200), index=True, nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    
    # 项目分类
    project_type = Column(String(50), nullable=False, comment="项目类型：货物/工程/服务")
    procurement_method = Column(String(50), comment="采购方式：公开招标/邀请招标/竞争性谈判/单一来源/询价")
    budget_source = Column(String(100), comment="资金来源")
    
    # 项目金额
    budget_amount = Column(Numeric(15, 2), comment="预算金额")
    contract_amount = Column(Numeric(15, 2), comment="合同金额")
    final_amount = Column(Numeric(15, 2), comment="最终金额")
    
    # 项目时间
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")
    
    # 项目状态
    status = Column(String(20), default="planning", comment="项目状态：planning/procurement/implementation/acceptance/completed/cancelled")
    review_status = Column(String(20), default="pending", comment="审查状态：pending/in_progress/completed/rejected")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 项目参与方
    procuring_entity = Column(String(200), comment="采购人")
    procurement_agency = Column(String(200), comment="采购代理机构")
    winning_bidder = Column(String(200), comment="中标人")
    
    # 项目管理
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="项目负责人")
    department = Column(String(100), comment="所属部门")
    priority = Column(String(10), default="normal", comment="优先级：low/normal/high/urgent")
    
    # 审查信息
    review_required = Column(Boolean, default=True, comment="是否需要审查")
    current_review_stage = Column(String(20), comment="当前审查阶段")
    review_progress = Column(Integer, default=0, comment="审查进度(百分比)")
    
    # 风险评估
    risk_level = Column(String(10), default="medium", comment="风险等级：low/medium/high/critical")
    risk_factors = Column(Text, comment="风险因素")
    
    # 备注信息
    notes = Column(Text, comment="备注")
    tags = Column(Text, comment="标签(JSON格式)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    reviews = relationship("ProjectReview", back_populates="project")
    issues = relationship("Issue", back_populates="project")
    comparisons = relationship("ProjectComparison", foreign_keys="[ProjectComparison.project_id]", back_populates="project")
    compared_projects = relationship("ProjectComparison", foreign_keys="[ProjectComparison.compared_project_id]", back_populates="compared_project")


class Issue(Base):
    """问题跟踪模型"""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # 问题基本信息
    issue_code = Column(String(50), unique=True, nullable=False, comment="问题编号")
    title = Column(String(200), nullable=False, comment="问题标题")
    description = Column(Text, nullable=False, comment="问题描述")
    
    # 问题分类
    category = Column(String(50), nullable=False, comment="问题类别")
    subcategory = Column(String(50), comment="问题子类别")
    severity = Column(String(10), default="medium", comment="严重程度：low/medium/high/critical")
    
    # 问题状态
    status = Column(String(20), default="open", comment="状态：open/in_progress/resolved/closed/rejected")
    priority = Column(String(10), default="normal", comment="优先级：low/normal/high/urgent")
    
    # 责任人和时间
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="报告人")
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="负责人")
    due_date = Column(DateTime(timezone=True), comment="截止日期")
    
    # 解决方案
    resolution = Column(Text, comment="解决方案")
    resolution_date = Column(DateTime(timezone=True), comment="解决日期")
    verification_result = Column(Text, comment="验证结果")
    
    # 影响评估
    impact_assessment = Column(Text, comment="影响评估")
    cost_impact = Column(Numeric(15, 2), comment="成本影响")
    schedule_impact = Column(Integer, comment="进度影响(天数)")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), comment="解决时间")
    
    # 关联关系
    project = relationship("Project", back_populates="issues")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assignee_id])


class ProjectComparison(Base):
    """项目比对分析模型"""
    __tablename__ = "project_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    compared_project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # 比对信息
    comparison_type = Column(String(50), nullable=False, comment="比对类型")
    comparison_criteria = Column(Text, comment="比对标准")
    
    # 比对结果
    similarity_score = Column(Integer, comment="相似度分数(0-100)")
    differences = Column(Text, comment="差异分析")
    anomalies = Column(Text, comment="异常发现")
    risk_indicators = Column(Text, comment="风险指标")
    
    # 比对状态
    status = Column(String(20), default="pending", comment="状态：pending/completed/reviewed")
    analyst_id = Column(Integer, ForeignKey("users.id"), comment="分析人员")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    project = relationship("Project", foreign_keys=[project_id], back_populates="comparisons")
    compared_project = relationship("Project", foreign_keys=[compared_project_id], back_populates="compared_projects")
    analyst = relationship("User")