<template>
  <div>
    <div class="flex-between mb-24">
      <h2>投資組合最佳化</h2>
      <div class="text-sm text-muted">基於 Markowitz 效率前緣理論尋找最佳權重分配</div>
    </div>

    <!-- Optimization Config -->
    <div class="grid-2" style="gap:24px;">
      <!-- Left: config -->
      <div>
        <div class="card mb-16">
          <div class="card-header"><h3>選擇資產 (最少 2 個, 最多 10 個)</h3></div>
          <div class="card-body">
            <!-- Quick symbol search -->
            <div class="form-group">
              <label class="form-label">搜尋代碼或名稱</label>
              <input v-model="symbolSearch" type="text" class="form-control" placeholder="輸入 0050, SPY..." @keydown.enter="addSearchSymbol" />
            </div>

            <!-- Symbol type tabs -->
            <div class="flex gap-8 mb-12" style="flex-wrap:wrap;">
              <button v-for="t in symbolTypes" :key="t.value"
                :class="['cat-tab', { active: symbolType === t.value }]"
                @click="symbolType = t.value; loadSymbols()">{{ t.label }}</button>
            </div>

            <!-- Symbol list -->
            <div class="symbol-list mb-16">
              <div v-for="s in filteredSymbols.slice(0, 20)" :key="s.symbol"
                :class="['symbol-item', { selected: isSelected(s.symbol), disabled: selectedItems.length >= 10 && !isSelected(s.symbol) }]"
                @click="toggleSymbol(s)">
                <div class="flex-between">
                  <div>
                    <span class="fw-600">{{ s.symbol }}</span>
                    <span class="text-sm text-muted" style="margin-left:8px;">{{ s.name }}</span>
                  </div>
                  <span v-if="isSelected(s.symbol)" class="text-accent">✓</span>
                </div>
              </div>
            </div>

            <!-- Selected list -->
            <div v-if="selectedItems.length > 0">
              <div class="text-xs text-muted mb-8">已選擇 ({{ selectedItems.length }}/10)</div>
              <div class="flex gap-8" style="flex-wrap:wrap;">
                <div v-for="item in selectedItems" :key="item.symbol" class="badge badge-accent flex align-center gap-4">
                  {{ item.symbol }}
                  <span style="cursor:pointer;opacity:0.6;" @click="removeSymbol(item.symbol)">✕</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Date range -->
        <div class="card">
          <div class="card-body grid-2">
            <div class="form-group">
              <label class="form-label">回測開始日期</label>
              <input v-model="optConfig.start_date" type="date" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">結束日期</label>
              <input v-model="optConfig.end_date" type="date" class="form-control" />
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Action area -->
      <div>
        <div class="card mb-16">
          <div class="card-body" style="display:flex;flex-direction:column;justify-content:center;min-height:200px;text-align:center;">
            <p class="text-muted mb-16">
              系統將根據選定資產的歷史走勢，計算並建構出 <strong>效率前緣 (Efficient Frontier)</strong>。<br>
              提供「最大夏普值 (最高性價比)」與「最小波動率 (最穩健)」兩種最佳權重組合。
            </p>
            <button class="btn btn-primary btn-lg" style="width:100%;" @click="runOptimization"
              :disabled="runLoading || selectedItems.length < 2 || selectedItems.length > 10">
              <span v-if="runLoading" class="spinner" style="width:16px;height:16px;margin-right:8px;"></span>
              {{ runLoading ? '模型計算中...' : '🧬 開始最佳化分析' }}
            </button>
            <div v-if="selectedItems.length < 2" class="text-red text-sm mt-8">請至少選擇 2 個資產進行分析</div>
          </div>
        </div>
        <div v-if="optError" class="alert alert-error">{{ optError }}</div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="results" class="mt-32">
      <h3 class="mb-16">最佳化分析結果</h3>

      <div class="grid-2 mb-24" style="gap:24px;">
        <!-- Max Sharpe Portfolio -->
        <div class="card" style="border: 1px solid var(--accent);">
          <div class="card-header" style="background:var(--accent-glow);">
            <div class="flex-between w-full" style="width:100%;">
              <h3 class="text-accent">🏆 最大夏普值組合 (Max Sharpe)</h3>
              <button class="btn btn-ghost btn-sm" @click="exportToBacktest(results.max_sharpe)">使用此權重回測</button>
            </div>
          </div>
          <div class="card-body">
            <div class="grid-3 mb-16">
              <div>
                <div class="text-xs text-muted">預期年化報酬</div>
                <div class="fw-600 text-green">{{ (results.max_sharpe.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">年化波動率</div>
                <div class="fw-600">{{ (results.max_sharpe.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">夏普值</div>
                <div class="fw-600 text-accent">{{ results.max_sharpe.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div style="height: 250px;">
              <v-chart :option="maxSharpePieOption" autoresize />
            </div>
          </div>
        </div>

        <!-- Min Volatility Portfolio -->
        <div class="card" style="border: 1px solid var(--green);">
          <div class="card-header" style="background:rgba(63, 185, 80, 0.1);">
             <div class="flex-between w-full" style="width:100%;">
              <h3 class="text-green">🛡️ 最小波動率組合 (Min Volatility)</h3>
              <button class="btn btn-ghost btn-sm" @click="exportToBacktest(results.min_volatility)">使用此權重回測</button>
            </div>
          </div>
          <div class="card-body">
            <div class="grid-3 mb-16">
              <div>
                <div class="text-xs text-muted">預期年化報酬</div>
                <div class="fw-600 text-green">{{ (results.min_volatility.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">年化波動率</div>
                <div class="fw-600">{{ (results.min_volatility.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">夏普值</div>
                <div class="fw-600 text-accent">{{ results.min_volatility.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div style="height: 250px;">
              <v-chart :option="minVolPieOption" autoresize />
            </div>
          </div>
        </div>
      </div>

      <!-- Efficient Frontier Chart -->
      <div class="card mb-24">
        <div class="card-header">
          <h3>效率前緣 (Efficient Frontier)</h3>
          <span class="text-sm text-muted">顯示在相同風險下能產生的最高預期報酬</span>
        </div>
        <div class="card-body" style="height:400px;">
          <v-chart :option="efficientFrontierOption" autoresize />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
// Remove local API_BASE declaration

const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])
const results = ref(null)
const runLoading = ref(false)
const optError = ref('')

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
    tooltip: { trigger: 'item', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: '{b}: {c}%' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#0d1117', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c}%', color: '#e6edf3' },
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

  return {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' },
      backgroundColor: '#161b22', 
      borderColor: '#30363d', 
      textStyle: { color: '#e6edf3' },
      formatter: p => `風險 (波動率): ${p[0].value[0]}%<br/>預期報酬: ${p[0].value[1]}%` 
    },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: { 
      type: 'value', 
      name: '風險 (年化波動率 %)',
      nameLocation: 'middle',
      nameGap: 25,
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#21262d' } },
      scale: true
    },
    yAxis: { 
      type: 'value', 
      name: '預期報酬 (%)',
      nameLocation: 'middle',
      nameGap: 40,
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#21262d' } },
      scale: true
    },
    visualMap: {
      type: 'continuous',
      dimension: 2, // Color by Sharpe Ratio
      min: 0,
      max: 2, // Approximate typical sharpe max for color scale
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
        name: 'Max Sharpe',
        type: 'scatter',
        symbolSize: 15,
        itemStyle: { color: '#f85149', borderColor: '#fff', borderWidth: 2 },
        data: [maxSharpePoint],
        tooltip: { formatter: p => `🏆 最大夏普點<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      {
        name: 'Min Volatility',
        type: 'scatter',
        symbolSize: 15,
        itemStyle: { color: '#3fb950', borderColor: '#fff', borderWidth: 2 },
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

onMounted(() => {
  loadSymbols()
})
</script>

<style scoped>
.symbol-list { max-height: 240px; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.symbol-item { padding: 10px 14px; cursor: pointer; transition: background 0.1s; border-bottom: 1px solid var(--border); }
.symbol-item:last-child { border-bottom: none; }
.symbol-item:hover { background: var(--bg-glass); }
.symbol-item.selected { background: var(--accent-glow); border-left: 3px solid var(--accent); }
.symbol-item.disabled { opacity: 0.4; cursor: not-allowed; }
.cat-tab { padding: 5px 12px; border: 1px solid var(--border); border-radius: 20px; background: transparent; color: var(--text-secondary); font-family: inherit; font-size: 0.78rem; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.cat-tab.active { background: var(--accent); color: white; border-color: var(--accent); }
.align-center { align-items: center; }
</style>
