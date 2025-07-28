#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务模块
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EnhancedOCRService:
    """简化的OCR服务,用于测试"""

    def __init__(self):
        logger.info("OCR Service initialized (mock mode)")

    def detect_handwriting(self, image_path: str) -> bool:
        """检测图像是否包含手写内容(mock实现)"""
        return False

    def get_available_engines(self) -> List[str]:
        """获取可用的OCR引擎列表(模拟实现)"""
        logger.info("Getting available OCR engines (mock)")
        return ["mock_ocr"]

    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """提取文本(mock实现)"""
        return {
            "text": "这是模拟的OCR文本内容",
            "confidence": 0.95,
            "engine": "mock_ocr",
            "details": {},
        }

    def ocr_with_tesseract(self, image_path: str) -> Dict[str, Any]:
        """使用Tesseract进行OCR(mock实现)"""
        return self.extract_text(image_path)

    def ocr_with_paddle(self, image_path: str) -> Dict[str, Any]:
        """使用PaddleOCR进行OCR(mock实现)"""
        return self.extract_text(image_path)

    def ocr_with_trocr(self, image_path: str) -> Dict[str, Any]:
        """使用TrOCR进行手写文本识别(mock实现)"""
        return self.extract_text(image_path)

    def auto_select_engine(self, image_path: str) -> str:
        """自动选择最佳OCR引擎(mock实现)"""
        return "mock_ocr"

    def extract_text_with_auto_engine(self, image_path: str) -> Dict[str, Any]:
        """使用自动选择的引擎提取文本(mock实现)"""
        return self.extract_text(image_path)


# 全局OCR服务实例
ocr_service = EnhancedOCRService()
