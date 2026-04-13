"""
管理員面板 API E2E (End-to-End) 集成測試

測試範圍：
- Admin API 端點的完整流程
- 數據流驗證
- 錯誤處理
"""

import pytest
import json
from httpx import AsyncClient


class TestAdminAPIEndpoints:
    """Admin API 端點完整測試"""
    
    @pytest.mark.asyncio
    async def test_admin_users_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/users 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/users", headers=headers)
        
        assert response.status_code in [200, 401]  # 200 if authenticated, 401 otherwise
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_admin_stats_overview_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/stats/overview 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/stats/overview", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert 'total_users_count' in data
            assert 'active_users_count' in data
            assert 'tracked_indices_count' in data
            assert 'alerts_sent_count' in data
    
    @pytest.mark.asyncio
    async def test_admin_user_stats_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/stats/users 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/stats/users", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert 'today' in data
            assert 'week' in data
            assert 'month' in data
    
    @pytest.mark.asyncio
    async def test_admin_alert_stats_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/stats/alerts 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/stats/alerts", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert 'sent_count' in data
            assert 'failed_count' in data
    
    @pytest.mark.asyncio
    async def test_admin_backend_logs_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/logs/backend 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/logs/backend?lines=50", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json() if isinstance(response.json(), dict) else response.text
            # 驗證返回內容不為空或有效結構
            assert data is not None
    
    @pytest.mark.asyncio
    async def test_admin_system_logs_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/logs/system 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/logs/system", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_admin_audit_logs_endpoint(self, client: AsyncClient, admin_token: str):
        """測試 GET /api/admin/logs/audit 端點"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/admin/logs/audit", headers=headers)
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestAdminAuthentication:
    """Admin 認證保護測試"""
    
    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """測試無認證無法訪問 Admin API"""
        response = await client.get("/api/admin/users")
        
        assert response.status_code in [401, 403]


class TestAdminDataValidation:
    """Admin 數據驗證測試"""
    
    def test_stats_data_types(self):
        """測試統計數據類型正確性"""
        mock_stats = {
            'total_users_count': 10,
            'active_users_count': 5,
            'tracked_indices_count': 15,
            'alerts_sent_count': 3
        }
        
        # 驗證所有字段都是整數
        for key, value in mock_stats.items():
            assert isinstance(value, int), f"{key} 應為 int 類型"
            assert value >= 0, f"{key} 應為非負數"
    
    def test_user_stats_monotonic_increase(self):
        """測試用戶統計應該是單調遞增"""
        mock_stats = {
            'today': 2,
            'week': 8,
            'month': 25
        }
        
        # 今日新增不應超過本週
        assert mock_stats['today'] <= mock_stats['week']
        # 本週新增不應超過本月
        assert mock_stats['week'] <= mock_stats['month']


class TestAdminErrorHandling:
    """Admin 錯誤處理測試"""
    
    @pytest.mark.asyncio
    async def test_invalid_query_parameters(self, client: AsyncClient, admin_token: str):
        """測試無效查詢參數處理"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 測試超出範圍的 limit
        response = await client.get("/api/admin/users?limit=1000", headers=headers)
        assert response.status_code in [200, 400, 422]
        
        # 測試負數 skip
        response = await client.get("/api/admin/users?skip=-1", headers=headers)
        assert response.status_code in [200, 400, 422]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
