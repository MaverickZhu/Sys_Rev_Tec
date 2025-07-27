import random
import string
from typing import Dict, Any


def random_lower_string(length: int = 32) -> str:
    """生成随机小写字符串"""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    """生成随机邮箱地址"""
    return f"{random_lower_string()}@{random_lower_string()}.com"


def random_password() -> str:
    """生成随机密码"""
    return random_lower_string(12)


def random_phone() -> str:
    """生成随机手机号"""
    return f"1{''.join(random.choices(string.digits, k=10))}"


def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """生成随机浮点数"""
    return random.uniform(min_val, max_val)


def random_int(min_val: int = 1, max_val: int = 100) -> int:
    """生成随机整数"""
    return random.randint(min_val, max_val)


def random_bool() -> bool:
    """生成随机布尔值"""
    return random.choice([True, False])


def random_choice(choices: list) -> Any:
    """从列表中随机选择一个元素"""
    return random.choice(choices)


def random_dict(keys: list, value_generator=None) -> Dict[str, Any]:
    """生成随机字典"""
    if value_generator is None:
        value_generator = lambda: random_lower_string()
    
    return {key: value_generator() for key in keys}