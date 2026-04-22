<template>
  <div class="space-y-4">

    <!-- 設定區塊 -->
    <div class="glass-card">
      <div class="p-4 border-b border-[var(--border-color)] flex items-center gap-2">
        <Scale class="w-4 h-4 text-brand-500" />
        <span class="font-semibold text-[var(--text-primary)]">比較設定</span>
      </div>
      <div class="p-4 space-y-4">
        <!-- 幣值選擇器 -->
        <div class="mb-4">
          <CurrencySelector :show-hint="true" />
        </div>
        <!-- 共用時間段 + 初始金額 -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="space-y-1">
            <label class="block text-xs font-medium text-muted">開始日期</label>
            <input v-model="compareConfig.start_date" type="date"
              class="w-full h-9 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg px-3 focus:ring-brand-500 focus:border-brand-500" />
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-medium text-muted">結束日期</label>
            <input v-model="compareConfig.end_date" type="date"
              class="w-full h-9 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg px-3 focus:ring-brand-500 focus:border-brand-500" />
          </div>
          <div class="space-y-1">
            <label class="block text-xs font-medium text-muted">初始金額</label>
            <input v-model.number="compareConfig.initial_amount" type="number" step="1000" min="1000"
              class="w-full h-9 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg px-3 focus:ring-brand-500 focus:border-brand-500" />
          </div>
        </div>

        <!-- 組合數量選擇 -->
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium text-muted">比較組合數：</span>
          <div class="flex gap-1">
            <button v-for="n in [2, 3, 4]" :key="n"
              :class="['w-9 h-9 rounded-lg text-sm font-bold border transition-all',
                slotCount === n
                  ? 'bg-brand-500 text-white border-brand-500 shadow-sm shadow-brand-500/30'
                  : 'bg-transparent text-muted border-[var(--border-color)] hover:bg-[var(--input-bg)]']"
              @click="slotCount = n">
              {{ n }}
            </button>
          </div>
        </div>

        <!-- Portfolio Slot 卡片 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <div v-for="(slot, idx) in activeSlots" :key="idx"
            :class="['rounded-xl border-2 transition-all overflow-hidden',
              slot
                ? 'border-[var(--border-color)] bg-[var(--bg-main)]/50'
                : 'border-dashed border-[var(--border-color)]/60 bg-[var(--bg-sidebar)]/30']">
            <!-- 卡片標題 -->
            <div class="px-3 py-2.5 flex items-center gap-2 border-b border-[var(--border-color)]"
              :style="{ borderLeftWidth: '3px', borderLeftColor: PORTFOLIO_COLORS[idx], borderLeftStyle: 'solid' }">
              <span class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                :style="{ backgroundColor: PORTFOLIO_COLORS[idx] }"></span>
              <span class="text-sm font-bold text-[var(--text-primary)]">Portfolio {{ idx + 1 }}</span>
              <button v-if="slot" class="ml-auto p-0.5 text-muted hover:text-rose-500 transition-colors rounded"
                @click="slots[idx] = null">
                <X class="w-3.5 h-3.5" />
              </button>
            </div>
            <!-- 卡片內容 -->
            <div class="p-3">
              <div v-if="!slot" class="text-center py-4">
                <FolderOpen class="w-7 h-7 mx-auto text-muted opacity-50 mb-2" />
                <p class="text-xs text-muted mb-3">選擇已儲存組合</p>
              </div>
              <!-- 下拉選單 -->
              <select
                class="w-full h-8 text-xs bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-lg px-2 focus:ring-brand-500 focus:border-brand-500"
                :value="slot ? slot.id : ''"
                @change="onSlotSelect(idx, $event.target.value)">
                <option value="">-- 選擇組合 --</option>
                <option v-for="p in availableOptions(idx)" :key="p.id" :value="p.id">
                  {{ p.name }}
                </option>
              </select>
              <!-- 已選組合詳情 -->
              <div v-if="slot" class="mt-2 space-y-1">
                <div class="text-xs text-muted">
                  原始時段: {{ slot.start_date }} → {{ slot.end_date }}
                </div>
                <div class="flex flex-wrap gap-1 mt-1">
                  <span v-for="item in slot.items" :key="item.symbol"
                    class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium"
                    :style="{ backgroundColor: PORTFOLIO_COLORS[idx] + '20', color: PORTFOLIO_COLORS[idx] }">
                    {{ item.symbol }} {{ item.weight }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 錯誤訊息 -->
        <div v-if="compareError" class="p-3 text-sm text-rose-600 bg-rose-50 dark:bg-rose-500/10 dark:text-rose-400 rounded-lg">
          {{ compareError }}
        </div>

        <!-- 執行按鈕 -->
        <div class="flex justify-end">
          <button
            :disabled="comparing || filledSlots < 2"
            :class="['flex items-center px-5 py-2.5 text-sm font-bold rounded-lg transition-all shadow-sm bg-brand-500 text-white',
              comparing || filledSlots < 2
                ? 'opacity-60 cursor-not-allowed'
                : 'hover:bg-brand-600 shadow-sm']"
            @click="runCompare">
            <Loader2 v-if="comparing" class="w-4 h-4 mr-2 animate-spin" />
            <Play v-else class="w-4 h-4 mr-2" />
            {{ comparing ? '計算中...' : `執行比較分析 (${filledSlots} 個組合)` }}
          </button>
        </div>
      </div>
    </div>

    <!-- 結果區塊 -->
    <template v-if="compareResults">
      <!-- 截圖範圍開始 -->
      <div id="compare-results-content" class="space-y-4">
      
      <!-- 比較設定信息卡 -->
      <div class="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--border-color)] bg-brand-500/5">
          <div class="flex items-center gap-2">
            <Scale class="w-4 h-4 text-brand-500" />
            <span class="font-bold text-sm text-[var(--text-primary)]">比較設定</span>
          </div>
          <span class="text-xs font-bold px-2 py-1 rounded-md bg-brand-500/10 text-brand-600">{{ filledSlots }} 個組合</span>
        </div>
        <div class="border-t border-[var(--border-color)] px-4 py-3 bg-[var(--bg-main)]/30">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div class="text-[10px] text-muted uppercase tracking-wider font-bold mb-1">開始日期</div>
              <div class="font-mono text-xs text-[var(--text-primary)]">{{ compareConfig.start_date }}</div>
            </div>
            <div>
              <div class="text-[10px] text-muted uppercase tracking-wider font-bold mb-1">結束日期</div>
              <div class="font-mono text-xs text-[var(--text-primary)]">{{ compareConfig.end_date }}</div>
            </div>
            <div>
              <div class="text-[10px] text-muted uppercase tracking-wider font-bold mb-1">初始金額</div>
              <div class="font-mono text-xs text-[var(--text-primary)]">{{ preference.currencySymbol }}{{ compareConfig.initial_amount.toLocaleString() }}</div>
            </div>
            <div>
              <div class="text-[10px] text-muted uppercase tracking-wider font-bold mb-1">分析期間</div>
              <div class="font-mono text-xs text-[var(--text-primary)]">{{ calculateDays(compareConfig.start_date, compareConfig.end_date) }} 天</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 錯誤警示列 -->
      <div v-for="r in compareResults.filter(r => r.error)" :key="r.name"
        class="p-3 text-sm text-amber-700 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-300 rounded-lg">
        ⚠️ {{ r.name }} 計算失敗：{{ r.error }}
      </div>

      <!-- 績效比較表 -->
      <div class="glass-card overflow-hidden">
        <div class="p-4 border-b border-[var(--border-color)] flex items-center gap-2">
          <BarChart3 class="w-4 h-4 text-brand-500" />
          <span class="font-semibold text-[var(--text-primary)]">績效比較表 (Performance Summary)</span>
          <span class="text-xs text-muted ml-2">{{ compareConfigLabel }}</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-[var(--border-color)] bg-[var(--bg-sidebar)]/50">
                <th class="px-4 py-3 text-left text-xs font-bold text-muted uppercase tracking-wider">指標</th>
                <th v-for="(r, i) in successResults" :key="r.name"
                  class="px-4 py-3 text-center text-xs font-bold uppercase tracking-wider min-w-32">
                  <div class="flex flex-col items-center justify-center gap-1.5">
                    <span class="w-2.5 h-2.5 rounded-full inline-block flex-shrink-0"
                      :style="{ backgroundColor: PORTFOLIO_COLORS[resultOriginalIndex(i)] }"></span>
                    <span class="text-[var(--text-primary)] whitespace-normal break-words">{{ r.name }}</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--border-color)]/50">
              <tr v-for="row in summaryRows" :key="row.key"
                class="hover:bg-[var(--bg-sidebar)]/30 transition-colors">
                <td class="px-4 py-3 text-muted font-medium whitespace-nowrap">
                  <span class="flex items-center gap-1">
                    {{ row.label }}
                    <span v-if="row.tooltip"
                      v-tooltip="row.tooltip"
                      class="inline-flex items-center justify-center w-4 h-4 rounded-full border border-zinc-400 bg-white text-[10px] text-zinc-600 cursor-help leading-none select-none">?</span>
                  </span>
                </td>
                <td v-for="(r, i) in successResults" :key="r.name"
                  class="px-4 py-3 text-right font-mono"
                  :class="[cellClass(row, r, i), isBest(row, i) ? 'font-bold' : '']">
                  {{ formatCell(row, r) }}
                  <span v-if="isBest(row, i)" class="ml-1 text-[10px] opacity-60">★</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 成長曲線 + 年度報酬並排 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- 成長曲線 -->
        <div class="glass-card">
          <div class="p-4 border-b border-[var(--border-color)] flex items-center justify-between">
            <div class="flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-brand-500" />
              <span class="font-semibold text-[var(--text-primary)]">Portfolio Growth</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="flex items-center gap-1.5 text-xs text-muted cursor-pointer select-none">
                <input type="checkbox" v-model="useLogScale" class="w-3 h-3 rounded accent-brand-500" />
                對數座標
              </label>
            </div>
          </div>
          <div class="p-3" style="height: 360px;">
            <v-chart :option="growthChartOption" autoresize style="height:100%;" />
          </div>
        </div>

        <!-- 年度報酬 -->
        <div class="glass-card">
          <div class="p-4 border-b border-[var(--border-color)] flex items-center gap-2">
            <BarChart2 class="w-4 h-4 text-brand-500" />
            <span class="font-semibold text-[var(--text-primary)]">Annual Returns</span>
          </div>
          <div class="p-3" style="height: 360px;">
            <v-chart :option="annualChartOption" autoresize style="height:100%;" />
          </div>
        </div>
      </div>

      <!-- 回撤比較 (全寬) -->
      <div class="glass-card">
        <div class="p-4 border-b border-[var(--border-color)] flex items-center gap-2">
          <TrendingDown class="w-4 h-4 text-rose-500" />
          <span class="font-semibold text-[var(--text-primary)]">Drawdown Comparison</span>
          <span class="text-xs text-muted ml-1">（各組合從歷史高點的回撤幅度）</span>
        </div>
        <div class="p-3" style="height: 300px;">
          <v-chart :option="drawdownChartOption" autoresize style="height:100%;" />
        </div>
      </div>

      <!-- 分享按鈕 -->
      <div class="flex justify-end">
        <ShareImageButton capture-selector="#compare-results-content" result-type="compare" />
      </div>

      </div>
      <!-- 截圖範圍結束 -->
    </template>

    <!-- 空白提示 -->
    <div v-else class="glass-card py-16 text-center text-muted">
      <Scale class="w-10 h-10 mx-auto opacity-30 mb-3" />
      <p class="text-sm">選擇 2–4 個已儲存組合，設定共用時間段後執行比較</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import axios from 'axios'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, MarkPointComponent, MarkLineComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { Scale, FolderOpen, X, Play, Loader2, BarChart3, BarChart2, TrendingUp, TrendingDown } from 'lucide-vue-next'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { usePreferenceStore } from '../stores/preference'
