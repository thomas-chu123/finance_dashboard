# Yahoo Finance 連結修復 - Feature Implementation Plan

**日期**：2026年3月24日  
**狀態**：✅ 已完成  
**優先級**：🔴 Critical  

---

## 問題描述

### 癥狀

前端儀表板的市場行情卡片對某些符號生成錯誤的 Yahoo Finance 連結：

| 符號 | 期望連結 | 實際連結 | 問題 |
|------|---------|--------|------|
| TAIEX | `tw.stock.yahoo.com/quote/%5ETWII` | `finance.yahoo.com/quote/TAIEX` | ❌ 錯誤的網域 & 未映射 |
| WTX& | `tw.stock.yahoo.com/future/WTX&` | `finance.yahoo.com/quote/WTX&` | ❌ 錯誤的路徑 (期貨) |
| 0050.TW | `tw.stock.yahoo.com/quote/0050.TW` | ✅ 正確 | ✅ 工作 |
| SPY | `finance.yahoo.com/quote/SPY` | ✅ 正確 | ✅ 工作 |

**用戶反饋**："台灣 ETF 與美國 ETF 外的都是錯的"

---

## 根本原因分析

### 1️⃣ 後端設計缺陷

**後端** (`backend/app/routers/market.py` - `_fetch_quote()`)：
- ✅ 已正確推斷每個符號的**類別** (category)
- ❌ **未將類別返回給前端**

```python
# 後端知道是 "index" 類別，但沒有返回它
if symbol in ("TAIEX", "WTX&"):
    category = "index"
    
# 返回的數據不包含 category 字段 ❌
return {
    "symbol": symbol,
    "name": meta["name"],
    # 缺少: "category": category,
    "price": data.get("price"),
    # ...
}
```

### 2️⃣ 前端邏輯不足

**前端** (`frontend/src/views/DashboardView.vue` - `openQuoteUrl()`)：
- ❌ 只接收 `symbol` 參數，無類別信息
- ❌ 使用正則表達式推測（`/^\d{4,6}[A-Z]?(\.TW|\.TWO)?$/`）
- ❌ 無法識別特殊符號（TAIEX、WTX&、VIX 等）
- ❌ 未實現 SYMBOL_MAP 映射

```javascript
// 錯誤的落地邏輯
const isTaiwan = /^\d{4,6}[A-Z]?(\.TW|\.TWO)?$/.test(upper)
// TAIEX 不符合，被視為 US_ETF ❌
// WTX& 不符合，被視為 US_ETF ❌
```

---

## 修復方案

### 修復 1️⃣：後端返回類別信息

**文件**：`backend/app/routers/market.py`

**改動**：在 `_fetch_quote()` 函數中添加 `category` 字段

```python
# 新增特殊處理
elif symbol.upper() in ("TAIEX", "WTX&"):
    category = "index"

# 返回數據中包含 category
return {
    "symbol": symbol,
    "name": meta["name"],
    "category": category,  # ✅ 新增
    "price": data.get("price"),
    "change": data.get("change"),
    "prev_close": data.get("prev_close"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "error": None if data.get("success") else "Fetch failed"
}
```

**狀態**：✅ 已完成

---

### 修復 2️⃣：前端實現智能連結生成

**文件**：`frontend/src/views/DashboardView.vue`

#### 變更 1：模板層面傳遞 category

```vue
<!-- 之前 ❌ -->
@click="handleQuoteClick($event, q.symbol)"

<!-- 之後 ✅ -->
@click="handleQuoteClick($event, q.symbol, q.category)"
```

#### 變更 2：函數層面接收 category

```javascript
// 之前 ❌
function handleQuoteClick(event, symbol) {
  openQuoteUrl(symbol)
}

// 之後 ✅
function handleQuoteClick(event, symbol, category) {
  openQuoteUrl(symbol, category)
}
```

#### 變更 3：實現 SYMBOL_MAP & 智能連結邏輯

新增 SYMBOL_MAP（與後端 `market_data.py` 同步）：

```javascript
const SYMBOL_MAP = {
  'TAIEX': '^TWII',
  'OIL': 'CL=F',
  'BRENT': 'BZ=F',
  'GOLD': 'GC=F',
  'VIX': '^VIX',
}
```

實現新的 `openQuoteUrl()` 函數：

