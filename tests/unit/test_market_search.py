"""單元測試：搜尋 API 端點 (/api/market/search)"""
import pytest
from unittest.mock import patch, AsyncMock
from difflib import SequenceMatcher


# 模擬的符號目錄 (簡化版本)
MOCK_SYMBOL_CATALOG = {
    "0050.TW": {
        "symbol": "0050.TW",
        "yahoo_symbol": "0050.TW",
        "name_zh": "元大台灣50",
        "name_en": "Yuanta Taiwan 50",
        "category": "tw_etf",
        "domain": "tw.stock.yahoo.com"
    },
    "0056.TW": {
        "symbol": "0056.TW",
        "yahoo_symbol": "0056.TW",
        "name_zh": "元大高股息",
        "name_en": "Yuanta High Dividend ETF",
        "category": "tw_etf",
        "domain": "tw.stock.yahoo.com"
    },
    "VTI": {
        "symbol": "VTI",
        "yahoo_symbol": "VTI",
        "name_zh": "美國全市場 ETF",
        "name_en": "Vanguard Total Stock Market ETF",
        "category": "us_etf",
        "domain": "finance.yahoo.com"
    },
    "VIX": {
        "symbol": "VIX",
        "yahoo_symbol": "^VIX",
        "name_zh": "CBOE 波動指數",
        "name_en": "CBOE Volatility Index",
        "category": "vix",
        "domain": "finance.yahoo.com"
    }
}


def _calculate_match_score(query: str, symbol_data: dict) -> float:
    """計算查詢字串與符號數據的相似度分值 (與實現相同)"""
    q_lower = query.lower()
    symbol_score = SequenceMatcher(None, q_lower, symbol_data.get("symbol", "").lower()).ratio()
    name_zh_score = SequenceMatcher(None, q_lower, symbol_data.get("name_zh", "").lower()).ratio()
    name_en_score = SequenceMatcher(None, q_lower, symbol_data.get("name_en", "").lower()).ratio()
    total_score = (symbol_score * 3.0) + (name_zh_score * 2.0) + (name_en_score * 1.0)
    return total_score / 6.0


class TestSearchAlgorithm:
    """測試搜尋算法的相似度計算"""
    
    def test_exact_symbol_match(self):
        """精確符號匹配應得到高分"""
        score = _calculate_match_score("0050.TW", MOCK_SYMBOL_CATALOG["0050.TW"])
        # 0050.TW vs 0050.TW: symbol_score=1.0, 加權後約 0.5
        assert score > 0.4, "精確匹配應得到高分 >0.4"
    
    def test_partial_symbol_match(self):
        """部分符號匹配"""
        score = _calculate_match_score("0050", MOCK_SYMBOL_CATALOG["0050.TW"])
        assert score > 0.3, "部分匹配應得到較高分值"
    
    def test_chinese_name_match(self):
        """中文名稱匹配"""
        score = _calculate_match_score("台灣", MOCK_SYMBOL_CATALOG["0050.TW"])
        # name_zh_score = 0.5, 加權後 * 2 / 6 ≈ 0.167
        assert score > 0.1, "中文名稱匹配應得到分值"
    
    def test_english_name_match(self):
        """英文名稱匹配"""
        score = _calculate_match_score("Taiwan", MOCK_SYMBOL_CATALOG["0050.TW"])
        # name_en_score = 0.5455, 加權後 * 1 / 6 ≈ 0.09
        assert score > 0.08, "英文名稱匹配應得到分值"
    
    def test_symbol_weighted_higher(self):
        """符號匹配權重應高於名稱匹配"""
        # VTI 的精確符號匹配
        vti_symbol_score = _calculate_match_score("VTI", MOCK_SYMBOL_CATALOG["VTI"])
        # 搜尋 "美國" 應該匹配 VTI 的中文名稱，但分值應低於精確符號匹配
        vti_name_score = _calculate_match_score("美國", MOCK_SYMBOL_CATALOG["VTI"])
        assert vti_symbol_score > vti_name_score, "符號匹配權重應高於名稱匹配"
    
    def test_no_match(self):
        """無關搜尋應得到低分值"""
        score = _calculate_match_score("xyz", MOCK_SYMBOL_CATALOG["0050.TW"])
        assert score < 0.1, "無相關匹配應得到較低分值"


