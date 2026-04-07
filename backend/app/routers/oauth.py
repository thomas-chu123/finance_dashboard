"""OAuth 認證路由 - Google OAuth 2.0 支持."""
import logging
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Request, Header
from app.models import (
    GoogleOAuthRequest,
    OAuthTokenResponse,
    GoogleLoginUrlResponse,
    OAuthErrorResponse
)
from app.config import get_settings
from app.database import get_supabase
from app.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, decode_access_token
from app.services.oauth_service import GoogleOAuthService, OAuthStateToken
from app.services.google_oauth import GoogleOAuthUserService

router = APIRouter(prefix="/api/auth/oauth", tags=["oauth"])
logger = logging.getLogger("oauth_router")
settings = get_settings()


@router.get("/google/login-url", response_model=GoogleLoginUrlResponse)
async def get_google_login_url(request: Request):
    """
    獲取 Google 登入 URL.
    
    Returns:
        包含 Google OAuth 登入 URL 和 CSRF 狀態令牌
    """
    try:
        oauth_service = GoogleOAuthService()
        result = oauth_service.get_login_url()
        
        from datetime import datetime, timedelta
        expires_at = (datetime.utcnow() + timedelta(seconds=600)).isoformat()
        
        return GoogleLoginUrlResponse(
            login_url=result["login_url"],
            state=result["state"],
            state_expires_at=expires_at
        )
    except Exception as e:
        logger.error(f"獲取 Google 登入 URL 失敗: {str(e)}")
        raise HTTPException(status_code=400, detail="無法生成登入 URL")


@router.post("/google/callback", response_model=OAuthTokenResponse)
async def google_oauth_callback(
    code: str,
    state: str,
    request: Request
):
    """
    處理 Google OAuth 回調.
    
    Args:
        code: Google 授權碼
        state: CSRF 狀態令牌
    """
    try:
        # 驗證狀態令牌 (CSRF 防護)
        if not OAuthStateToken.validate(state):
            logger.warning(f"無效或過期的狀態令牌: {state[:10]}...")
            raise HTTPException(status_code=400, detail="無效的狀態令牌")
        
        logger.info(f"處理 Google OAuth 回調，授權碼: {code[:10]}...")
        
        # 注：實際的令牌交換應由客戶端直接使用 Google SDK 完成
        # 這裡只處理客戶端已驗證的 ID token
        raise HTTPException(
            status_code=400,
            detail="請使用 /token-exchange 端點交換 Google ID token"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google 回調處理失敗: {str(e)}")
        raise HTTPException(status_code=400, detail="認證失敗")


@router.post("/google/token-exchange", response_model=OAuthTokenResponse)
async def google_token_exchange(body: GoogleOAuthRequest):
    """
    交換 Google ID token 為應用 JWT token.
    
    Args:
        body: 包含 Google ID token
    """
    try:
        if not body.id_token:
            raise HTTPException(status_code=400, detail="缺少 id_token")
        
        logger.info(f"交換 Google token: {body.id_token[:20]}...")
        
        # 驗證 Google ID token
        oauth_service = GoogleOAuthService()
        google_payload = oauth_service.verify_id_token(body.id_token)
        
        if not google_payload:
            logger.warning("Google ID token 驗證失敗")
            raise HTTPException(status_code=401, detail="無效的 Google token")
        
        # 獲取或創建用戶
        try:
            user = GoogleOAuthUserService.get_or_create_user(google_payload)
            is_new_user = False  # TODO: 檢查用戶是否為新建
        except Exception as e:
            logger.error(f"用戶創建失敗: {str(e)}")
            raise HTTPException(status_code=400, detail="用戶創建失敗")
        
        # 生成應用 JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Google token 交換成功，用戶: {user['email']}")
        
        return OAuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user["id"],
            email=user["email"],
            display_name=user.get("display_name"),
            is_new_user=is_new_user,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token 交換失敗: {str(e)}")
        raise HTTPException(status_code=400, detail="Token 交換失敗")
