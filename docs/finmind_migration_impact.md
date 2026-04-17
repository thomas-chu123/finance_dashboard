# FinMind 作為主要數據源的影響分析報告

## 摘要

當前代碼**已經部分支持** FinMind 作為優先數據源（Priority 1）。將 FinMind 升級為**完全主要數據源**需要有限的修改，複雜度為 **中低**。

## 現狀評估

### ✅ 已實現

1. **FinMind 集成已完成**
   - `fetch_finmind_adjusted_prices()` - 還原價格
   - `fetch_finmind_unadjusted_prices()` - 實際收盤價
   - `_fetch_finmind_prices()` - 內部通用函數

2. **優先級邏輯已存在**
   - `get_historical_prices()` 中第 394 行：
   ```python
   if _is_taiwan_stock(symbol) and FINMIND_API_TOKEN:
       # 優先使用 FinMind
   ```

3. **環境變數已配置**
   - `.env` 中已有 `FinMind_API` token
   - 讀取正確：`FINMIND_API_TOKEN = os.getenv("FinMind_API")`

4. **台灣股票檢測正常**
   - `_is_taiwan_stock()` 正確識別台灣股票/ETF
   - 支援格式：純數字、.TW、.TWO 後綴

### ⚠️ 需要改進

1. **FinMind 覆蓋範圍不完全**
   - FinMind 支援 `TaiwanStockPrice*` 數據集
   - **不支援**美股、指數等非台灣資產
   - ETF 支持狀態未確認（需要驗證 0050.TW、0052.TW 等是否在 FinMind）

2. **未實現 auto_adjust 替代方案**
   - 當前 yfinance 使用 `auto_adjust=True/False` 切換
   - FinMind 返回 `TaiwanStockPriceAdj`（已還原）或 `TaiwanStockPrice`（未還原）
   - **差異**：yfinance 的 auto_adjust 有拆股延遲問題，FinMind 的拆股調整更準確

3. **缺少拆股歷史記錄**
   - 無本地拆股事件表
   - 無法手動驗證或覆蓋 FinMind 的拆股信息

4. **環境變數文檔缺失**
   - `backend/.env.example` 中未包含 `FinMind_API`
   - 新用戶無法知道需要配置此變數

## 影響範圍分析

### 🔴 受影響的主要函數

| 文件 | 函數 | 調用位置 | 修改必要性 | 複雜度 |
|------|------|---------|----------|--------|
| `backtest_engine.py` | `run_backtest()` | Line 87 | ✅ 無需修改 | - |
| `backtest_engine.py` | `_beta()` | Line 226 | ✅ 無需修改 | - |
| `monte_carlo_engine.py` | `run_monte_carlo()` | Line 41 | ✅ 無需修改 | - |
| `rsi_service.py` | `calculate_rsi()` | Line 132 | ✅ 無需修改 | - |
| `optimize.py` | 優化端點 | Line 56, 211 | ✅ 無需修改 | - |
| `market_data.py` | `get_historical_prices()` | Line 377 | ⚠️ 小改進 | 低 |
| `market_data.py` | `fetch_live_price()` | Line 295 | ⚠️ 需評估 | 中 |

### ✅ 不需要修改的原因

因為所有數據消費端都通過 `get_historical_prices()` 抽象層，所以：
- 回測引擎、RSI 服務、蒙地卡羅模擬等都自動受益
- 修改 `get_historical_prices()` 的優先級，所有調用端自動應用

## 建議修改方案

### 方案 A：最小改動（推薦短期）

**目標**：確保 FinMind 作為台灣股票/ETF 的主要數據源

**修改項目**：

1. **更新 `backend/.env.example`**
   ```python
   # ==========================================
   # FinMind API Configuration (Taiwan Stocks/ETFs)
   # ==========================================
   FinMind_API=your_finmind_api_token
   ```
   - 文件：`backend/.env.example`
   - 行數：新增 3 行
   - 複雜度：🟢 平凡

