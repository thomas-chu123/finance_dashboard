---
goal: 從台股 ETF 擴展到支持所有台灣股票的系統設計
version: 1.0
date_created: 2026-04-01
status: 'Planned'
tags: ['feature', 'backend', 'database', 'api', 'frontend']
---

# 台灣股票市場數據支持擴展計劃

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

**目標**：從現有的「台股 ETF 專用」架構擴展到支持所有台灣股票（包括 ETF、上市股票、上櫃股票）。使用 TWSE 官方 OpenAPI `/v1/exchangeReport/STOCK_DAY_AVG_ALL` 端點作為數據源。

## 1. 需求 & 約束

- **REQ-001**: 支持所有台灣股票代碼（4-6 位數字），包括上市公司和上櫃公司
- **REQ-002**: 使用 TWSE OpenAPI (`https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL`) 作為台灣股票清單的主要數據源
- **REQ-003**: 保持現有 yfinance/FinMind 作為日線歷史價格數據源
- **REQ-004**: 向後兼容現有的台股 ETF 功能（不破壞現有 API）
- **REQ-005**: 支持在投資組合、回測、監控等功能中使用台灣股票
- **CON-001**: TWSE OpenAPI 返回格式為 JSON，包含股票基本信息和日均量
- **CON-002**: 數據庫遷移須無縫過渡，不影響生產環境
- **GUD-001**: 遵循現有命名規範（同步服務為 `tw_*_sync.py`，路由為大寫類別）
- **GUD-002**: 所有確認儲存變更需使用 RLS（Row Level Security）
- **PAT-001**: 市場符號分類系統（category）需要擴展支持 `tw_stock` 類別

## 2. 實施步驟

### Phase 1: 數據庫模式更新

**GOAL-001**: 創建 Supabase 表以支持台灣股票清單

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-1.1 | 建立 `tw_stock_list` 表，包含字段：`symbol`, `name`, `type` (stock/etf), `isin`, `updated_at`, 主鍵為 `symbol` | P0 |
| TASK-1.2 | 在 `tw_stock_list` 表上啟用 RLS 策略，允許公開讀取（所有認證用戶可讀） | P0 |
| TASK-1.3 | 建立遷移文件 `docs/migrations/20260401_tw_stock_support.sql` | P0 |
| TASK-1.4 | 在 `tracked_indices` 表中添加 `category` 支持 `tw_stock`（如果尚未支持） | P1 |

**關鍵 SQL 結構**:
```sql
create table public.tw_stock_list (
  symbol text primary key,
  name text not null,
  type text not null, -- 'stock' or 'etf'
  isin text,
  updated_at timestamp with time zone default now()
);

alter table public.tw_stock_list enable row level security;

create policy "Allow public read on tw_stock_list" on public.tw_stock_list
  for select using (true);
```

---

### Phase 2: 後端服務實施

**GOAL-002**: 實現台灣股票數據同步服務

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-2.1 | 創建 `backend/app/services/tw_stock_sync.py`，實現 `sync_tw_stock_list()` 函數 | P0 |
| TASK-2.2 | 在 `tw_stock_sync.py` 中實現 TWSE API 解析邏輯，提取 symbol、name、type | P0 |
| TASK-2.3 | 實現批量 upsert 到 `tw_stock_list` 表（分批 200 條記錄） | P0 |
| TASK-2.4 | 添加日志記錄和錯誤處理 | P1 |
| TASK-2.5 | 在 `tw_stock_sync.py` 中添加快取檢查邏輯（避免頻繁同步） | P1 |

**實現參考**:
- 模仿 `tw_etf_sync.py` 的結構
- API 端點: `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL`
- HTTP Headers 與 ETF 同步類似
- 解析 JSON 響應中的 symbol 和 name 欄位

---

