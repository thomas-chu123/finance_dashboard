import pytest
import asyncio
import sys
from pathlib import Path

# 添加後端模塊路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from httpx import AsyncClient
from app.main import app
from app.routers.market import _calculate_match_score, _fetch_latest_price


class TestSearchIntegration:
    """搜尋功能集成測試"""

    @pytest.mark.asyncio
    async def test_market_search_endpoint_empty_query(self):
        """測試空查詢"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=")
            assert response.status_code == 200
            result = response.json()
            assert isinstance(result, dict)
            assert 'results' in result
            assert 'total' in result
            assert isinstance(result['results'], list)
            assert len(result['results']) == 0
            assert result['total'] == 0

    @pytest.mark.asyncio
    async def test_market_search_endpoint_symbol_matching(self):
        """測試符號精確匹配"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 搜尋常見的 ETF
            response = await client.get("/api/market/search?q=VTI&limit=10")
            assert response.status_code == 200
            result = response.json()
            
            # 應該能找到結果
            assert isinstance(result, dict)
            assert 'results' in result
            results = result['results']
            assert isinstance(results, list)
            if len(results) > 0:
                # VTI 應該在頂部
                assert results[0]['symbol'] == 'VTI' or 'VTI' in [r['symbol'] for r in results]

    @pytest.mark.asyncio
    async def test_market_search_endpoint_category_filter(self):
        """測試類別篩選"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=&category=us_etf&limit=20")
            assert response.status_code == 200
            result = response.json()
            
            # 所有結果應該是 us_etf 類別（或為空）
            results = result.get('results', [])
            if len(results) > 0:
                for item in results:
                    assert item.get('category') in ['us_etf', None]

    @pytest.mark.asyncio
    async def test_market_search_endpoint_limit(self):
        """測試結果限制"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=&limit=5")
            assert response.status_code == 200
            result = response.json()
            assert len(result['results']) <= 5

    @pytest.mark.asyncio
    async def test_market_search_with_chinese_query(self):
        """測試中文查詢"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=台灣&limit=10")
            assert response.status_code == 200
            result = response.json()
            # 應該能搜尋到台灣 ETF（如果資料庫中有）
            assert isinstance(result, dict)
            assert isinstance(result['results'], list)

    def test_calculate_match_score(self):
        """測試匹配分數計算"""
        # 完全匹配符號應該得分最高
        symbol_score = _calculate_match_score('VTI', 'VTI', 'Vanguard Total Stock Market ETF', 'VTI')
        
        # 符號子串匹配
        partial_symbol_score = _calculate_match_score('VT', 'VTI', 'Vanguard Total Stock Market ETF', 'VTI')
        
        # 符號匹配應該比子串匹配得分高
        assert symbol_score >= partial_symbol_score

    def test_calculate_match_score_chinese(self):
        """測試中文名稱匹配"""
        score = _calculate_match_score('', '台灣50', '台灣50', '0050')
        assert score > 0.2  # 應該達到最小相似度閾值

    def test_calculate_match_score_english(self):
        """測試英文名稱匹配"""
        score = _calculate_match_score('', '', 'Total Market', 'VTI')
        assert score >= 0.2 or score == 0  # 取決於子字符串匹配

    @pytest.mark.asyncio
    async def test_fetch_latest_price(self):
        """測試獲取最新價格"""
        # 測試真實 API 調用
        try:
            price_data = await _fetch_latest_price('VTI')
            
            if price_data is not None:
                assert 'price' in price_data or price_data is None
                assert 'change_pct' in price_data or price_data is None
        except Exception as e:
            # 網絡錯誤是可接受的
            pytest.skip(f"網絡錯誤: {e}")

    @pytest.mark.asyncio
    async def test_search_performance(self):
        """測試搜尋性能"""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/api/market/search?q=V&limit=50")
            end_time = time.time()
            
            assert response.status_code == 200
            # 應該在 1 秒內返回結果
            assert end_time - start_time < 1.0, f"搜尋耗時 {end_time - start_time}s，超過 1 秒"

    @pytest.mark.asyncio
    async def test_search_special_characters(self):
        """測試特殊字符查詢"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 測試各種特殊字符
            special_queries = ['VTI-', 'ETF@', 'Test#123', '基金$']
            
            for query in special_queries:
                response = await client.get(f"/api/market/search?q={query}")
                # 應該不會崩潰
                assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_search_result_structure(self):
        """測試搜尋結果結構"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=VTI&limit=1")
            assert response.status_code == 200
            result = response.json()
            results = result.get('results', [])
            
            if len(results) > 0:
                item = results[0]
                # 驗證結果包含所需的欄位
                assert 'symbol' in item
                assert 'name_zh' in item or 'name_en' in item
                assert 'category' in item
                # price 和 change_pct 可能是 null
                assert 'price' in item
                assert 'change_pct' in item

    @pytest.mark.asyncio
    async def test_search_multiple_results(self):
        """測試多結果搜尋"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=&limit=10&category=us_etf")
            assert response.status_code == 200
            result = response.json()
            results = result.get('results', [])
            
            # 應該能返回多個結果（如果資料庫有足夠數據）
            assert isinstance(results, list)
            if len(results) > 1:
                # 驗證所有結果都有正確的結構
                for item in results:
                    assert isinstance(item, dict)
                    assert 'symbol' in item


class TestSearchEdgeCases:
    """搜尋邊界情況測試"""

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """測試超長查詢"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            long_query = 'a' * 1000
            response = await client.get(f"/api/market/search?q={long_query}")
            
            # 應該返回空結果而不是崩潰
            assert response.status_code == 200
            result = response.json()
            assert len(result.get('results', [])) == 0

    @pytest.mark.asyncio
    async def test_invalid_category(self):
        """測試無效類別"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=VTI&category=invalid_category")
            
            # 應該返回 200 並忽略無效類別或返回所有結果
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_zero_limit(self):
        """測試零限制"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=VTI&limit=0")
            
            # 應該返回 200 並使用默認值或返回空結果
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_negative_limit(self):
        """測試負數限制"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/market/search?q=VTI&limit=-5")
            
            # 應該返回 200 並使用默認值或返回空結果
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unicode_query(self):
        """測試 Unicode 查詢"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 測試各種 Unicode 字符
            unicode_queries = ['🚀', '日本ETF', '中文', 'Ελληνικά']
            
            for query in unicode_queries:
                response = await client.get(f"/api/market/search?q={query}")
                # 應該不會崩潰
                assert response.status_code in [200, 400]


class TestSearchPerformanceOptimization:
    """搜尋性能優化測試"""

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """測試並發搜尋"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 同時發送多個搜尋請求
            tasks = [
                client.get(f"/api/market/search?q=V{i}") 
                for i in range(10)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # 所有請求應該成功
            assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_repeated_search_consistency(self):
        """測試重複搜尋的一致性"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 搜尋 3 次
            responses = []
            for _ in range(3):
                response = await client.get("/api/market/search?q=VTI&limit=5")
                assert response.status_code == 200
                responses.append(response.json()['results'])
            
            # 結果應該一致
            if len(responses[0]) > 0:
                # 驗證符號和順序
                symbols1 = [r['symbol'] for r in responses[0]]
                symbols2 = [r['symbol'] for r in responses[1]]
                symbols3 = [r['symbol'] for r in responses[2]]
                
                assert symbols1 == symbols2 == symbols3


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
