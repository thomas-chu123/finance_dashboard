<template>
  <div>
    <div class="flex-between mb-24">
      <h2>回測管理</h2>
      <div class="flex gap-8">
        <button class="btn btn-ghost btn-sm" @click="showSaved = !showSaved">
          {{ showSaved ? '📊 執行回測' : '📂 已儲存' }}
        </button>
      </div>
    </div>

    <!-- Saved portfolios list -->
    <div v-if="showSaved">
      <div v-if="!savedPortfolios.length" style="padding:48px;text-align:center;color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:12px;">📂</div>
        尚無已儲存的回測
      </div>
      <div v-else class="grid-2">
        <div v-for="p in savedPortfolios" :key="p.id" class="card">
          <div class="card-header">
            <div>
              <div class="fw-600">{{ p.name }}</div>
              <div class="text-sm text-muted">{{ p.start_date }} → {{ p.end_date }}</div>
            </div>
            <div class="flex gap-8">
              <button class="btn btn-ghost btn-sm" @click="loadSaved(p)">載入</button>
              <button class="btn btn-danger btn-sm" @click="deleteSaved(p.id)">🗑️</button>
            </div>
          </div>
          <div class="card-body" v-if="p.results_json?.metrics">
            <div class="grid-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">CAGR</div>
                <div class="fw-600 text-green">{{ p.results_json.metrics.cagr }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-accent">{{ p.results_json.metrics.sharpe_ratio }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">Max DD</div>
                <div class="fw-600 text-red">{{ p.results_json.metrics.max_drawdown }}%</div>
              </div>
            </div>
            <div class="mt-16">
              <div class="text-xs text-muted mb-12">組合資產</div>
              <div class="flex gap-8" style="flex-wrap:wrap;">
                <span v-for="item in p.items" :key="item.symbol" class="badge badge-blue">
                  {{ item.symbol }} {{ item.weight }}%
                </span>
              </div>
            </div>
            <div class="mt-16">
              <button class="btn btn-ghost btn-sm" style="width:100%;" @click="addToTracking(p.items)">
                📡 一鍵加入追蹤
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Backtest runner -->
    <div v-else>
      <div class="grid-2" style="gap:24px;">
        <!-- Left: config -->
        <div>
          <div class="card mb-16">
            <div class="card-header"><h3>選擇資產 (最多 10 個)</h3></div>
            <div class="card-body">
              <!-- Quick symbol search -->
              <div class="form-group">
                <label class="form-label">搜尋代碼或名稱</label>
                <input v-model="symbolSearch" type="text" class="form-control" placeholder="輸入 0050, SPY, VIX..." @keydown.enter="addSearchSymbol" />
              </div>

              <!-- Symbol type tabs -->
              <div class="flex gap-8 mb-12" style="flex-wrap:wrap;">
                <button v-for="t in symbolTypes" :key="t.value"
                  :class="['cat-tab', { active: symbolType === t.value }]"
                  @click="symbolType = t.value; loadSymbols()">{{ t.label }}</button>
              </div>

              <!-- Symbol list -->
              <div class="symbol-list">
                <div v-for="s in filteredSymbols.slice(0, 1000)" :key="s.symbol"
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
            </div>
          </div>

          <!-- Date range + amount -->
          <div class="card">
            <div class="card-body">
              <div class="grid-2">
                <div class="form-group">
                  <label class="form-label">開始日期</label>
                  <input v-model="btConfig.start_date" type="date" class="form-control" />
                </div>
                <div class="form-group">
                  <label class="form-label">結束日期</label>
                  <input v-model="btConfig.end_date" type="date" class="form-control" />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">初始金額 (USD)</label>
                <input v-model.number="btConfig.initial_amount" type="number" class="form-control" />
                <div class="text-xs text-muted mt-4">註：若包含台灣資產，系統將自動依歷史匯率換算為美金計價。</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: selected + weights -->
        <div>
          <div class="card mb-16">
            <div class="card-header">
              <h3>已選資產 ({{ selectedItems.length }}/10)</h3>
              <div class="text-sm" :class="totalWeight === 100 ? 'text-green' : 'text-red'">
                總權重: {{ totalWeight.toFixed(1) }}%
              </div>
            </div>
            <div class="card-body">
              <div v-if="!selectedItems.length" style="color:var(--text-muted);font-size:0.875rem;padding:16px 0;">
                請從左側選擇資產
              </div>
              <div v-for="item in selectedItems" :key="item.symbol" class="selected-item">
                <div class="flex-between" style="margin-bottom:6px;">
                  <div>
                    <span class="fw-600">{{ item.symbol }}</span>
                    <span class="text-xs text-muted" style="margin-left:8px;">{{ item.name }}</span>
                  </div>
                  <div class="flex gap-8 align-center">
                    <span class="fw-600 text-accent">{{ item.weight.toFixed(1) }}%</span>
                    <button class="btn btn-danger btn-sm" style="padding:2px 8px;" @click="removeSymbol(item.symbol)">✕</button>
                  </div>
                </div>
                <input v-model.number="item.weight" type="range" min="1" max="100" step="1"
                  @input="adjustWeights(item.symbol, item.weight)" />
              </div>

              <div v-if="selectedItems.length > 1" class="mt-16 flex gap-8">
                <button class="btn btn-ghost btn-sm" style="flex:1;" @click="equalizeWeights">
                  ⚖️ 平均分配
                </button>
                <button class="btn btn-success btn-sm" style="flex:1;" @click="showSaveModal = true">
                  💾 儲存組合
                </button>
              </div>
              <div v-else-if="selectedItems.length === 1" class="mt-16">
                <button class="btn btn-success btn-sm" style="width:100%;" @click="showSaveModal = true">
                  💾 儲存組合
                </button>
              </div>
            </div>
          </div>

          <div v-if="backtestError" class="alert alert-error mb-16">{{ backtestError }}</div>

          <div v-if="runLoading" class="progress-wrapper mb-16">
            <div class="progress-info flex-between mb-8">
              <span class="text-sm fw-600">
                🚀 {{ runProgress < 100 ? '正在計算結果...' : '計算完成！' }}
              </span>
              <span class="text-xs text-accent fw-700">{{ Math.floor(runProgress) }}%</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: runProgress + '%' }"></div>
            </div>
          </div>

          <button v-else class="btn btn-primary btn-lg" style="width:100%;" @click="runBacktest"
            :disabled="runLoading || selectedItems.length === 0 || Math.abs(totalWeight - 100) > 0.5">
            🚀 執行回測
          </button>
        </div>
      </div>

      <!-- Results -->
      <div v-if="results" class="mt-24">
        <div class="flex-between mb-16">
          <h3>回測結果 <span class="text-sm text-muted">({{ results.date_range?.start }} → {{ results.date_range?.end }})</span></h3>
          <div class="flex gap-8">
            <button class="btn btn-ghost btn-sm" @click="addAllToTracking">📡 加入追蹤</button>
            <button class="btn btn-success btn-sm" @click="showSaveModal = true">💾 儲存回測</button>
          </div>
        </div>

        <!-- Metrics -->
        <div class="grid-4 mb-24" v-if="results?.metrics">
          <div class="stat-card">
            <div class="stat-label">CAGR 年化報酬</div>
            <div :class="['stat-value', (results.metrics.cagr || 0) >= 0 ? 'text-green' : 'text-red']">{{ results.metrics.cagr }}%</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Sharpe Ratio</div>
            <div class="stat-value text-accent">{{ results.metrics.sharpe_ratio }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Sortino Ratio</div>
            <div class="stat-value text-purple">{{ results.metrics.sortino_ratio }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Beta</div>
            <div class="stat-value">{{ results.metrics.beta }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">最大回撤</div>
            <div class="stat-value text-red">{{ results.metrics.max_drawdown }}%</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">年化標準差</div>
            <div class="stat-value">{{ results.metrics.annual_std }}%</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">VaR (95%)</div>
            <div class="stat-value text-yellow">{{ results.metrics.var_95 }}%</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">期末資產</div>
            <div class="stat-value text-green">${{ (results.metrics.final_amount || 0).toLocaleString() }}</div>
            <div class="stat-change" :class="(results.metrics.total_return || 0) >= 0 ? 'up' : 'down'">
              總報酬 {{ results.metrics.total_return }}%
            </div>
          </div>
        </div>

        <!-- Charts -->
        <div class="grid-2 mb-24" style="gap:24px;">
          <!-- Portfolio growth chart -->
          <div class="card">
            <div class="card-header"><h3>資產成長曲線 (Portfolio Growth)</h3></div>
            <div class="card-body" style="height:420px;">
              <v-chart :option="growthChartOption" autoresize style="height:100%;" />
            </div>
          </div>

          <!-- Annual returns -->
          <div class="card">
            <div class="card-header"><h3>年度報酬率</h3></div>
            <div class="card-body" style="height:300px;">
              <v-chart :option="annualReturnChartOption" autoresize style="height:100%;" />
            </div>
          </div>
        </div>

        <!-- Asset contributions -->
        <div class="card mb-24">
          <div class="card-header"><h3>各資產貢獻度</h3></div>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr><th>代碼</th><th>名稱</th><th>權重</th><th>報酬貢獻 (USD)</th></tr>
              </thead>
              <tbody>
                <tr v-for="(contrib, symbol) in (results.asset_contributions || {})" :key="symbol">
                  <td class="fw-600 text-accent">{{ symbol }}</td>
                  <td>{{ contrib.name }}</td>
                  <td>{{ contrib.weight }}%</td>
                  <td :class="(contrib.return_contribution || 0) >= 0 ? 'text-green' : 'text-red'">
                    ${{ (contrib.return_contribution || 0).toLocaleString() }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Drawdown chart -->
        <div class="card mb-24" v-if="results.drawdown_series">
          <div class="card-header">
            <h3>回撤曲線 (Drawdown)</h3>
            <span class="text-sm text-muted">最大回撤：<span class="text-red fw-600">{{ results.metrics.max_drawdown }}%</span></span>
          </div>
          <div class="card-body" style="height:240px;">
            <v-chart :option="drawdownChartOption" autoresize style="height:100%;" />
          </div>
        </div>

        <!-- Monthly Returns Heatmap -->
        <div class="card mb-24" v-if="results.monthly_returns">
          <div class="card-header">
            <h3>月度報酬率熱力圖</h3>
          </div>
          <div class="card-body" style="height:320px;">
            <v-chart :option="monthlyReturnsHeatmapOption" autoresize style="height:100%;" />
          </div>
        </div>

        <!-- Correlation heatmap -->
        <div class="card" v-if="results.correlation_matrix && results.available_symbols?.length > 1">
          <div class="card-header">
            <h3>相關性熱力圖</h3>
            <span class="text-xs text-muted">1.0 = 完全正相關 · -1.0 = 完全負相關</span>
          </div>
          <div class="card-body" style="height:320px;">
            <v-chart :option="correlationHeatmapOption" autoresize style="height:100%;" />
          </div>
        </div>
      </div>
    </div>

    <!-- Save modal -->
    <Transition name="fade">
      <div v-if="showSaveModal" class="modal-overlay">
        <div class="modal">
          <div class="modal-header"><h3>儲存回測</h3><button class="modal-close" @click="showSaveModal = false">✕</button></div>
          <div class="modal-body">
            <div class="form-group">
              <label class="form-label">回測名稱</label>
              <input v-model="saveName" type="text" class="form-control" placeholder="例: 台美混合 2020-2024" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="showSaveModal = false">取消</button>
            <button class="btn btn-primary" @click="saveBacktest">儲存</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { useTrackingStore } from '../stores/tracking'

const auth = useAuthStore()
const trackingStore = useTrackingStore()

// Remove local API_BASE declaration
const showSaved = ref(false)
const savedPortfolios = ref([])
const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])
const results = ref(null)
const runLoading = ref(false)
const runProgress = ref(0)
const backtestError = ref('')
const showSaveModal = ref(false)
const saveName = ref('')

const symbolTypes = [
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'index', label: '指數/原物料' },
  { value: 'crypto', label: '加密貨幣' },
]

const btConfig = reactive({
  start_date: '2020-01-01',
  end_date: new Date().toISOString().split('T')[0],
  initial_amount: 100000,
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  return availableSymbols.value.filter(s =>
    !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
})

const totalWeight = computed(() => selectedItems.value.reduce((s, i) => s + (i.weight || 0), 0))

function isSelected(sym) { return selectedItems.value.some(i => i.symbol === sym) }

function toggleSymbol(s) {
  if (isSelected(s.symbol)) {
    removeSymbol(s.symbol)
  } else if (selectedItems.value.length < 10) {
    selectedItems.value.push({ ...s, weight: Math.floor(100 / (selectedItems.value.length + 1)) })
    equalizeWeights()
  }
}

function removeSymbol(sym) {
  selectedItems.value = selectedItems.value.filter(i => i.symbol !== sym)
  equalizeWeights()
}

function equalizeWeights() {
  if (!selectedItems.value.length) return
  const w = parseFloat((100 / selectedItems.value.length).toFixed(1))
  selectedItems.value.forEach((item, idx) => {
    item.weight = idx === selectedItems.value.length - 1 ? 100 - w * (selectedItems.value.length - 1) : w
  })
}

function addSearchSymbol() {
  const sym = symbolSearch.value.trim().toUpperCase()
  if (!sym || isSelected(sym) || selectedItems.value.length >= 10) return
  selectedItems.value.push({ symbol: sym, name: sym, category: symbolType.value, weight: 0 })
  equalizeWeights()
  symbolSearch.value = ''
}

async function loadSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest/symbols`, { headers: auth.headers })
    const data = res.data
    if (symbolType.value === 'us_etf') availableSymbols.value = data.us_etf || []
    else if (symbolType.value === 'tw_etf') availableSymbols.value = data.tw_etf || []
    else if (symbolType.value === 'crypto') {
      availableSymbols.value = (data.indices || []).filter(s => s.category === 'crypto')
    }
    else availableSymbols.value = (data.indices || []).filter(s => s.category !== 'crypto')
  } catch (e) { console.error('Symbol load failed', e) }
}

async function runBacktest() {
  backtestError.value = ''
  runLoading.value = true
  runProgress.value = 0
  results.value = null

  // Progress simulation
  const progressInterval = setInterval(() => {
    if (runProgress.value < 20) {
      runProgress.value += 2 // Fast start
    } else if (runProgress.value < 85) {
      runProgress.value += 0.5 // Normal slow
    } else if (runProgress.value < 98) {
      runProgress.value += 0.1 // Crawl
    }
  }, 100)

  try {
    const res = await axios.post(`${API_BASE}/api/backtest/run`, {
      items: selectedItems.value.map(i => ({ symbol: i.symbol, name: i.name, weight: i.weight, category: i.category })),
      start_date: btConfig.start_date,
      end_date: btConfig.end_date,
      initial_amount: btConfig.initial_amount,
    }, { headers: auth.headers })
    
    clearInterval(progressInterval)
    runProgress.value = 100
    
    // Give a moment for the 100% state to be visible
    await new Promise(r => setTimeout(r, 400))
    console.log('[DEBUG] Backtest results:', res.data)
    results.value = res.data
  } catch (e) {
    clearInterval(progressInterval)
    console.error('[DEBUG] Backtest error:', e)
    backtestError.value = e.response?.data?.detail || e.message
  } finally {
    runLoading.value = false
    runProgress.value = 0
  }
}

const growthChartOption = computed(() => {
  if (!results.value?.portfolio_value_series) return {}
  const dates = Object.keys(results.value.portfolio_value_series)
  const values = dates.map(d => parseFloat(results.value.portfolio_value_series[d]))

  const series = [{ 
    name: 'Portfolio 1',
    data: values, 
    type: 'line', 
    smooth: true, 
    symbol: 'none', 
    lineStyle: { color: '#1e40af', width: 2.5 }, // More solid blue like reference
    areaStyle: { 
      color: { 
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1, 
        colorStops: [
          { offset: 0, color: 'rgba(30, 64, 175, 0.2)' }, 
          { offset: 1, color: 'rgba(30, 64, 175, 0)' }
        ] 
      } 
    } 
  }]

  // Add benchmark if available
  if (results.value?.benchmark_value_series && Object.keys(results.value.benchmark_value_series).length > 0) {
    const bmData = results.value.benchmark_value_series
    const initialAmt = results.value?.metrics?.initial_amount || 0
    if (initialAmt > 0) {
      const bmValues = dates.map(d => {
        const val = bmData[d] || 1
        return parseFloat((val * initialAmt).toFixed(2))
      })
      series.push({
        name: 'Portfolio 2', // Reference uses Portfolio 1/2 naming style
        data: bmValues,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2, type: 'solid' } // Teal/Green like reference
      })
    }
  }

  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e', fontFamily: 'Inter, sans-serif' },
    grid: { left: 80, right: 40, top: 40, bottom: 80 }, // More space for labels
    legend: { 
      show: true, 
      textStyle: { color: '#8b949e' }, 
      bottom: '2%', 
      left: 'center', 
      orient: 'horizontal',
      icon: 'roundRect'
    },
    xAxis: { 
      type: 'category', 
      name: 'Year',
      nameLocation: 'middle',
      nameGap: 35,
      data: dates, 
      axisLabel: { 
        fontSize: 10, 
        color: '#8b949e', 
        interval: Math.floor(dates.length / 8),
        formatter: (value) => value.split('-')[0] // Only show year if possible, or keeps as is
      }, 
      axisLine: { lineStyle: { color: '#30363d' } },
      splitLine: { show: false } // Cleaner look like reference
    },
    yAxis: { 
      type: 'log', // Logarithmic scale as requested
      name: 'Portfolio Balance ($)',
      nameLocation: 'middle',
      nameGap: 60,
      axisLabel: { 
        formatter: v => '$' + v.toLocaleString(), 
        color: '#8b949e' 
      }, 
      splitLine: { lineStyle: { color: '#21262d' } }, 
      scale: true 
    },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => {
      let html = `${p[0].axisValue}<br/>`
      p.forEach(s => { html += `${s.marker} ${s.seriesName}: $${parseFloat(s.value).toLocaleString()}<br/>` })
      return html
    }},
    series: series
  }
})

const annualReturnChartOption = computed(() => {
  if (!results.value?.annual_returns) return {}
  const years = Object.keys(results.value.annual_returns)
  const vals = years.map(y => (results.value.annual_returns[y] * 100).toFixed(2))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#e6edf3' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: years, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } },
    yAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${p[0].axisValue}: ${p[0].value}%` },
    series: [{
      data: vals.map(v => ({ value: v, itemStyle: { color: parseFloat(v) >= 0 ? '#3fb950' : '#f85149' } })),
      type: 'bar', barMaxWidth: 40,
    }]
  }
})

