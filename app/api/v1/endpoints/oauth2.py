"""OAuth2 API端点

提供OAuth2授权服务器的API接口
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.oauth2 import oauth2_server
from app.models.user import User
from app.schemas.oauth2 import (
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    OAuth2ClientWithSecret,
    OAuth2ClientUpdate,
    OAuth2AuthorizeRequest,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
    OAuth2ErrorResponse,
    OAuth2ScopeList,
    OAuth2Scope
)
from app.crud.crud_oauth2_client import oauth2_client

router = APIRouter()
security = HTTPBasic()


@router.post("/clients", response_model=OAuth2ClientWithSecret)
def create_oauth2_client(
    *,
    db: Session = Depends(deps.get_db),
    client_in: OAuth2ClientCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """创建OAuth2客户端
    
    需要管理员权限
    """
    if not current_user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    client = oauth2_client.create_client(db=db, obj_in=client_in)
    
    # 构建响应，包含明文密钥（仅此一次）
    response_data = OAuth2ClientWithSecret(
        id=client.id,
        client_id=client.client_id,
        client_secret=getattr(client, 'plain_client_secret', ''),
        client_name=client.client_name,
        client_description=client.client_description,
        grant_types=client.grant_types,
        response_types=client.response_types,
        redirect_uris=client.redirect_uris,
        scopes=client.scopes,
        is_confidential=client.is_confidential,
        is_active=client.is_active,
        created_at=client.created_at,
        updated_at=client.updated_at
    )
    
    return response_data


@router.get("/clients", response_model=List[OAuth2ClientResponse])
def list_oauth2_clients(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """获取OAuth2客户端列表
    
    需要管理员权限
    """
    if not current_user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    clients = oauth2_client.get_active_clients(db, skip=skip, limit=limit)
    return clients


@router.get("/clients/{client_id}", response_model=OAuth2ClientResponse)
def get_oauth2_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """获取OAuth2客户端详情
    
    需要管理员权限
    """
    if not current_user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    client = oauth2_client.get_by_client_id(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户端不存在"
        )
    
    return client


@router.put("/clients/{client_id}", response_model=OAuth2ClientResponse)
def update_oauth2_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: str,
    client_in: OAuth2ClientUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """更新OAuth2客户端
    
    需要管理员权限
    """
    if not current_user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    client = oauth2_client.get_by_client_id(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户端不存在"
        )
    
    client = oauth2_client.update(db, db_obj=client, obj_in=client_in)
    return client


@router.delete("/clients/{client_id}")
def deactivate_oauth2_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """停用OAuth2客户端
    
    需要管理员权限
    """
    if not current_user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    client = oauth2_client.deactivate_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户端不存在"
        )
    
    return {"message": "客户端已停用"}


@router.get("/authorize")
def authorize_get(
    response_type: str = Query(..., description="响应类型"),
    client_id: str = Query(..., description="客户端ID"),
    redirect_uri: str = Query(..., description="重定向URI"),
    scope: str = Query(None, description="权限范围"),
    state: str = Query(None, description="状态参数"),
    db: Session = Depends(deps.get_db),
) -> HTMLResponse:
    """OAuth2授权页面（GET请求）
    
    显示授权确认页面
    """
    # 验证客户端
    client = oauth2_client.get_by_client_id(db, client_id=client_id)
    if not client or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的客户端"
        )
    
    # 验证重定向URI
    if not client.check_redirect_uri(redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的重定向URI"
        )
    
    # 解析权限范围
    scopes = scope.split() if scope else []
    scope_descriptions = []
    for s in scopes:
        if s in oauth2_server.get_supported_scopes():
            scope_descriptions.append({
                "name": s,
                "description": oauth2_server.get_supported_scopes()[s]
            })
    
    # 构建授权页面HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>授权确认</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 500px; margin: 0 auto; }}
            .client-info {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .scopes {{ margin: 20px 0; }}
            .scope-item {{ margin: 10px 0; padding: 10px; background: #e8f4fd; border-radius: 3px; }}
            .buttons {{ text-align: center; margin-top: 30px; }}
            .btn {{ padding: 10px 20px; margin: 0 10px; border: none; border-radius: 3px; cursor: pointer; }}
            .btn-approve {{ background: #007bff; color: white; }}
            .btn-deny {{ background: #6c757d; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>授权确认</h2>
            <div class="client-info">
                <h3>{client.client_name}</h3>
                <p>{client.client_description or '该应用请求访问您的账户'}</p>
            </div>
            
            {f'''
            <div class="scopes">
                <h4>请求的权限：</h4>
                {''.join([f'<div class="scope-item"><strong>{s["name"]}</strong>: {s["description"]}</div>' for s in scope_descriptions])}
            </div>
            ''' if scope_descriptions else ''}
            
            <form method="post" action="/api/v1/oauth2/authorize">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope or ''}">
                <input type="hidden" name="state" value="{state or ''}">
                
                <div class="buttons">
                    <button type="submit" name="action" value="approve" class="btn btn-approve">授权</button>
                    <button type="submit" name="action" value="deny" class="btn btn-deny">拒绝</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/authorize")
def authorize_post(
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(None),
    state: str = Form(None),
    action: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> RedirectResponse:
    """OAuth2授权处理（POST请求）
    
    处理用户的授权决定
    """
    # 构建授权请求对象
    auth_request = OAuth2AuthorizeRequest(
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state
    )
    
    if action == "deny":
        # 用户拒绝授权
        error_params = "error=access_denied&error_description=用户拒绝授权"
        if state:
            error_params += f"&state={state}"
        redirect_url = f"{redirect_uri}?{error_params}"
        return RedirectResponse(url=redirect_url)
    
    elif action == "approve":
        # 用户同意授权
        redirect_url, error = oauth2_server.authorize(db, auth_request, current_user)
        return RedirectResponse(url=redirect_url)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的操作"
        )


@router.post("/token", response_model=OAuth2TokenResponse)
def token(
    grant_type: str = Form(...),
    code: str = Form(None),
    redirect_uri: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    refresh_token: str = Form(None),
    username: str = Form(None),
    password: str = Form(None),
    scope: str = Form(None),
    db: Session = Depends(deps.get_db),
    credentials: HTTPBasicCredentials = Depends(security),
) -> Any:
    """OAuth2令牌端点
    
    处理各种授权类型的令牌请求
    """
    # 如果使用HTTP Basic认证，优先使用Basic认证的凭证
    if credentials.username and credentials.password:
        client_id = credentials.username
        client_secret = credentials.password
    
    # 构建令牌请求对象
    token_request = OAuth2TokenRequest(
        grant_type=grant_type,
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        username=username,
        password=password,
        scope=scope
    )
    
    # 处理令牌请求
    return oauth2_server.token(db, token_request)


@router.get("/scopes", response_model=OAuth2ScopeList)
def get_supported_scopes() -> Any:
    """获取支持的OAuth2权限范围"""
    scopes_dict = oauth2_server.get_supported_scopes()
    scopes = [
        OAuth2Scope(name=name, description=description)
        for name, description in scopes_dict.items()
    ]
    return OAuth2ScopeList(scopes=scopes)


@router.get("/.well-known/oauth-authorization-server")
def oauth2_metadata() -> Any:
    """OAuth2授权服务器元数据
    
    符合RFC 8414标准
    """
    from app.core.config import settings
    
    base_url = f"http://localhost:{settings.PORT or 8000}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/api/v1/oauth2/authorize",
        "token_endpoint": f"{base_url}/api/v1/oauth2/token",
        "scopes_supported": list(oauth2_server.get_supported_scopes().keys()),
        "response_types_supported": oauth2_server.SUPPORTED_RESPONSE_TYPES,
        "grant_types_supported": oauth2_server.SUPPORTED_GRANT_TYPES,
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post"
        ],
        "code_challenge_methods_supported": ["S256"],
        "service_documentation": f"{base_url}/docs"
    }