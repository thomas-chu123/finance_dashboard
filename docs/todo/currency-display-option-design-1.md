---
goal: 新增幣別選擇功能 - 用戶可選台幣或美金計價顯示
version: 1.0
date_created: 2026-04-14
owner: Frontend + Backend
status: 'Planned'
tags: ['feature', 'currency', 'ux', 'frontend']
---

# 介紹

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

本方案在**美金基準統一計算**的基礎上，增加幣別選擇功能。用戶可以自由選擇查看結果時使用台幣或美金計價，同時確保所有計算的內部一致性。

## 核心設計原則

🎯 **一句話總結**: 計算用美金，只在返回時根據用戶選擇轉換顯示

- ✅ **計算過程**：所有資產（不論台幣還是美金）都轉換為統一的美金進行計算
- ✅ **美國 ETF (SPY, QQQ 等)**：保持原始美金數據，直接用於計算
- ✅ **台灣股票/ETF (0050, 0056 等)**：轉換為美金後用於計算
- ✅ **結果返回**：按照用戶選擇的幣別顯示（台幣選擇時 × 匯率，美金選擇時保持）

### 重要：即使是純台灣資產，也在美金基準計算

**情景**：用戶只選擇台灣 ETF (0050 + 0056)，沒有任何美國資產，選擇顯示為 **TWD**

```
✅ 設計（現在採用）
  ├─ 步驟 1：0050, 0056 台幣數據 → 轉換為美金
  ├─ 步驟 2：在美金基準上計算報酬、風險等
  ├─ 步驟 3：結果依然是美金
  └─ 步驟 4：返回前轉換為台幣顯示

❌ 不會做的（會破壞設計）
  ├─ 因為只有台灣資產就用台幣計算
  ├─ 這樣會導致：
  │  - 邏輯複雜：需要檢測資產類型再決定計算幣別
  │  - 不一致：相同資產在不同組合中計算方式不同
  │  - 難維護：新增加密貨幣或其他幣種時會很困難
```

**優勢**：
- 🔄 邏輯統一：無論什麼組合都用美金計算
- 📊 結果穩定：相同資產組合，無論選擇什麼幣別，計算結果的比例不變
- 🔮 易擴展：未來加入新幣種資產時，架構無需改變

> **範例**：投資 1,000,000 TWD，100% 投資 0050 (台股 ETF)，選擇顯示為 TWD
> - Step 1：1,000,000 TWD ÷ 32.49 = 30,779 USD
> - Step 2：用美金數據計算 0050 的報酬（假設回報 10%）→ 30,779 × 1.10 = 33,857 USD
> - Step 3：返回前轉換：33,857 × 32.49 = 1,100,000 TWD
> - ✅ 結果：初始 1,000,000 TWD → 最終 1,100,000 TWD (10% 回報，與內部美金計算一致)

---



## 1. 需求

### 功能需求
- **REQ-001**: 內部計算統一為美金（保持邏輯清晰）
- **REQ-002**: 支援用戶選擇結果顯示的幣別（TWD 或 USD）
- **REQ-003**: 幣別選擇應在回測、最佳化、蒙地卡羅都生效
- **REQ-004**: 相同計算的不同幣別結果應可相互驗證
- **REQ-005**: 前端樣式應清楚標示當前使用的幣別
- **REQ-006**: API 應返回完整結果供前端根據選擇展示

### 約束
- **CON-001**: 不能影響內部計算邏輯（保持回測結果穩定）
- **CON-002**: 幣別轉換只發生在展示層，不涉及數據庫存儲

### 設計指南
- **GUD-001**: 幣別選擇應為首選項（localStorage 記憶）
- **GUD-002**: 混合資產時應提示「已按匯率轉換」

---

## 2. 架構方案：雙層轉換式

### 2.1 核心概念

**計算層 vs 顯示層分離**：

