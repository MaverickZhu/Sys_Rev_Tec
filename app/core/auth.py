from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer()


class AuthManager:
    """认证管理器

    提供JWT token生成、验证和密码处理功能
    """

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            bool: 密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希

        Args:
            password: 明文密码

        Returns:
            str: 哈希密码
        """
        return pwd_context.hash(password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量

        Returns:
            str: JWT访问令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",
                "iss": "sys-rev-tec",
                "aud": "sys-rev-tec-users",
            }
        )

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量

        Returns:
            str: JWT刷新令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh",
                "iss": "sys-rev-tec",
                "aud": "sys-rev-tec-users",
            }
        )

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """验证JWT令牌

        Args:
            token: JWT令牌
            token_type: 令牌类型 (access/refresh)

        Returns:
            dict: 解码后的令牌数据

        Raises:
            HTTPException: 令牌无效时抛出异常
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="sys-rev-tec-users",
                issuer="sys-rev-tec",
            )

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def extract_token_from_credentials(
        self, credentials: HTTPAuthorizationCredentials
    ) -> str:
        """从认证凭据中提取令牌

        Args:
            credentials: HTTP认证凭据

        Returns:
            str: JWT令牌

        Raises:
            HTTPException: 认证方案不正确时抛出异常
        """
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return credentials.credentials

    def create_token_pair(self, user_data: dict) -> dict:
        """创建访问令牌和刷新令牌对

        Args:
            user_data: 用户数据

        Returns:
            dict: 包含访问令牌和刷新令牌的字典
        """
        access_token = self.create_access_token(data=user_data)
        refresh_token = self.create_refresh_token(data={"sub": user_data.get("sub")})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }


# 全局认证管理器实例
auth_manager = AuthManager()


# 便捷函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return auth_manager.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return auth_manager.get_password_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    return auth_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    return auth_manager.create_refresh_token(data, expires_delta)


def verify_token(token: str, token_type: str = "access") -> dict:
    """验证令牌"""
    return auth_manager.verify_token(token, token_type)


def create_token_pair(user_data: dict) -> dict:
    """创建令牌对"""
    return auth_manager.create_token_pair(user_data)
