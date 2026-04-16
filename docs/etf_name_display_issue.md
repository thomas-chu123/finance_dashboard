# ETF 列表缺少名稱顯示 - 根本原因分析

## 🔍 問題描述

在「回測管理」、「最佳化」、「蒙地卡羅」頁面中，ETF 列表（台灣 ETF、美國 ETF）僅顯示代碼，不顯示名稱。

**影響的頁面**:
- ✗ BacktestView.vue
- ✗ OptimizeView.vue
- ✗ MonteCarloView.vue

---

## 📊 根本原因

### 問題時間線

```
Commit 4c8ae6c: feat(search): parallelize fetching Taiwan and US ETF lists
├─ 修改 backend/app/services/market_data.py
│  └─ fetch_tw_etf_list() 返回字段從 "name" 改為 "name_zh"
│  └─ fetch_us_etf_list() 返回字段從 "name" 改為 "name_zh" 和 "name_en"
│
└─ 結果: 前端期望 "name"，但後端返回 "name_zh"
```

### 具體變更

**後端 (backend/app/services/market_data.py)** - 提交 4c8ae6c

```python
# fetch_tw_etf_list() 返回
{
    "symbol": "...",
    "name_zh": row["name"],      # ← 字段名改為 name_zh
    "name_en": "",
    "category": "tw_etf",
    "yahoo_symbol": "..."
}

# fetch_us_etf_list() 返回
{
    "symbol": "...",
    "name_zh": row["name"],      # ← 字段名改為 name_zh
    "name_en": row["name"],
    "category": "us_etf",
    "yahoo_symbol": "..."
}
```

**前端仍然期望** (所有三個頁面都是):

```vue
<!-- BacktestView.vue:205 -->
<span class="text-[10px] text-[var(--text-secondary)]">{{ s.name }}</span>

<!-- BacktestView.vue:590 -->
!q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)

<!-- 相同的 bug 也在 OptimizeView.vue 和 MonteCarloView.vue 中 -->
```

---

## 🔧 解決方案

### 方案 A: 修改後端返回 "name" 字段 (推薦) ⭐⭐⭐

**優勢**: 不需要改前端代碼，最小化影響

**代碼修改** (backend/app/services/market_data.py):

```python
async def fetch_tw_etf_list():
    # ... 
    return [
        {
            "symbol": ...,
            "name": row["name"],      # ← 改回 "name" (搜尋功能使用 name_zh)
            "name_zh": row["name"],   # ← 保留 name_zh 給搜尋功能
            "name_en": "",
            "category": "tw_etf",
            "yahoo_symbol": ...
        }
        for row in all_rows
    ]

async def fetch_us_etf_list():
    # ...
    return [
        {
            "symbol": ...,
            "name": row["name"],      # ← 改回 "name"
            "name_zh": row["name"],   # ← 保留 name_zh 給搜尋功能
            "name_en": row["name"],
            "category": "us_etf",
            "yahoo_symbol": ...
        }
        for row in all_rows
    ]
```

**影響**: 
- ✅ 修復回測、最佳化、蒙地卡羅
- ✅ 搜尋功能仍可使用 name_zh
- ✅ 最小化代碼改動

---

### 方案 B: 修改前端使用 "name_zh" 字段

**代碼修改** (所有三個頁面):

```vue
<!-- BacktestView.vue:205 -->
<span class="text-[10px]">{{ s.name_zh || s.name }}</span>

<!-- BacktestView.vue:590 -->
!q || s.symbol.toLowerCase().includes(q) || (s.name_zh || s.name).toLowerCase().includes(q)
```

**劣勢**:
- 需要改 3 個檔案
- 代碼變複雜（防禦性檢查）

---

## 📋 修復清單

### 後端 (方案 A 推薦)

```python
# 文件: backend/app/services/market_data.py

# 第 1 個修改點: fetch_tw_etf_list()
return [
    {
        "symbol": row["symbol"] if ... else row["symbol"] + ".TW",
        "name": row["name"],          # ← ADD THIS
        "name_zh": row["name"],
        "name_en": "",
        "category": "tw_etf",
        "yahoo_symbol": ...
    }
    for row in all_rows
]

# 第 2 個修改點: fetch_us_etf_list()
return [
    {
        "symbol": row["symbol"],
        "name": row["name"],          # ← ADD THIS
        "name_zh": row["name"],
        "name_en": row["name"],
        "category": "us_etf",
        "yahoo_symbol": ...
    }
    for row in all_rows
]
```

### 前端 (如果使用方案 B)

```vue
<!-- BacktestView.vue (第 205 行) -->
{{ s.name_zh || s.name }}

<!-- BacktestView.vue (第 590 行搜尋過濾) -->
!q || s.symbol.toLowerCase().includes(q) || (s.name_zh || s.name).toLowerCase().includes(q)

<!-- 相同改動應用於:
     - OptimizeView.vue
     - MonteCarloView.vue
-->
```

---

## 🎯 推薦方案: 方案 A (後端修改)

```bash
# Step 1: 編輯 backend/app/services/market_data.py
# - 在 fetch_tw_etf_list() 返回中添加 "name" 字段
# - 在 fetch_us_etf_list() 返回中添加 "name" 字段

# Step 2: 驗證後端語法
cd backend
python -m py_compile app/services/market_data.py

# Step 3: 測試搜尋功能仍可用
# - 訪問搜尋功能，確認 name_zh 仍可用於搜尋

# Step 4: 測試回測/最佳化/蒙地卡羅頁面
# - 驗證 ETF 名稱正確顯示
```

---

## ⚠️ 影響範圍

| 組件 | 字段使用 | 影響 |
|------|---------|------|
| BacktestView | s.name | ✗ 缺少名稱 |
| OptimizeView | s.name | ✗ 缺少名稱 |
| MonteCarloView | s.name | ✗ 缺少名稱 |
| GlobalSearchModal | name_zh | ✓ 正常 |
| useSearchStore | name_zh | ✓ 正常 |

---

## 🔍 驗證步驟

### 修復前測試

```bash
# 1. 查看當前返回值
curl http://localhost:8000/api/backtest/symbols | jq '.tw_etf[0]'
# 輸出: { "symbol": "...", "name_zh": "...", "category": "tw_etf" }
# 問題: 沒有 "name" 字段
```

### 修復後測試

```bash
# 1. 重新檢查返回值
curl http://localhost:8000/api/backtest/symbols | jq '.tw_etf[0]'
# 輸出: { "symbol": "...", "name": "...", "name_zh": "...", "category": "tw_etf" }
# ✓ 現在有 "name" 字段

# 2. 訪問回測頁面，驗證 ETF 名稱顯示
# 3. 測試搜尋功能 (使用 name_zh)
# 4. 驗證最佳化和蒙地卡羅頁面
```

---

## 📝 提交信息 (建議)

```
fix(etf-display): restore name field in backtest/optimize/montecarlo ETF lists

Problem:
- Commit 4c8ae6c changed backend to return name_zh instead of name
- Frontend components still expect name field
- Result: ETF lists in backtest, optimize, monte carlo show only codes

Solution:
- Add "name" field back to fetch_tw_etf_list() return
- Add "name" field back to fetch_us_etf_list() return
- Keep "name_zh" for search functionality compatibility

Affected files:
- backend/app/services/market_data.py

Affected pages:
- BacktestView
- OptimizeView
- MonteCarloView

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