const drawdownChartOption = computed(() => {
  if (!results.value?.drawdown_series) return {}
  const dates = Object.keys(results.value.drawdown_series)
  const vals = dates.map(d => parseFloat(results.value.drawdown_series[d].toFixed(2)))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#e6edf3' },
    grid: { left: 60, right: 20, top: 10, bottom: 40 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 10, color: '#8b949e', interval: Math.floor(dates.length / 6) }, axisLine: { lineStyle: { color: '#30363d' } } },
    yAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } }, max: 0 },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${p[0].axisValue}<br/>回撤：${p[0].value}%` },
    series: [{
      data: vals, type: 'line', smooth: true, symbol: 'none',
      lineStyle: { color: '#f85149', width: 1.5 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(248,81,73,0.4)' }, { offset: 1, color: 'rgba(248,81,73,0.02)' }] } }
    }]
  }
})

const correlationHeatmapOption = computed(() => {
  if (!results.value?.correlation_matrix || !results.value?.available_symbols) return {}
  const syms = results.value.available_symbols
  const matrix = results.value.correlation_matrix
  // Build [x, y, value] triples
  const data = []
  syms.forEach((rowSym, yi) => {
    syms.forEach((colSym, xi) => {
      const val = (matrix[rowSym]?.[colSym] ?? 0)
      data.push([xi, yi, parseFloat(val.toFixed(3))])
    })
  })
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e' },
    grid: { left: 70, right: 80, top: 20, bottom: 70 },
    xAxis: { type: 'category', data: syms, axisLabel: { color: '#8b949e', rotate: 30 }, axisLine: { lineStyle: { color: '#30363d' } } },
    yAxis: { type: 'category', data: syms, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } },
    visualMap: {
      min: -1, max: 1, calculable: true, orient: 'vertical', right: 0, top: 'center',
      inRange: { color: ['#f85149', '#21262d', '#3fb950'] },
      textStyle: { color: '#8b949e' }, precision: 2
    },
    tooltip: { backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${syms[p.value[1]]} vs ${syms[p.value[0]]}<br/>相關係數：${p.value[2]}` },
    series: [{ type: 'heatmap', data, label: { show: syms.length <= 6, color: '#e6edf3', fontSize: 11 } }]
  }
})

