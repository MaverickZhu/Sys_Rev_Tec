import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.token_blacklist import TokenBlacklist
from app.schemas.token_blacklist import (
    TokenBlacklistCreate,
    TokenBlacklistQuery,
    TokenBlacklistStats,
    TokenBlacklistUpdate,
)


class CRUDTokenBlacklist(CRUDBase[TokenBlacklist, TokenBlacklistCreate, TokenBlacklistUpdate]):
    """Token黑名单CRUD操作"""

    def create_token_hash(self, token: str) -> str:
        """创建token哈希值"""
        return hashlib.sha256(token.encode()).hexdigest()

    def add_to_blacklist(
        self,
        db: Session,
        *,
        jti: str,
        token: str,
        user_id: Optional[int] = None,
        token_type: str = "access",
        expires_at: datetime,
        reason: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenBlacklist:
        """添加token到黑名单"""
        token_hash = self.create_token_hash(token)
        
        # 检查是否已存在
        existing = db.query(TokenBlacklist).filter(
            or_(
                TokenBlacklist.jti == jti,
                TokenBlacklist.token_hash == token_hash
            )
        ).first()
        
        if existing:
            return existing
        
        db_obj = TokenBlacklist(
            jti=jti,
            token_hash=token_hash,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
            reason=reason,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def is_token_blacklisted(self, db: Session, *, jti: str = None, token: str = None) -> bool:
        """检查token是否在黑名单中"""
        if not jti and not token:
            return False
        
        query = db.query(TokenBlacklist)
        
        if jti:
            query = query.filter(TokenBlacklist.jti == jti)
        elif token:
            token_hash = self.create_token_hash(token)
            query = query.filter(TokenBlacklist.token_hash == token_hash)
        
        return query.first() is not None

    def get_blacklist_info(
        self, db: Session, *, jti: str = None, token: str = None
    ) -> Optional[TokenBlacklist]:
        """获取黑名单信息"""
        if not jti and not token:
            return None
        
        query = db.query(TokenBlacklist)
        
        if jti:
            query = query.filter(TokenBlacklist.jti == jti)
        elif token:
            token_hash = self.create_token_hash(token)
            query = query.filter(TokenBlacklist.token_hash == token_hash)
        
        return query.first()

    def blacklist_user_tokens(
        self,
        db: Session,
        *,
        user_id: int,
        reason: str = "用户注销",
        token_type: Optional[str] = None,
    ) -> int:
        """将用户的所有token加入黑名单（逻辑上，实际需要配合JWT管理）"""
        # 这里只是记录，实际的token失效需要在JWT验证时检查
        # 返回受影响的记录数（这里是模拟）
        return 0

    def cleanup_expired_tokens(self, db: Session) -> int:
        """清理已过期的黑名单token"""
        now = datetime.utcnow()
        result = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).delete()
        db.commit()
        return result

    def get_blacklist_by_query(
        self, db: Session, *, query_params: TokenBlacklistQuery
    ) -> List[TokenBlacklist]:
        """根据查询参数获取黑名单"""
        query = db.query(TokenBlacklist)
        
        # 应用过滤条件
        if query_params.user_id is not None:
            query = query.filter(TokenBlacklist.user_id == query_params.user_id)
        
        if query_params.token_type:
            query = query.filter(TokenBlacklist.token_type == query_params.token_type)
        
        if query_params.reason:
            query = query.filter(TokenBlacklist.reason.ilike(f"%{query_params.reason}%"))
        
        if query_params.ip_address:
            query = query.filter(TokenBlacklist.ip_address == query_params.ip_address)
        
        if query_params.start_date:
            query = query.filter(TokenBlacklist.blacklisted_at >= query_params.start_date)
        
        if query_params.end_date:
            query = query.filter(TokenBlacklist.blacklisted_at <= query_params.end_date)
        
        # 排序和分页
        query = query.order_by(TokenBlacklist.blacklisted_at.desc())
        query = query.offset(query_params.skip).limit(query_params.limit)
        
        return query.all()

    def get_blacklist_count(self, db: Session, *, query_params: TokenBlacklistQuery) -> int:
        """获取黑名单总数"""
        query = db.query(TokenBlacklist)
        
        # 应用相同的过滤条件
        if query_params.user_id is not None:
            query = query.filter(TokenBlacklist.user_id == query_params.user_id)
        
        if query_params.token_type:
            query = query.filter(TokenBlacklist.token_type == query_params.token_type)
        
        if query_params.reason:
            query = query.filter(TokenBlacklist.reason.ilike(f"%{query_params.reason}%"))
        
        if query_params.ip_address:
            query = query.filter(TokenBlacklist.ip_address == query_params.ip_address)
        
        if query_params.start_date:
            query = query.filter(TokenBlacklist.blacklisted_at >= query_params.start_date)
        
        if query_params.end_date:
            query = query.filter(TokenBlacklist.blacklisted_at <= query_params.end_date)
        
        return query.count()

    def get_blacklist_stats(self, db: Session) -> TokenBlacklistStats:
        """获取黑名单统计信息"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 总数
        total_blacklisted = db.query(TokenBlacklist).count()
        
        # 按类型统计
        access_tokens = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_type == "access"
        ).count()
        
        refresh_tokens = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_type == "refresh"
        ).count()
        
        # 今日新增
        today_blacklisted = db.query(TokenBlacklist).filter(
            TokenBlacklist.blacklisted_at >= today_start
        ).count()
        
        # 已过期
        expired_tokens = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).count()
        
        return TokenBlacklistStats(
            total_blacklisted=total_blacklisted,
            access_tokens=access_tokens,
            refresh_tokens=refresh_tokens,
            today_blacklisted=today_blacklisted,
            expired_tokens=expired_tokens,
        )

    def remove_from_blacklist(self, db: Session, *, jti: str) -> bool:
        """从黑名单中移除token"""
        result = db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).delete()
        db.commit()
        return result > 0


token_blacklist = CRUDTokenBlacklist(TokenBlacklist)