**GOAL-003**: 更新市場數據服務以支持台灣股票

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-3.1 | 更新 `backend/app/services/market_data.py` 中的 `_is_taiwan_stock()` 函數以支持通用符號檢測 | P0 |
| TASK-3.2 | 創建 `fetch_tw_stock_list()` 函數或合併至現有 `fetch_tw_etf_list()` 函數 | P0 |
| TASK-3.3 | 更新符號分類邏輯，區分 `tw_etf` 和 `tw_stock` 類別 | P0 |
| TASK-3.4 | 確保 yfinance/FinMind 日線數據源支持台灣股票符號 | P0 |
| TASK-3.5 | 在 `SYMBOL_CATALOG` 中添加台灣股票符號映射（可選，用於特殊流動性符號） | P2 |

**實現詳情**:
```python
# 更新 _is_taiwan_stock() 邏輯
def _is_taiwan_stock(symbol: str) -> bool:
    """Detect if a symbol is a Taiwan stock/ETF."""
    clean_sym = symbol.split(".")[0]
    # 4-6 位純數字或有 .TW/.TWO 后綴的符號
    if (clean_sym.isdigit() and 4 <= len(clean_sym) <= 6) or \
       any(symbol.upper().endswith(s) for s in [".TW", ".TWO"]):
        return True
    return False

async def fetch_tw_stock_list() -> list[dict]:
    # 從 Supabase 的 tw_stock_list 讀取，或觸發同步
    ...
```

---

### Phase 3: API 路由和端點更新

**GOAL-004**: 擴展 API 端點以返回台灣股票

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-4.1 | 更新 `backend/app/routers/market.py` 的 `_fetch_quote()` 函數，支持 `tw_stock` 分類 | P0 |
| TASK-4.2 | 修改 `/api/market/symbols` 端點，返回 `tw_stock` 符號列表 | P0 |
| TASK-4.3 | 添加新端點 `/api/market/tw-stocks` 用於獲取所有台灣股票清單（可選） | P1 |
| TASK-4.4 | 更新 `_fetch_quote()` 中的符號推斷邏輯，正確識別台股股票 vs ETF | P0 |

**端點示例**:
```python
@router.get("/symbols")
async def get_available_symbols():
    tw_etfs = await fetch_tw_etf_list()
    tw_stocks = await fetch_tw_stock_list()
    us_etfs = await fetch_us_etf_list()
    indices = get_index_list()
    return {
        "tw_etf": tw_etfs,
        "tw_stock": tw_stocks,  # 新增
        "us_etf": us_etfs,
        "index": indices
    }
```

---

### Phase 4: 調度器和定時任務

**GOAL-005**: 集成台灣股票同步至調度系統

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-5.1 | 在 `backend/app/scheduler.py` 中添加 `run_tw_stock_sync()` 函數 | P0 |
| TASK-5.2 | 在調度器中註冊每日定時任務（建議 01:30 AM 台灣時間，在 ETF 同步後） | P0 |
| TASK-5.3 | 在 `backend/app/main.py` 添加手動觸發端點 `/api/admin/sync-tw-stock` | P0 |
| TASK-5.4 | 更新 `docs/migrations/20260401_admin_system.sql` 中的 `scheduled_jobs` 表（若使用此表管理任務） | P1 |

**實現示例**:
```python
# scheduler.py
async def run_tw_stock_sync():
    """Wrapper to run sync_tw_stock_list and log outcome."""
    try:
        count = await sync_tw_stock_list()
        logger.info(f"[Scheduler] TW Stock sync complete: {count} records updated.")
    except Exception as e:
        logger.error(f"[Scheduler] TW Stock sync failed: {e}")

# 註冊定時任務
scheduler.add_job(
    run_tw_stock_sync,
    "cron",
    day_of_week="0-4",
    hour=1,
    minute=30,
    timezone="Asia/Taipei",
    id="tw_stock_sync"
)
```

---

### Phase 5: 數據模型和驗證

**GOAL-006**: 更新 Pydantic 模型以支持台灣股票

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-6.1 | 在 `backend/app/models/__init__.py` 中更新 `VALID_CATEGORIES`，添加 `tw_stock` | P0 |
| TASK-6.2 | 確保 `TrackingCreate` 和 `TrackingUpdate` 模型支持 `tw_stock` 類別 | P0 |
| TASK-6.3 | 更新任何其他引用 VALID_CATEGORIES 的模型 | P1 |

