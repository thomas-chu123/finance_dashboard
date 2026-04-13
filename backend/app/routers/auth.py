"""Authentication router using custom JWT."""
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from app.models import RegisterRequest, LoginRequest, TokenResponse
from app.database import get_supabase
from app.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.services.portfolio_template_service import init_user_default_portfolios

import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(body: RegisterRequest):
    logger.info(f"Registration attempt for : {body.email}")
    
    sb = get_supabase()
    try:
        # Check if email exists
        res = sb.table("profiles").select("id").eq("email", body.email).execute()
        if res.data:
            logger.warning(f"Registration failed: Email {body.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user profile directly in profiles table
        hashed_pw = get_password_hash(body.password)
        new_user_id = str(uuid.uuid4())
        
        profile_data = {
            "id": new_user_id,
            "email": body.email,
            "display_name": body.display_name or body.email.split("@")[0],
            "hashed_password": hashed_pw
        }
        
        insert_res = sb.table("profiles").insert(profile_data).execute()
        if not insert_res.data:
            logger.error(f"Registration failed: Profile creation failed for {body.email}")
            raise HTTPException(status_code=400, detail="Registration failed during profile creation")
        
        # Initialize default portfolios for new user
        try:
            portfolio_ids = init_user_default_portfolios(new_user_id)
            logger.info(f"Initialized {len(portfolio_ids)} default portfolios for user {new_user_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize default portfolios for user {new_user_id}: {str(e)}")
            
        logger.info(f"Registration successful for: {body.email} (ID: {new_user_id})")

        return {"message": "Registration successful", "user_id": new_user_id}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Unexpected error during registration for {body.email}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    import logging
    logger = logging.getLogger("auth")
    logger.info(f"Login attempt for: {body.email}")
    
    sb = get_supabase()
    try:
        res = sb.table("profiles").select("*").eq("email", body.email).execute()
        if not res.data:
            logger.warning(f"Login failed: User {body.email} not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        user = res.data[0]
        logger.info(f"User {body.email} found, verifying password...")
        
        if not user.get("hashed_password") or not verify_password(body.password, user["hashed_password"]):
             logger.warning(f"Login failed: Invalid password for {body.email}")
             raise HTTPException(status_code=401, detail="Invalid credentials")
             
        logger.info(f"Password verified for {body.email}, generating token...")
             
        # Generate JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]}, expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            user_id=user["id"],
            email=user["email"],
        )
    except Exception as e:
        import logging
        logger = logging.getLogger("auth")
        
        # Log details about the inputs to help debug "72 bytes" error
        try:
            pw_len = len(body.password) if body.password else 0
            pw_type = type(body.password).__name__
            user_id = user.get("id") if 'user' in locals() else "unknown"
            hash_val = user.get("hashed_password") if 'user' in locals() else None
            hash_type = type(hash_val).__name__ if hash_val else "None"
            
            logger.error(f"Login failure for {body.email}: {str(e)}")
            logger.error(f"Debug Info - PW Len: {pw_len}, PW Type: {pw_type}, Hash Type: {hash_type}, UserID: {user_id}")
            
            # If it's the specific bcrypt error, add more context
            if "72 bytes" in str(e):
                error_detail = f"Security Error: {str(e)} (PW Len: {pw_len}, Type: {pw_type})"
                raise HTTPException(status_code=401, detail=error_detail)
        except HTTPException:
            raise
        except Exception as log_e:
            logger.error(f"Error during failure logging: {log_e}")

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(authorization: str = ""):
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(body: dict):
    """請求密碼重設."""
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    logger.info(f"Password reset requested for: {email}")
    
    sb = get_supabase()
    try:
        # 檢查使用者是否存在
        res = sb.table("profiles").select("id, email").eq("email", email).execute()
        if not res.data:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            # 為了安全，仍然返回成功（不透露使用者是否存在）
            return {"message": "If this email exists, you will receive a password reset link"}
        
        # 在真實環境中，應該發送電子郵件
        # 這裡我們簡化流程，直接允許重設
        logger.info(f"Password reset link would be sent to: {email}")
        
        return {"message": "Password reset instructions have been sent to your email"}
    except Exception as e:
        logger.error(f"Error during password reset request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process password reset request")


@router.post("/reset-password")
async def reset_password(body: dict):
    """使用者自助重設密碼."""
    email = body.get("email")
    new_password = body.get("new_password")
    
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email and new password are required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    logger.info(f"Password reset attempt for: {email}")
    
    sb = get_supabase()
    try:
        # 查找使用者
        res = sb.table("profiles").select("id").eq("email", email).execute()
        if not res.data:
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = res.data[0]["id"]
        
        # 更新密碼
        hashed_pw = get_password_hash(new_password)
        update_res = sb.table("profiles").update({
            "hashed_password": hashed_pw
        }).eq("id", user_id).execute()
        
        if not update_res.data:
            logger.error(f"Failed to update password for user: {user_id}")
            raise HTTPException(status_code=500, detail="Failed to reset password")
        
        logger.info(f"Password successfully reset for user: {email}")
        return {"message": "Password has been successfully reset"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during password reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset password")
