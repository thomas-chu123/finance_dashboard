"""Google OAuth 2.0 服務 - 令牌驗證、交換和管理."""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from app.config import get_settings

logger = logging.getLogger("oauth_service")
settings = get_settings()


class OAuthStateToken:
    """OAuth 狀態令牌管理 (CSRF 防護)."""
    
    # 簡單的內存存儲 (生產環境建議使用 Redis)
    _state_store: Dict[str, Dict[str, Any]] = {}
    STATE_TOKEN_EXPIRY = 600  # 10 分鐘
    
    @classmethod
    def generate(cls) -> str:
        """生成安全的狀態令牌."""
        state = secrets.token_urlsafe(32)
        cls._state_store[state] = {
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=cls.STATE_TOKEN_EXPIRY)
        }
        logger.debug(f"生成狀態令牌: {state[:10]}...")
        return state
    
    @classmethod
    def validate(cls, state: str) -> bool:
        """驗證狀態令牌是否有效且未過期."""
        if state not in cls._state_store:
            logger.warning(f"無效狀態令牌: {state[:10]}...")
            return False
        
        token_data = cls._state_store[state]
        if datetime.utcnow() > token_data["expires_at"]:
            logger.warning(f"狀態令牌已過期: {state[:10]}...")
            del cls._state_store[state]
            return False
        
        # 使用後刪除令牌
        del cls._state_store[state]
        logger.debug(f"狀態令牌驗證成功: {state[:10]}...")
        return True


class GoogleOAuthService:
    """Google OAuth 2.0 服務."""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.oauth_redirect_uri
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
        logger.info("Google OAuth 服務已初始化")
    
    def get_login_url(self) -> Dict[str, str]:
        """生成 Google 登入 URL."""
        state = OAuthStateToken.generate()
        
        # Google OAuth URL
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={'+'.join(self.scopes)}"
            f"&state={state}"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        
        logger.info(f"生成登入 URL，state: {state[:10]}...")
        return {"login_url": google_auth_url, "state": state}
    
    def verify_id_token(self, token: str) -> Optional[Dict[str, Any]]:
        """驗證 Google ID Token."""
        try:
            payload = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id
            )
            logger.info(f"ID Token 驗證成功，用戶: {payload.get('email')}")
            return payload
        except ValueError as e:
            logger.error(f"ID Token 驗證失敗: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"驗證過程中發生錯誤: {str(e)}")
            return None
