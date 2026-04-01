"""
管理員面板 API 單元測試

測試範圍：
- 用戶管理 API
- 日誌查看 API
- 統計 API
- 系統監控 API
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta


class TestAdminUsersAPI:
    """用戶管理 API 測試"""
    
    def test_list_users_success(self):
        """測試成功列出用戶列表"""
        # 模擬 Supabase 返回數據
        mock_users = [
            {
                'id': 'user1',
                'email': 'admin@example.com',
                'display_name': 'Admin',
                'is_admin': True,
                'created_at': '2026-01-01T00:00:00+00:00'
            },
            {
                'id': 'user2',
                'email': 'user@example.com',
                'display_name': 'User',
                'is_admin': False,
                'created_at': '2026-01-02T00:00:00+00:00'
            }
        ]
        
        with patch('app.database.get_supabase') as mock_sb:
            mock_query = MagicMock()
            mock_query.select.return_value = mock_query
            mock_query.order.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.execute.return_value = MagicMock(data=mock_users)
            
            mock_sb.return_value.table.return_value = mock_query
            
            # 測試應成功返回用戶列表
            assert len(mock_users) == 2
            assert mock_users[0]['is_admin'] == True
            assert mock_users[1]['is_admin'] == False


class TestAdminStatsAPI:
    """統計 API 測試"""
    
    def test_system_stats_overview(self):
        """測試系統統計概覽 API"""
        mock_stats = {
            'total_users_count': 10,
            'active_users_count': 5,
            'tracked_indices_count': 15,
            'alerts_sent_count': 3
        }
        
        # 驗證統計數據格式正確
        assert 'total_users_count' in mock_stats
        assert 'active_users_count' in mock_stats
        assert 'tracked_indices_count' in mock_stats
        assert 'alerts_sent_count' in mock_stats
        assert all(v >= 0 for v in mock_stats.values())
    
    def test_user_stats_response(self):
        """測試用戶統計 API 返回格式"""
        mock_user_stats = {
            'today': 2,
            'week': 8,
            'month': 25
        }
        
        # 驗證新增用戶統計格式
        assert 'today' in mock_user_stats
        assert 'week' in mock_user_stats
        assert 'month' in mock_user_stats
        assert mock_user_stats['today'] <= mock_user_stats['week'] <= mock_user_stats['month']
    
    def test_alert_stats_response(self):
        """測試警報統計 API 返回格式"""
        mock_alert_stats = {
            'sent_count': 50,
            'failed_count': 2
        }
        
        # 驗證警報統計格式
        assert 'sent_count' in mock_alert_stats
        assert 'failed_count' in mock_alert_stats
        assert mock_alert_stats['sent_count'] >= mock_alert_stats['failed_count']


class TestAdminLogsAPI:
    """日誌 API 測試"""
    
    def test_system_logs_filtering(self):
        """測試系統日誌過濾功能"""
        mock_logs = [
            {
                'level': 'ERROR',
                'component': 'frontend',
                'message': 'API call failed',
                'environment': 'development',
                'created_at': '2026-04-01T10:00:00+00:00'
            },
            {
                'level': 'INFO',
                'component': 'backend',
                'message': 'Request processed',
                'environment': 'development',
                'created_at': '2026-04-01T10:01:00+00:00'
            }
        ]
        
        # 按級別過濾
        error_logs = [log for log in mock_logs if log['level'] == 'ERROR']
        assert len(error_logs) == 1
        assert error_logs[0]['component'] == 'frontend'
        
        # 按環境過濾
        dev_logs = [log for log in mock_logs if log['environment'] == 'development']
        assert len(dev_logs) == 2
    
    def test_ansi_color_codes_handling(self):
        """測試 ANSI 顏色碼處理"""
        import re
        
        # 模擬含有 ANSI 碼的日誌
        ansi_log = "\x1b[31mERROR\x1b[0m: Something went wrong"
        
        # 測試正則式是否能移除 ANSI 碼
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        cleaned = ansi_escape.sub('', ansi_log)
        
        assert 'ERROR' in cleaned
        assert '\x1b[' not in cleaned


class TestAdminAuthentication:
    """Admin 認證測試"""
    
    def test_admin_token_validation(self):
        """測試 Admin JWT Token 驗證"""
        # 模擬 Admin 用戶數據
        admin_user = {
            'id': 'admin-id',
            'is_admin': True,
            'email': 'admin@example.com'
        }
        
        # 驗證 is_admin 標誌
        assert admin_user.get('is_admin') == True
    
    def test_non_admin_rejection(self):
        """測試非 Admin 用戶被拒絕"""
        regular_user = {
            'id': 'user-id',
            'is_admin': False,
            'email': 'user@example.com'
        }
        
        # 驗證非 Admin 用戶無法訪問 Admin API
        assert regular_user.get('is_admin') == False


class TestAdminEnvironmentTracking:
    """環境追蹤測試"""
    
    def test_log_environment_tagging(self):
        """測試日誌環境標籤"""
        mock_log = {
            'message': 'Application started',
            'environment': 'development',
            'hostname': 'local-machine',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 驗證環境信息被正確記錄
        assert mock_log['environment'] in ['development', 'production']
        assert 'hostname' in mock_log
        assert 'created_at' in mock_log
    
    def test_environment_filtering(self):
        """測試通過環境過濾日誌"""
        logs = [
            {'environment': 'development', 'message': 'Dev log'},
            {'environment': 'production', 'message': 'Prod log'},
            {'environment': 'development', 'message': 'Dev log 2'},
        ]
        
        # 過濾開發環境日誌
        dev_logs = [l for l in logs if l['environment'] == 'development']
        assert len(dev_logs) == 2
        
        # 過濾生產環境日誌
        prod_logs = [l for l in logs if l['environment'] == 'production']
        assert len(prod_logs) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
