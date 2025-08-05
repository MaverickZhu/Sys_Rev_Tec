from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class OCRResult(Base):
    """OCR识别结果模型"""

    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=True, comment="文件存储路径")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    file_type = Column(String(50), nullable=True, comment="文件类型")

    # OCR处理信息
    ocr_engine = Column(
        String(50), nullable=False, default="tesseract", comment="OCR引擎"
    )
    language = Column(String(20), nullable=False, default="chi_sim", comment="识别语言")
    status = Column(String(20), nullable=False, default="pending", comment="处理状态")

    # 识别结果
    extracted_text = Column(Text, nullable=True, comment="提取的文本内容")
    confidence = Column(Float, nullable=True, comment="识别置信度")
    processing_time = Column(Float, nullable=True, comment="处理时间（秒）")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 关联信息
    document_id = Column(
        Integer, ForeignKey("documents.id"), nullable=True, comment="关联文档ID"
    )
    processed_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="处理者ID"
    )

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # 关系
    # document = relationship("Document", back_populates="ocr_results")
    # processor = relationship("User", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<OCRResult(id={self.id}, filename='{self.filename}', status='{self.status}')>"
