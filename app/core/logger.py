import logging
import sys
from typing import Optional

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# 创建默认logger
logger = logging.getLogger("cache_system")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取指定名称的logger"""
    if name:
        return logging.getLogger(name)
    return logger
