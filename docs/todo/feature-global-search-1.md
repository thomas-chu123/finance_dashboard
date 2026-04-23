---
goal: 實作全局搜尋功能，支持指數搜尋、快速添加到追蹤、及上下文搜尋
version: 1.0
date_created: 2026-04-15
status: 'Planned'
tags: [feature, search, ui, api]
---

# 搜尋功能實行計劃

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

## 1. 需求與限制

### 功能需求
- **REQ-001**: 用戶能在投資總覽頁快速搜尋指數並添加到追蹤卡片
- **REQ-002**: 搜尋支持按名稱、代碼、類別篩選 (台灣ETF、美股ETF、基金等)
- **REQ-003**: 搜尋結果實時顯示（debounce 500ms）
- **REQ-004**: 支援全局搜尋（快捷鍵 Cmd/Ctrl + K）和上下文搜尋
- **REQ-005**: 搜尋結果應顯示當前價格、走勢、類別信息

### 技術限制
- **CON-001**: 必須使用現有的 `/api/market/symbol-catalog` API
- **CON-002**: 前端搜尋應優先使用本地 catalog，避免過多 HTTP 請求
- **CON-003**: 搜尋 UI 需要支持深色模式

### 性能指標
- **PAT-001**: 搜尋響應時間 < 200ms (本地篩選)
- **PAT-002**: 每次搜尋按鍵最多發起一次 HTTP 請求 (使用 debounce)
- **GUD-001**: 搜尋框應支持快捷鍵啟動 (Cmd+K / Ctrl+K)

## 2. 實作步驟

### Phase 1：後端 API 層 (搜尋端點)

**GOAL-001**: 新增搜尋 API 端點支持按關鍵字、類別篩選指數

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-001 | 新增 `GET /api/market/search` 端點 (支持 q, category, limit 參數) | | |
| TASK-002 | 實作分詞搜尋邏輯 (symbol + name_zh + name_en 模糊匹配) | | |
| TASK-003 | 端點返回結果含當前價格、走勢、分類 | | |
| TASK-004 | 添加單元測試 `test_market_search.py` | | |

**實現細節**：
```python
# File: backend/app/routers/market.py - 新增端點

@router.get("/search")
async def search_symbols(
    q: str = Query("", min_length=1),
    category: Optional[str] = Query(None),  # 篩選: tw_etf, us_etf, fund, index
    limit: int = Query(15, le=50)
):
    """搜尋指數/基金，支持按名稱、代碼、類別篩選。
    
    Args:
        q: 搜尋關鍵字 (支持 symbol 或 name_zh 或 name_en)
        category: 篩選類別 (tw_etf, us_etf, fund, index, vix, oil, exchange)
        limit: 返回結果數量 (最多50)
    
    Returns:
        {
            "results": [
                {
                    "symbol": "0050.TW",
                    "yahoo_symbol": "0050.TW",
                    "name_zh": "元大台灣50",
                    "name_en": "Yuanta Taiwan 50",
                    "category": "tw_etf",
                    "price": 156.25,
                    "change": 1.5,
                    "change_pct": 0.97
                },
                ...
            ],
            "total": 3
        }
    """
```

### Phase 2：前端 API 層

**GOAL-002**: 建立前端 API 客戶端供 UI 組件使用

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-005 | 建立 `frontend/src/api/search.js` API 客戶端模組 | | |
| TASK-006 | 實作搜尋請求函數 (含 debounce 和 cache) | | |
| TASK-007 | 建立 Pinia store `useSearchStore` 管理搜尋狀態 | | |

**實現細節**：
```javascript
// File: frontend/src/api/search.js

import axios from 'axios'
import { debounce } from '../utils/debounce'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

let cachedResults = {}

export const searchSymbols = debounce(async (query, category = null, limit = 15) => {
  const cacheKey = `${query}:${category}:${limit}`
  
  if (cachedResults[cacheKey]) {
    return cachedResults[cacheKey]
  }
  
  const res = await axios.get(`${API_BASE}/api/market/search`, {
    params: { q: query, category, limit }
  })
  
  cachedResults[cacheKey] = res.data.results
  return res.data.results
}, 500)

export const clearSearchCache = () => {
  cachedResults = {}
}
```