const monthlyReturnsHeatmapOption = computed(() => {
  if (!results.value?.monthly_returns) return {}
  const mr = results.value.monthly_returns
  const years_raw = mr.years || []
  const years = years_raw.map(String)
  const months = mr.months || []
  const data = []
  const heatmap_raw = mr.data || []
  
  years.forEach((year, xIndex) => {
    months.forEach((month, yIndex) => {
      try {
        // Handle both 2D (matrix) and potentially 1D/broken data
        const row = heatmap_raw[xIndex]
        if (!row) return
        
        const val = row[yIndex]
        if (val !== null && val !== undefined && !isNaN(val)) {
          // backend uses ratio, frontend heatmap wants % value or ratio?
          // The previous code did parseFloat((val * 100).toFixed(2))
          data.push([xIndex, yIndex, parseFloat((val * 100).toFixed(2))])
        }
      } catch (err) {
        console.error(`[DEBUG] Heatmap compute error at ${xIndex},${yIndex}`, err)
      }
    })
  })

  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e' },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: years, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } }, splitArea: { show: true } },
    yAxis: { type: 'category', data: months, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } }, splitArea: { show: true } },
    visualMap: {
      min: -15, max: 15, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#f85149', '#161b22', '#3fb950'] },
      textStyle: { color: '#8b949e' }, formatter: v => v + '%'
    },
    tooltip: { backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${years[p.value[0]]} ${months[p.value[1]]}<br/>報酬：${p.value[2]}%` },
    series: [{ 
      type: 'heatmap', 
      data, 
      label: { show: true, color: '#e6edf3', fontSize: 10, formatter: p => p.value[2] + '%' },
      itemStyle: { borderColor: '#0d1117', borderWidth: 1 }
    }]
  }
})

async function loadSavedPortfolios() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest`, { headers: auth.headers })
    savedPortfolios.value = res.data
  } catch (e) { console.error('Load saved failed', e) }
}

