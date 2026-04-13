"""審計日誌服務 - 記錄所有管理員操作."""
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from app.database import get_supabase

logger = logging.getLogger(__name__)


class AuditService:
    """審計日誌服務，用於記錄系統中的管理操作."""

    @staticmethod
    def log_action(
        user_id: str,
        action: str,
        target_user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        記錄審計日誌。

        Args:
            user_id: 執行操作的使用者 ID（可為 None，例如系統操作）
            action: 操作名稱（如 'delete_user', 'update_user', 'pause_job'）
            target_user_id: 目標使用者 ID（如果適用）
            changes: 變更內容（JSON）
            ip_address: 操作者 IP 地址

        Returns:
            成功為 True，失敗為 False
        """
        try:
            sb = get_supabase()
            entry = {
                "user_id": user_id,
                "action": action,
                "target_user_id": target_user_id,
                "changes": changes,
                "ip_address": ip_address,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            result = sb.table("audit_logs").insert([entry]).execute()
            logger.info(f"[Audit] 已記錄操作: {action} by {user_id}")
            return True
        except Exception as e:
            logger.error(f"[Audit] 無法記錄審計日誌: {e}")
            return False

    @staticmethod
    def get_audit_logs(
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list:
        """
        查詢審計日誌。

        Args:
            limit: 返回記錄數上限
            offset: 分頁偏移
            user_id: 篩選特定使用者的操作
            action: 篩選特定操作類型

        Returns:
            審計日誌列表
        """
        try:
            sb = get_supabase()
            query = sb.table("audit_logs").select("*")

            if user_id:
                query = query.eq("user_id", user_id)
            if action:
                query = query.eq("action", action)

            result = (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"[Audit] 無法查詢審計日誌: {e}")
            return []

    @staticmethod
    def get_user_activity(user_id: str, limit: int = 50) -> list:
        """
        取得特定使用者的活動記錄。

        Args:
            user_id: 使用者 ID
            limit: 返回記錄數上限

        Returns:
            使用者活動日誌列表
        """
        try:
            sb = get_supabase()
            result = (
                sb.table("audit_logs")
                .select("*")
                .eq("target_user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"[Audit] 無法取得使用者活動: {e}")
            return []