2. **優化 yfinance 的 auto_adjust 參數**
   - 修改 `get_historical_prices()` 第 420 行
   - 將 `auto_adjust=True` 改為 `auto_adjust=False`
   - 原因：使用未調整數據，避免 yfinance 的拆股延遲問題
   - 影響：僅當 FinMind 不可用時才使用 yfinance
   - 複雜度：🟢 平凡

   ```python
   # 當前（有問題）
   hist = await asyncio.to_thread(ticker.history, ..., auto_adjust=True)
   
   # 改進為（建議）
   hist = await asyncio.to_thread(ticker.history, ..., auto_adjust=False)
   price_col = "Adj Close"  # 使用還原價而非 Close
   ```

3. **驗證 FinMind ETF 支持**
   - 測試 0050.TW、0052.TW 等 ETF 是否在 FinMind
   - 如果支持：自動受益
   - 如果不支持：在 yfinance 中處理

   ```python
   # 檢驗代碼（不需提交）
   import requests
   token = "YOUR_FINMIND_TOKEN"
   resp = requests.get(
       "https://api.finmindtrade.com/api/v4/data",
       params={
           "dataset": "TaiwanStockPriceAdj",
           "data_id": "0050",  # 不含 .TW
           "start_date": "2025-01-01",
           "end_date": "2025-02-01",
           "token": token
       }
   )
   print(resp.json())
   ```

### 方案 B：完整改進（推薦中期）

**目標**：實現完全的數據源策略，支持多源合併和拆股管理

**修改項目**：

1. **建立 Supabase 拆股歷史表** （新增）
   ```sql
   CREATE TABLE stock_splits (
       id BIGSERIAL PRIMARY KEY,
       symbol VARCHAR(20) NOT NULL,
       split_date DATE NOT NULL,
       old_price DECIMAL(10, 4),
       new_price DECIMAL(10, 4),
       ratio DECIMAL(10, 4),  -- new_price / old_price
       source VARCHAR(50),  -- 'finmind', 'yahoo', 'manual'
       verified BOOLEAN DEFAULT FALSE,
       created_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE INDEX idx_stock_splits_symbol ON stock_splits(symbol);
   ```
   - 複雜度：🟡 簡單

2. **新增拆股檢測和同步函數** （`market_data.py` 中新增）
   ```python
   async def detect_stock_splits(symbol: str) -> list[dict]:
       """
       通過比較 Close 和 Adj Close 差異來檢測拆股
       返回 [{date, ratio}, ...]
       """
       pass
   
   async def sync_stock_splits_to_db():
       """
       定期同步拆股信息到 Supabase
       由 scheduler 每周調用一次
       """
       pass
   ```
   - 複雜度：🟡 中等

3. **增強 `get_historical_prices()` 邏輯** （修改）
   ```python
   # 優先級邏輯
   # 1. FinMind (台灣股票/ETF)
   # 2. 本地拆股調整 (FinMind 返回的數據)
   # 3. yfinance (美股/指數) - 使用 auto_adjust=False
   # 4. 本地拆股表驗證和覆蓋
   ```
   - 複雜度：🟡 中等

4. **更新 scheduler.py** （修改）
   - 新增每周同步拆股信息的任務
   - 複雜度：🟡 簡單

### 方案 C：完全自動化（推薦長期）

**目標**：完全消除 yfinance 拆股延遲的影響

**修改項目**：

1. 實現自動拆股倍數計算引擎
2. 多源數據驗證機制
3. 異常檢測和告警系統

---

## 詳細修改清單

### 🟢 立即可做（0.5 小時）

| 項目 | 文件 | 修改 | 風險 | 收益 |
|------|------|------|------|------|
| 更新 env 文檔 | `backend/.env.example` | 新增 `FinMind_API` | 無 | 🟢 低 - 文檔清晰 |
| 修改 yfinance 參數 | `market_data.py` L420 | `auto_adjust=True` → `False` | 🟡 中 - 需測試 | 🟢 高 - 修復拆股延遲 |

### 🟡 短期改進（2-3 小時）

| 項目 | 文件 | 修改 | 風險 | 收益 |
|------|------|------|------|------|
| FinMind ETF 驗證 | 測試腳本 | 檢驗 0050/0052 覆蓋 | 無 | 🟡 中 - 確認支持範圍 |
| 添加錯誤處理 | `market_data.py` | 增強 FinMind 失敗回退邏輯 | 無 | 🟡 中 - 提高穩定性 |

### 🟠 中期改進（4-6 小時）

