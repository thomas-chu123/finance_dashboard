"""用戶偏好設置服務"""
from app.database import get_supabase
from typing import Optional, List


class UserPreferencesService:
    """管理用戶偏好設置的服務類"""

    @staticmethod
    def get_default_card_order() -> List[str]:
        """
        獲取默認卡片順序
        
        Returns:
            List[str]: 默認卡片 ID 陣列
        """
        return [
            'market-ticker',
            'tracking-table',
            'alert-logs',
            'status-sidebar'
        ]

    @staticmethod
    def get_user_preferences(user_id: str) -> dict:
        """
        獲取用戶偏好設置，若不存在則自動建立
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            dict: 用戶偏好設置對象，包含 card_order 等字段
            
        Raises:
            Exception: 資料庫查詢失敗
        """
        try:
            sb = get_supabase()
            
            # 嘗試從 user_preferences 表查詢數據
            response = sb.table('user_preferences').select('*').eq('user_id', user_id).single().execute()
            
            if response.data:
                return response.data
            else:
                # 如果用戶偏好設置不存在，自動建立新記錄
                print(f"Creating user preferences for {user_id}")
                default_card_order = UserPreferencesService.get_default_card_order()
                insert_response = sb.table('user_preferences').insert({
                    'user_id': user_id,
                    'card_order': default_card_order
                }).execute()
                
                if insert_response.data:
                    return insert_response.data[0] if isinstance(insert_response.data, list) else insert_response.data
                else:
                    # 若建立失敗，返回預設值
                    return {
                        'user_id': user_id,
                        'card_order': default_card_order,
                        'created_at': None,
                        'updated_at': None
                    }
        except Exception as e:
            # 如果表不存在或查詢失敗，返回默認值，日誌中作為警告
            print(f"Failed to fetch/create user preferences for {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'card_order': UserPreferencesService.get_default_card_order(),
                'created_at': None,
                'updated_at': None
            }

    @staticmethod
    def update_user_preferences(user_id: str, preferences: dict) -> dict:
        """
        更新用戶偏好設置
        
        Args:
            user_id: 用戶 ID
            preferences: 包含要更新字段的字典（例如：{'card_order': [...]}）
            
        Returns:
            dict: 更新後的用戶偏好設置
            
        Raises:
            Exception: 資料庫更新失敗
        """
        try:
            sb = get_supabase()
            
            # 檢查用戶偏好設置是否存在
            existing = sb.table('user_preferences').select('*').eq('user_id', user_id).single().execute()
            
            if existing.data:
                # 更新現有記錄
                update_data = {
                    **preferences,
                    'updated_at': 'now()'  # Supabase 會自動替換為當前時間戳
                }
                response = sb.table('user_preferences').update(update_data).eq('user_id', user_id).execute()
            else:
                # 創建新記錄
                insert_data = {
                    'user_id': user_id,
                    **preferences
                }
                response = sb.table('user_preferences').insert(insert_data).execute()
            
            if response.data:
                return response.data[0] if isinstance(response.data, list) else response.data
            else:
                raise Exception("Failed to update user preferences")
        except Exception as e:
            print(f"Failed to update user preferences for {user_id}: {str(e)}")
            raise

    @staticmethod
    def update_card_order(user_id: str, card_order: List[str]) -> dict:
        """
        更新卡片順序
        
        Args:
            user_id: 用戶 ID
            card_order: 卡片 ID 陣列
            
        Returns:
            dict: 更新後的用戶偏好設置
            
        Raises:
            Exception: 更新失敗
        """
        if not isinstance(card_order, list):
            raise ValueError("card_order must be a list")
        
        if not card_order:
            card_order = UserPreferencesService.get_default_card_order()
        
        return UserPreferencesService.update_user_preferences(
            user_id,
            {'card_order': card_order}
        )

    @staticmethod
    def reset_user_preferences(user_id: str) -> dict:
        """
        重置用戶偏好設置為默認值
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            dict: 重置後的用戶偏好設置
            
        Raises:
            Exception: 重置失敗
        """
        default_card_order = UserPreferencesService.get_default_card_order()
        return UserPreferencesService.update_user_preferences(
            user_id,
            {'card_order': default_card_order}
        )