async function deleteSaved(id) {
  if (!confirm('確定刪除此回測？')) return
  await axios.delete(`${API_BASE}/api/backtest/${id}`, { headers: auth.headers })
  await loadSavedPortfolios()
}

function loadSaved(p) {
  showSaved.value = false
  selectedItems.value = p.items.map(i => ({ ...i }))
  btConfig.start_date = p.start_date
  btConfig.end_date = p.end_date
  btConfig.initial_amount = p.initial_amount
  if (p.results_json) results.value = p.results_json
}

async function saveBacktest() {
  if (!saveName.value.trim()) return
  try {
    await axios.post(`${API_BASE}/api/backtest/save`, {
      name: saveName.value,
      items: selectedItems.value,
      start_date: btConfig.start_date,
      end_date: btConfig.end_date,
      initial_amount: btConfig.initial_amount,
      results_json: results.value,
    }, { headers: auth.headers })
    showSaveModal.value = false
    saveName.value = ''
    await loadSavedPortfolios()
    alert('回測已儲存！')
  } catch (e) { alert('儲存失敗: ' + (e.response?.data?.detail || e.message)) }
}

async function addAllToTracking() {
  const symbols = selectedItems.value.map(i => i.symbol)
  const names = selectedItems.value.map(i => i.name)
  const categories = selectedItems.value.map(i => i.category)
  await trackingStore.addFromBacktest(symbols, names, categories)
  alert(`已將 ${symbols.length} 個資產加入追蹤！`)
}

