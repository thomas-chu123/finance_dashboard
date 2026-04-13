"""Scheduler 管理服務 - 暫停、恢復、立即執行排程任務."""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from app.database import get_supabase
from app.scheduler import scheduler

logger = logging.getLogger(__name__)


class SchedulerManagementService:
    """管理 APScheduler 任務的服務."""

    @staticmethod
    def get_all_jobs() -> List[Dict[str, Any]]:
        """
        列出所有 scheduler 任務及其狀態。

        Returns:
            任務列表
        """
        try:
            sb = get_supabase()
            # 從資料庫查詢所有任務
            result = sb.table("scheduler_jobs").select("*").order("job_name").execute()
            jobs = result.data or []

            # 補充當前調度器中的實時狀態
            for job in jobs:
                job_id = job.get("job_id")
                try:
                    apscheduler_job = scheduler.get_job(job_id)
                    if apscheduler_job:
                        job["next_run_at"] = apscheduler_job.next_run_time.isoformat() if apscheduler_job.next_run_time else None
                        job["is_enabled"] = apscheduler_job.func is not None
                except Exception:
                    pass

            return jobs
        except Exception as e:
            logger.error(f"[Scheduler] 無法列出所有任務: {e}")
            return []

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """
        取得特定任務的詳細資訊。

        Args:
            job_id: 任務 ID

        Returns:
            任務詳情或 None
        """
        try:
            sb = get_supabase()
            result = sb.table("scheduler_jobs").select("*").eq("job_id", job_id).single().execute()

            if not result.data:
                return None

            job = result.data
            # 補充實時狀態
            try:
                apscheduler_job = scheduler.get_job(job_id)
                if apscheduler_job:
                    job["next_run_at"] = apscheduler_job.next_run_time.isoformat() if apscheduler_job.next_run_time else None
            except Exception:
                pass

            return job
        except Exception as e:
            logger.error(f"[Scheduler] 無法取得任務 {job_id}: {e}")
            return None

    @staticmethod
    def pause_job(job_id: str) -> bool:
        """
        暫停指定的 scheduler 任務。

        Args:
            job_id: 任務 ID

        Returns:
            成功為 True，失敗為 False
        """
        try:
            sb = get_supabase()
            scheduler.pause_job(job_id)

            # 更新資料庫狀態
            sb.table("scheduler_jobs").update({"is_enabled": False}).eq("job_id", job_id).execute()

            logger.info(f"[Scheduler] 已暫停任務: {job_id}")
            return True
        except Exception as e:
            logger.error(f"[Scheduler] 無法暫停任務 {job_id}: {e}")
            return False

    @staticmethod
    def resume_job(job_id: str) -> bool:
        """
        恢復指定的 scheduler 任務。

        Args:
            job_id: 任務 ID

        Returns:
            成功為 True，失敗為 False
        """
        try:
            sb = get_supabase()
            scheduler.resume_job(job_id)

            # 更新資料庫狀態
            sb.table("scheduler_jobs").update({"is_enabled": True}).eq("job_id", job_id).execute()

            logger.info(f"[Scheduler] 已恢復任務: {job_id}")
            return True
        except Exception as e:
            logger.error(f"[Scheduler] 無法恢復任務 {job_id}: {e}")
            return False

    @staticmethod
    async def execute_job_now(job_id: str) -> bool:
        """
        立即執行指定的 scheduler 任務（異步）。

        Args:
            job_id: 任務 ID

        Returns:
            成功為 True，失敗為 False
        """
        try:
            sb = get_supabase()

            # 更新任務狀態為執行中
            sb.table("scheduler_jobs").update({
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat()
            }).eq("job_id", job_id).execute()

            # 取得任務函數並執行
            apscheduler_job = scheduler.get_job(job_id)
            if not apscheduler_job:
                logger.warning(f"[Scheduler] 任務未找到: {job_id}")
                return False

            # 在背景執行任務以避免阻塞
            asyncio.create_task(_execute_job_async(job_id, apscheduler_job.func))
            logger.info(f"[Scheduler] 已開始執行任務: {job_id}")
            return True
        except Exception as e:
            logger.error(f"[Scheduler] 無法執行任務 {job_id}: {e}")
            return False

    @staticmethod
    def get_job_history(job_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        查詢特定任務的執行歷史。

        Args:
            job_id: 任務 ID
            limit: 返回記錄數上限

        Returns:
            執行歷史列表
        """
        try:
            sb = get_supabase()

            # 先查詢任務 UUID
            job_record = sb.table("scheduler_jobs").select("id").eq("job_id", job_id).single().execute()
            if not job_record.data:
                return []

            # 查詢執行歷史
            result = (
                sb.table("scheduler_job_runs")
                .select("*")
                .eq("job_id", job_record.data["id"])
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"[Scheduler] 無法查詢任務歷史 {job_id}: {e}")
            return []


async def _execute_job_async(job_id: str, job_func):
    """
    在背景非同步執行任務，並紀錄執行結果。

    Args:
        job_id: 任務 ID
        job_func: 任務函數
    """
    sb = get_supabase()
    start_time = datetime.now(timezone.utc)

    try:
        # 取得任務記錄的 UUID
        job_record = sb.table("scheduler_jobs").select("id").eq("job_id", job_id).single().execute()
        if not job_record.data:
            logger.error(f"[Scheduler] 無法找到任務記錄: {job_id}")
            return

        job_uuid = job_record.data["id"]

        # 執行任務
        if asyncio.iscoroutinefunction(job_func):
            await job_func()
        else:
            # 在執行緒池中執行同步函數以避免阻塞
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, job_func)

        # 記錄成功
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        sb.table("scheduler_job_runs").insert([{
            "job_id": job_uuid,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "status": "success",
            "duration_ms": duration_ms,
        }]).execute()

        sb.table("scheduler_jobs").update({
            "status": "idle",
            "last_run_at": end_time.isoformat(),
        }).eq("job_id", job_id).execute()

        logger.info(f"[Scheduler] 任務執行成功: {job_id} (耗時 {duration_ms}ms)")

    except Exception as e:
        # 記錄失敗
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        try:
            job_record = sb.table("scheduler_jobs").select("id").eq("job_id", job_id).single().execute()
            if job_record.data:
                job_uuid = job_record.data["id"]
                sb.table("scheduler_job_runs").insert([{
                    "job_id": job_uuid,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                    "status": "error",
                    "duration_ms": duration_ms,
                    "error_message": str(e),
                }]).execute()

            sb.table("scheduler_jobs").update({
                "status": "idle",
                "error_message": str(e),
            }).eq("job_id", job_id).execute()
        except Exception as log_e:
            logger.error(f"[Scheduler] 無法記錄任務失敗: {log_e}")

        logger.error(f"[Scheduler] 任務執行失敗: {job_id} - {e}")