import CurrencySelector from './CurrencySelector.vue'
import ShareImageButton from './ShareImageButton.vue'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, ToolboxComponent, MarkPointComponent, MarkLineComponent])

const props = defineProps({
  savedPortfolios: { type: Array, default: () => [] }
})

const auth = useAuthStore()
const preference = usePreferenceStore()

// ── 顏色定義 ──────────────────────────────────────────
const PORTFOLIO_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444']

// ── 設定狀態 ──────────────────────────────────────────
const slotCount = ref(2)
const slots = ref([null, null, null, null])   // savedPortfolio 物件 or null

const compareConfig = reactive({
  start_date: '2020-01-01',
  end_date: new Date().toISOString().split('T')[0],
  initial_amount: 10000,
})

const compareResults = ref(null)
const comparing = ref(false)
const compareError = ref('')
const useLogScale = ref(false)

// ── 衍生計算 ──────────────────────────────────────────
const activeSlots = computed(() => slots.value.slice(0, slotCount.value))
const filledSlots = computed(() => activeSlots.value.filter(Boolean).length)

const compareConfigLabel = computed(() =>
  `${compareConfig.start_date} → ${compareConfig.end_date} ｜ 初始 $${compareConfig.initial_amount.toLocaleString()}`
)

function availableOptions(idx) {
  const selectedIds = slots.value
    .filter((s, i) => s && i !== idx)
    .map(s => s.id)
  return props.savedPortfolios.filter(p => !selectedIds.includes(p.id))
}