```javascript
// File: frontend/src/stores/useSearchStore.js (Pinia)

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { searchSymbols } from '../api/search'

export const useSearchStore = defineStore('search', () => {
  const query = ref('')
  const results = ref([])
  const isLoading = ref(false)
  const selectedCategory = ref(null)
  
  const categories = [
    { label: '全部', value: null },
    { label: '台灣ETF', value: 'tw_etf' },
    { label: '美股ETF', value: 'us_etf' },
    { label: '基金', value: 'fund' },
    { label: '指數', value: 'index' }
  ]
  
  const performSearch = async (q, category = null) => {
    if (quit || q.length < 1) {
      results.value = []
      return
    }
    
    isLoading.value = true
    try {
      results.value = await searchSymbols(q, category)
    } finally {
      isLoading.value = false
    }
  }
  
  return {
    query,
    results,
    isLoading,
    selectedCategory,
    categories,
    performSearch
  }
})
```

### Phase 3：前端 UI 組件

**GOAL-003**: 實作搜尋 UI 組件（全局搜尋 + 上下文搜尋）

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-008 | 新增 `GlobalSearchModal.vue` 組件（Cmd/Ctrl+K 啟動） | | |
| TASK-009 | 新增 `SymbolSearchInput.vue` 組件（可複用的搜尋輸入框） | | |
| TASK-010 | 在 DashboardView 集成搜尋組件 | | |
| TASK-011 | 在 LayoutView 集成全局搜尋快捷鍵監聽 | | |

**實現細節**：

