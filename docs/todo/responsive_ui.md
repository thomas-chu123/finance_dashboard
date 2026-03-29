---
goal: 將 Vue 3 前端改造為手機友善的 Responsive UI
version: 1.0
date_created: 2026-03-27
last_updated: 2026-03-27
owner: 前端團隊
status: 'Planned'
tags: ['feature', 'responsive', 'mobile', 'ux', 'tailwind']
---

# Introduction

本計畫基於現有程式碼掃描結果，針對 `finance_dashboard` 前端進行手機友善改造。
目標是讓所有頁面在 375px（iPhone SE）至 1440px 之間都能流暢顯示與操作。

## 現狀分析

| 頁面 / 元件 | 響應式 class 數量 | 主要問題 |
|------------|-----------------|---------|
| `LayoutView.vue` | 11 | 側邊欄遮罩邏輯基本完整，但 header search bar `hidden sm:block` 在行動端消失 |
| `BacktestView.vue` | 15 | 分頁按鈕排列、圖表高度固定、結果表格無行動端 card 版型 |
| `OptimizeView.vue` | 11 | 與 Backtest 類似，需圖表和表格的行動端版型 |
| `DashboardView.vue` | 4 | `min-w-[700px]` 追蹤表格在行動端溢出 |
| `TrackingView.vue` | 4 | 多欄表格沒有行動端 card 版型 |
| `LoginView.vue` | 0 | 登入表單沒有任何響應式處理 |
| `GuideView.vue` | 0 | 說明頁完全沒有響應式設定 |
| `LineView.vue` | 2 | LINE 綁定頁面幾乎沒有行動端適配 |
| `UsersView.vue` | 2 | 用戶管理表格無行動端版型 |
| `RSIChart.vue` | 0 | RSI 圖表沒有動態高度 |
| `RSIParametersForm.vue` | 0 | 參數表單無任何響應式 class |
| `TriggerModeSelector.vue` | 0 | 觸發模式選擇完全沒有行動端適配 |

---

## 設計原則

### 核心斷點（Tailwind CSS v4）

```
xs:  < 480px    超小螢幕（舊手機）
sm:  480px      現代手機橫屏
md:  768px      平板
lg:  1024px     小型桌面
xl:  1280px     標準桌面
2xl: 1536px     大型桌面
```

### 行動優先策略（Mobile First）

```html
<!-- ❌ 桌面優先（現有方式）-->
<div class="grid grid-cols-4 sm:grid-cols-2">

<!-- ✅ 行動優先（改造目標）-->
<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
```

### 觸摸目標最小尺寸

- 所有可點擊元素最小 `44x44px`（Apple HIG 標準）
- 按鈕使用 `py-3 px-4`（行動端）vs `py-2 px-3`（桌面端）
- 表格行高至少 `48px`，方便手指點擊

---

## Implementation Steps

### Phase 1：全域基礎設定（1-2 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-001 | 新增 viewport meta 確保行動端縮放正確 | `index.html` |
| TASK-002 | 設定 Tailwind `container` 最大寬度 | `tailwind.config` / `style.css` |
| TASK-003 | 全域字型尺寸：行動端 14px / 桌面 15px | `assets/main.css` |
| TASK-004 | 整理 CSS 自訂變數的行動端覆寫 | `assets/main.css` |

**TASK-001 詳細**：
```html
<!-- frontend/index.html -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
<!-- maximum-scale=5.0 允許用戶手動放大（無障礙需求） -->
```

**TASK-003 詳細**：
```css
/* assets/main.css */
html { font-size: 14px; }
@media (min-width: 1024px) { html { font-size: 15px; } }
```

---

### Phase 2：LayoutView 導航改造（2-3 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-005 | 行動端底部導覽列（Bottom Navigation Bar） | `LayoutView.vue` |
| TASK-006 | 行動端 header 改為 icon-only，隱藏搜尋列 | `LayoutView.vue` |
| TASK-007 | 搜尋功能移至全螢幕 Modal（行動端） | `LayoutView.vue` |
| TASK-008 | 側邊欄在行動端以 Drawer 形式滑入 | `LayoutView.vue` |

**現有問題**：
```html
<!-- src/views/LayoutView.vue: 27 行 -->
<!-- 問題：搜尋列只在 sm 以上顯示，行動端完全看不到 -->
<div class="relative max-w-md w-full hidden sm:block">
```