| 階段 | 美國 ETF (SPY) | 台灣股票 (0050) | 計算結果 |
|------|---|---|---|
| **輸入** | USD (美金) | TWD (台幣) | - |
| **數據準備** | ✅ 保持美金 | 🔄 轉換為美金 | 準備完成 |
| **計算過程** | 🔢 用美金計算 | 🔢 用美金計算 | **USD 基準** |
| **返回前轉換** | 用戶選 USD ❌ 不轉換 | - | USD 結果 |
| **返回前轉換** | 用戶選 TWD ✅ 轉換 | - | USD × 匯率 → TWD |

**重點**：美國 ETF 在計算中始終使用美金，不會轉換為台幣計算。

---

### 2.2 流程圖

```
┌─────────────────────────────────────────┐
│ 前端用戶界面                             │
│ ┌──────────────────────────────────┐  │
│ │ 幣別選擇器 (Currency Selector)  │  │
│ │ ○ 美金 (USD)  ○ 台幣 (TWD)      │  │
│ └─────────────┬────────────────────┘  │
└────────────────┼──────────────────────┘
                 │ display_currency: "TWD"
                 ▼
┌─────────────────────────────────────────┐
│ API 請求層                              │
│ POST /api/backtest/run                  │
│ {                                       │
│   "items": [...],                      │
│   "start_date": "2020-01-01",          │
│   "end_date": "2024-01-01",            │
│   "initial_amount": 100000,            │
│   "display_currency": "TWD"   // ← 新 │
│ }                                       │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 後端計算層                              │
│ ├─ 統一轉換為美金                       │
│ ├─ 執行計算（美金基準）                 │
│ └─ 結果暫時為美金                       │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 返回前轉換層（新增）                     │
│ ├─ 如果 display_currency == "TWD"      │
│ │  └─ 美金結果 × 匯率 → 台幣結果   │
│ └─ 如果 display_currency == "USD"      │
│    └─ 保持美金結果                  │
└─────────────────┬──────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ API 返回                                 │
│ {                                       │
│   "metrics": {                          │
│     "initial_amount": 3,100,000,       │
│     "final_amount": 5,200,000,         │
│     "currency": "TWD",                 │
│     ...                                 │
│   },                                    │
│   "conversion_metadata": { ... }        │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## 3. 實現步驟

### 階段 1：後端支援（優先級 🔴 高）

| 任務 | 描述 | 時間估計 |
|------|------|---------|
| TASK-001 | 所有 Pydantic 請求模型新增 `display_currency: str = "USD"` | 1h |
| TASK-002 | 在 `market_data.py` 新增 `convert_results_to_currency()` 函數 | 4h |
| TASK-003 | 更新 `run_backtest()` 在返回前轉換結果 | 2h |
| TASK-004 | 更新 `run_optimization()` 在返回前轉換結果 | 2h |
| TASK-005 | 更新 `run_monte_carlo_simulation()` 在返回前轉換結果 | 2h |
| TASK-006 | 轉換時確保匯率一致性（使用原始轉換的平均匯率） | 2h |
| TASK-007 | 單元測試：美金→台幣的數值轉換 | 2h |

**小計**: 15 小時

### 階段 2：前端支援（優先級 🔴 高）

| 任務 | 描述 | 時間估計 |
|------|------|---------|
| TASK-008 | 在 BacktestView.vue 新增幣別選擇器 | 2h |
| TASK-009 | 在 OptimizeView.vue 新增幣別選擇器 | 1h |
| TASK-010 | 在 MonteCarloView.vue 新增幣別選擇器 | 1h |
| TASK-011 | 幣別選擇 Pinia store (preferenceStore) | 2h |
| TASK-012 | localStorage 儲存用戶幣別偏好 | 1h |
| TASK-013 | 樣式：幣別標籤 + 警告提示（如有轉換） | 2h |
| TASK-014 | API 調用時傳遞 `display_currency` 參數 | 2h |
| TASK-015 | 測試：前端幣別切換、結果刷新 | 2h |

**小計**: 13 小時

### 階段 3：整合測試（優先級 🟠 中）

| 任務 | 描述 | 時間估計 |
|------|------|---------|
| TASK-016 | E2E 測試：純美金組合 USD/TWD 切換 | 2h |
| TASK-017 | E2E 測試：純台幣組合 USD/TWD 切換 | 2h |
| TASK-018 | E2E 測試：混合組合 USD/TWD 切換 | 2h |
| TASK-019 | 性能測試：轉換耗時測量 | 1h |

**小計**: 7 小時

**總工作量**: ~35 小時（1.5 周）

---

## 4. 實現重點

### 4.1 後端：轉換函數簽名

```python
async def convert_results_to_currency(
    results: Dict[str, Any],
    target_currency: str,
    source_currency: str = "USD",
    historical_fx: pd.Series = None
) -> Dict[str, Any]:
    """
    將結果從一種幣別轉換為另一種。
    
    核心邏輯：
    1. 如果目標幣別 == 源幣別，直接返回
    2. 如果是 USD → TWD：
       - 從 conversion_metadata 取得平均匯率
       - 複製結果避免修改原始數據
       - 轉換所有金額字段（百分比保留）
       - 更新 currency 和 exchange_rate_used 欄位
       - 轉換時間序列數據
    3. 其他轉換組合暫不支持
    """