**修改示例**:
```python
# models/__init__.py
VALID_CATEGORIES = {"vix", "oil", "us_etf", "tw_etf", "tw_stock", "index", "crypto"}

# TrackingCreate 和 TrackingUpdate 已默認支持所有類別，無需改動
```

---

### Phase 6: 前端更新

**GOAL-007**: 更新前端 UI 以支持台灣股票選擇和顯示

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-7.1 | 更新 `frontend/src/api/marketApi.js` 的 API 調用，支持新的 `tw_stock` 端點 | P1 |
| TASK-7.2 | 在 Pinia store 中添加 `tw_stock` 符號列表（在 `frontend/src/stores/` 中） | P1 |
| TASK-7.3 | 更新符號選擇元件（通常在 `components/`），顯示台灣股票與 ETF 分開 | P1 |
| TASK-7.4 | 在投資組合、回測等頁面添加台灣股票搜索和篩選功能 | P2 |
| TASK-7.5 | 在警告/監控頁面的符號選擇中添加台灣股票選項 | P2 |

**前端實現參考**:
- 調用 `/api/market/symbols` 並解析 `tw_stock` 數組
- 在 UI 中將 `tw_stock` 與 `tw_etf` 分類顯示（例如 「台灣股票」和「台灣 ETF」兩個標籤頁）
- 符號搜索時同時搜索股票代碼和公司名稱

---

### Phase 7: 測試與驗證

**GOAL-008**: 添加完整測試覆蓋

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-7.1 | 在 `tests/unit/test_tw_stock_sync.py` 添加單元測試，測試 `sync_tw_stock_list()` | P0 |
| TASK-7.2 | 添加集成測試 `tests/e2e/test_tw_stock_api.py`，測試新的 API 端點 | P0 |
| TASK-7.3 | 測試 yfinance/FinMind 是否正確支持新的台灣股票符號 | P0 |
| TASK-7.4 | 測試數據庫 RLS 政策，確保權限正確 | P1 |
| TASK-7.5 | 測試投資組合和回測功能是否支持台灣股票 | P1 |

**測試用例示例**:
```python
# tests/unit/test_tw_stock_sync.py
@pytest.mark.asyncio
async def test_sync_tw_stock_list():
    """Test fetching and upserting TW stocks from TWSE."""
    count = await sync_tw_stock_list()
    assert count > 0
    # Verify sample symbols are present
    sb = get_supabase()
    res = sb.table("tw_stock_list").select("symbol").eq("symbol", "2330").execute()
    assert res.data and len(res.data) > 0
```

---

### Phase 8: 遷移和部署

**GOAL-009**: 安全部署數據庫變更和新代碼

| Task | 詳細描述 | 優先級 |
|------|--------|--------|
| TASK-8.1 | 創建並測試遷移文件 (`docs/migrations/20260401_tw_stock_support.sql`) | P0 |
| TASK-8.2 | 在生產環境前，在開發/測試環境執行遷移 | P0 |
| TASK-8.3 | 手動執行首次 `sync_tw_stock_list()` 以填充初始數據 | P0 |
| TASK-8.4 | 更新部署文檔 (`docs/deploy/deploy.md`) 描述新的同步任務 | P1 |
| TASK-8.5 | 驗證現有 API 與新功能向後兼容性 | P0 |

---

## 3. 替代方案

- **ALT-001**: 合併 `tw_etf_list` 和新的 `tw_stock_list` 為單一 `tw_security_list` 表，使用 `type` 欄位區分。優點：簡化查詢；缺點：打破現有代碼。
- **ALT-002**: 使用第三方 API（FinMind、Fugleapi）替代 TWSE OpenAPI。優點：可能更豐富的數據；缺點：成本、API 限制、依賴外部服務。
- **ALT-003**: 只支持 TWSE 上市股票，不支持上櫃。優點：減少數據量；缺點：功能受限。

**選定方案**：ALT-001 之改進版——保留現有 `tw_etf_list` 表，創建新的 `tw_stock_list` 表，在應用層統一處理。這樣向後兼容且支持未來擴展。