**TASK-005 改造目標**：
```html
<!-- 行動端底部導覽列：lg 以上隱藏，lg 以下顯示 -->
<nav class="fixed bottom-0 left-0 right-0 z-50 lg:hidden
            bg-[var(--bg-sidebar)] border-t border-[var(--border-color)]
            flex items-center justify-around h-14 safe-area-bottom">
  <router-link v-for="item in mobileNavItems" :key="item.path" :to="item.path"
    class="flex flex-col items-center gap-0.5 px-3 py-2 min-w-[44px]
           text-zinc-500 transition-colors"
    active-class="text-brand-500">
    <component :is="item.icon" class="w-5 h-5" />
    <span class="text-[10px] font-medium">{{ item.label }}</span>
  </router-link>
</nav>

<!-- 為底部導覽列留空間 -->
<main class="... pb-14 lg:pb-0">
```

**TASK-006 改造目標**：
```html
<!-- header 行動端簡化 -->
<header class="h-14 lg:h-16 ...">
  <!-- 行動端只顯示 logo + 搜尋 icon + 頭像 -->
  <button class="lg:hidden p-2" @click="openMobileSearch">
    <SearchIcon class="w-5 h-5" />
  </button>
</header>
```

---

### Phase 3：DashboardView 改造（2-3 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-009 | 修正 `min-w-[700px]` 追蹤表格溢出問題 | `DashboardView.vue` |
| TASK-010 | 指標卡片（KPI Cards）行動端單欄顯示 | `DashboardView.vue` |
| TASK-011 | ECharts 圖表行動端動態高度 | `DashboardView.vue` |
| TASK-012 | 圖表 legend 在行動端改為可滾動水平版型 | `DashboardView.vue` |

**TASK-009 現有問題**：
```html
<!-- DashboardView.vue: 87 行 -->
<!-- 問題：min-w-[700px] 強制導致水平滾動 -->
<div class="min-w-[700px]">
```

**TASK-009 修正**：
```html
<!-- 保留 overflow-x-auto，移除 min-w，改成響應式欄位 -->
<div class="overflow-x-auto -mx-4 sm:mx-0">
  <!-- 行動端：隱藏次要欄位，只顯示代碼、名稱、價格、漲跌幅 -->
  <div class="grid grid-cols-4 sm:grid-cols-7 min-w-[360px] sm:min-w-[600px]">
    <th class="hidden sm:table-cell">類別</th>
    <th class="hidden sm:table-cell">觸發模式</th>
    <th class="hidden md:table-cell">RSI</th>
  </div>
</div>
```

**TASK-011 圖表高度**：
```javascript
// composable：動態圖表高度
const chartHeight = computed(() => {
  if (window.innerWidth < 640) return '220px'
  if (window.innerWidth < 1024) return '300px'
  return '400px'
})
```

---

### Phase 4：TrackingView 表格改造（2-3 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-013 | 行動端改用 Card List 版型替代表格 | `TrackingView.vue` |
| TASK-014 | 篩選分類 Tabs 改為水平可滾動 | `TrackingView.vue` |
| TASK-015 | 操作按鈕（新增、重整）移至底部 FAB | `TrackingView.vue` |
| TASK-016 | 持倉詳情展開為 Modal（行動端） | `TrackingView.vue` |

**TASK-013 Card 版型**：
```html
<!-- TrackingView.vue -->
<!-- 行動端：Card 版型 -->
<div class="block md:hidden space-y-2 px-4">
  <div v-for="item in filteredItems" :key="item.id"
       class="bg-[var(--bg-card)] rounded-xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-2">
      <div>
        <span class="font-bold text-sm">{{ item.symbol }}</span>
        <span class="text-xs text-zinc-500 ml-2">{{ item.name }}</span>
      </div>
      <span :class="item.change >= 0 ? 'text-green-500' : 'text-red-500'"
            class="font-bold text-sm">
        {{ item.price }}
      </span>
    </div>
    <div class="grid grid-cols-3 gap-2 text-xs text-zinc-500">
      <span>漲跌幅：<b class="text-[var(--text-primary)]">{{ item.changePercent }}%</b></span>
      <span>RSI：<b class="text-[var(--text-primary)]">{{ item.rsi }}</b></span>
      <span>類別：<b class="text-[var(--text-primary)]">{{ item.category }}</b></span>
    </div>
  </div>
</div>

<!-- 桌面端：原有表格版型 -->
<div class="hidden md:block overflow-x-auto">
  <table class="w-full text-left">...</table>
</div>
```

