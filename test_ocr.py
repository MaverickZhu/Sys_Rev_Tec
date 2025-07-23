#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR功能测试脚本
用于测试PaddleOCR、TrOCR和Tesseract的集成效果
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.ocr_service import ocr_service
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ocr_engines():
    """测试OCR引擎"""
    print("=" * 60)
    print("OCR引擎测试")
    print("=" * 60)
    
    # 检查OCR服务初始化状态
    print(f"\n1. OCR服务状态:")
    available_engines = ocr_service.get_available_engines()
    print(f"   - 可用引擎: {', '.join(available_engines)}")
    print(f"   - PaddleOCR可用: {'paddleocr' in available_engines}")
    print(f"   - TrOCR可用: {'trocr' in available_engines}")
    print(f"   - Tesseract可用: {'tesseract' in available_engines}")
    
    # 显示配置信息
    print(f"\n2. 配置信息:")
    print(f"   - OCR置信度阈值: {settings.OCR_CONFIDENCE_THRESHOLD}")
    print(f"   - 手写检测阈值: {settings.OCR_HANDWRITING_THRESHOLD}")
    print(f"   - 最大图像尺寸: {settings.OCR_MAX_IMAGE_SIZE}")
    print(f"   - PDF DPI: {settings.PDF_DPI}")
    
    # 测试图像预处理
    print(f"\n3. 测试图像预处理功能...")
    try:
        import cv2
        import numpy as np
        
        # 创建测试图像
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_image, 'Test OCR', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 保存测试图像
        test_image_path = "test_image.png"
        cv2.imwrite(test_image_path, test_image)
        
        # 测试预处理
        processed_image = ocr_service.preprocess_image(test_image_path)
        print(f"   ✓ 图像预处理成功，输出尺寸: {processed_image.shape}")
        
        # 测试手写检测
        is_handwritten = ocr_service.detect_handwriting(test_image_path)
        print(f"   ✓ 手写检测完成，结果: {is_handwritten}")
        
        # 清理测试文件
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            
    except Exception as e:
        print(f"   ✗ 图像预处理测试失败: {e}")
    
    print(f"\n4. OCR引擎可用性测试:")
    
    available_engines = ocr_service.get_available_engines()
    
    # 测试Tesseract
    if 'tesseract' in available_engines:
        try:
            # 这里只是测试导入，不进行实际OCR
            import pytesseract
            print(f"   ✓ Tesseract引擎可用")
        except Exception as e:
            print(f"   ✗ Tesseract引擎测试失败: {e}")
    else:
        print(f"   ✗ Tesseract引擎不可用")
    
    # 测试PaddleOCR
    if 'paddleocr' in available_engines:
        try:
            # 这里只是测试导入，不进行实际OCR
            print(f"   ✓ PaddleOCR引擎可用")
        except Exception as e:
            print(f"   ✗ PaddleOCR引擎测试失败: {e}")
    else:
        print(f"   ✗ PaddleOCR引擎不可用")
    
    # 测试TrOCR
    if 'trocr' in available_engines:
        try:
            # 这里只是测试导入，不进行实际OCR
            print(f"   ✓ TrOCR引擎可用")
        except Exception as e:
            print(f"   ✗ TrOCR引擎测试失败: {e}")
    else:
        print(f"   ✗ TrOCR引擎不可用")

def test_with_sample_image():
    """使用示例图像测试OCR"""
    print(f"\n" + "=" * 60)
    print("示例图像OCR测试")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建包含中英文文本的测试图像
        test_image = np.ones((200, 600, 3), dtype=np.uint8) * 255
        
        # 添加中文文本
        cv2.putText(test_image, 'Hello World', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_image, 'OCR Test 123', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_image, 'Government Procurement', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # 保存测试图像
        test_image_path = "sample_test.png"
        cv2.imwrite(test_image_path, test_image)
        
        print(f"\n测试图像已创建: {test_image_path}")
        
        # 执行OCR测试
        available_engines = ocr_service.get_available_engines()
        if available_engines:
            print(f"\n开始OCR识别...")
            result = ocr_service.extract_text(test_image_path)
            
            print(f"\nOCR结果:")
            print(f"   - 使用引擎: {result['engine']}")
            print(f"   - 置信度: {result['confidence']:.2f}")
            print(f"   - 识别文本: {repr(result['text'])}")
            print(f"   - 详细信息: {result.get('details', {})}")
        else:
            print(f"\n⚠️  没有可用的OCR引擎，请安装相关依赖")
        
        # 清理测试文件
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            
    except Exception as e:
        print(f"\n✗ 示例图像OCR测试失败: {e}")
        import traceback
        traceback.print_exc()

def show_installation_guide():
    """显示安装指南"""
    print(f"\n" + "=" * 60)
    print("OCR依赖安装指南")
    print("=" * 60)
    
    print(f"\n如果某些OCR引擎不可用，请按以下步骤安装:")
    
    print(f"\n1. PaddleOCR (推荐用于中文):")
    print(f"   pip install paddlepaddle paddleocr")
    
    print(f"\n2. TrOCR (手写识别):")
    print(f"   pip install transformers torch torchvision")
    
    print(f"\n3. Tesseract (备选方案):")
    print(f"   - Windows: 下载安装 https://github.com/UB-Mannheim/tesseract/wiki")
    print(f"   - pip install pytesseract")
    
    print(f"\n4. 图像处理依赖:")
    print(f"   pip install opencv-python Pillow pdf2image")
    
    print(f"\n5. 完整安装命令:")
    print(f"   pip install -r requirements.txt")

if __name__ == "__main__":
    try:
        print("政府采购项目审查系统 - OCR功能测试")
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        
        # 基础功能测试
        test_ocr_engines()
        
        # 示例图像测试
        test_with_sample_image()
        
        # 安装指南
        show_installation_guide()
        
        print(f"\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print(f"\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()