```vue
<-- Purpose: Consolidio-- Purpose: File: frontend/src/components/GlobalSearchModal.vue -->

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-start justify-center pt-24">
      <-- Purpose: Consolidio-- Purpose: Backdrop -->
      <div 
        class="absolute inset-0 bg-black/50 backdrop-blur-sm" 
        @click="close"
      />
      
      <-- Purpose: Consolidio-- Purpose: Modal -->
      <div class="relative w-full max-w-2xl mx-4 bg-[var(--bg-main)] rounded-lg shadow-2xl border border-[var(--border-color)]">
        <-- Purpose: Consolidio-- Purpose: Search Input -->
        <div class="flex items-center px-4 py-3 border-b border-[var(--border-color)]">
          <Search :size="18" class="text-zinc-400" />
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            placeholder="搜尋指數、基金代碼或名稱... (輸入 ? 查看幫助)"
            class="flex-1 ml-3 bg-transparent outline-none text-[var(--text-primary)] placeholder-zinc-500"
            @input="handleInput"
          />
          <kbd class="hidden sm:inline px-2 py-1 text-xs font-semibold bg-zinc-200 dark:bg-zinc-700 rounded">ESC</kbd>
        </div>
        
        <-- Purpose: Consolidio-- Purpose: Category Filter -->
        <div class="px-4 py-2 flex gap-2 border-b border-[var(--border-color)] overflow-x-auto">
          <button
            v-for="cat in searchStore.categories"
            :key="cat.value"
            :class="[
              'px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-colors',
              searchStore.selectedCategory === cat.value 
                ? 'bg-brand-500 text-white' 
                : 'bg-[var(--input-bg)] text-zinc-600 hover:text-[var(--text-primary)]'
            ]"
            @click="searchStore.selectedCategory = cat.value"
          >
            {{ cat.label }}
          </button>
        </div>
        
        <-- Purpose: Consolidio-- Purpose: Results -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="searchStore.isLoading" class="p-8 flex justify-center">
            <Loader2 class="animate-spin text-brand-500" />
          </div>
          <div v-else-if="!query" class="p-4 text-center text-zinc-500">
            輸入關鍵字開始搜尋
          </div>
          <div v-else-if="!searchStore.results.length" class="p-4 text-center text-zinc-500">
            找不到相符的結果
          </div>
          
          <template v-else>
            <div
              v-for="(item, idx) in searchStore.results"
              :key="item.symbol"
              :class="[
                'px-4 py-3 border-b border-[var(--border-color)]/50 cursor-pointer hover:bg-[var(--bg-sidebar)]/50 transition-colors',
                selectedIndex === idx ? 'bg-brand-500/10' : ''
              ]"
              @click="selectResult(item)"
              @mouseenter="selectedIndex = idx"
            >
              <div class="flex items-start justify-between">
                <div>
                  <div class="font-bold text-[var(--text-primary)]">
                    {{ item.name_zh }}
                    <span class="text-xs text-zinc-500 font-normal ml-1">{{ item.symbol }}</span>
                  </div>
                  <div class="text-xs text-zinc-500 mt-0.5">
                    {{ item.name_en }} · {{ getCategoryLabel(item.category) }}
                  </div>
                </div>
                <div class="text-right">
                  <div class="font-bold text-[var(--text-primary)]">
                    {{ item.price ? `$${item.price.toFixed(2)}` : 'N/A' }}
                  </div>
                  <div :class="['text-xs font-bold', item.change > 0 ? 'text-rose-600' : 'text-brand-600']">
                    {{ item.change > 0 ? '+' : '' }}{{ item.change_pct?.toFixed(2) }}%
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
        
        <-- Purpose: Consolidio-- Purpose: Footer (Action Hints) -->
        <div class="px-4 py-2 bg-[var(--bg-sidebar)]/50 text-xs text-zinc-500 flex justify-between text-center">
          <span><kbd>↑↓</kbd> 導航</span>
          <span><kbd>Enter</kbd> 選擇</span>
          <span><kbd>Esc</kbd> 關閉</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Search, Loader2 } from 'lucide-vue-next'
import { useSearchStore } from '../stores/useSearchStore'

const searchStore = useSearchStore()
const inputRef = ref(null)
const isOpen = ref(false)
const query = ref('')
const selectedIndex = ref(0)

const open = async () => {
  isOpen.value = true
  await nextTick()
  inputRef.value?.focus()
}

const close = () => {
  isOpen.value = false
  query.value = ''
  selectedIndex.value = 0
}

const handleInput = async (e) => {
  query.value = e.target.value
  selectedIndex.value = 0
  await searchStore.performSearch(
    query.value,
    searchStore.selectedCategory
  )
}

const selectResult = async (item) => {
  // 觸發添加到追蹤的操作
  emit('select', item)
  close()
}

const getCategoryLabel = (cat) => {
  return searchStore.categories.find(c => c.value === cat)?.label || cat
}

// 監聽快捷鍵 Cmd+K / Ctrl+K
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault()
      open()
    }
    if (isOpen.value && e.key === 'Escape') {
      close()
    }
  })
}

defineExpose({ open, close })
</script>
```

### Phase 4：集成到 DashboardView

**GOAL-004**: 在投資總覽頁面集成搜尋功能

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-012 | 在 DashboardView.vue 的自訂指數按鈕旁添加快速搜尋輸入框 | | |
| TASK-013 | 搜尋結果支持一鍵添加到追蹤 | | |
| TASK-014 | 集成全局搜尋快捷鍵到 LayoutView | | |

**實現細節** (DashboardView 修改):
```vue
<-- Purpose: Consolidio-- Purpose: In DashboardView 的標題欄 -->
<div class="flex items-center gap-2">
  <-- Purpose: Consolidio-- Purpose: 快速搜尋輸入框 -->
  <SymbolSearchInput 
    @select="handleAddTracking"
    placeholder="快速搜尋並添加..."
  />
  
  <-- Purpose: Consolidio-- Purpose: 原有的自訂指數按鈕 -->
  <button @click="openQuoteModal" class="...">
    <Settings :size="14" /> 自訂指數
  </button>
</div>

<-- Purpose: Consolidio-- Purpose: 全局搜尋 Modal -->
<GlobalSearchModal 
  ref="globalSearchRef"
  @select="handleAddTracking"
/>
```