**TASK-015 FAB 按鈕**：
```html
<!-- 行動端浮動新增按鈕（底部右側） -->
<button class="fixed bottom-20 right-4 lg:hidden z-40
               w-14 h-14 rounded-full bg-brand-500 text-white shadow-xl
               flex items-center justify-center"
        @click="showAddModal = true">
  <PlusIcon class="w-6 h-6" />
</button>
```

---

### Phase 5：BacktestView / OptimizeView 改造（3-4 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-017 | 分頁按鈕改為水平滾動 chip 排列 | `BacktestView.vue` |
| TASK-018 | 資產配置面板：行動端改為全螢幕 bottom sheet | `BacktestView.vue` |
| TASK-019 | 圖表動態高度（行動端 250px / 桌面 400px） | `BacktestView.vue` |
| TASK-020 | 結果指標卡片改為 2 欄 grid（行動端） | `BacktestView.vue` |
| TASK-021 | OptimizeView 輸入面板行動端全寬版型 | `OptimizeView.vue` |
| TASK-022 | 有效前緣圖在行動端隱藏次要軸標籤 | `OptimizeView.vue` |

**TASK-017 分頁改造**：
```html
<!-- 行動端：水平滾動的分頁 -->
<div class="flex overflow-x-auto scrollbar-none gap-2 pb-1 -mx-4 px-4 md:mx-0 md:px-0 md:flex-wrap">
  <button v-for="tab in tabs" :key="tab.value"
    class="flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg
           border transition-all whitespace-nowrap"
    :class="activeTab === tab.value ? 'bg-brand-500 text-white border-brand-500' : '...'">
    {{ tab.label }}
  </button>
</div>
```

**TASK-019 圖表高度**：
```html
<v-chart :option="growthChartOption" autoresize
  :style="{ height: isMobile ? '250px' : '400px' }" />
```

---

### Phase 6：RSI 元件改造（1-2 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-023 | `RSIChart.vue` 動態高度和字型縮減 | `RSIChart.vue` |
| TASK-024 | `RSIParametersForm.vue` 表單欄位全寬排列 | `RSIParametersForm.vue` |
| TASK-025 | `TriggerModeSelector.vue` 按鈕群組行動端換行 | `TriggerModeSelector.vue` |
| TASK-026 | `RSIMonitoringDashboard.vue` 監控卡片 1 欄顯示 | `RSIMonitoringDashboard.vue` |

**TASK-024 表單全寬**：
```html
<!-- 現有：並排兩欄 -->
<div class="grid grid-cols-2 gap-4">

<!-- 改造：行動端單欄、桌面雙欄 -->
<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
```

---

### Phase 7：LoginView / 其他頁面（1 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-027 | 登入頁面卡片行動端全寬、padding 調整 | `LoginView.vue` |
| TASK-028 | GuideView 文字排版行動端 max-w 和字距 | `GuideView.vue` |
| TASK-029 | LineView QR Code 置中、說明文字換行 | `LineView.vue` |
| TASK-030 | UsersView 使用者表格改為 Card 版型（行動端） | `UsersView.vue` |

**TASK-027 改造**：
```html
<!-- LoginView.vue -->
<!-- 行動端：card 全寬，桌面：固定寬度置中 -->
<div class="min-h-screen flex items-center justify-center p-4">
  <div class="w-full max-w-md bg-[var(--bg-card)] rounded-2xl p-6 sm:p-8
              border border-[var(--border-color)] shadow-2xl">
```

---

### Phase 8：通用 Composable 和工具（1 天）

| Task | 說明 | 文件 |
|------|------|------|
| TASK-031 | 新建 `useBreakpoint.js` composable | `composables/useBreakpoint.js` |
| TASK-032 | 新建 `useSafeArea.js` 處理 iOS 安全區 | `composables/useSafeArea.js` |
| TASK-033 | CSS 新增 `safe-area-bottom` 工具類 | `assets/main.css` |

