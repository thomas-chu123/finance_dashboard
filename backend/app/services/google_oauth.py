"""Google OAuth 用戶管理服務."""
import logging
from typing import Optional, Dict, Any
from app.database import get_supabase
import uuid

logger = logging.getLogger("google_oauth")


class GoogleOAuthUserService:
    """Google OAuth 用戶管理."""
    
    @staticmethod
    def get_or_create_user(google_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據 Google 數據獲取或創建用户.
        
        Args:
            google_data: Google ID token payload
            
        Returns:
            用戶資料字典
        """
        logger.info(f"[GET_OR_CREATE_USER] 開始處理 Google 用戶數據")
        
        sb = get_supabase()
        email = google_data.get("email")
        google_id = google_data.get("sub")
        display_name = google_data.get("name", email.split("@")[0] if email else "User")
        picture_url = google_data.get("picture")
        
        logger.info(f"[GET_OR_CREATE_USER] Google 數據 - email: {email}")
        logger.info(f"[GET_OR_CREATE_USER] Google 數據 - google_id: {google_id[:20]}..." if google_id else "")
        logger.info(f"[GET_OR_CREATE_USER] Google 數據 - display_name: {display_name}")
        logger.info(f"[GET_OR_CREATE_USER] Google 數據 - picture_url: {picture_url[:50]}..." if picture_url else "")
        
        if not email or not google_id:
            logger.error(f"[GET_OR_CREATE_USER] ❌ 缺少必要的 Google 用戶數據 | email={bool(email)}, google_id={bool(google_id)}")
            raise ValueError("缺少 email 或 google_id")
        
        try:
            # ===== 尋找現有用戶 =====
            logger.info(f"[GET_OR_CREATE_USER] 查詢現有用戶: {email}")
            res = sb.table("profiles").select("*").eq("email", email).execute()
            
            if res.data:
                user = res.data[0]
                logger.info(f"[GET_OR_CREATE_USER] ✅ 找到現有用戶: {email} (ID: {user['id']})")
                logger.info(f"[GET_OR_CREATE_USER] 現有 google_id: {user.get('google_id')}")
                
                # 如果沒有 google_id，則更新
                if not user.get("google_id"):
                    logger.info(f"[GET_OR_CREATE_USER] 更新用戶 google_id...")
                    update_data = {
                        "google_id": google_id,
                        "oauth_provider": "google",
                        "picture_url": picture_url
                    }
                    logger.info(f"[GET_OR_CREATE_USER] 更新數據: {update_data}")
                    
                    sb.table("profiles").update(update_data).eq("id", user["id"]).execute()
                    logger.info(f"[GET_OR_CREATE_USER] ✅ 用戶 google_id 更新成功")
                
                return user
            
            # ===== 創建新用戶 =====
            logger.info(f"[GET_OR_CREATE_USER] 未找到現有用戶，開始創建新用戶...")
            new_user_id = str(uuid.uuid4())
            new_user_data = {
                "id": new_user_id,
                "email": email,
                "display_name": display_name,
                "google_id": google_id,
                "oauth_provider": "google",
                "picture_url": picture_url,
                "hashed_password": None  # OAuth 用戶無需密碼
            }
            
            logger.info(f"[GET_OR_CREATE_USER] 新用戶數據準備完成:")
            logger.info(f"[GET_OR_CREATE_USER]   - id: {new_user_id}")
            logger.info(f"[GET_OR_CREATE_USER]   - email: {email}")
            logger.info(f"[GET_OR_CREATE_USER]   - display_name: {display_name}")
            logger.info(f"[GET_OR_CREATE_USER]   - google_id: {google_id[:20]}...")
            logger.info(f"[GET_OR_CREATE_USER]   - oauth_provider: google")
            
            logger.info(f"[GET_OR_CREATE_USER] 開始插入新用戶到資料庫...")
            insert_res = sb.table("profiles").insert(new_user_data).execute()
            
            if insert_res.data:
                logger.info(f"[GET_OR_CREATE_USER] ✅ 新 Google 用戶創建成功: {email} (ID: {new_user_id})")
                return insert_res.data[0]
            
            logger.error(f"[GET_OR_CREATE_USER] ❌ 創建用戶失敗: {email} - 無返回數據")
            raise Exception("用戶創建失敗")
            
        except Exception as e:
            logger.error(f"[GET_OR_CREATE_USER] ❌ 用戶操作失敗: {str(e)}", exc_info=True)
            raise