### Phase 5：測試與優化

**GOAL-005**: 測試搜尋功能和性能優化

| Task | 描述 | 完成 | 日期 |
|------|------|------|------|
| TASK-015 | 編寫單元測試 `test_search_api.py` (後端) | | |
| TASK-016 | 編寫前端 E2E 測試 (searchbar 功能) | | |
| TASK-017 | 性能測試 (搜尋響應時間 < 200ms) | | |
| TASK-018 | 用戶驗收測試 (UAT) | | |

## 3. 替代方案

- **ALT-001**: 使用第三方搜尋庫 (Algolia)
  - 優點: 功能齊全、快速
  - 缺點: 額外成本、需要遷移數據
  - **決策**: 不選用 — 數據量小，本地搜尋足夠

- **ALT-002**: 搜尋結果顯示在下拉菜單 vs Modal
  - 優點（Modal）: 更好的用戶體驗、支持鍵盤導航
  - **決策**: 全局搜尋用 Modal，快速搜尋用下拉菜單

## 4. 依賴

- **DEP-001**: Vue 3 Composition API (已有)
- **DEP-002**: Pinia store (已有)
- **DEP-003**: Lucide Vue 圖標庫 (已有)
- **DEP-004**: Axios HTTP 客戶端 (已有)

## 5. 受影響的文件

| 文件 | 修改類型 | 說明 |
|------|---------|------|
| `backend/app/routers/market.py` | 新增 | 新增 `/api/market/search` 端點 |
| `frontend/src/api/search.js` | 新建 | 搜尋 API 客戶端 |
| `frontend/src/stores/useSearchStore.js` | 新建 | Pinia 搜尋狀態管理 |
| `frontend/src/components/GlobalSearchModal.vue` | 新建 | 全局搜尋 Modal 組件 |
| `frontend/src/components/SymbolSearchInput.vue` | 新建 | 快速搜尋輸入框組件 |
| `frontend/src/views/DashboardView.vue` | 修改 | 集成搜尋組件 |
| `frontend/src/views/LayoutView.vue` | 修改 | 集成全局搜尋快捷鍵 |

## 6. 測試計劃

| 測試 | 類型 | 描述 |
|------|------|------|
| **TEST-001** | 單元測試 | 搜尋 API 端點 (模糊匹配、分類篩選) |
| **TEST-002** | 單元測試 | Pinia store 搜尋狀態管理 |
| **TEST-003** | 集成測試 | 搜尋 API 與前端集成 |
| **TEST-004** | E2E 測試 | 全局搜尋快捷鍵流程 (Cmd+K → 搜尋 → 添加追蹤) |
| **TEST-005** | 性能測試 | 搜尋響應時間、Debounce 效果 |
| **TEST-006** | UAT | 用戶測試 (易用性、響應時間) |

## 7. 風險與假設

- **RISK-001**: 大量搜尋請求可能影響後端性能
  - 緩解: 實作搜尋結果 cache 和前端 debounce
  
- **RISK-002**: 符號和名稱的多語言匹配可能不完美
  - 緩解: 支持 symbol、name_zh、name_en 三種匹配方式

- **RISK-003**: 新手用戶可能不知道 Cmd+K 快捷鍵
  - 緩解: 首次使用時顯示提示、在新手教程中提及

- **ASSUMPTION-001**: 假設 `/api/market/symbol-catalog` 數據已完整
- **ASSUMPTION-002**: 假設前端已支持 Pinia 狀態管理

## 8. 相關文檔 / 延伸閱讀

- [後端架構文檔](../../docs/backend/backend.md)
- [前端架構文檔](../../docs/frontend/frontend.md)
- [API 文檔 - /api/market/symbols](../../docs/backend/backend.md#api-market-symbols)

