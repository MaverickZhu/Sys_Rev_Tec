#!/usr/bin/env python3

from app.services.document_service import document_service
from app.db.session import SessionLocal
import traceback

def test_cache_issue():
    db = SessionLocal()
    try:
        print("测试直接调用 get_ocr_statistics...")
        result = document_service.get_ocr_statistics(db)
        print("成功:", result)
    except Exception as e:
        print("错误:", e)
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_cache_issue()