**TASK-031 useBreakpoint.js**：
```javascript
// composables/useBreakpoint.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useBreakpoint() {
  const isMobile = ref(false)      // < 768px
  const isTablet = ref(false)      // 768px - 1023px
  const isDesktop = ref(false)     // >= 1024px

  function update() {
    const w = window.innerWidth
    isMobile.value  = w < 768
    isTablet.value  = w >= 768 && w < 1024
    isDesktop.value = w >= 1024
  }

  onMounted(() => { update(); window.addEventListener('resize', update) })
  onUnmounted(() => window.removeEventListener('resize', update))

  return { isMobile, isTablet, isDesktop }
}
```

**TASK-033 安全區 CSS**：
```css
/* assets/main.css */
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.safe-area-top {
  padding-top: env(safe-area-inset-top, 0px);
}

/* 隱藏滾動條但保留功能 */
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar { display: none; }
```

---

### Phase 9：測試和驗證（1-2 天）

| Task | 說明 |
|------|------|
| TASK-034 | 在 Chrome DevTools 手機模擬模式測試所有頁面 |
| TASK-035 | 在真實 iPhone（Safari）上測試 |
| TASK-036 | 在真實 Android（Chrome）上測試 |
| TASK-037 | 測試觸摸點擊區域是否足夠（44x44px） |
| TASK-038 | 測試橫屏（Landscape）顯示是否正常 |
| TASK-039 | 使用 Lighthouse 確認 PWA 和 Mobile 評分 |

---

## 文件變更清單

| 文件 | 類型 | 優先級 |
|------|------|-------|
| `frontend/index.html` | 修改 | 高 |
| `frontend/src/assets/main.css` | 修改 | 高 |
| `frontend/src/views/LayoutView.vue` | 修改 | 最高 |
| `frontend/src/views/DashboardView.vue` | 修改 | 高 |
| `frontend/src/views/TrackingView.vue` | 修改 | 高 |
| `frontend/src/views/BacktestView.vue` | 修改 | 高 |
| `frontend/src/views/OptimizeView.vue` | 修改 | 中 |
| `frontend/src/views/LoginView.vue` | 修改 | 中 |
| `frontend/src/views/LineView.vue` | 修改 | 低 |
| `frontend/src/views/UsersView.vue` | 修改 | 低 |
| `frontend/src/views/GuideView.vue` | 修改 | 低 |
| `frontend/src/components/RSIChart.vue` | 修改 | 中 |
| `frontend/src/components/RSIParametersForm.vue` | 修改 | 中 |
| `frontend/src/components/TriggerModeSelector.vue` | 修改 | 中 |
| `frontend/src/components/RSIMonitoringDashboard.vue` | 修改 | 中 |
| `frontend/src/composables/useBreakpoint.js` | 新建 | 高 |
| `frontend/src/composables/useSafeArea.js` | 新建 | 中 |

---

## 常見行動端問題速查

| 問題 | 原因 | 解法 |
|------|------|------|
| 表格水平溢出 | `min-w-[700px]` 固定寬度 | `overflow-x-auto` + 行動端 Card 版型 |
| 按鈕太小難點擊 | `py-1.5 px-3` 太小 | 行動端改為 `py-3 px-4`（min 44px）|
| 圖表高度固定 | `style="height:400px"` | 改用 `isMobile ? '250px' : '400px'` |
| 搜尋列消失 | `hidden sm:block` | 行動端改為全螢幕 search modal |
| 多欄 Grid 擠壓 | `grid-cols-4` 無 sm 斷點 | 改 `grid-cols-1 md:grid-cols-2 xl:grid-cols-4` |
| 文字截斷亂跳 | `truncate` + 固定寬度 | 配合 `min-w-0` 使用 |
| iOS 底部遮擋 | 未處理 safe area | 使用 `env(safe-area-inset-bottom)` |
| 字體太小 | `text-xs` 在行動端 | 行動端最小 `text-sm`（14px）|

---

## 相關資源

- [Tailwind CSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [Google Mobile-Friendly Test](https://search.google.com/test/mobile-friendly)
- [Apple HIG - Touch Targets](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [ECharts 響應式配置](https://echarts.apache.org/handbook/en/concepts/chart-size/)
- [iOS Safe Area - CSS env()](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)
