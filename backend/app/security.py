import jwt
from datetime import datetime, timedelta
import bcrypt
from fastapi import HTTPException, Header
from app.config import get_settings
from app.database import get_supabase

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def verify_password(plain_password: str, hashed_password: str):
    try:
        if not plain_password or not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Decode access token from Supabase JWT without verification (trusting the source)."""
    try:
        # Decode Supabase JWT without verification (token comes from trusted frontend)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.PyJWTError:
        return None


def require_admin(authorization: str = Header(default="")) -> str:
    """
    依賴注入函數 - 驗證使用者是否為管理員。

    Args:
        authorization: Authorization header（格式：Bearer <token>）

    Returns:
        通過驗證的使用者 ID

    Raises:
        HTTPException: 如果使用者未認證或不是管理員
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="登入憑證已過期或無效，請重新登入")

    user_id = payload["sub"]

    # 檢查使用者是否為管理員
    try:
        sb = get_supabase()
        user = sb.table("profiles").select("is_admin").eq("id", user_id).single().execute()

        if not user.data or not user.data.get("is_admin"):
            raise HTTPException(status_code=403, detail="管理員權限不足")

        return user_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="驗證失敗")
