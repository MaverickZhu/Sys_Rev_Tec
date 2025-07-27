from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 文档基本信息
    filename = Column(String(255), nullable=False, comment="文件名")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    file_type = Column(String(50), nullable=False, comment="文件类型")
    mime_type = Column(String(100), comment="MIME类型")
    
    # 文档分类
    document_category = Column(String(50), nullable=False, comment="文档类别")
    document_type = Column(String(100), comment="具体文档类型")
    review_stage = Column(String(20), comment="所属审查阶段")
    
    # 文档状态
    status = Column(String(20), default="uploaded", comment="状态：uploaded/processing/processed/error")
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    is_ocr_processed = Column(Boolean, default=False, comment="是否已OCR处理")
    
    # 文档内容
    extracted_text = Column(Text, comment="提取的文本内容")
    ocr_text = Column(Text, comment="OCR识别的文本")
    ocr_engine = Column(String(20), comment="使用的OCR引擎：tesseract/paddleocr/trocr")
    ocr_confidence = Column(Integer, comment="OCR识别置信度(0-100)")
    is_handwritten = Column(Boolean, default=False, comment="是否包含手写内容")
    ocr_details = Column(Text, comment="OCR详细信息(JSON格式)")
    summary = Column(Text, comment="文档摘要")
    keywords = Column(Text, comment="关键词(JSON格式)")
    
    # AI向量化相关
    is_vectorized = Column(Boolean, default=False, comment="是否已向量化")
    vector_model = Column(String(100), comment="使用的向量化模型")
    embedding_dimension = Column(Integer, comment="向量维度")
    chunk_count = Column(Integer, comment="文本分块数量")
    vectorized_at = Column(DateTime(timezone=True), comment="向量化完成时间")
    vector_status = Column(String(20), default="pending", comment="向量化状态：pending/processing/completed/failed")
    
    # 智能分析结果
    ai_summary = Column(Text, comment="AI生成的摘要")
    ai_keywords = Column(Text, comment="AI提取的关键词(JSON格式)")
    document_classification = Column(String(100), comment="AI文档分类")
    risk_assessment = Column(Text, comment="风险评估结果(JSON格式)")
    compliance_analysis = Column(Text, comment="合规性分析结果(JSON格式)")
    entity_extraction = Column(Text, comment="实体抽取结果(JSON格式)")
    
    # 版本控制
    version = Column(String(20), default="1.0", comment="版本号")
    parent_document_id = Column(Integer, ForeignKey("documents.id"), comment="父文档ID")
    
    # 审查相关
    review_priority = Column(String(10), default="normal", comment="审查优先级：low/normal/high/urgent")
    compliance_status = Column(String(20), comment="合规状态：compliant/non_compliant/pending")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), comment="处理完成时间")
    
    # 关联关系
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")
    parent_document = relationship("Document", remote_side=[id])
    child_documents = relationship("Document", overlaps="parent_document")
    annotations = relationship("DocumentAnnotation", back_populates="document")
    compliance_checks = relationship("ComplianceCheck", back_populates="document")
    ocr_results = relationship("OCRResult", back_populates="document", cascade="all, delete-orphan")


class DocumentAnnotation(Base):
    """文档标注模型"""
    __tablename__ = "document_annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    annotator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 标注信息
    annotation_type = Column(String(50), nullable=False, comment="标注类型")
    content = Column(Text, nullable=False, comment="标注内容")
    position = Column(Text, comment="标注位置(JSON格式)")
    
    # 标注状态
    status = Column(String(20), default="active", comment="状态：active/resolved/deleted")
    importance = Column(String(10), default="normal", comment="重要性：low/normal/high")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    document = relationship("Document", back_populates="annotations")
    annotator = relationship("User")


class ComplianceCheck(Base):
    """合规性检查模型"""
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("compliance_rules.id"), nullable=False)
    
    # 检查结果
    check_result = Column(String(20), nullable=False, comment="检查结果：pass/fail/warning/error")
    confidence_score = Column(Integer, comment="置信度分数(0-100)")
    
    # 检查详情
    matched_content = Column(Text, comment="匹配的内容")
    violation_details = Column(Text, comment="违规详情")
    suggestions = Column(Text, comment="改进建议")
    
    # 检查信息
    check_method = Column(String(50), comment="检查方法：auto/manual/hybrid")
    checker_id = Column(Integer, ForeignKey("users.id"), comment="检查人员ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    document = relationship("Document", back_populates="compliance_checks")
    rule = relationship("ComplianceRule", back_populates="checks")
    checker = relationship("User")


class ComplianceRule(Base):
    """合规规则模型"""
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 规则基本信息
    rule_code = Column(String(50), unique=True, nullable=False, comment="规则编码")
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    
    # 规则分类
    category = Column(String(50), nullable=False, comment="规则类别")
    subcategory = Column(String(50), comment="子类别")
    applicable_stage = Column(String(20), comment="适用阶段")
    
    # 规则内容
    rule_content = Column(Text, nullable=False, comment="规则内容")
    check_pattern = Column(Text, comment="检查模式(正则表达式或关键词)")
    severity = Column(String(10), default="medium", comment="严重程度：low/medium/high/critical")
    
    # 法律依据
    legal_basis = Column(Text, comment="法律依据")
    reference_documents = Column(Text, comment="参考文件")
    
    # 规则状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_automated = Column(Boolean, default=False, comment="是否支持自动检查")
    
    # 版本信息
    version = Column(String(20), default="1.0", comment="版本号")
    effective_date = Column(DateTime(timezone=True), comment="生效日期")
    expiry_date = Column(DateTime(timezone=True), comment="失效日期")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    checks = relationship("ComplianceCheck", back_populates="rule")