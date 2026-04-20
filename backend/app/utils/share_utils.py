"""短碼生成和驗證工具。用於投組分享 URL 的短碼生成。"""
import secrets
import string
from typing import Optional


def generate_share_key(length: int = 12) -> str:
    """生成唯一的短碼用於分享連結。
    
    格式: xxx-xxx-xxx (12 字符，含 3 個連接符 = 20 字符總長)
    
    使用字母 + 數字 (base36)，碰撞概率極低 (~36^12)
    
    Args:
        length: 短碼中字母數字部分的長度（不含連接符）
        
    Returns:
        格式化的短碼，如 "abc-123-xyz"
    """
    # 使用小寫字母 + 數字
    alphabet = string.ascii_lowercase + string.digits
    
    # 生成隨機字符串
    key_chars = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # 格式化為 xxx-xxx-xxx
    return f"{key_chars[:4]}-{key_chars[4:8]}-{key_chars[8:12]}"


def validate_share_key(key: str) -> bool:
    """驗證短碼格式。
    
    Args:
        key: 待驗證的短碼
        
    Returns:
        True 若格式有效，否則 False
    """
    import re
    # 允許 10-20 字符，含小寫字母、數字、連接符
    pattern = r'^[a-z0-9\-]{10,20}$'
    return bool(re.match(pattern, key))


def generate_unique_share_key(
    existing_keys: Optional[set[str]] = None,
    max_attempts: int = 100
) -> Optional[str]:
    """生成唯一短碼，避免碰撞。
    
    Args:
        existing_keys: 已存在的短碼集合
        max_attempts: 最多嘗試次數
        
    Returns:
        新的唯一短碼，若失敗則返回 None
    """
    if existing_keys is None:
        existing_keys = set()
    
    for _ in range(max_attempts):
        key = generate_share_key()
        if key not in existing_keys:
            return key
    
    return None