async function addToTracking(items) {
  await trackingStore.addFromBacktest(items.map(i => i.symbol), items.map(i => i.name || i.symbol), items.map(i => i.category || 'us_etf'))
  alert('已加入追蹤！')
}

onMounted(async () => {
  await loadSymbols()
  await loadSavedPortfolios()

  const presetStr = sessionStorage.getItem('backtest_preset')
  if (presetStr) {
    try {
      const preset = JSON.parse(presetStr)
      selectedItems.value = preset.items
      btConfig.start_date = preset.start_date
      btConfig.end_date = preset.end_date
      sessionStorage.removeItem('backtest_preset') // clean up
      
      // Auto run backtest if valid
      if (selectedItems.value.length > 0) {
        // Ensure total weight is approx 100 before running automatically
        const total = selectedItems.value.reduce((s, i) => s + i.weight, 0)
        if (Math.abs(total - 100) < 0.5) {
            setTimeout(() => runBacktest(), 500) // slight delay to let UI render
        }
      }
    } catch (e) {
      console.error('Failed to parse preset', e)
    }
  }
})
</script>

<style scoped>
.symbol-list { max-height: 240px; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.symbol-item { padding: 10px 14px; cursor: pointer; transition: background 0.1s; border-bottom: 1px solid var(--border); }
.symbol-item:last-child { border-bottom: none; }
.symbol-item:hover { background: var(--bg-glass); }
.symbol-item.selected { background: var(--accent-glow); border-left: 3px solid var(--accent); }
.symbol-item.disabled { opacity: 0.4; cursor: not-allowed; }
.selected-item { padding: 12px; background: var(--bg-glass); border-radius: var(--radius-sm); margin-bottom: 10px; }
.cat-tab { padding: 5px 12px; border: 1px solid var(--border); border-radius: 20px; background: transparent; color: var(--text-secondary); font-family: inherit; font-size: 0.78rem; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.cat-tab.active { background: var(--accent); color: white; border-color: var(--accent); }
.align-center { align-items: center; }

/* Progress Bar Styles */
.progress-wrapper {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  animation: slideUp 0.3s ease-out;
}

.progress-track {
  height: 8px;
  background: var(--bg-base);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
  transition: width 0.2s ease-out;
  border-radius: 4px;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