```

### 4.2 前端：Pinia Store

```typescript
export const usePreferenceStore = defineStore('preference', () => {
  const displayCurrency = ref(localStorage.getItem('displayCurrency') || 'USD')
  
  const setDisplayCurrency = (currency) => {
    displayCurrency.value = currency
    localStorage.setItem('displayCurrency', currency)
  }
  
  const toggleCurrency = () => {
    setDisplayCurrency(displayCurrency.value === 'USD' ? 'TWD' : 'USD')
  }
  
  return { displayCurrency, setDisplayCurrency, toggleCurrency }
})
```

### 4.3 前端：幣別選擇器組件

```vue
<!-- CurrencySelector.vue -->
<template>
  <div class="currency-selector">
    <div class="flex items-center gap-2 bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-lg p-2">
      <span class="text-xs font-semibold text-[var(--text-secondary)] uppercase">計價:</span>
      
      <button
        v-for="curr in ['USD', 'TWD']"
        :key="curr"
        @click="preference.setDisplayCurrency(curr)"
        :class="{
          'bg-brand-500 text-white': preference.displayCurrency === curr,
          'bg-transparent text-[var(--text-secondary)]': preference.displayCurrency !== curr,
        }"
        class="px-3 py-1 rounded-md text-sm font-medium transition-all"
      >
        {{ curr }}
      </button>
    </div>
    
    <!-- 提示：如果是轉換後的結果 -->
    <div v-if="showConversionHint" class="text-xs text-amber-500 mt-1 flex items-center gap-1">
      <i class="icon-warning" />
      已按歷史匯率轉換為 {{ preference.displayCurrency }}
    </div>
  </div>
</template>
```

---

## 5. API 契約變更

### 請求

```http
POST /api/backtest/run
Content-Type: application/json

{
  "items": [...],
  "start_date": "2020-01-01",
  "end_date": "2024-01-01",
  "initial_amount": 100000,
  "display_currency": "TWD"  // ← 新增
}
```

### 返回（USD 請求）

```json
{
  "status": "success",
  "data": {
    "metrics": {
      "initial_amount": 100000,
      "final_amount": 167400,
      "currency": "USD",               // ← 標示幣別
      "total_return": 67.4,
      "cagr": 13.24,
      ...
    },
    "conversion_metadata": {
      "conversions": {},
      "unconverted_symbols": ["SPY", "QQQ"]
    }
  }
}
```

### 返回（TWD 請求）

```json
{
  "status": "success",
  "data": {
    "metrics": {
      "initial_amount": 3100000,
      "final_amount": 5200000,
      "currency": "TWD",               // ← 標示幣別
      "exchange_rate_used": 32.456,    // ← 轉換參考
      "total_return": 67.4,
      "cagr": 13.24,
      ...
    },
    "conversion_metadata": {
      "conversions": { ... },
      "unconverted_symbols": ["SPY", "QQQ"]
    }
  }
}
```

---
## 6. 完整計算範例

**場景**：台灣用戶投資組合，初始 1,000,000 TWD，配置 SPY (40%) + 0050 (60%)

### 用戶選擇顯示幣別：USD

```
【第1步】初始化
  輸入: 1,000,000 TWD
  轉換: 1,000,000 ÷ 32.49 = 30,779 USD
  