function onSlotSelect(idx, portfolioId) {
  if (!portfolioId) {
    slots.value[idx] = null
    return
  }
  const found = props.savedPortfolios.find(p => p.id === portfolioId)
  slots.value[idx] = found || null
}

function resultOriginalIndex(successIdx) {
  // 找出第 successIdx 個成功結果在原 compareResults 陣列中的索引
  let count = 0
  for (let i = 0; i < (compareResults.value?.length || 0); i++) {
    if (!compareResults.value[i].error) {
      if (count === successIdx) return i
      count++
    }
  }
  return successIdx
}

const successResults = computed(() =>
  (compareResults.value || []).filter(r => !r.error)
)

// ── 執行比較 ──────────────────────────────────────────
async function runCompare() {
  compareError.value = ''
  const selected = activeSlots.value.filter(Boolean)
  if (selected.length < 2) {
    compareError.value = '請至少選擇 2 個組合'
    return
  }

  comparing.value = true
  try {
    const portfolios = selected.map(p => ({
      name: p.name,
      items: p.items.map(it => ({
        symbol: it.symbol,
        name: it.name || it.symbol,
        weight: it.weight,
        category: it.category || 'us_etf',
      })),
    }))

    const res = await axios.post(
      `${API_BASE}/api/backtest/compare`,
      {
        portfolios,
        start_date: compareConfig.start_date,
        end_date: compareConfig.end_date,
        initial_amount: compareConfig.initial_amount,
      },
      { headers: auth.headers }
    )
    compareResults.value = res.data
  } catch (e) {
    compareError.value = e.response?.data?.detail || e.message || '比較計算失敗'
  } finally {
    comparing.value = false
  }
}

