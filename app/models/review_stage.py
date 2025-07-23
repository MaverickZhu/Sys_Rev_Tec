from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class ReviewStage(Base):
    """审查阶段模型"""
    __tablename__ = "review_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="阶段名称")
    description = Column(Text, comment="阶段描述")
    order_index = Column(Integer, nullable=False, comment="阶段顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    review_points = relationship("ReviewPoint", back_populates="stage")
    project_reviews = relationship("ProjectReview", back_populates="stage")


class ReviewPoint(Base):
    """审查要点模型"""
    __tablename__ = "review_points"
    
    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("review_stages.id"), nullable=False)
    code = Column(String(20), unique=True, nullable=False, comment="要点编码")
    title = Column(String(200), nullable=False, comment="要点标题")
    description = Column(Text, comment="要点描述")
    review_type = Column(String(20), nullable=False, comment="审查类型：manual/auto/both")
    is_required = Column(Boolean, default=True, comment="是否必审")
    risk_level = Column(String(10), default="medium", comment="风险等级：low/medium/high")
    order_index = Column(Integer, nullable=False, comment="要点顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 审查标准和依据
    review_criteria = Column(Text, comment="审查标准")
    legal_basis = Column(Text, comment="法律依据")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    stage = relationship("ReviewStage", back_populates="review_points")
    review_results = relationship("ReviewResult", back_populates="review_point")


class ProjectReview(Base):
    """项目审查记录模型"""
    __tablename__ = "project_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("review_stages.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String(20), default="pending", comment="审查状态：pending/in_progress/completed/rejected")
    start_date = Column(DateTime(timezone=True), comment="开始时间")
    end_date = Column(DateTime(timezone=True), comment="结束时间")
    
    # 审查结果统计
    total_points = Column(Integer, default=0, comment="总要点数")
    completed_points = Column(Integer, default=0, comment="已完成要点数")
    passed_points = Column(Integer, default=0, comment="通过要点数")
    failed_points = Column(Integer, default=0, comment="未通过要点数")
    
    # 审查意见
    review_opinion = Column(Text, comment="审查意见")
    conclusion = Column(String(20), comment="审查结论：pass/fail/conditional_pass")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    project = relationship("Project", back_populates="reviews")
    stage = relationship("ReviewStage", back_populates="project_reviews")
    reviewer = relationship("User")
    review_results = relationship("ReviewResult", back_populates="project_review")


class ReviewResult(Base):
    """审查结果模型"""
    __tablename__ = "review_results"
    
    id = Column(Integer, primary_key=True, index=True)
    project_review_id = Column(Integer, ForeignKey("project_reviews.id"), nullable=False)
    review_point_id = Column(Integer, ForeignKey("review_points.id"), nullable=False)
    
    result = Column(String(20), nullable=False, comment="审查结果：pass/fail/na/pending")
    score = Column(Integer, comment="评分")
    findings = Column(Text, comment="发现的问题")
    evidence = Column(Text, comment="证据材料")
    recommendations = Column(Text, comment="整改建议")
    
    # 审查人员和时间
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    review_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # 整改状态
    rectification_status = Column(String(20), default="pending", comment="整改状态：pending/in_progress/completed")
    rectification_deadline = Column(DateTime(timezone=True), comment="整改期限")
    rectification_result = Column(Text, comment="整改结果")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    project_review = relationship("ProjectReview", back_populates="review_results")
    review_point = relationship("ReviewPoint", back_populates="review_results")
    reviewer = relationship("User")