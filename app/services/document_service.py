#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档服务模块
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from pdf2image import convert_from_path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.models.document import Document
from app.services.cache_service import cache_service
from app.services.ocr_service import ocr_service


class DocumentService:
    """文档服务类"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

        # 支持的文件类型
        self.supported_image_types = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
        self.supported_pdf_types = {".pdf"}
        self.supported_doc_types = {".doc", ".docx", ".txt", ".rtf"}

    def is_image_file(self, filename: str) -> bool:
        """检查是否为图像文件"""
        return Path(filename).suffix.lower() in self.supported_image_types

    def is_pdf_file(self, filename: str) -> bool:
        """检查是否为PDF文件"""
        return Path(filename).suffix.lower() in self.supported_pdf_types

    def is_document_file(self, filename: str) -> bool:
        """检查是否为文档文件"""
        return Path(filename).suffix.lower() in self.supported_doc_types

    def is_text_file(self, filename: str) -> bool:
        """检查是否为文本文件"""
        return Path(filename).suffix.lower() in {".txt", ".md", ".rtf"}

    async def save_uploaded_file(self, file: UploadFile, project_id: int) -> str:
        """保存上传的文件"""
        try:
            # 创建项目目录
            project_dir = self.upload_dir / f"project_{project_id}"
            project_dir.mkdir(exist_ok=True)

            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{file.filename}"
            file_path = project_dir / unique_filename

            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            logger.info(f"File saved: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")
            raise

    def process_document_ocr(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理文档OCR"""
        try:
            file_path = document.file_path

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # 根据文件类型选择处理方式
            if self.is_image_file(document.filename):
                return self._process_image_ocr(document, db)
            elif self.is_pdf_file(document.filename):
                return self._process_pdf_ocr(document, db)
            elif self.is_text_file(document.filename):
                return self._process_text_file(document, db)
            else:
                logger.warning(f"Unsupported file type for OCR: {document.filename}")
                return {
                    "success": False,
                    "message": (f"Unsupported file type for OCR: {document.filename}"),
                }

        except Exception as e:
            logger.error(f"OCR processing failed for document {document.id}: {e}")
            return {"success": False, "message": f"OCR processing failed: {str(e)}"}

    def _process_image_ocr(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理图像文件OCR"""
        try:
            # 使用增强OCR服务进行文本提取
            ocr_result = ocr_service.extract_text(document.file_path)

            # 更新文档记录
            document.ocr_text = ocr_result["text"]
            document.ocr_engine = ocr_result["engine"]
            document.ocr_confidence = int(ocr_result["confidence"] * 100)
            document.is_ocr_processed = True
            document.is_handwritten = ocr_service.detect_handwriting(document.file_path)
            document.ocr_details = json.dumps(
                ocr_result.get("details", {}), ensure_ascii=False
            )
            document.processed_at = datetime.utcnow()

            # 如果没有提取到文本内容,使用OCR文本
            if not document.extracted_text and document.ocr_text:
                document.extracted_text = document.ocr_text

            db.commit()

            # 清除相关缓存
            cache_service.clear_pattern("get_ocr_statistics:*", "app")

            logger.info(
                f"Image OCR completed for document {document.id} "
                f"using {ocr_result['engine']}"
            )

            return {
                "success": True,
                "text": ocr_result["text"],
                "engine": ocr_result["engine"],
                "confidence": ocr_result["confidence"],
                "is_handwritten": document.is_handwritten,
            }

        except Exception as e:
            logger.error(f"Image OCR failed for document {document.id}: {e}")
            raise

    def _process_pdf_ocr(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理PDF文件OCR"""
        try:
            # 对于PDF文件,需要先转换为图像再进行OCR
            # 这里可以使用pdf2image库
            try:
                # 转换PDF为图像
                pages = convert_from_path(document.file_path, dpi=200)

                all_text = []
                all_confidences = []
                engines_used = []

                # 处理每一页
                for i, page in enumerate(pages):
                    # 保存临时图像
                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as temp_file:
                        page.save(temp_file.name, "PNG")

                        # 对图像进行OCR
                        ocr_result = ocr_service.extract_text(temp_file.name)

                        if ocr_result["text"].strip():
                            all_text.append(
                                f"--- 第{i + 1}页 ---\n{ocr_result['text']}"
                            )
                            all_confidences.append(ocr_result["confidence"])
                            engines_used.append(ocr_result["engine"])

                        # 删除临时文件
                        os.unlink(temp_file.name)

                # 合并结果
                combined_text = "\n\n".join(all_text)
                avg_confidence = (
                    sum(all_confidences) / len(all_confidences)
                    if all_confidences
                    else 0
                )
                primary_engine = (
                    max(set(engines_used), key=engines_used.count)
                    if engines_used
                    else "none"
                )

                # 更新文档记录
                document.ocr_text = combined_text
                document.ocr_engine = primary_engine
                document.ocr_confidence = int(avg_confidence * 100)
                document.is_ocr_processed = True
                document.is_handwritten = any(
                    ocr_service.detect_handwriting(temp_file.name) for temp_file in []
                )
                document.ocr_details = json.dumps(
                    {
                        "pages_processed": len(pages),
                        "engines_used": engines_used,
                        "avg_confidence": avg_confidence,
                    },
                    ensure_ascii=False,
                )
                document.processed_at = datetime.utcnow()

                # 如果没有提取到文本内容,使用OCR文本
                if not document.extracted_text and document.ocr_text:
                    document.extracted_text = document.ocr_text

                db.commit()

                # 清除相关缓存
                cache_service.clear_pattern("get_ocr_statistics:*", "app")

                logger.info(
                    f"PDF OCR completed for document {document.id} "
                    f"({len(pages)} pages) using {primary_engine}"
                )

                return {
                    "success": True,
                    "text": combined_text,
                    "engine": primary_engine,
                    "confidence": avg_confidence,
                    "pages_processed": len(pages),
                }

            except ImportError:
                logger.error("pdf2image library not installed")
                return {
                    "success": False,
                    "message": "PDF processing requires pdf2image library",
                }

        except Exception as e:
            logger.error(f"PDF OCR failed for document {document.id}: {e}")
            raise

    def _process_text_file(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理文本文件"""
        try:
            with open(document.file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            # 更新文档记录
            document.extracted_text = text_content
            document.is_ocr_processed = True
            document.ocr_engine = "text_extraction"
            document.ocr_confidence = 100
            document.processed_at = datetime.utcnow()

            db.commit()

            logger.info(f"Text file processed for document {document.id}")

            return {
                "success": True,
                "text": text_content,
                "engine": "text_extraction",
                "confidence": 1.0,
            }

        except Exception as e:
            logger.error(f"Text file processing failed for document {document.id}: {e}")
            raise

    def get_document_stats(self, db: Session) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            total_docs = db.query(Document).count()
            processed_docs = (
                db.query(Document).filter(Document.is_ocr_processed.is_(True)).count()
            )
            return {
                "total_documents": total_docs,
                "processed_documents": processed_docs,
                "processing_rate": (
                    processed_docs / total_docs * 100 if total_docs > 0 else 0
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get document stats: {e}")
            return {"error": str(e)}


# 全局文档服务实例
document_service = DocumentService()
