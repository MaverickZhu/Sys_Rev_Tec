import os
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.document import Document
from app.services.ocr_service import ocr_service
from app.core.config import settings
from app.utils.cache_decorator import cache_medium
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class DocumentService:
    """文档处理服务"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 支持的文件类型
        self.supported_image_types = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.supported_pdf_types = {'.pdf'}
        self.supported_doc_types = {'.doc', '.docx', '.txt', '.rtf'}
        
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
        return Path(filename).suffix.lower() in {'.txt', '.md', '.rtf'}
    
    async def save_uploaded_file(self, file: UploadFile, project_id: int) -> str:
        """保存上传的文件"""
        try:
            # 创建项目目录
            project_dir = self.upload_dir / f"project_{project_id}"
            project_dir.mkdir(exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(file.filename).suffix
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
                    'success': False,
                    'message': f'Unsupported file type for OCR: {document.filename}'
                }
                
        except Exception as e:
            logger.error(f"OCR processing failed for document {document.id}: {e}")
            return {
                'success': False,
                'message': f'OCR processing failed: {str(e)}'
            }
    
    def _process_image_ocr(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理图像文件OCR"""
        try:
            # 使用增强OCR服务进行文本提取
            ocr_result = ocr_service.extract_text(document.file_path)
            
            # 更新文档记录
            document.ocr_text = ocr_result['text']
            document.ocr_engine = ocr_result['engine']
            document.ocr_confidence = int(ocr_result['confidence'] * 100)
            document.is_ocr_processed = True
            document.is_handwritten = ocr_service.detect_handwriting(document.file_path)
            document.ocr_details = json.dumps(ocr_result.get('details', {}), ensure_ascii=False)
            document.processed_at = datetime.utcnow()
            
            # 如果没有提取到文本内容，使用OCR文本
            if not document.extracted_text and document.ocr_text:
                document.extracted_text = document.ocr_text
            
            db.commit()
            
            # 清除相关缓存
            cache_service.clear_pattern("get_ocr_statistics:*", "app")
            
            logger.info(f"Image OCR completed for document {document.id} using {ocr_result['engine']}")
            
            return {
                'success': True,
                'text': ocr_result['text'],
                'engine': ocr_result['engine'],
                'confidence': ocr_result['confidence'],
                'is_handwritten': document.is_handwritten
            }
            
        except Exception as e:
            logger.error(f"Image OCR failed for document {document.id}: {e}")
            raise
    
    def _process_pdf_ocr(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理PDF文件OCR"""
        try:
            # 对于PDF文件，需要先转换为图像再进行OCR
            # 这里可以使用pdf2image库
            try:
                from pdf2image import convert_from_path
                import tempfile
                
                # 转换PDF为图像
                pages = convert_from_path(document.file_path, dpi=200)
                
                all_text = []
                all_confidences = []
                engines_used = []
                
                # 处理每一页
                for i, page in enumerate(pages):
                    # 保存临时图像
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                        page.save(temp_file.name, 'PNG')
                        
                        # 对图像进行OCR
                        ocr_result = ocr_service.extract_text(temp_file.name)
                        
                        if ocr_result['text'].strip():
                            all_text.append(f"--- 第{i+1}页 ---\n{ocr_result['text']}")
                            all_confidences.append(ocr_result['confidence'])
                            engines_used.append(ocr_result['engine'])
                        
                        # 删除临时文件
                        os.unlink(temp_file.name)
                
                # 合并结果
                combined_text = '\n\n'.join(all_text)
                avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
                primary_engine = max(set(engines_used), key=engines_used.count) if engines_used else 'none'
                
                # 更新文档记录
                document.ocr_text = combined_text
                document.ocr_engine = primary_engine
                document.ocr_confidence = int(avg_confidence * 100)
                document.is_ocr_processed = True
                document.is_handwritten = any(ocr_service.detect_handwriting(document.file_path) for _ in range(min(3, len(pages))))  # 检查前3页
                document.ocr_details = json.dumps({
                    'pages_processed': len(pages),
                    'engines_used': engines_used,
                    'page_confidences': all_confidences
                }, ensure_ascii=False)
                document.processed_at = datetime.utcnow()
                
                # 如果没有提取到文本内容，使用OCR文本
                if not document.extracted_text and document.ocr_text:
                    document.extracted_text = document.ocr_text
                
                db.commit()
                
                # 清除相关缓存
                cache_service.clear_pattern("get_ocr_statistics:*", "app")
                
                logger.info(f"PDF OCR completed for document {document.id}, processed {len(pages)} pages")
                
                return {
                    'success': True,
                    'text': combined_text,
                    'engine': primary_engine,
                    'confidence': avg_confidence,
                    'pages_processed': len(pages),
                    'is_handwritten': document.is_handwritten
                }
                
            except ImportError:
                logger.warning("pdf2image not available, cannot process PDF files")
                return {
                    'success': False,
                    'message': 'PDF processing requires pdf2image library. Install with: pip install pdf2image'
                }
                
        except Exception as e:
            logger.error(f"PDF OCR failed for document {document.id}: {e}")
            raise
    
    def _process_text_file(self, document: Document, db: Session) -> Dict[str, Any]:
        """处理文本文件"""
        try:
            # 直接读取文本文件内容
            with open(document.file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            # 更新文档记录
            document.ocr_text = text_content
            document.ocr_engine = 'text_reader'
            document.ocr_confidence = 100  # 文本文件置信度为100%
            document.is_ocr_processed = True
            document.is_handwritten = False  # 文本文件不是手写的
            document.ocr_details = json.dumps({
                'file_type': 'text',
                'encoding': 'utf-8',
                'character_count': len(text_content)
            }, ensure_ascii=False)
            document.processed_at = datetime.utcnow()
            
            # 如果没有提取到文本内容，使用读取的文本
            if not document.extracted_text and document.ocr_text:
                document.extracted_text = document.ocr_text
            
            db.commit()
            
            # 清除相关缓存
            cache_service.clear_pattern("get_ocr_statistics:*", "app")
            
            logger.info(f"Text file processing completed for document {document.id}")
            
            return {
                'success': True,
                'text': text_content,
                'engine': 'text_reader',
                'confidence': 1.0,
                'is_handwritten': False
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(document.file_path, 'r', encoding='gbk') as file:
                    text_content = file.read()
                
                # 更新文档记录（使用gbk编码）
                document.ocr_text = text_content
                document.ocr_engine = 'text_reader'
                document.ocr_confidence = 100
                document.is_ocr_processed = True
                document.is_handwritten = False
                document.ocr_details = json.dumps({
                    'file_type': 'text',
                    'encoding': 'gbk',
                    'character_count': len(text_content)
                }, ensure_ascii=False)
                document.processed_at = datetime.utcnow()
                
                if not document.extracted_text and document.ocr_text:
                    document.extracted_text = document.ocr_text
                
                db.commit()
                
                cache_service.clear_pattern("get_ocr_statistics:*", "app")
                
                logger.info(f"Text file processing completed for document {document.id} using gbk encoding")
                
                return {
                    'success': True,
                    'text': text_content,
                    'engine': 'text_reader',
                    'confidence': 1.0,
                    'is_handwritten': False
                }
                
            except Exception as e:
                logger.error(f"Text file processing failed for document {document.id}: {e}")
                return {
                    'success': False,
                    'message': f'Text file processing failed: {str(e)}'
                }
        
        except Exception as e:
            logger.error(f"Text file processing failed for document {document.id}: {e}")
            return {
                'success': False,
                'message': f'Text file processing failed: {str(e)}'
            }
    
    def batch_process_ocr(self, document_ids: List[int], db: Session) -> Dict[str, Any]:
        """批量处理OCR"""
        results = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for doc_id in document_ids:
            try:
                document = db.query(Document).filter(Document.id == doc_id).first()
                if not document:
                    results['skipped'] += 1
                    results['details'].append({
                        'document_id': doc_id,
                        'status': 'skipped',
                        'message': 'Document not found'
                    })
                    continue
                
                if document.is_ocr_processed:
                    results['skipped'] += 1
                    results['details'].append({
                        'document_id': doc_id,
                        'status': 'skipped',
                        'message': 'Already processed'
                    })
                    continue
                
                # 处理OCR
                result = self.process_document_ocr(document, db)
                
                if result['success']:
                    results['processed'] += 1
                    results['details'].append({
                        'document_id': doc_id,
                        'status': 'success',
                        'engine': result.get('engine'),
                        'confidence': result.get('confidence')
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'document_id': doc_id,
                        'status': 'failed',
                        'message': result.get('message')
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'document_id': doc_id,
                    'status': 'failed',
                    'message': str(e)
                })
                logger.error(f"Failed to process document {doc_id}: {e}")
        
        return results
    
    def get_ocr_statistics(self, db: Session, project_id: Optional[int] = None) -> Dict[str, Any]:
        """获取OCR统计信息"""
        query = db.query(Document)
        
        if project_id:
            query = query.filter(Document.project_id == project_id)
        
        total_docs = query.count()
        ocr_processed = query.filter(Document.is_ocr_processed == True).count()
        handwritten_docs = query.filter(Document.is_handwritten == True).count()
        
        # 按引擎统计
        engine_stats = {}
        for engine in ['tesseract', 'paddleocr', 'trocr']:
            count = query.filter(Document.ocr_engine == engine).count()
            if count > 0:
                engine_stats[engine] = count
        
        # 置信度统计
        from sqlalchemy import func
        confidence_query = query.filter(Document.ocr_confidence.isnot(None))
        
        # 构建置信度查询，应用相同的筛选条件
        avg_confidence_query = db.query(func.avg(Document.ocr_confidence)).filter(
            Document.ocr_confidence.isnot(None)
        )
        if project_id:
            avg_confidence_query = avg_confidence_query.filter(Document.project_id == project_id)
        
        avg_confidence = avg_confidence_query.scalar() or 0
        
        return {
            'total_documents': total_docs,
            'ocr_processed': ocr_processed,
            'ocr_pending': total_docs - ocr_processed,
            'handwritten_documents': handwritten_docs,
            'engine_usage': engine_stats,
            'average_confidence': round(avg_confidence, 2),
            'processing_rate': round((ocr_processed / total_docs * 100), 2) if total_docs > 0 else 0
        }

# 全局文档服务实例
document_service = DocumentService()