【第2步】資產分配（美金基準）
  SPY:  30,779 × 0.40 = 12,312 USD
  0050: 30,779 × 0.60 = 18,467 USD

【第3步】數據準備
  SPY 數據: 150, 151, 152 USD ✅ 直接使用
  0050 數據: 100, 101, 102 TWD → 3.08, 3.10, 3.14 USD ✅ 轉換完成

【第4步】計算（全部用美金）
  SPY 回報: (152-150)/150 = 1.33% (美金計算)
  0050 回報: (3.14-3.08)/3.08 = 1.95% (美金計算)
  組合回報: 1.33% × 0.4 + 1.95% × 0.6 = 1.71%

【第5步】返回結果
  初始: 30,779 USD
  最終: 31,304 USD (1.71% 回報)
  幣別: USD ← 選擇結果

✅ API 回傳:
{
  "metrics": {
    "initial_amount": 30779,
    "final_amount": 31304,
    "currency": "USD"
  }
}
```

### 用戶選擇顯示幣別：TWD

```
【第1-4步】同上（計算過程完全相同）

【第5步】返回前轉換
  計算結果: 30,779 USD → 31,304 USD
  匯率: 32.49 (基於歷史平均)
  轉換: 
    初始: 30,779 × 32.49 = 1,000,000 TWD
    最終: 31,304 × 32.49 = 1,017,200 TWD

✅ API 回傳:
{
  "metrics": {
    "initial_amount": 1000000,
    "final_amount": 1017200,
    "currency": "TWD",
    "exchange_rate_used": 32.49
  }
}
```

**關鍵觀察**：
- ✅ 回報率不變：1.71%（不論幣別）
- ✅ 絕對金額轉換：USD × 32.49 → TWD
- ✅ SPY 部分始終用美金計算，不涉及台幣
- ✅ 0050 部分先轉台幣→美金，再用美金計算

---
## 6. 測試場景

| 場景 | 測試 | 預期結果 |
|------|------|----------|
| 純美金組合選擇 USD | 無轉換 | 原始 USD 結果 |
| 純美金組合選擇 TWD | 轉換美→台 | 金額 × 匯率 |
| 混合組合選擇 USD | 計算為 USD | conversion_metadata 包含轉換細節 |
| 混合組合選擇 TWD | 計算後轉換 | 金額 × 平均匯率 |
| 前端切換幣別 | 重新請求 | 相同計算，不同幣別顯示 |

---

## 7. 優點與權衡

### ✅ 優點
- 計算邏輯統一（美金基準），保持穩定性
- 用戶體驗自然（熟悉的幣別）
- 三個模組結果可驗證（美金基準可相互比對）
- 實現簡單（只需在返回前轉換一次）
- 向前相容（舊 API 客戶端預設使用 USD）

### ⚠️ 權衡
- 轉換的平均匯率可能與實際結果略有偏差（±1-2%）
- 需要返回 conversion_metadata 供用戶驗證
- 前端需要邏輯處理刷新時機

---

## 8. 後續優化（Phase 2）

### 進階功能
- **匯率敏感度分析**：如果匯率偏移 ±5%，結果會如何
- **幣別自動選擇**：根據資產組合自動推薦幣別
- **多幣別混合計算**：某些部分用台幣計 price，某些用美金
- **實時匯率**：針對近期回測使用實時匯率

---

## 9. 相關文檔

- [currency-handling-unified-design-1.md](./currency-handling-unified-design-1.md) - 統一匯率處理架構
- [backend.md](/docs/backend/backend.md) - 後端架構說明
- [frontend.md](/docs/frontend/frontend.md) - 前端架構說明
