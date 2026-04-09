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


@router.api_route("/google/callback", methods=["GET", "POST"])
async def google_oauth_callback(
    code: str = None,
    state: str = None,
    request: Request = None
):
    """
    處理 Google OAuth 回調 - 支持 GET 和 POST 方法.
    
    GET: Google 授權重定向用
    POST: 備用端點
    
    Args:
        code: Google 授權碼
        state: CSRF 狀態令牌
    """
    try:
        # ===== 1. 接收回調參數 =====
        logger.info(f"[OAUTH_CALLBACK] 開始處理回調")
        logger.info(f"[OAUTH_CALLBACK] 請求方法: {request.method if request else 'Unknown'}")
        logger.info(f"[OAUTH_CALLBACK] 接收到 code: {code[:20] if code else 'None'}...")
        logger.info(f"[OAUTH_CALLBACK] 接收到 state: {state[:20] if state else 'None'}...")
        
        # 驗證傳入參數
        if not code or not state:
            logger.error(f"[OAUTH_CALLBACK] ❌ 缺少授權碼或狀態令牌 | code={bool(code)}, state={bool(state)}")
            raise HTTPException(status_code=400, detail="缺少授權碼或狀態令牌")
        
        logger.info(f"[OAUTH_CALLBACK] ✅ 參數驗證通過")
        
        # ===== 2. 驗證狀態令牌 (CSRF 防護) =====
        logger.info(f"[OAUTH_CALLBACK] 開始驗證狀態令牌...")
        if not OAuthStateToken.validate(state):
            logger.error(f"[OAUTH_CALLBACK] ❌ 狀態令牌驗證失敗: {state[:10]}...")
            raise HTTPException(status_code=400, detail="無效的狀態令牌")
        
        logger.info(f"[OAUTH_CALLBACK] ✅ 狀態令牌驗證成功")
        
        logger.info(f"[OAUTH_CALLBACK] 授權成功，授權碼: {code[:10]}...")
        logger.info(f"[OAUTH_CALLBACK] 返回授權碼到前端進行令牌交換")
        
        # 返回授權碼到前端處理（前端使用 Google SDK 完成令牌交換）
        return {
            "code": code,
            "status": "success",
            "message": "Google authorization successful. Please complete token exchange on client side.",
            "redirect_path": f"/auth/callback?code={code}&state={state}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OAUTH_CALLBACK] ❌ 回調處理失敗: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="認證失敗")


@router.post("/google/token-exchange", response_model=OAuthTokenResponse)
async def google_token_exchange(body: GoogleOAuthRequest):
    """
    交換 Google ID token 為應用 JWT token.
    
    Args:
        body: 包含 Google ID token
    """
    try:
        # ===== 1. 接收 ID token =====
        logger.info(f"[TOKEN_EXCHANGE] 開始令牌交換流程")
        if not body.id_token:
            logger.error(f"[TOKEN_EXCHANGE] ❌ 缺少 id_token")
            raise HTTPException(status_code=400, detail="缺少 id_token")
        
        logger.info(f"[TOKEN_EXCHANGE] ✅ 接收到 id_token: {body.id_token[:30]}...")
        
        # ===== 2. 驗證 Google ID token =====
        logger.info(f"[TOKEN_EXCHANGE] 開始驗證 Google ID token...")
        oauth_service = GoogleOAuthService()
        logger.info(f"[TOKEN_EXCHANGE] GoogleOAuthService 初始化完成")
        logger.info(f"[TOKEN_EXCHANGE] 使用 client_id: {oauth_service.client_id[:10]}...")
        
        google_payload = oauth_service.verify_id_token(body.id_token)
        
        if not google_payload:
            logger.error(f"[TOKEN_EXCHANGE] ❌ Google ID token 驗證失敗")
            raise HTTPException(status_code=401, detail="無效的 Google token")
        
        logger.info(f"[TOKEN_EXCHANGE] ✅ Google ID token 驗證成功")
        logger.info(f"[TOKEN_EXCHANGE] Google payload - email: {google_payload.get('email')}")
        logger.info(f"[TOKEN_EXCHANGE] Google payload - sub: {google_payload.get('sub')}")
        logger.info(f"[TOKEN_EXCHANGE] Google payload - name: {google_payload.get('name')}")
        logger.info(f"[TOKEN_EXCHANGE] Google payload - picture: {google_payload.get('picture')[:30]}..." if google_payload.get('picture') else "")
        
        # ===== 3. 獲取或創建用戶 =====
        logger.info(f"[TOKEN_EXCHANGE] 開始獲取或創建用戶...")
        try:
            user = GoogleOAuthUserService.get_or_create_user(google_payload)
            logger.info(f"[TOKEN_EXCHANGE] ✅ 用戶操作成功")
            logger.info(f"[TOKEN_EXCHANGE] 用戶 ID: {user['id']}")
            logger.info(f"[TOKEN_EXCHANGE] 用戶 email: {user['email']}")
            logger.info(f"[TOKEN_EXCHANGE] 用戶 display_name: {user.get('display_name')}")
            is_new_user = False  # TODO: 檢查用戶是否為新建
        except Exception as e:
            logger.error(f"[TOKEN_EXCHANGE] ❌ 用戶創建失敗: {str(e)}", exc_info=True)
            raise HTTPException(status_code=400, detail="用戶創建失敗")
        
        # ===== 4. 生成應用 JWT token =====
        logger.info(f"[TOKEN_EXCHANGE] 開始生成 JWT token...")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.info(f"[TOKEN_EXCHANGE] token 過期時間: {ACCESS_TOKEN_EXPIRE_MINUTES} 分鐘")
        
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"[TOKEN_EXCHANGE] ✅ JWT token 生成成功")
        logger.info(f"[TOKEN_EXCHANGE] token 長度: {len(access_token)} 字符")
        
        # ===== 5. 返回響應 =====
        logger.info(f"[TOKEN_EXCHANGE] ✅ 令牌交換完成，返回響應")
        logger.info(f"[TOKEN_EXCHANGE] 返回用戶: {user['email']} (ID: {user['id']})")
        
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
        logger.error(f"[TOKEN_EXCHANGE] ❌ 令牌交換失敗: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Token 交換失敗")
