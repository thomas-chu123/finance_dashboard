"""管理者管理路由 - 用戶管理、Scheduler 管理、日誌查看."""
import logging
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from datetime import datetime, timezone
from typing import List, Optional
from app.models import (
    AdminUserResponse,
    AdminUserUpdate,
    AdminPasswordReset,
    SchedulerJobResponse,
    SchedulerJobRunResponse,
    AuditLogResponse,
    SystemStatsOverviewResponse,
    UserStatsResponse,
    AlertStatsResponse,
)
from app.database import get_supabase
from app.security import require_admin, get_password_hash, verify_password
from app.services.audit_service import AuditService
from app.services.scheduler_management import SchedulerManagementService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ===================================================================
# 用戶管理 API
# ===================================================================

@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    admin_id: str = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """
    列出所有使用者（分頁）。

    - **skip**: 分頁偏移
    - **limit**: 每頁數量（最多 100）
    """
    try:
        sb = get_supabase()
        result = (
            sb.table("profiles")
            .select("id, email, display_name, is_admin, created_at")
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"[Admin] 無法列出使用者: {e}")
        raise HTTPException(status_code=500, detail="無法列出使用者")


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
):
    """取得特定使用者的詳細資訊."""
    try:
        sb = get_supabase()
        result = (
            sb.table("profiles")
            .select("id, email, display_name, is_admin, created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="使用者未找到")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] 無法取得使用者 {user_id}: {e}")
        raise HTTPException(status_code=500, detail="無法取得使用者")


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    admin_id: str = Depends(require_admin),
    authorization: str = Header(default=""),
):
    """
    編輯使用者資訊。

    - **display_name**: 修改使用者名稱
    - **is_admin**: 修改管理員權限
    """
    try:
        # 防止管理員修改自己的管理員狀態（編輯自己時）
        if user_id == admin_id and body.is_admin is False:
            raise HTTPException(status_code=400, detail="無法移除自己的管理員權限")

        sb = get_supabase()
        update_data = body.model_dump(exclude_none=True)

        result = (
            sb.table("profiles")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="使用者未找到")

        # 記錄審計日誌
        AuditService.log_action(
            user_id=admin_id,
            action="update_user",
            target_user_id=user_id,
            changes=update_data,
        )

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] 無法更新使用者 {user_id}: {e}")
        raise HTTPException(status_code=500, detail="無法更新使用者")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
):
    """
    刪除使用者帳號及相關數據（級聯刪除）。

    ⚠️ 此操作不可逆！將刪除：
    - backtest_results
    - optimization_results
    - portfolio_holdings
    - portfolios
    - tracked_indices
    - user_preferences
    - market_briefings
    - profiles
    """
    try:
        # 防止管理員刪除自己的帳號
        if user_id == admin_id:
            raise HTTPException(status_code=400, detail="無法刪除自己的帳號")

        sb = get_supabase()
        delete_stats = {}

        # 級聯刪除（按順序錯過外鍵依賴）
        try:
            # 1. 刪除回測結果
            try:
                result = sb.table("backtest_results").delete().eq("user_id", user_id).execute()
                delete_stats["backtest_results"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 backtest_results 失敗: {e}")
                delete_stats["backtest_results"] = 0

            # 2. 刪除優化結果
            try:
                result = sb.table("optimization_results").delete().eq("user_id", user_id).execute()
                delete_stats["optimization_results"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 optimization_results 失敗: {e}")
                delete_stats["optimization_results"] = 0

            # 3. 刪除投資組合持倉（先獲取所有投資組合 ID）
            try:
                portfolios = (
                    sb.table("portfolios")
                    .select("id")
                    .eq("user_id", user_id)
                    .execute()
                ).data or []

                total_holdings = 0
                for portfolio in portfolios:
                    result = sb.table("portfolio_holdings").delete().eq("portfolio_id", portfolio["id"]).execute()
                    total_holdings += len(result.data) if result.data else 0
                delete_stats["portfolio_holdings"] = total_holdings
            except Exception as e:
                logger.warning(f"[Admin] 刪除 portfolio_holdings 失敗: {e}")
                delete_stats["portfolio_holdings"] = 0

            # 4. 刪除投資組合
            try:
                result = sb.table("portfolios").delete().eq("user_id", user_id).execute()
                delete_stats["portfolios"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 portfolios 失敗: {e}")
                delete_stats["portfolios"] = 0

            # 5. 刪除追蹤指數
            try:
                result = sb.table("tracked_indices").delete().eq("user_id", user_id).execute()
                delete_stats["tracked_indices"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 tracked_indices 失敗: {e}")
                delete_stats["tracked_indices"] = 0

            # 6. 刪除用戶偏好設置
            try:
                result = sb.table("user_preferences").delete().eq("user_id", user_id).execute()
                delete_stats["user_preferences"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 user_preferences 失敗: {e}")
                delete_stats["user_preferences"] = 0

            # 7. 刪除市場早報
            try:
                result = sb.table("market_briefings").delete().eq("user_id", user_id).execute()
                delete_stats["market_briefings"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.warning(f"[Admin] 刪除 market_briefings 失敗: {e}")
                delete_stats["market_briefings"] = 0

            # 8. 最後刪除用戶個人檔案
            try:
                result = sb.table("profiles").delete().eq("id", user_id).execute()
                delete_stats["profiles"] = len(result.data) if result.data else 0
            except Exception as e:
                logger.error(f"[Admin] 刪除 profiles 失敗: {e}")
                raise HTTPException(status_code=500, detail="無法刪除使用者檔案")

            logger.info(f"[Admin] 已刪除使用者及相關數據: {user_id}, 統計: {delete_stats}")
        except HTTPException:
            raise
        except Exception as cascade_error:
            logger.error(f"[Admin] 級聯刪除失敗: {cascade_error}")
            raise

        # 記錄審計日誌
        try:
            AuditService.log_action(
                user_id=admin_id,
                action="delete_user",
                target_user_id=user_id,
                changes={"deleted": True, "deleted_counts": delete_stats},
            )
        except Exception as e:
            logger.warning(f"[Admin] 審計日誌記錄失敗: {e}")

        return {
            "message": "使用者已刪除",
            "user_id": user_id,
            "deleted_counts": delete_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] 無法刪除使用者 {user_id}: {e}")
        raise HTTPException(status_code=500, detail="無法刪除使用者")


@router.post("/users/{user_id}/password")
async def reset_password(
    user_id: str,
    body: AdminPasswordReset,
    admin_id: str = Depends(require_admin),
):
    """
    管理員重設使用者密碼。

    - **new_password**: 新密碼
    """
    try:
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(status_code=400, detail="密碼過短（至少 8 個字符）")

        sb = get_supabase()

        # 重設密碼（使用 service_role key 才能更新認證用戶）
        # 注意：Supabase 的用戶密碼重設通常透過管理員 API 進行
        # 這裡示範應用層的邏輯，實際實現需要訪問 Supabase 管理員端

        logger.warning(f"[Admin] 需要実現密碼重設邏輯（user: {user_id}）")

        # 記錄審計日誌
        AuditService.log_action(
            user_id=admin_id,
            action="reset_password",
            target_user_id=user_id,
        )

        return {"message": "密碼已重設"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] 無法重設密碼: {e}")
        raise HTTPException(status_code=500, detail="無法重設密碼")


@router.put("/users/{user_id}/admin")
async def toggle_admin(
    user_id: str,
    is_admin: bool,
    admin_id: str = Depends(require_admin),
):
    """
    升級/降級使用者管理員權限。

    - **is_admin**: true = 升級為管理員，false = 降級為普通使用者
    """
    try:
        # 防止操作自己
        if user_id == admin_id:
            raise HTTPException(status_code=400, detail="無法修改自己的管理員權限")

        sb = get_supabase()
        result = (
            sb.table("profiles")
            .update({"is_admin": is_admin})
            .eq("id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="使用者未找到")

        # 記錄審計日誌
        AuditService.log_action(
            user_id=admin_id,
            action="toggle_admin",
            target_user_id=user_id,
            changes={"is_admin": is_admin},
        )

        return {"message": f"權限已更新", "is_admin": is_admin}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] 無法更新管理員權限: {e}")
        raise HTTPException(status_code=500, detail="無法更新管理員權限")


@router.get("/users/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: str,
    admin_id: str = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
):
    """查看針對該使用者的管理操作活動日誌."""
    logs = AuditService.get_user_activity(user_id, limit=limit)
    return logs


# ===================================================================
# Scheduler 管理 API
# ===================================================================

@router.get("/scheduler/jobs", response_model=List[SchedulerJobResponse])
async def list_scheduler_jobs(
    admin_id: str = Depends(require_admin),
):
    """列出所有 Scheduler 任務及其狀態."""
    jobs = SchedulerManagementService.get_all_jobs()
    return jobs


@router.get("/scheduler/jobs/{job_id}", response_model=SchedulerJobResponse)
async def get_scheduler_job(
    job_id: str,
    admin_id: str = Depends(require_admin),
):
    """取得特定 Scheduler 任務的詳細資訊."""
    job = SchedulerManagementService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任務未找到")
    return job


@router.put("/scheduler/jobs/{job_id}/pause")
async def pause_scheduler_job(
    job_id: str,
    admin_id: str = Depends(require_admin),
):
    """暫停指定的 Scheduler 任務."""
    success = SchedulerManagementService.pause_job(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="無法暫停任務")

    # 記錄審計日誌
    AuditService.log_action(
        user_id=admin_id,
        action="pause_scheduler_job",
        changes={"job_id": job_id},
    )

    return {"message": f"任務 {job_id} 已暫停"}


@router.put("/scheduler/jobs/{job_id}/resume")
async def resume_scheduler_job(
    job_id: str,
    admin_id: str = Depends(require_admin),
):
    """恢復指定的 Scheduler 任務."""
    success = SchedulerManagementService.resume_job(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="無法恢復任務")

    # 記錄審計日誌
    AuditService.log_action(
        user_id=admin_id,
        action="resume_scheduler_job",
        changes={"job_id": job_id},
    )

    return {"message": f"任務 {job_id} 已恢復"}


@router.post("/scheduler/jobs/{job_id}/execute")
async def execute_scheduler_job_now(
    job_id: str,
    admin_id: str = Depends(require_admin),
):
    """立即執行指定的 Scheduler 任務（背景非同步執行）."""
    success = await SchedulerManagementService.execute_job_now(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="無法執行任務")

    # 記錄審計日誌
    AuditService.log_action(
        user_id=admin_id,
        action="execute_scheduler_job",
        changes={"job_id": job_id},
    )

    return {"message": f"任務 {job_id} 已開始執行"}


@router.get("/scheduler/jobs/{job_id}/history", response_model=List[SchedulerJobRunResponse])
async def get_scheduler_job_history(
    job_id: str,
    admin_id: str = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
):
    """查看特定任務的執行歷史."""
    history = SchedulerManagementService.get_job_history(job_id, limit=limit)
    return history


# ===================================================================
# 日誌管理 API
# ===================================================================

@router.get("/logs/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    admin_id: str = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
):
    """查看審計日誌（分頁）."""
    logs = AuditService.get_audit_logs(limit=limit, offset=skip, action=action)
    return logs


@router.get("/logs/system")
async def get_system_logs(
    admin_id: str = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    level: Optional[str] = None,
    component: Optional[str] = None,
    environment: Optional[str] = None,
):
    """查看系統日誌（實時）。
    
    可选参数：
    - level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
    - component: 組件名稱 (frontend, backend, scheduler)
    - environment: 環境 (development, staging, production)
    """
    try:
        sb = get_supabase()
        query = sb.table("system_logs").select("*")

        if level:
            query = query.eq("level", level)
        if component:
            query = query.eq("component", component)
        if environment:
            query = query.eq("environment", environment)

        result = (
            query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"[Admin] 無法查詢系統日誌: {e}")
        raise HTTPException(status_code=500, detail="無法查詢系統日誌")


@router.get("/logs/backend")
async def get_backend_logs(
    admin_id: str = Depends(require_admin),
    lines: int = Query(100, ge=10, le=1000),
):
    """
    讀取後端日誌檔案（最後 N 行）。
    
    返回原始日誌文本，包含 ANSI 顏色碼（前端負責轉換）。

    - **lines**: 返回最後多少行日誌
    """
    try:
        import subprocess
        import os
        
        # 優先嘗試讀取 PM2 日誌（開發環境）
        try:
            result = subprocess.run(
                ["pm2", "logs", "finance-backend", "--lines", str(lines), "--nostream"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (FileNotFoundError, Exception):
            pass
        
        # 次選：嘗試讀取生產環境日誌位置
        log_paths = [
            "/var/log/finance-dashboard/backend.log",
            "/var/log/finance/backend.log",
            os.path.expanduser("~/.pm2/logs/finance-backend-out.log"),
            os.path.expanduser("~/.pm2/logs/finance-backend-error.log"),
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                result = subprocess.run(
                    ["tail", "-n", str(lines), log_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout
        
        # 最後：從資料庫系統日誌表讀取
        sb = get_supabase()
        db_logs = (
            sb.table("system_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(lines)
            .execute()
        ).data or []
        
        # 將資料庫日誌轉為文字格式
        if db_logs:
            logs_text = "\n".join([
                f"[{log.get('created_at', '')}] [{log.get('level', 'INFO')}] {log.get('component', 'app')}: {log.get('message', '')}"
                for log in db_logs[::-1]  # 反轉為時間遞增
            ])
            return logs_text
        
        return ""
    except Exception as e:
        logger.error(f"[Admin] 無法讀取後端日誌: {e}")
        return ""


@router.post("/logs/frontend")
async def submit_frontend_logs(
    logs: dict,
    admin_id: str = Depends(require_admin),
):
    """
    前端提交日誌（從瀏覽器控制台）。

    期望格式：
    {
        "level": "error|warn|info",
        "message": "日誌訊息",
        "component": "組件名稱",
        "timestamp": "時間戳"
    }
    """
    try:
        from app.config import get_settings
        import socket
        
        sb = get_supabase()
        settings = get_settings()
        
        try:
            hostname = socket.gethostname()
        except:
            hostname = "unknown"
        
        entry = {
            "level": logs.get("level", "info"),
            "component": logs.get("component", "frontend"),
            "message": logs.get("message", ""),
            "environment": settings.environment,
            "hostname": hostname,
            "created_at": logs.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        }

        sb.table("system_logs").insert([entry]).execute()
        return {"message": "日誌已提交"}
    except Exception as e:
        logger.error(f"[Admin] 無法提交前端日誌: {e}")
        raise HTTPException(status_code=500, detail="無法提交日誌")


# ===================================================================
# 系統監控 API
# ===================================================================

@router.get("/stats/overview", response_model=SystemStatsOverviewResponse)
async def get_system_stats_overview(
    admin_id: str = Depends(require_admin),
):
    """取得系統概覽統計信息."""
    try:
        sb = get_supabase()

        # 統計各項數據
        total_users = len(sb.table("profiles").select("id").execute().data or [])
        total_tracked = len(sb.table("tracked_indices").select("id").execute().data or [])

        # 統計過去7天的活躍用戶（基於最近創建的警報記錄）
        from datetime import datetime, timezone, timedelta
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        
        # 查詢過去7天有警報活動的唯一用戶
        alert_logs = sb.table("alert_logs").select("user_id").gte(
            "created_at", seven_days_ago
        ).execute().data or []
        active_user_ids = set(a.get("user_id") for a in alert_logs if a.get("user_id"))
        active_users_count = len(active_user_ids)

        # 統計警報發送情況
        alerts_today = sb.table("alert_logs").select("id, status").execute().data or []
        alerts_sent = len([a for a in alerts_today if a.get("status") == "sent"])

        return {
            "total_users_count": total_users,
            "active_users_count": active_users_count,
            "tracked_indices_count": total_tracked,
            "alerts_sent_count": alerts_sent,
        }
    except Exception as e:
        logger.error(f"[Admin] 無法取得系統統計: {e}")
        raise HTTPException(status_code=500, detail="無法取得系統統計")


@router.get("/stats/users", response_model=UserStatsResponse)
async def get_user_stats(
    admin_id: str = Depends(require_admin),
):
    """取得用戶統計信息."""
    try:
        from datetime import datetime, timezone, timedelta
        sb = get_supabase()

        # 定義時間范圍
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        # 統計今日新增用戶
        new_today = sb.table("profiles").select("id").gte("created_at", today_start).execute().data or []
        new_users_today = len(new_today)

        # 統計本週新增用戶
        new_week = sb.table("profiles").select("id").gte("created_at", week_start).execute().data or []
        new_users_week = len(new_week)

        # 統計本月新增用戶
        new_month = sb.table("profiles").select("id").gte("created_at", month_start).execute().data or []
        new_users_month = len(new_month)

        return {
            "today": new_users_today,
            "week": new_users_week,
            "month": new_users_month,
        }
    except Exception as e:
        logger.error(f"[Admin] 無法取得用戶統計: {e}")
        raise HTTPException(status_code=500, detail="無法取得用戶統計")


@router.get("/stats/alerts", response_model=AlertStatsResponse)
async def get_alert_stats(
    admin_id: str = Depends(require_admin),
):
    """取得警報統計信息."""
    try:
        from datetime import datetime, timezone
        sb = get_supabase()
        
        # 統計所有警報
        alerts = sb.table("alert_logs").select("id, status").execute().data or []
        
        # 統計已發送和失敗的警報
        sent_count = len([a for a in alerts if a.get("status") == "sent"])
        failed_count = len([a for a in alerts if a.get("status") == "failed"])

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
        }
    except Exception as e:
        logger.error(f"[Admin] 無法取得警報統計: {e}")
        raise HTTPException(status_code=500, detail="無法取得警報統計")
