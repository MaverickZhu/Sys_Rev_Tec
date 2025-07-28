#!/usr/bin/env python3
"""
OCR 服务主程序
独立的OCR处理服务，通过Redis队列接收任务
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict

import redis

# 添加app目录到Python路径
sys.path.append("/app")
sys.path.append("/app/app")

from app.services.ocr_service import ocr_service

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OCRWorker:
    """OCR工作进程"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.queue_name = os.getenv("OCR_QUEUE_NAME", "ocr_tasks")
        self.redis_client = None
        self.connect_redis()

    def connect_redis(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            time.sleep(5)
            self.connect_redis()

    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理OCR任务"""
        try:
            image_path = task_data.get("image_path")
            task_id = task_data.get("task_id")

            logger.info(f"Processing OCR task {task_id} for image: {image_path}")

            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # 执行OCR
            result = ocr_service.extract_text(image_path)

            logger.info(f"OCR task {task_id} completed successfully")
            return {"status": "success", "task_id": task_id, "result": result}

        except Exception as e:
            logger.error(f"Error processing OCR task: {e}")
            return {
                "status": "error",
                "task_id": task_data.get("task_id"),
                "error": str(e),
            }

    def run(self):
        """运行OCR工作进程"""
        logger.info("Starting OCR worker...")

        while True:
            try:
                # 从Redis队列获取任务
                task_data = self.redis_client.blpop(self.queue_name, timeout=10)

                if task_data:
                    queue_name, task_json = task_data
                    task = json.loads(task_json)

                    # 处理任务
                    result = self.process_task(task)

                    # 将结果存储到Redis
                    result_key = f"ocr_result:{task['task_id']}"
                    self.redis_client.setex(
                        result_key,
                        3600,
                        json.dumps(result),  # 1小时过期
                    )

                else:
                    # 没有任务时短暂休息
                    time.sleep(1)

            except redis.ConnectionError:
                logger.error("Redis connection lost, reconnecting...")
                self.connect_redis()
            except Exception as e:
                logger.error(f"Unexpected error in OCR worker: {e}")
                time.sleep(5)


def main():
    """主函数"""
    logger.info("Starting OCR Service...")

    # 等待Redis服务可用
    max_retries = 30
    for i in range(max_retries):
        try:
            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0")
            )
            redis_client.ping()
            logger.info("Redis is available")
            break
        except Exception:
            logger.warning(f"Waiting for Redis... ({i + 1}/{max_retries})")
            time.sleep(2)
    else:
        logger.error("Redis is not available after maximum retries")
        sys.exit(1)

    # 启动OCR工作进程
    worker = OCRWorker()
    worker.run()


if __name__ == "__main__":
    main()
