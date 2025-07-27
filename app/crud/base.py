from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.sql import Select

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# 简单的内存缓存
class SimpleCache:
    def __init__(self, ttl: int = 300):  # 5分钟TTL
        self._cache = {}
        self._ttl = ttl
    
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
        key_data = {
            "model": self.model.__name__,
            "method": method,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
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
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
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
        return None
    
    def get_by_ids(self, db: Session, *, ids: List[Any]) -> List[ModelType]:
        """批量获取记录（优化的IN查询）"""
        if not ids:
            return []
        
        cache_key = self._generate_cache_key("get_by_ids", ids=sorted(ids))
        
        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 使用IN查询批量获取
        result = db.query(self.model).filter(self.model.id.in_(ids)).all()
        
        # 缓存结果
        self._set_cache(cache_key, result)
        
        return result
    
    def count(self, db: Session, **filters) -> int:
        """计数查询（支持缓存）"""
        cache_key = self._generate_cache_key("count", **filters)
        
        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        query = db.query(self.model)
        
        # 应用过滤条件
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        result = query.count()
        
        # 缓存结果
        self._set_cache(cache_key, result)
        
        return result
    
    def exists(self, db: Session, id: Any) -> bool:
        """检查记录是否存在（优化查询）"""
        cache_key = self._generate_cache_key("exists", id=id)
        
        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 使用exists()查询，比count()更高效
        result = db.query(db.query(self.model).filter(self.model.id == id).exists()).scalar()
        
        # 缓存结果
        self._set_cache(cache_key, result)
        
        return result
    
    def bulk_create(self, db: Session, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """批量创建记录（优化性能）"""
        if not objs_in:
            return []
        
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        # 批量插入
        db.add_all(db_objs)
        db.commit()
        
        # 批量刷新
        for db_obj in db_objs:
            db.refresh(db_obj)
        
        # 清除相关缓存
        self._invalidate_cache_pattern(f"{self.model.__name__}")
        
        return db_objs
    
    def bulk_update(self, db: Session, *, updates: List[Dict[str, Any]]) -> int:
        """批量更新记录（优化性能）"""
        if not updates:
            return 0
        
        updated_count = 0
        
        for update_data in updates:
            if "id" not in update_data:
                continue
            
            record_id = update_data.pop("id")
            
            # 使用bulk update
            result = db.query(self.model).filter(self.model.id == record_id).update(update_data)
            updated_count += result
        
        db.commit()
        
        # 清除相关缓存
        self._invalidate_cache_pattern(f"{self.model.__name__}")
        
        return updated_count
    
    def get_paginated(
        self, 
        db: Session, 
        *, 
        page: int = 1, 
        page_size: int = 20,
        order_by: str = "id",
        order_desc: bool = False,
        **filters
    ) -> Dict[str, Any]:
        """分页查询（支持缓存和排序）"""
        cache_key = self._generate_cache_key(
            "get_paginated", 
            page=page, 
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc,
            **filters
        )
        
        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        query = db.query(self.model)
        
        # 应用过滤条件
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.filter(getattr(self.model, field) == value)
        
        # 计算总数
        total = query.count()
        
        # 应用排序
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        # 应用分页
        skip = (page - 1) * page_size
        items = query.offset(skip).limit(page_size).all()
        
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        result = {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
        # 缓存结果
        self._set_cache(cache_key, result)
        
        return result