// ── 績效比較表設定 ─────────────────────────────────────
const summaryRows = [
  { key: 'initial_amount',  label: '起始金額',            format: 'dollar',  tooltip: null,         higherBetter: null },
  { key: 'final_amount',    label: '最終金額',            format: 'dollar',  tooltip: '回測期間結束時的總資產價值，反映整體絕對獲利金額', higherBetter: true },
  { key: 'cagr',            label: '年化報酬 (CAGR)',     format: 'pct',     tooltip: '複合年均增長率（Compound Annual Growth Rate）：將整體報酬換算成每年平均成長率，消除時間長短影響，數值越高越好', higherBetter: true },
  { key: 'annual_std',      label: '標準差 (Volatility)', format: 'pct',     tooltip: '年化報酬率的標準差，衡量投資組合波動程度。數值越低代表報酬越穩定，風險越低', higherBetter: false },
  { key: 'best_year_val',   label: '最佳年度',            format: 'pct',     tooltip: '回測期間單一日曆年度中最高的年化報酬率',         higherBetter: true },
  { key: 'worst_year_val',  label: '最差年度',            format: 'pct',     tooltip: '回測期間單一日曆年度中最低的年化報酬率，反映最壞情況下損失',         higherBetter: false },
  { key: 'max_drawdown',    label: '最大回撤',            format: 'pct',     tooltip: '從歷史高點到最低谷的最大跌幅，衡量最大可能虧損幅度。數值越接近 0 越好', higherBetter: false },
  { key: 'sharpe_ratio',    label: 'Sharpe Ratio',        format: 'num2',    tooltip: '夏普比率：(年化報酬 - 無風險利率) ÷ 標準差，衡量每承擔一單位總風險所獲得的超額報酬。> 1 為良好，> 2 為優秀', higherBetter: true },
  { key: 'sortino_ratio',   label: 'Sortino Ratio',       format: 'num2',    tooltip: '索提諾比率：僅計算下行風險（虧損波動），比 Sharpe Ratio 更精準衡量風險調整後報酬。數值越高越好', higherBetter: true },
]

