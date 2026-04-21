"""圖像分享服務 - 存儲和管理 PNG 分享。"""
import hashlib
import logging
import os
from datetime import datetime, timedelta
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
    ) -> str:
        """保存圖像文件。
        
        Args:
            image_data: PNG 圖像二進制數據
            image_hash: 圖像哈希值
            result_type: 結果類型
            
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
            return str(filepath)
        except OSError as e:
            logger.error(f"❌ 保存圖像失敗: {e}")
            raise

    def get_image(self, image_hash: str) -> str:
        """獲取圖像文件路徑。
        
        Args:
            image_hash: 圖像哈希值，可能包含結果類型前綴（如 backtest_a1b2c3d4）
            
        Returns:
            文件路徑
            
        Raises:
            FileNotFoundError: 如果文件不存在或已過期
        """
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

        # 檢查過期時間
        file_age_days = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).days
        if file_age_days > self.expiry_days:
            logger.info(f"⏰ 圖像已過期: {filepath.name}")
            try:
                filepath.unlink()
            except OSError as e:
                logger.warning(f"⚠️  刪除過期圖像失敗: {e}")
            raise FileNotFoundError(f"Image expired: {image_hash}")

        return str(filepath)

    def cleanup_expired_images(self) -> int:
        """清理過期的圖像文件。
        
        Returns:
            刪除的文件數
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=self.expiry_days)

        for filepath in self.image_dir.glob("*.png"):
            try:
                file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if file_mtime < cutoff_time:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"🗑️  已刪除過期圖像: {filepath.name}")
            except OSError as e:
                logger.warning(f"⚠️  無法處理文件 {filepath.name}: {e}")

        if deleted_count > 0:
            logger.info(f"✅ 清理完成：刪除了 {deleted_count} 個過期圖像")

        return deleted_count