| 項目 | 文件 | 修改 | 風險 | 收益 |
|------|------|------|------|------|
| Supabase 拆股表 | `docs/migrations/` | 新增 SQL schema | 🟢 低 | 🟠 高 - 長期數據源 |
| 拆股檢測函數 | `market_data.py` | 新增自動檢測邏輯 | 🟡 中 | 🟠 高 - 自動驗證 |
| Scheduler 集成 | `scheduler.py` | 新增同步任務 | 🟡 中 | 🟠 中 - 定期更新 |

---

## 風險評估

### �� 低風險修改

- **更新 env 文檔**：零風險，純文檔
- **Supabase 表創建**：新表，不影響現有邏輯

### 🟡 中等風險修改

- **修改 yfinance auto_adjust 參數**
  - 風險：需測試所有數據消費端（backtest、RSI、optimizer）
  - 緩解：修改前先在測試環境驗證
  - 測試覆蓋：需回測 2020-2025 全年數據

- **FinMind 覆蓋範圍**
  - 風險：若 FinMind 不支持某些 ETF，會回退 yfinance
  - 緩解：已有回退邏輯，但需驗證
  - 測試覆蓋：抽樣測試 20+ 個常用 ETF

### 🟢 低風險集成

- **拆股檢測函數**
  - 風險：僅做檢測，不影響當前回測邏輯
  - 可獨立部署在 scheduler 中

---

## 實施順序建議

### 第一階段（立即）- 驗證和文檔
1. ✅ 驗證 FinMind API 可用性
2. ✅ 測試 FinMind 對台灣 ETF 的覆蓋
3. ✅ 更新 `backend/.env.example`

### 第二階段（本週）- 核心修復
1. ⚠️ 修改 `get_historical_prices()` auto_adjust 參數
2. ✅ 增強錯誤處理和日誌
3. ✅ 在 dev 環境測試所有回測、RSI、優化功能

### 第三階段（本月）- 增強穩定性
1. 建立 Supabase 拆股表
2. 實現自動拆股檢測
3. 集成 scheduler 同步任務

---

## 測試計劃

### Unit Tests（需要新增）

```python
# 測試 FinMind 覆蓋
def test_finmind_covers_common_etfs():
    symbols = ['0050', '0051', '0052', '0056', '0057', '0058', '0059']
    for sym in symbols:
        series = await fetch_finmind_adjusted_prices(sym, ...)
        assert not series.empty
```

### Integration Tests（已存在，需要擴展）

```python
# 測試不同數據源的結果一致性
def test_finmind_vs_yfinance_returns():
    symbol = '0050'
    finmind_ret = await get_historical_prices(symbol, ...)  # 用 FinMind
    yfinance_ret = ...  # 用 yfinance
    assert abs(finmind_ret[-1] - yfinance_ret[-1]) < 1%  # 允許 1% 差異
```

### Regression Tests（需要運行）

```bash
# 回測 2025 全年數據，檢查是否仍有異常下跌
pytest tests/test_backtest_0050_0052_2025.py -v

# 驗證所有 RSI 指標計算無異常
pytest tests/test_rsi_calculation.py -v
```

---

## 成本-收益分析

| 工作項 | 成本（小時） | 收益 | 優先級 |
|--------|----------|------|--------|
| 文檔更新 + 驗證 | 0.5 | 🟢 明確依賴配置 | P0 |
| auto_adjust 參數修改 | 1 | 🟠 修復拆股延遲 | P1 |
| 增強錯誤處理 | 1 | 🟡 提高穩定性 | P2 |
| FinMind ETF 測試 | 1 | 🟡 確認覆蓋 | P1 |
| 拆股表設計 | 1 | 🟠 長期數據源 | P2 |
| 拆股檢測實現 | 2 | 🟠 自動驗證 | P2 |
| Scheduler 集成 | 1 | 🟡 定期同步 | P3 |
| **總計** | **7.5 小時** | **高** | |

---

## 建議決策

### 如果時間有限（< 2 小時）
✅ 只做第一階段 + 修改 auto_adjust 參數
- 最小風險
- 立即修復 2025 異常下跌問題

### 如果有一周時間
✅ 第一 + 二階段
- 完整驗證和測試
- 確保質量

### 如果要長期解決
✅ 全三階段 + 持續監控
- 完整的數據管理策略
- 準備處理未來的 yfinance 問題