function getMetricValue(row, r) {
  if (!r.metrics) return null
  if (row.key === 'initial_amount') return compareConfig.initial_amount
  if (row.key === 'best_year_val') {
    const ar = r.annual_returns
    if (!ar) return null
    return Math.max(...Object.values(ar)) * 100
  }
  if (row.key === 'worst_year_val') {
    const ar = r.annual_returns
    if (!ar) return null
    return Math.min(...Object.values(ar)) * 100
  }
  return r.metrics[row.key] ?? null
}

function formatCell(row, r) {
  const val = getMetricValue(row, r)
  if (val === null || val === undefined) return '—'
  if (row.format === 'dollar') return '$' + Math.round(val).toLocaleString()
  if (row.format === 'pct') return val.toFixed(2) + '%'
  if (row.format === 'num2') return Number(val).toFixed(2)
  return val
}

function isBest(row, successIdx) {
  if (row.higherBetter === null || successResults.value.length < 2) return false
  const vals = successResults.value.map(r => getMetricValue(row, r))
  const current = vals[successIdx]
  if (current === null) return false
  if (row.higherBetter) return current === Math.max(...vals.filter(v => v !== null))
  return current === Math.min(...vals.filter(v => v !== null))
}

function cellClass(row, r, i) {
  const val = getMetricValue(row, r)
  if (val === null) return 'text-muted'
  if (row.key === 'cagr' || row.key === 'best_year_val') return val >= 0 ? 'text-rose-600 dark:text-rose-400' : 'text-brand-600 dark:text-brand-400'
  if (row.key === 'max_drawdown' || row.key === 'worst_year_val') return 'text-brand-600 dark:text-brand-400'
  return 'text-[var(--text-primary)]'
}

// ── 共用 X 軸合併 ──────────────────────────────────────
function mergedDates(seriesKey) {
  return [...new Set(
    successResults.value.flatMap(r => Object.keys(r[seriesKey] || {}))
  )].sort()
}

