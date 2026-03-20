"""Authentication router using custom JWT."""
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from app.models import RegisterRequest, LoginRequest, TokenResponse
from app.database import get_supabase
from app.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(body: RegisterRequest):
    import logging
    logger = logging.getLogger("auth")
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