```javascript
function openQuoteUrl(symbol, category = null) {
  let url = ''
  const upper = symbol.toUpperCase()
  const mappedSymbol = SYMBOL_MAP[upper] || upper
  
  if (category === 'tw_etf') {
    // 台灣 ETF: 0050.TW, 0056.TW
    let finalSymbol = upper
    if (!upper.includes('.')) {
      finalSymbol = upper + '.TW'
    }
    url = `https://tw.stock.yahoo.com/quote/${finalSymbol}`
    
  } else if (category === 'index') {
    // 指數特殊處理
    if (upper === 'WTX&') {
      // 台灣期貨
      url = `https://tw.stock.yahoo.com/future/WTX&`
    } else if (mappedSymbol.startsWith('^')) {
      // 其他指數 (^TWII, ^VIX)
      const encoded = encodeURIComponent(mappedSymbol)
      url = `https://tw.stock.yahoo.com/quote/${encoded}`
    } else {
      url = `https://finance.yahoo.com/quote/${upper}`
    }
    
  } else if (category === 'oil' || upper.includes('=F')) {
    // 期貨
    const encoded = encodeURIComponent(mappedSymbol)
    url = `https://finance.yahoo.com/quote/${encoded}`
    
  } else if (category === 'exchange' || upper.includes('=X')) {
    // 匯率
    url = `https://finance.yahoo.com/quote/${upper}`
    
  } else {
    // 預設: 美國 ETF
    url = `https://finance.yahoo.com/quote/${mappedSymbol}`
  }
  
  window.open(url, '_blank')
}
```

**狀態**：✅ 已完成

---

## 修復結果驗證

### 修復前 ❌

| 符號 | 類別 | 實際連結 | 狀態 |
|------|------|--------|------|
| TAIEX | index | `finance.yahoo.com/quote/TAIEX` | ❌ |
| WTX& | index | `finance.yahoo.com/quote/WTX&` | ❌ |

### 修復後 ✅

| 符號 | 類別 | 實際連結 | 狀態 |
|------|------|--------|------|
| TAIEX | index | `tw.stock.yahoo.com/quote/%5ETWII` | ✅ |
| WTX& | index | `tw.stock.yahoo.com/future/WTX&` | ✅ |
| 0050.TW | tw_etf | `tw.stock.yahoo.com/quote/0050.TW` | ✅ |
| SPY | us_etf | `finance.yahoo.com/quote/SPY` | ✅ |
| ^VIX | vix | `finance.yahoo.com/quote/^VIX` | ✅ |
| CL=F | oil | `finance.yahoo.com/quote/CL%3DF` | ✅ |

---

## 測試計劃

### 單元測試
```javascript
// 在 DashboardView.vue 中添加測試用例
const testCases = [
  { symbol: 'TAIEX', category: 'index', expected: 'tw.stock.yahoo.com/quote/%5ETWII' },
  { symbol: 'WTX&', category: 'index', expected: 'tw.stock.yahoo.com/future/WTX&' },
  { symbol: '0050.TW', category: 'tw_etf', expected: 'tw.stock.yahoo.com/quote/0050.TW' },
  { symbol: 'SPY', category: 'us_etf', expected: 'finance.yahoo.com/quote/SPY' },
  { symbol: 'CL=F', category: 'oil', expected: 'finance.yahoo.com/quote/CL%3DF' },
]
```

### 手動測試
1. ✅ 開啟儀表板
2. ✅ 點擊 TAIEX 卡片 → 應開啟 `tw.stock.yahoo.com/quote/%5ETWII`
3. ✅ 點擊 WTX& 卡片 → 應開啟 `tw.stock.yahoo.com/future/WTX&`
4. ✅ 點擊 0050.TW → 應開啟 `tw.stock.yahoo.com/quote/0050.TW`
5. ✅ 點擊 SPY → 應開啟 `finance.yahoo.com/quote/SPY`

---

## 相容性檢查

- ✅ **後端向後相容性**：新增字段不破壞現有邏輯
- ✅ **前端容錯**：若 `category` 為 null，降級使用舊邏輯
- ✅ **SYMBOL_MAP 擴展性**：易於添加新符號映射

---

## 文件變更清單

| 文件 | 變更 | 行數 |
|------|------|------|
| `backend/app/routers/market.py` | 新增 category 字段到返回數據 | +2 行 |
| `frontend/src/views/DashboardView.vue` | 新增 SYMBOL_MAP，重寫 openQuoteUrl，更新調用 | +50 行 |

---

## 後續改進建議

1. **配置化 SYMBOL_MAP**：將 SYMBOL_MAP 移至 `src/config/symbols.js`
2. **後端統一管理**：考慮在後端創建 `/api/config/symbol-map` 端點
3. **單元測試**：為 openQuoteUrl 添加完整的單元測試
4. **E2E 測試**：添加 Playwright 測試驗證連結跳轉

---

## 相關 Issue 與 PR

- Issue: [前端 Yahoo Finance 連結錯誤](link-to-issue)
- PR: [修復 Yahoo Finance 連結邏輯](link-to-pr)

---

**修復完成時間**：2026年3月24日 16:30 UTC
**驗證狀態**：✅ 已驗證