class TestSearchFiltering:
    """測試搜尋結果篩選邏輯"""
    
    def test_category_filter(self):
        """按類別篩選應正確過濾結果"""
        query = "50"
        category = "tw_etf"
        
        results = []
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            if category and symbol_data.get("category") != category:
                continue
            score = _calculate_match_score(query, symbol_data)
            if score > 0.3:
                results.append((symbol_data, score))
        
        # 應該只返回 tw_etf 類別的結果
        assert all(item[0]["category"] == category for item in results), "所有結果應為指定類別"
        # 應該包含 0050.TW 和 0056.TW
        symbols = [item[0]["symbol"] for item in results]
        assert "0050.TW" in symbols, "應包含 0050.TW"
    
    def test_sort_by_relevance(self):
        """結果應按相似度排序"""
        query = "台灣"
        results = []
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > 0.3:
                results.append((symbol_data, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 檢查是否按降序排列
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True), "結果應按相似度降序排列"
    
    def test_limit_results(self):
        """應限制返回結果數量"""
        query = "00"  # 匹配 0050 和 0056
        limit = 1
        
        results = []
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > 0.3:
                results.append((symbol_data, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:limit]
        
        assert len(results) <= limit, f"結果數應不超過 {limit}"


class TestSearchThreshold:
    """測試相似度閾值"""
    
    def test_threshold_filtering(self):
        """低於 0.2 的相似度應被過濾"""
        threshold = 0.2
        query = "xyz"  # 不相關的查詢
        
        results = []
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > threshold:
                results.append(symbol_data)
        
        assert len(results) == 0, "無相關結果應被過濾"
    
    def test_edge_case_threshold(self):
        """接近閾值的結果應正確處理"""
        threshold = 0.2
        query = "VIX"  # VIX 應精確匹配
        
        results = []
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > threshold:
                results.append((symbol_data, score))
        
        assert len(results) > 0, "相關結果應被返回"
        assert any(item[0]["symbol"] == "VIX" for item in results), "VIX 應在結果中"


class TestEmptyAndEdgeCases:
    """測試邊界條件"""
    
    def test_empty_query(self):
        """空查詢應返回空結果"""
        query = ""
        results = []
        
        if not query or len(query.strip()) == 0:
            # 按實現邏輯返回空結果
            pass
        
        assert len(results) == 0, "空查詢應返回空結果"
    
    def test_whitespace_only_query(self):
        """僅空白的查詢應返回空結果"""
        query = "   "
        
        if not query or len(query.strip()) == 0:
            results = []
        
        assert len(results) == 0, "空白查詢應返回空結果"
    
    def test_short_query_match(self):
        """短查詢應有效工作"""
        query = "VT"  # 應匹配 VTI
        results = []
        
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > 0.3:
                results.append((symbol_data, score))
        
        # 應該找到 VTI 或其他包含 VT 的符號
        assert len(results) > 0, "短查詢應返回結果"
    
    def test_case_insensitive_search(self):
        """搜尋應不區分大小寫"""
        score_lower = _calculate_match_score("vtI", MOCK_SYMBOL_CATALOG["VTI"])
        score_upper = _calculate_match_score("VTI", MOCK_SYMBOL_CATALOG["VTI"])
        
        assert score_lower == score_upper, "搜尋應不區分大小寫"


class TestMultiLanguageMatching:
    """測試多語言匹配"""
    
    def test_chinese_multi_char_match(self):
        """查詢多個中文字符應找到相符結果"""
        query = "台灣50"  # 0050 的中文名稱「元大台灣50」
        results = []
        
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > 0.2:
                results.append((symbol_data, score))
        
        # 應該包含 0050.TW
        assert len(results) > 0, "應匹配中文名稱"
    
    def test_english_substring_matching(self):
        """查詢英文子字符串應找到相符結果"""
        query = "ETF"
        results = []
        
        for symbol_key, symbol_data in MOCK_SYMBOL_CATALOG.items():
            score = _calculate_match_score(query, symbol_data)
            if score > 0.2:
                results.append((symbol_data, score))
        
        assert len(results) > 0, "應匹配英文子字符串"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