// ── 共用 ECharts 樣式 ──────────────────────────────────
const chartTextStyle = { color: '#8b949e', fontFamily: 'Inter, sans-serif' }
const tooltipStyle = { backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3', fontSize: 12 } }
const splitLineStyle = { lineStyle: { color: '#2d333b', type: 'solid' } }
const axisLineStyle = { lineStyle: { color: '#30363d', width: 1 } }

// ── 成長曲線 ──────────────────────────────────────────
const growthChartOption = computed(() => {
  if (!successResults.value.length) return {}
  const dates = mergedDates('portfolio_value_series')

  const series = successResults.value.map((r, si) => {
    const colorIdx = resultOriginalIndex(si)
    return {
      name: r.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: PORTFOLIO_COLORS[colorIdx], width: 2 },
      data: dates.map(d => r.portfolio_value_series[d] ?? null),
      connectNulls: true,
    }
  })

  return {
    backgroundColor: 'transparent',
    textStyle: chartTextStyle,
    animation: false,
    grid: { left: 72, right: 20, top: 30, bottom: 60 },
    legend: {
      bottom: 4, left: 'center', icon: 'roundRect',
      textStyle: { color: '#8b949e', fontSize: 11 },
      data: successResults.value.map((r, si) => ({
        name: r.name,
        itemStyle: { color: PORTFOLIO_COLORS[resultOriginalIndex(si)] },
      })),
    },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { fontSize: 10, color: '#8b949e', formatter: v => v.substring(0, 7) },
      axisLine: axisLineStyle, splitLine: { show: false },
    },
    yAxis: {
      type: useLogScale.value ? 'log' : 'value',
      scale: true,
      name: 'Balance ($)',
      nameLocation: 'middle', nameGap: 55,
      axisLabel: { formatter: v => '$' + v.toLocaleString(), color: '#8b949e', fontSize: 10 },
      axisLine: axisLineStyle, splitLine: splitLineStyle,
    },
    tooltip: {
      ...tooltipStyle, trigger: 'axis',
      formatter: params => {
        let html = `<div style="font-size:11px;font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.value !== null) {
            html += `<div>${p.marker} ${p.seriesName}: <b>$${parseFloat(p.value).toLocaleString()}</b></div>`
          }
        })
        return html
      },
    },
    series,
  }
})

// ── 年度報酬 ──────────────────────────────────────────
const annualChartOption = computed(() => {
  if (!successResults.value.length) return {}
  const allYears = [...new Set(
    successResults.value.flatMap(r => Object.keys(r.annual_returns || {}))
  )].sort()

  const series = successResults.value.map((r, si) => {
    const colorIdx = resultOriginalIndex(si)
    const color = PORTFOLIO_COLORS[colorIdx]
    return {
      name: r.name,
      type: 'bar',
      barGap: '8%',
      itemStyle: {
        color: params => params.value >= 0 ? color : color + '88',
        borderRadius: [2, 2, 0, 0],
      },
      data: allYears.map(y => {
        const v = r.annual_returns?.[y]
        return v !== undefined ? parseFloat((v * 100).toFixed(2)) : null
      }),
    }
  })

  return {
    backgroundColor: 'transparent',
    textStyle: chartTextStyle,
    animation: false,
    grid: { left: 52, right: 12, top: 30, bottom: 60 },
    legend: {
      bottom: 4, left: 'center', icon: 'roundRect',
      textStyle: { color: '#8b949e', fontSize: 11 },
      data: successResults.value.map((r, si) => ({
        name: r.name,
        itemStyle: { color: PORTFOLIO_COLORS[resultOriginalIndex(si)] },
      })),
    },
    xAxis: {
      type: 'category', data: allYears,
      axisLabel: { fontSize: 10, color: '#8b949e', rotate: 30 },
      axisLine: axisLineStyle, splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: v => v + '%', color: '#8b949e', fontSize: 10 },
      axisLine: axisLineStyle, splitLine: splitLineStyle,
      splitNumber: 6,
    },
    tooltip: {
      ...tooltipStyle, trigger: 'axis',
      formatter: params => {
        let html = `<div style="font-size:11px;font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.value !== null) {
            const color = p.value >= 0 ? '#f85149' : '#79c0ff'
            html += `<div>${p.marker} ${p.seriesName}: <b style="color:${color}">${p.value}%</b></div>`
          }
        })
        return html
      },
    },
    series,
  }
})

// ── 回撤比較 ──────────────────────────────────────────
const drawdownChartOption = computed(() => {
  if (!successResults.value.length) return {}
  const dates = mergedDates('drawdown_series')

  const series = successResults.value.map((r, si) => {
    const colorIdx = resultOriginalIndex(si)
    const color = PORTFOLIO_COLORS[colorIdx]
    return {
      name: r.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color, width: 1.5 },
      areaStyle: { color, opacity: 0.07 },
      data: dates.map(d => r.drawdown_series[d] ?? null),
      connectNulls: true,
    }
  })

  return {
    backgroundColor: 'transparent',
    textStyle: chartTextStyle,
    animation: false,
    grid: { left: 56, right: 20, top: 20, bottom: 60 },
    legend: {
      bottom: 4, left: 'center', icon: 'roundRect',
      textStyle: { color: '#8b949e', fontSize: 11 },
      data: successResults.value.map((r, si) => ({
        name: r.name,
        itemStyle: { color: PORTFOLIO_COLORS[resultOriginalIndex(si)] },
      })),
    },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { fontSize: 10, color: '#8b949e', formatter: v => v.substring(0, 7) },
      axisLine: axisLineStyle, splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      max: 0,
      axisLabel: { formatter: v => v + '%', color: '#8b949e', fontSize: 10 },
      axisLine: axisLineStyle, splitLine: splitLineStyle,
    },
    tooltip: {
      ...tooltipStyle, trigger: 'axis',
      formatter: params => {
        let html = `<div style="font-size:11px;font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.value !== null) {
            html += `<div>${p.marker} ${p.seriesName}: <b style="color:#f85149">${parseFloat(p.value).toFixed(2)}%</b></div>`
          }
        })
        return html
      },
    },
    series,
  }
})

// ── 日期計算 ──────────────────────────────────────────
function calculateDays(startDate, endDate) {
  const start = new Date(startDate).getTime()
  const end = new Date(endDate).getTime()
  const diffTime = Math.abs(end - start)
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}
</script>

<style scoped>
</style>
