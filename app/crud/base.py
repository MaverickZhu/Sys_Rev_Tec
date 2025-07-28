import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SimpleCache:
    """简单的内存缓存实现"""

    def __init__(self, default_ttl: int = 300):
        self._cache = {}
        self._ttl = default_ttl

    def get(self, key: str) -> Any:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._ttl):
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, datetime.now())

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()


# 全局缓存实例
cache = SimpleCache()


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.cache_enabled = True
        self.cache_ttl = 300  # 5分钟

    def _generate_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = {"model": self.model.__name__, "method": method, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        # 使用SHA256哈希（用于缓存键，非安全用途）
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    def _get_from_cache(self, cache_key: str) -> Any:
        """从缓存获取数据"""
        if not self.cache_enabled:
            return None
        return cache.get(cache_key)

    def _set_cache(self, cache_key: str, value: Any) -> None:
        """设置缓存"""
        if self.cache_enabled:
            cache.set(cache_key, value)

    def _invalidate_cache_pattern(self, pattern: str) -> None:
        """根据模式清除缓存"""
        # 简单实现：清除所有相关模型的缓存
        cache.clear()

    def enable_cache(self, ttl: int = 300) -> None:
        """启用缓存"""
        self.cache_enabled = True
        self.cache_ttl = ttl

    def disable_cache(self) -> None:
        """禁用缓存"""
        self.cache_enabled = False

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """获取单个记录（支持缓存）"""
        cache_key = self._generate_cache_key("get", id=id)

        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 从数据库查询
        result = db.query(self.model).filter(self.model.id == id).first()

        # 缓存结果
        if result:
            self._set_cache(cache_key, result)

        return result

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """获取多个记录（支持缓存）"""
        cache_key = self._generate_cache_key("get_multi", skip=skip, limit=limit)

        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 从数据库查询
        result = db.query(self.model).offset(skip).limit(limit).all()

        # 缓存结果
        self._set_cache(cache_key, result)

        return result

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建记录（自动清除相关缓存）"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # 清除相关缓存
        self._invalidate_cache_pattern(f"{self.model.__name__}")

        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """更新记录（自动清除相关缓存）"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field) and update_data[field] is not None:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # 清除相关缓存
        self._invalidate_cache_pattern(f"{self.model.__name__}")

        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """删除记录（自动清除相关缓存）"""
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()

            # 清除相关缓存
            self._invalidate_cache_pattern(f"{self.model.__name__}")

        return obj
