"""OAuth2客户端CRUD操作

提供OAuth2客户端和授权码的数据库操作功能
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.oauth2_client import OAuth2Client, OAuth2AuthorizationCode
from app.schemas.oauth2 import OAuth2ClientCreate, OAuth2ClientUpdate
from app.core.auth import get_password_hash
import secrets
import string


class CRUDOAuth2Client(CRUDBase[OAuth2Client, OAuth2ClientCreate, OAuth2ClientUpdate]):
    """OAuth2客户端CRUD操作类"""
    
    def create_client(self, db: Session, *, obj_in: OAuth2ClientCreate) -> OAuth2Client:
        """创建OAuth2客户端
        
        Args:
            db: 数据库会话
            obj_in: 客户端创建数据
            
        Returns:
            OAuth2Client: 创建的客户端对象
        """
        # 生成客户端ID和密钥
        client_id = self._generate_client_id()
        client_secret = self._generate_client_secret()
        
        db_obj = OAuth2Client(
            client_id=client_id,
            client_secret=get_password_hash(client_secret),  # 加密存储
            client_name=obj_in.client_name,
            client_description=obj_in.client_description,
            grant_types=obj_in.grant_types,
            response_types=obj_in.response_types,
            redirect_uris=obj_in.redirect_uris,
            scopes=obj_in.scopes,
            is_confidential=obj_in.is_confidential
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # 返回明文密钥（仅此一次）
        db_obj.plain_client_secret = client_secret
        return db_obj
    
    def get_by_client_id(self, db: Session, *, client_id: str) -> Optional[OAuth2Client]:
        """根据客户端ID获取客户端
        
        Args:
            db: 数据库会话
            client_id: 客户端ID
            
        Returns:
            Optional[OAuth2Client]: 客户端对象或None
        """
        return db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id).first()
    
    def authenticate_client(self, db: Session, *, client_id: str, client_secret: str) -> Optional[OAuth2Client]:
        """验证客户端凭证
        
        Args:
            db: 数据库会话
            client_id: 客户端ID
            client_secret: 客户端密钥
            
        Returns:
            Optional[OAuth2Client]: 验证成功的客户端对象或None
        """
        from app.core.auth import verify_password
        
        client = self.get_by_client_id(db, client_id=client_id)
        if not client:
            return None
        
        if not client.is_active:
            return None
        
        if not verify_password(client_secret, client.client_secret):
            return None
        
        return client
    
    def get_active_clients(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[OAuth2Client]:
        """获取活跃的客户端列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            
        Returns:
            List[OAuth2Client]: 客户端列表
        """
        return (
            db.query(OAuth2Client)
            .filter(OAuth2Client.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def deactivate_client(self, db: Session, *, client_id: str) -> Optional[OAuth2Client]:
        """停用客户端
        
        Args:
            db: 数据库会话
            client_id: 客户端ID
            
        Returns:
            Optional[OAuth2Client]: 更新后的客户端对象或None
        """
        client = self.get_by_client_id(db, client_id=client_id)
        if client:
            client.is_active = False
            db.commit()
            db.refresh(client)
        return client
    
    def _generate_client_id(self) -> str:
        """生成客户端ID"""
        return f"client_{secrets.token_urlsafe(16)}"
    
    def _generate_client_secret(self) -> str:
        """生成客户端密钥"""
        return secrets.token_urlsafe(32)


class CRUDOAuth2AuthorizationCode:
    """OAuth2授权码CRUD操作类"""
    
    def create_authorization_code(
        self, 
        db: Session, 
        *, 
        client_id: str, 
        user_id: int, 
        redirect_uri: str, 
        scopes: List[str],
        expires_in: int = 600  # 10分钟
    ) -> OAuth2AuthorizationCode:
        """创建授权码
        
        Args:
            db: 数据库会话
            client_id: 客户端ID
            user_id: 用户ID
            redirect_uri: 重定向URI
            scopes: 授权范围
            expires_in: 过期时间（秒）
            
        Returns:
            OAuth2AuthorizationCode: 创建的授权码对象
        """
        code = self._generate_authorization_code()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        db_obj = OAuth2AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=expires_at
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_code(self, db: Session, *, code: str) -> Optional[OAuth2AuthorizationCode]:
        """根据授权码获取记录
        
        Args:
            db: 数据库会话
            code: 授权码
            
        Returns:
            Optional[OAuth2AuthorizationCode]: 授权码对象或None
        """
        return db.query(OAuth2AuthorizationCode).filter(OAuth2AuthorizationCode.code == code).first()
    
    def use_authorization_code(
        self, 
        db: Session, 
        *, 
        code: str, 
        client_id: str, 
        redirect_uri: str
    ) -> Optional[OAuth2AuthorizationCode]:
        """使用授权码
        
        Args:
            db: 数据库会话
            code: 授权码
            client_id: 客户端ID
            redirect_uri: 重定向URI
            
        Returns:
            Optional[OAuth2AuthorizationCode]: 授权码对象或None
        """
        auth_code = db.query(OAuth2AuthorizationCode).filter(
            and_(
                OAuth2AuthorizationCode.code == code,
                OAuth2AuthorizationCode.client_id == client_id,
                OAuth2AuthorizationCode.redirect_uri == redirect_uri,
                OAuth2AuthorizationCode.is_used == False
            )
        ).first()
        
        if auth_code and auth_code.is_valid():
            auth_code.is_used = True
            db.commit()
            db.refresh(auth_code)
            return auth_code
        
        return None
    
    def cleanup_expired_codes(self, db: Session) -> int:
        """清理过期的授权码
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 清理的记录数
        """
        current_time = datetime.now(timezone.utc)
        result = db.query(OAuth2AuthorizationCode).filter(
            OAuth2AuthorizationCode.expires_at < current_time
        ).delete()
        db.commit()
        return result
    
    def _generate_authorization_code(self) -> str:
        """生成授权码"""
        return secrets.token_urlsafe(32)


# 创建CRUD实例
oauth2_client = CRUDOAuth2Client(OAuth2Client)
oauth2_authorization_code = CRUDOAuth2AuthorizationCode()