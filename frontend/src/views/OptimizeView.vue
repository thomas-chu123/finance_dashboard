<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)]">投資組合最佳化</h2>
        <div class="text-xs sm:text-sm text-[var(--text-muted)]">基於 Markowitz 效率前緣理論尋找最佳權重分配</div>
      </div>
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 w-[calc(100%+2rem)] sm:w-auto">
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            !showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = false">
          <Dna class="w-4 h-4 mr-2" />開始最佳化
        </button>
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = true; loadSavedPortfolios()">
          <FolderOpen class="w-4 h-4 mr-2" />
          已儲存
        </button>
      </div>
    </div>

    <!-- Saved portfolios list -->
    <div v-if="showSaved">
      <div v-if="!savedPortfolios.length" style="padding:48px;text-align:center;color:var(--text-muted);">
        <FolderOpen class="w-12 h-12 mx-auto text-gray-400 mb-3" />
        尚無已儲存的優化組合
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="p in savedPortfolios" :key="p.id" class="glass-card">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
            <div>
              <div class="font-semibold text-[var(--text-primary)]">{{ p.name }}</div>
              <div class="text-sm text-muted">{{ p.start_date }} → {{ p.end_date }}</div>
            </div>
            <div class="flex items-center gap-2">
              <button class="flex items-center px-3 py-1.5 text-sm font-medium text-muted hover:text-brand-500 dark:hover:text-brand-400 transition-colors rounded-lg" @click="loadSaved(p)">載入</button>
              <button class="p-1.5 text-muted hover:text-rose-600 dark:hover:text-rose-400 transition-colors rounded-md hover:bg-rose-50 dark:hover:bg-rose-900/20" @click="deleteSaved(p.id)"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div v-if="p.results_json?.max_sharpe" class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-accent">{{ p.results_json.max_sharpe.sharpe.toFixed(4) }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">Return</div>
                <div class="fw-600 text-rose-600">{{ (p.results_json.max_sharpe.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">Volatility</div>
                <div class="fw-600 text-brand-600">{{ (p.results_json.max_sharpe.volatility * 100).toFixed(2) }}%</div>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">Return</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">Volatility</div>
                <div class="fw-600 text-muted">--</div>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-xs text-muted mb-2">組合資產</div>
              <div class="flex items-center gap-2" style="flex-wrap:wrap;">
                <span v-for="item in p.items" :key="item.symbol" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-500 text-white">
                  {{ item.symbol }} {{ item.weight }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Optimization Config -->
    <div v-if="!showSaved" class="grid grid-cols-1 md:grid-cols-2 gap-3" style="gap:12px;">
      <!-- Left: config -->
      <div>
        <div class="glass-card mb-2">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between"><h3>選擇資產 (最少 2 個, 最多 10 個)</h3></div>
          <div class="p-3 sm:p-4">
            <!-- Quick symbol search -->
            <div class="space-y-1 mb-2">
              <label class="block text-sm font-medium text-[var(--text-muted)]">搜尋代碼或名稱</label>
              <input v-model="symbolSearch" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" placeholder="輸入 0050, SPY..." @keydown.enter="addSearchSymbol" />
            </div>

            <!-- Symbol type tabs -->
            <div class="flex gap-2 mb-6 overflow-x-auto scrollbar-none pb-1">
              <button v-for="t in symbolTypes" :key="t.value"
                :class="['px-3 py-1.5 text-xs font-medium rounded-full border transition-colors cursor-pointer whitespace-nowrap', symbolType === t.value ? 'bg-brand-500 text-white border-brand-500' : 'bg-transparent text-[var(--text-muted)] border-[var(--border-color)] hover:bg-[var(--input-bg)]']"
                @click="symbolType = t.value; loadSymbols()">{{ t.label }}</button>
            </div>

            <!-- Symbol list -->
            <div class="max-h-40 overflow-y-auto border border-[var(--border-color)] rounded-xl bg-[var(--bg-main)]/50 mb-3">
              <div v-for="s in filteredSymbols.slice(0, 1000)" :key="s.symbol"
                :class="['px-3 py-2 cursor-pointer transition-all border-b border-[var(--border-color)] last:border-0 symbol-item', isSelected(s.symbol) ? 'bg-brand-500/10' : 'hover:bg-[var(--input-bg)]', { 'opacity-40 cursor-not-allowed': selectedItems.length >= 10 && !isSelected(s.symbol) }]"
                @click="toggleSymbol(s)">
                <div class="flex flex-col flex-1 min-w-0 pr-4">
                  <span class="font-bold text-[var(--text-primary)] truncate">{{ s.symbol }}</span>
                  <span class="text-xs text-[var(--text-muted)] truncate">{{ s.name }}</span>
                </div>
                <div v-if="isSelected(s.symbol)" class="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-brand-500 text-white shadow-sm">
                  <Check class="w-4 h-4" />
                </div>
              </div>
            </div>

            <!-- Selected list -->
            <div v-if="selectedItems.length > 0">
              <div class="text-xs text-muted mb-4">已選擇 ({{ selectedItems.length }}/10)</div>
              <div class="flex items-center gap-2" style="flex-wrap:wrap;">
                <div v-for="item in selectedItems" :key="item.symbol" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium" :style="{ backgroundColor: 'rgba(34, 197, 94, 0.15)', color: '#16a34a' }">
                  {{ item.symbol }}
                  <span style="cursor:pointer;opacity:0.6;" @click="removeSymbol(item.symbol)"><X class="w-3 h-3" /></span>
                </div>
              </div>
            </div>
          </div>
        </div>

      <!-- Date range -->
        <div class="glass-card">
          <div class="p-3 sm:p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="space-y-1 mb-2 min-w-0">
                <label class="block text-sm font-medium text-[var(--text-muted)]">回測開始日期</label>
                <input v-model="optConfig.start_date" type="date" class="w-full max-w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" />
              </div>
              <div class="space-y-1 mb-2 min-w-0">
                <label class="block text-sm font-medium text-[var(--text-muted)]">結束日期</label>
                <input v-model="optConfig.end_date" type="date" class="w-full max-w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Action area -->
      <div>
        <div class="glass-card mb-2">
          <div class="p-3 sm:p-4" style="display:flex;flex-direction:column;justify-content:center;min-height:180px;text-align:center;">
            <p class="text-[var(--text-muted)] mb-3" style="font-size: 0.8rem; line-height: 1.5;">
              系統將根據選定資產的歷史走勢，計算並建構出 <strong>效率前緣 (Efficient Frontier)</strong>。
            </p>
            <p class="text-[var(--text-muted)] mb-6" style="font-size: 0.8rem; line-height: 1.5;">
              提供「最大夏普值 (最高性價比)」與「最小波動率 (最穩健)」兩種最佳權重組合。
            </p>
            <button class="px-5 py-3 bg-brand-500 hover:bg-brand-600 text-white text-base font-medium rounded-lg transition-colors shadow-sm w-full" style="width:100%;" @click="runOptimization"
              :disabled="runLoading || selectedItems.length < 2 || selectedItems.length > 10">
              <template v-if="runLoading">
                <Loader2 class="w-4 h-4 mr-2 inline animate-spin" />模型計算中...
              </template>
              <template v-else>
                <Dna class="w-4 h-4 mr-2 inline" />開始最佳化分析
              </template>
            </button>
            <div v-if="selectedItems.length < 2" class="text-red text-sm mt-8">請至少選擇 2 個資產進行分析</div>
          </div>
        </div>
        <div v-if="optError" class="p-3 mb-3 text-sm text-red-500 rounded-lg bg-red-500/10 border border-red-500/20">{{ optError }}</div>
      </div>
    </div><!-- end !showSaved -->

    <!-- Results Section -->
    <div v-if="results && !showSaved" class="mt-16">
      <h3 class="mb-2">最佳化分析結果</h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        <!-- Max Sharpe Portfolio -->
        <div class="glass-card" style="border: 3px solid #f85149;">
          <div class="p-4 border-b-2 border-[#f85149] font-semibold text-[var(--text-primary)] flex items-center justify-between" style="background:rgba(248, 81, 73, 0.08);">
            <div class="optimize-header w-full">
              <h3 class="text-brand-500"><Trophy class="w-5 h-5 mr-2 inline" />最大夏普值組合 (Max Sharpe)</h3>
              <button class="px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="exportToBacktest(results.max_sharpe)">使用此權重回測</button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <div>
                <div class="text-xs text-[var(--text-muted)]">預期年化報酬</div>
                <div class="fw-600 text-rose-600">{{ (results.max_sharpe.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">年化波動率</div>
                <div class="font-semibold text-[var(--text-primary)]">{{ (results.max_sharpe.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">夏普值</div>
                <div class="fw-600 text-accent">{{ results.max_sharpe.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div :style="{ height: isMobile ? '200px' : '250px' }">
              <v-chart :option="maxSharpePieOption" autoresize />
            </div>
          </div>
        </div>

        <!-- Min Volatility Portfolio -->
        <div class="glass-card" style="border: 3px solid #3fb950;">
          <div class="p-4 border-b-2 border-[#3fb950] font-semibold text-[var(--text-primary)] flex items-center justify-between" style="background:rgba(63, 185, 80, 0.12);">
             <div class="optimize-header w-full">
              <h3 class="text-brand-600"><Shield class="w-5 h-5 mr-2 inline" />最小波動率組合 (Min Volatility)</h3>
              <button class="px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="exportToBacktest(results.min_volatility)">使用此權重回測</button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <div>
                <div class="text-xs text-[var(--text-muted)]">預期年化報酬</div>
                <div class="fw-600 text-rose-600">{{ (results.min_volatility.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">年化波動率</div>
                <div class="font-semibold text-[var(--text-primary)]">{{ (results.min_volatility.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">夏普值</div>
                <div class="fw-600 text-accent">{{ results.min_volatility.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div :style="{ height: isMobile ? '200px' : '250px' }">
              <v-chart :option="minVolPieOption" autoresize />
            </div>
          </div>
        </div>
      </div>

      <!-- Efficient Frontier Chart -->
      <div class="glass-card mb-2">
        <div class="p-4 border-b-2 border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
          <h3>效率前緣 (Efficient Frontier)</h3>
          <span class="text-sm text-[var(--text-muted)]">顯示在相同風險下能產生的最高預期報酬</span>
        </div>
        <div class="p-3 sm:p-4" :style="{ height: isMobile ? '280px' : '380px' }">
          <v-chart :option="efficientFrontierOption" autoresize />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Trophy, Shield, Dna, X, Check, Loader2, FolderOpen, Trash2 } from 'lucide-vue-next'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { useBreakpoint } from '../composables/useBreakpoint'

const auth = useAuthStore()
const router = useRouter()
const { isMobile, isTablet, isDesktop } = useBreakpoint()
// Remove local API_BASE declaration

const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])
const results = ref(null)
const runLoading = ref(false)
const optError = ref('')
const showSaved = ref(false)
const savedPortfolios = ref([])

const symbolTypes = [
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'indices', label: '指數/原物料' },
]

const optConfig = reactive({
  start_date: '2015-01-01', // Optimization needs slightly longer history ideally
  end_date: new Date().toISOString().split('T')[0]
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  return availableSymbols.value.filter(s =>
    !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
})

function isSelected(sym) { return selectedItems.value.some(i => i.symbol === sym) }

function toggleSymbol(s) {
  if (isSelected(s.symbol)) {
    removeSymbol(s.symbol)
  } else if (selectedItems.value.length < 10) {
    selectedItems.value.push(s)
  }
}

function removeSymbol(sym) {
  selectedItems.value = selectedItems.value.filter(i => i.symbol !== sym)
}

function addSearchSymbol() {
  const sym = symbolSearch.value.trim().toUpperCase()
  if (!sym || isSelected(sym) || selectedItems.value.length >= 10) return
  selectedItems.value.push({ symbol: sym, name: sym, category: symbolType.value })
  symbolSearch.value = ''
}

async function loadSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest/symbols`, { headers: auth.headers })
    const data = res.data
    if (symbolType.value === 'us_etf') availableSymbols.value = data.us_etf || []
    else if (symbolType.value === 'tw_etf') availableSymbols.value = data.tw_etf || []
    else availableSymbols.value = data.indices || []
  } catch (e) { console.error('Symbol load failed', e) }
}

async function runOptimization() {
  optError.value = ''
  runLoading.value = true
  results.value = null
  try {
    const res = await axios.post(`${API_BASE}/api/optimize`, {
      symbols: selectedItems.value.map(i => i.symbol),
      start_date: optConfig.start_date,
      end_date: optConfig.end_date
    }, { headers: auth.headers })
    results.value = res.data.results
  } catch (e) {
    optError.value = e.response?.data?.detail || e.message
  } finally {
    runLoading.value = false
  }
}

function createPieOption(portfolioData) {
  if (!portfolioData) return {}
  const data = Object.entries(portfolioData.weights)
    .filter(([sym, w]) => w > 0.01) // ignore weights less than 0.01%
    .map(([sym, w]) => ({ name: sym, value: w.toFixed(2) }))
  
  return {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(22, 27, 34, 0.9)', borderColor: 'rgba(48, 54, 61, 0.8)', textStyle: { color: '#e6edf3' }, formatter: '{b}: {c}%' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: 'transparent', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c}%', color: 'inherit' },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: data
      }
    ]
  }
}

const maxSharpePieOption = computed(() => createPieOption(results.value?.max_sharpe))
const minVolPieOption = computed(() => createPieOption(results.value?.min_volatility))

const efficientFrontierOption = computed(() => {
  if (!results.value?.efficient_frontier) return {}
  
  // Format [x(vol), y(ret)]
  const v_list = results.value.efficient_frontier.volatilities
  const r_list = results.value.efficient_frontier.returns
  const frontierPoints = v_list.map((v, idx) => [
    (v * 100).toFixed(2), 
    (r_list[idx] * 100).toFixed(2)
  ])

  const maxSharpeInfo = results.value.max_sharpe
  const minVolInfo = results.value.min_volatility

  const maxSharpePoint = [
    (maxSharpeInfo.volatility * 100).toFixed(2), 
    (maxSharpeInfo.return * 100).toFixed(2)
  ]
  const minVolPoint = [
    (minVolInfo.volatility * 100).toFixed(2), 
    (minVolInfo.return * 100).toFixed(2)
  ]

  const assetPoints = (results.value.asset_points || []).map(p => ({
    name: p.symbol,
    value: [(p.volatility * 100).toFixed(2), (p.return * 100).toFixed(2)]
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(22, 27, 34, 0.9)', 
      borderColor: 'rgba(48, 54, 61, 0.8)', 
      textStyle: { color: '#e6edf3' },
      formatter: p => `風險 (波動率): ${p[0].value[0]}%<br/>預期報酬: ${p[0].value[1]}%` 
    },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { 
      type: 'value', 
      name: '風險 (年化波動率 %)',
      nameLocation: 'middle',
      nameGap: 25,
      axisLabel: { color: '#8b949e', show: !isMobile.value },
      splitLine: { lineStyle: { color: 'rgba(139, 148, 158, 0.1)' } },
      scale: true
    },
    yAxis: { 
      type: 'value', 
      name: '預期報酬 (%)',
      nameLocation: 'middle',
      nameGap: 40,
      axisLabel: { color: '#8b949e', show: !isMobile.value },
      splitLine: { lineStyle: { color: 'rgba(139, 148, 158, 0.1)' } },
      scale: true
    },
    visualMap: {
      type: 'continuous',
      dimension: 2, 
      min: 0,
      max: 2, 
      calculable: true,
      orient: 'vertical',
      right: 0,
      top: 'center',
      inRange: { color: ['#1f6feb', '#58a6ff', '#3fb950', '#f85149'] },
      textStyle: { color: '#8b949e' },
      show: false 
    },
    series: [
      {
        name: '效率前緣',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#58a6ff' },
        data: frontierPoints
      },
      {
        name: '個別資產',
        type: 'scatter',
        symbolSize: 8,
        itemStyle: { color: '#8b949e', opacity: 0.6 },
        label: { 
          show: true, 
          position: 'right', 
          color: '#8b949e', 
          fontSize: 10, 
          formatter: '{b}',
          distance: 5
        },
        data: assetPoints,
        tooltip: { formatter: p => `資產: ${p.name}<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      {
        name: 'Max Sharpe 圓圈',
        type: 'scatter',
        symbolSize: 17.5,
        itemStyle: { 
          color: 'transparent', 
          borderColor: '#f85149', 
          borderWidth: 2,
          opacity: 0.8
        },
        label: { show: false },
        data: [maxSharpePoint],
        tooltip: { show: false }
      },
      {
        name: 'Max Sharpe',
        type: 'scatter',
        symbolSize: 14,
        itemStyle: { color: '#f85149', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'top',
          color: '#f85149',
          fontWeight: 'bold',
          formatter: '🏆 Max Sharpe',
          distance: 10
        },
        data: [maxSharpePoint],
        tooltip: { formatter: p => `🏆 最大夏普點<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      {
        name: 'Min Volatility 圓圈',
        type: 'scatter',
        symbolSize: 17.5,
        itemStyle: { 
          color: 'transparent', 
          borderColor: '#3fb950', 
          borderWidth: 2,
          opacity: 0.8
        },
        label: { show: false },
        data: [minVolPoint],
        tooltip: { show: false }
      },
      {
        name: 'Min Volatility',
        type: 'scatter',
        symbolSize: 14,
        itemStyle: { color: '#3fb950', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'bottom',
          color: '#3fb950',
          fontWeight: 'bold',
          formatter: '🛡️ Min Vol',
          distance: 10
        },
        data: [minVolPoint],
        tooltip: { formatter: p => `🛡️ 最小波動點<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      }
    ]
  }
})

function exportToBacktest(portfolioData) {
  // Store configured weights into sessionStorage to pass to backtest view
  const items = selectedItems.value.map(item => ({
    symbol: item.symbol,
    name: item.name,
    category: item.category,
    weight: portfolioData.weights[item.symbol] || 0
  })).filter(i => i.weight > 0.01)

  const preset = {
    items,
    start_date: optConfig.start_date,
    end_date: optConfig.end_date
  }
  
  sessionStorage.setItem('backtest_preset', JSON.stringify(preset))
  router.push('/backtest')
}

async function loadSavedPortfolios() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest`, { headers: auth.headers })
    savedPortfolios.value = res.data
  } catch (e) { console.error('Load saved failed', e) }
}

async function deleteSaved(id) {
  if (!confirm('確定刪除此優化組合？')) return
  try {
    await axios.delete(`${API_BASE}/api/backtest/${id}`, { headers: auth.headers })
    await loadSavedPortfolios()
  } catch (e) { console.error('Delete failed', e) }
}

function loadSaved(p) {
  showSaved.value = false
  selectedItems.value = p.items.map(i => ({ ...i }))
  optConfig.start_date = p.start_date
  optConfig.end_date = p.end_date
  if (p.results_json) results.value = p.results_json
}

onMounted(async () => {
  try {
    await loadSymbols()
    console.log('[OptimizeView] Symbols loaded successfully')
  } catch (error) {
    console.error('[OptimizeView] Failed to load symbols:', error)
  }
})
</script>

<style scoped>
.optimize-header {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
}

.symbol-item {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  width: 100% !important;
}
</style>


