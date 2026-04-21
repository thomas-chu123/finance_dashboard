"""圖像分享服務 - 存儲和管理 PNG 分享。"""
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class ImageShareManager:
    """管理圖像分享的生成、存儲和過期。"""

    def __init__(self):
        self.settings = get_settings()
        self.image_dir = Path(self.settings.temp_dir or "/tmp")
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.expiry_days = 30

    def _get_supabase(self):
        """延遲載入 Supabase client，避免循環導入。"""
        from app.database import get_supabase
        return get_supabase()

    def generate_image_hash(self, portfolio_id: str, result_type: str) -> str:
        """生成圖像哈希值。
        
        Args:
            portfolio_id: 投組 ID
            result_type: 結果類型 (backtest/optimize/monte_carlo)
            
        Returns:
            哈希值
        """
        data = f"{portfolio_id}_{result_type}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def save_image(
        self,
        image_data: bytes,
        image_hash: str,
        result_type: str,
        user_id: Optional[str] = None,
    ) -> str:
        """保存圖像文件並寫入 Supabase metadata。
        
        Args:
            image_data: PNG 圖像二進制數據
            image_hash: 圖像哈希值
            result_type: 結果類型 (backtest/optimize/monte_carlo)
            user_id: 上傳用戶的 UUID（用於寫入 portfolio_shares）
            
        Returns:
            文件路徑
            
        Raises:
            ValueError: 如果圖像數據無效
            OSError: 如果保存失敗
        """
        if not image_data:
            raise ValueError("Image data cannot be empty")

        # 驗證 PNG 簽名
        if not image_data.startswith(b"\x89PNG"):
            raise ValueError("Invalid PNG format")

        filename = f"{result_type}_{image_hash}.png"
        filepath = self.image_dir / filename

        try:
            filepath.write_bytes(image_data)
            logger.info(f"✅ 圖像已保存: {filename}")
        except OSError as e:
            logger.error(f"❌ 保存圖像失敗: {e}")
            raise

        # 寫入 Supabase metadata（允許失敗不影響主流程）
        if user_id:
            self._write_metadata(image_hash, result_type, user_id)

        return str(filepath)

    def _write_metadata(self, image_hash: str, result_type: str, user_id: str) -> None:
        """將 PNG 分享 metadata 寫入 portfolio_shares 表。
        
        Args:
            image_hash: 圖像哈希值
            result_type: 結果類型
            user_id: 用戶 UUID
        """
        try:
            supabase = self._get_supabase()
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=self.expiry_days)

            supabase.table("portfolio_shares").insert({
                "user_id": user_id,
                "share_key": image_hash,
                "result_type": result_type,
                "image_hash": image_hash,
                "share_type": "snapshot",
                "is_public": True,
                "expires_at": expires_at.isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }).execute()
            logger.info(f"✅ 已寫入 portfolio_shares metadata: {image_hash}")
        except Exception as e:
            logger.warning(f"⚠️  寫入 portfolio_shares 失敗（不影響分享功能）: {e}")

    def get_image(self, image_hash: str) -> str:
        """獲取圖像文件路徑，同時檢查 Supabase expires_at。
        
        Args:
            image_hash: 圖像哈希值，可能包含結果類型前綴（如 backtest_a1b2c3d4）
            
        Returns:
            文件路徑
            
        Raises:
            FileNotFoundError: 如果文件不存在或已過期
        """
        # 先檢查 Supabase metadata 是否過期
        self._check_db_expiry(image_hash)

        # 支持兩種格式：
        # 1. 完整格式：backtest_a1b2c3d4e5f6g7h8 (完整文件名無 .png)
        # 2. 簡化格式：a1b2c3d4e5f6g7h8（需要從 temp_dir 中查找）
        
        image_dir = self.image_dir
        
        # 首先嘗試直接查找（包括 .png 副檔名）
        if not image_hash.endswith('.png'):
            potential_paths = list(image_dir.glob(f"*{image_hash}*.png"))
            if potential_paths:
                filepath = potential_paths[0]
            else:
                # 嘗試作為完整文件名（無 .png）
                possible_file = image_dir / f"{image_hash}.png"
                if possible_file.exists():
                    filepath = possible_file
                else:
                    raise FileNotFoundError(f"Image not found: {image_hash}")
        else:
            filepath = image_dir / image_hash

        if not filepath.exists():
            raise FileNotFoundError(f"Image file not found: {image_hash}")

        # 備用過期檢查：若無 Supabase metadata，以檔案 mtime 為依據
        file_age_days = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).days
        if file_age_days > self.expiry_days:
            logger.info(f"⏰ 圖像已過期（mtime）: {filepath.name}")
            try:
                filepath.unlink()
            except OSError as e:
                logger.warning(f"⚠️  刪除過期圖像失敗: {e}")
            raise FileNotFoundError(f"Image expired: {image_hash}")

        return str(filepath)

    def _check_db_expiry(self, image_hash: str) -> None:
        """從 Supabase 檢查圖像是否已過期。過期則刪除 DB 記錄並拋出例外。
        
        Args:
            image_hash: 圖像哈希值
            
        Raises:
            FileNotFoundError: 如果 DB 記錄顯示已過期
        """
        try:
            supabase = self._get_supabase()
            now = datetime.now(timezone.utc).isoformat()
            result = supabase.table("portfolio_shares") \
                .select("id, expires_at") \
                .eq("image_hash", image_hash) \
                .lt("expires_at", now) \
                .execute()

            if result.data:
                record_id = result.data[0]["id"]
                logger.info(f"⏰ DB 記錄已過期: {image_hash}，刪除記錄")
                supabase.table("portfolio_shares").delete().eq("id", record_id).execute()
                raise FileNotFoundError(f"Image expired (DB): {image_hash}")
        except FileNotFoundError:
            raise
        except Exception as e:
            # DB 查詢失敗時不阻塞檔案讀取（降級到 mtime 檢查）
            logger.warning(f"⚠️  DB 過期檢查失敗（降級到 mtime）: {e}")

    def cleanup_expired_images(self) -> int:
        """清理過期的圖像文件，以 Supabase expires_at 為主要依據。
        
        Returns:
            刪除的文件數
        """
        deleted_count = 0

        # 優先使用 Supabase metadata 清理
        try:
            deleted_count = self._cleanup_by_db()
        except Exception as e:
            logger.warning(f"⚠️  DB 清理失敗，降級到 mtime 清理: {e}")
            deleted_count = self._cleanup_by_mtime()

        # 同步刪除孤立的 /tmp PNG（無對應 DB 記錄、超過 30 天）
        orphan_count = self._cleanup_orphan_files()
        total = deleted_count + orphan_count

        if total > 0:
            logger.info(f"✅ 清理完成：刪除了 {total} 個過期圖像（DB: {deleted_count}, 孤立: {orphan_count}）")

        return total

    def _cleanup_by_db(self) -> int:
        """從 Supabase 查詢過期記錄並刪除對應檔案。"""
        supabase = self._get_supabase()
        now = datetime.now(timezone.utc).isoformat()

        result = supabase.table("portfolio_shares") \
            .select("id, image_hash, result_type") \
            .lt("expires_at", now) \
            .not_.is_("image_hash", "null") \
            .execute()

        if not result.data:
            return 0

        deleted_count = 0
        ids_to_delete = []

        for record in result.data:
            image_hash = record.get("image_hash")
            result_type = record.get("result_type", "")
            ids_to_delete.append(record["id"])

            # 刪除對應的 PNG 檔案
            for filepath in self.image_dir.glob(f"*{image_hash}*.png"):
                try:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"🗑️  已刪除過期圖像: {filepath.name}")
                except OSError as e:
                    logger.warning(f"⚠️  無法刪除文件 {filepath.name}: {e}")

        # 批次刪除 DB 記錄
        if ids_to_delete:
            supabase.table("portfolio_shares").delete().in_("id", ids_to_delete).execute()
            logger.info(f"🗑️  已刪除 {len(ids_to_delete)} 筆過期 DB 記錄")

        return deleted_count

    def _cleanup_by_mtime(self) -> int:
        """備用：以檔案 mtime 為依據清理過期圖像（無 DB 時使用）。"""
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=self.expiry_days)

        for filepath in self.image_dir.glob("*.png"):
            try:
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if file_mtime < cutoff_time:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"🗑️  已刪除過期圖像（mtime）: {filepath.name}")
            except OSError as e:
                logger.warning(f"⚠️  無法處理文件 {filepath.name}: {e}")

        return deleted_count

    def _cleanup_orphan_files(self) -> int:
        """刪除 /tmp 中無 DB 記錄且超過 30 天的孤立 PNG 檔案。"""
        try:
            supabase = self._get_supabase()
            cutoff_time = datetime.now() - timedelta(days=self.expiry_days)
            deleted_count = 0

            for filepath in self.image_dir.glob("*.png"):
                try:
                    file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if file_mtime >= cutoff_time:
                        continue  # 未到期

                    # 從檔名提取 hash（格式：{result_type}_{hash}.png）
                    parts = filepath.stem.split("_", 1)
                    file_hash = parts[1] if len(parts) == 2 else filepath.stem

                    # 確認 DB 中無對應記錄
                    result = supabase.table("portfolio_shares") \
                        .select("id") \
                        .eq("image_hash", file_hash) \
                        .execute()

                    if not result.data:
                        filepath.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️  已刪除孤立圖像: {filepath.name}")
                except OSError as e:
                    logger.warning(f"⚠️  無法處理孤立文件 {filepath.name}: {e}")

            return deleted_count
        except Exception as e:
            logger.warning(f"⚠️  孤立檔案清理失敗: {e}")
            return 0
