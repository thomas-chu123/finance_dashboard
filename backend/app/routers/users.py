"""User management router."""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.models import ProfileUpdate, ProfileResponse
from app.database import get_supabase

router = APIRouter(prefix="/api/users", tags=["users"])


def get_user_id(authorization: str = "") -> str:
    """Extract user ID from custom JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    
    from app.security import decode_access_token
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="登入憑證已過期或無效，請重新登入 (Token expired/invalid)")
        
    return payload["sub"]


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    res = sb.table("profiles").select("*").eq("id", user_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return res.data


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(body: ProfileUpdate, authorization: str = Header(default="")):
    user_id = get_user_id(authorization)
    sb = get_supabase()
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    res = sb.table("profiles").update(update_data).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Update failed")
    return res.data[0]


@router.get("", response_model=list[ProfileResponse])
async def list_users(authorization: str = Header(default="")):
    """Admin only: list all users."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    # Check if admin
    me = sb.table("profiles").select("is_admin").eq("id", user_id).single().execute()
    if not me.data or not me.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    res = sb.table("profiles").select("*").order("created_at").execute()
    return res.data or []


@router.put("/{target_user_id}/admin")
async def toggle_admin(target_user_id: str, is_admin: bool, authorization: str = Header(default="")):
    """Toggle admin status for a user."""
    user_id = get_user_id(authorization)
    sb = get_supabase()
    me = sb.table("profiles").select("is_admin").eq("id", user_id).single().execute()
    if not me.data or not me.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    res = sb.table("profiles").update({"is_admin": is_admin}).eq("id", target_user_id).execute()
    return {"message": "Updated", "is_admin": is_admin}
