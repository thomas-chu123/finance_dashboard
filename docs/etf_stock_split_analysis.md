# 0052.TW 和 0050.TW ETF 拆股數據異常診斷報告

## 問題描述

在 2025 年的回測中，0052.TW 出現異常的下跌，但 0050.TW 沒有同樣的問題，儘管兩者都進行了拆股。

## 根本原因分析

### 1. yfinance 的拆股調整不一致

yfinance 使用 `auto_adjust` 參數控制歷史價格調整：
- **`auto_adjust=True`**：自動調整所有歷史數據以補償拆股和除息
- **`auto_adjust=False`**：返回原始收盤價和還原價

### 2. 拆股歷史

**0052.TW (富邦台灣公司治理)**
- 2024 年 4-5 月：進行了 ~3 倍拆股
  - 舊比例（2024年1-3月）：Close vs Adj Close 差異 0.87%
  - 新比例（2024年5月至今）：差異 0.30%

**0050.TW (元大台灣50)**
- 2025 年 1 月中旬：進行了 ~1.04 倍拆股
  - 舊比例（2025年1月10日前）：差異 3.4%
  - 新比例（2025年1月17日後）：差異 2.1%

### 3. 數據差異影響

**調整 vs 未調整數據的累積報酬差異**
| ETF | 調整報酬 | 未調整報酬 | 差異 | 原因 |
|-----|---------|----------|------|------|
| 0052.TW | 184.16% | 176.13% | 8.03% | 股利調整 |
| 0050.TW | 147.13% | 106.14% | 40.98% | 拆股調整 |

### 4. 為什麼 0052 有異常但 0050 沒有

實際上**都有異常**，但表現形式不同：

- **0052.TW**：因為拆股在 2024 年發生，yfinance 的調整已穩定，所以回測結果相對正常
- **0050.TW**：因為拆股在 2025 年才發生（最近），yfinance 可能**還未完全更新**調整倍數
  - 導致最近數據的"異常下跌"可能是調整因子變化造成的

### 5. yfinance 的問題

yfinance 依賴 Yahoo Finance API，而 Yahoo Finance 對拆股信息的更新有延遲。特別是對台灣 ETF 的拆股信息更新不夠及時。

## 症狀

1. 2025 年出現大幅下跌（實際是拆股調整）
2. 使用 `auto_adjust=True` 的數據與實際交易價格不匹配
3. 不同時期的拆股調整倍數不一致

## 解決方案

### 短期修復（推薦）

在回測引擎中**優先使用未調整數據**，然後手動應用拆股調整：

```python
# 使用未調整的收盤價（Close）進行回測
hist = ticker.history(start=start_date, end=end_date, auto_adjust=False)
price_data = hist['Close']  # 使用未調整價格而非 auto_adjust=True

# 然後使用 FinMind 或本地數據庫來應用準確的拆股調整
```

### 中期改進

1. **使用 FinMind 作為主要數據源**
   - FinMind 是台灣本地數據提供商
   - 對台灣股票和 ETF 的拆股信息更新及時
   - 已在代碼中支持（`fetch_finmind_adjusted_prices`）

2. **維護本地拆股調整表**
   ```python
   STOCK_SPLITS = {
       '0052.TW': [
           {'date': '2024-05-01', 'ratio': 3.0},
       ],
       '0050.TW': [
           {'date': '2025-01-17', 'ratio': 1.04},
       ]
   }
   ```

### 長期解決方案

1. 實現自動拆股檢測機制
   - 監控 Close 和 Adj Close 的差異
   - 自動計算拆股倍數
   - 更新本地拆股調整表

2. 構建多數據源合併策略
   - 優先：FinMind（台灣股票/ETF）
   - 次優：Yahoo Finance（美股）
   - 備用：本地數據庫

## 建議行動

1. **立即**：
   - 檢查是否需要更新回測數據
   - 確認是否需要重新執行歷史回測

2. **短期**（本週）：
   - 在 `get_historical_prices()` 中調查 FinMind 覆蓋範圍
   - 優先使用 FinMind 的還原價數據

3. **中期**（本月）：
   - 建立拆股歷史記錄表
   - 實現自動拆股倍數檢測

## 技術細節

### yfinance auto_adjust 工作原理

```python
# auto_adjust=False 返回：
# Close: 實際交易收盤價
# Adj Close: 經過拆股和除息調整的價格
# 調整倍數 = Close / Adj Close

# auto_adjust=True 返回：
# Close: 已調整的價格（相當於 Adj Close）
# 但調整倍數遵循最新的拆股信息
```

### 問題發生原因

yfinance 的 `auto_adjust` 依賴 Yahoo Finance 的拆股數據庫。如果 Yahoo Finance 的拆股信息更新延遲，則 `auto_adjust=True` 的結果會不準確。

## 相關文件

- 回測引擎：`backend/app/services/backtest_engine.py` (Line 87)
- 市場數據：`backend/app/services/market_data.py` (Line 377-420)
- FinMind 集成：`backend/app/services/market_data.py` (fetch_finmind_adjusted_prices)