---

## 4. 依賴關係

- **DEP-001**: Supabase PostgreSQL 數據庫及 RLS 功能
- **DEP-002**: TWSE OpenAPI 的穩定可用性和 JSON 格式
- **DEP-003**: yfinance 和 FinMind API 的台灣股票符號支持
- **DEP-004**: FastAPI 異步框架和 httpx 客戶端
- **DEP-005**: APScheduler 用於定時任務

---

## 5. 影響的文件

| 文件路徑 | 變更類型 | 說明 |
|--------|--------|------|
| `backend/app/services/tw_stock_sync.py` | 新建 | 台灣股票同步服務 |
| `backend/app/services/market_data.py` | 修改 | 添加 `fetch_tw_stock_list()`，更新符號檢測邏輯 |
| `backend/app/routers/market.py` | 修改 | 更新 `_fetch_quote()`，支持 `tw_stock` 類別 |
| `backend/app/scheduler.py` | 修改 | 註冊 `run_tw_stock_sync()` 定時任務 |
| `backend/app/main.py` | 修改 | 添加 `/api/admin/sync-tw-stock` 端點 |
| `backend/app/models/__init__.py` | 修改 | 更新 `VALID_CATEGORIES` |
| `docs/migrations/20260401_tw_stock_support.sql` | 新建 | 數據庫遷移腳本 |
| `tests/unit/test_tw_stock_sync.py` | 新建 | 單元測試 |
| `tests/e2e/test_tw_stock_api.py` | 新建 | 集成測試 |
| `frontend/src/api/marketApi.js` | 修改 | 添加 `tw_stock` API 調用 |
| `frontend/src/stores/marketStore.js` | 修改 | 添加 `tw_stock` 符號列表狀態 |
| `frontend/src/components/...` | 修改 | UI 符號選擇元件 |
| `docs/deploy/deploy.md` | 修改 | 更新部署指南 |

---

## 6. 測試計劃

**單元測試**:
- `test_tw_stock_sync.py`: 測試 TWSE API 解析和數據庫 upsert
- `test_market_data.py`: 測試 `fetch_tw_stock_list()` 和符號檢測

**集成測試**:
- `test_tw_stock_api.py`: 測試 `/api/market/symbols` 返回 `tw_stock`
- `test_tracking_api.py`: 測試跟蹤台灣股票（RLS、警告觸發）
- `test_backtest_api.py`: 測試以台灣股票進行回測

**性能測試**:
- 驗證 `fetch_tw_stock_list()` 在 <1s 內完成（Redis 快取）
- 驗證 `sync_tw_stock_list()` 在 <30s 內完成

**兼容性測試**:
- 驗證現有 ETF 功能未受影響
- 驗證舊代碼仍然使用 `tw_etf` 類別正常工作

---

## 7. 風險與假設

| 風險/假設 | 影響 | 緩解措施 |
|---------|------|--------|
| **RISK-001**: TWSE API 變更或不可用 | 高 | 實施重試邏輯、快取、備用數據源 |
| **RISK-002**: yfinance 不支持某些台灣股票符號 | 中 | 使用 FinMind API 作為備份，測試常見符號 |
| **RISK-003**: 數據庫遷移失敗導致生產環境宕機 | 高 | 在測試環境完整驗證、備份、回滾計劃 |
| **ASSUMPTION-001**: TWSE API 返回格式穩定 | 中 | 定期監控 API 響應，版本控制 |
| **ASSUMPTION-002**: 台灣股票符號為 4-6 位純數字 | 低 | 已驗證，但需監控上市公司變化 |

---

## 8. 相關規範 & 進一步閱讀

- [TWSE OpenAPI 文檔](https://openapi.twse.com.tw/)
- [专项指南: 现有 TW ETF 同步实现](backend/app/services/tw_etf_sync.py)
- [市场数据服务架构](backend/app/services/market_data.py)
- [API 路由结构](backend/app/routers/market.py)
- [Supabase RLS 政策](https://supabase.com/docs/guides/auth/row-level-security)

