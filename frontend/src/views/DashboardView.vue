<template>
  <div>
    <h2 class="mb-24">投資總覽</h2>

    <!-- Stat cards -->
    <div class="grid-4 mb-24">
      <div class="stat-card">
        <div class="stat-label">追蹤指數數量</div>
        <div class="stat-value text-accent">{{ trackingStore.items.length }}</div>
        <div class="stat-change">{{ activeCount }} 個啟用中</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">觸發通知記錄</div>
        <div class="stat-value">{{ trackingStore.alertLogs.length }}</div>
        <div class="stat-change">近 50 筆</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">電子郵件通知</div>
        <div :class="['stat-value', auth.profile?.notify_email ? 'text-green' : 'text-muted']">
          {{ auth.profile?.notify_email ? '已啟用' : '停用' }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">LINE 通知</div>
        <div :class="['stat-value', auth.profile?.notify_line ? 'text-green' : 'text-muted']">
          {{ auth.profile?.notify_line ? '已啟用' : '停用' }}
        </div>
      </div>
    </div>

    <!-- Live Market Quotes -->
    <div class="card mb-24">
      <div class="card-header">
        <h3>📡 即時市場報價</h3>
        <div class="flex gap-8 align-center">
          <span v-if="quotesLoading" class="spinner" style="width:14px;height:14px;"></span>
          <span class="text-xs text-muted">{{ quotesLastUpdated || '載入中...' }}</span>
          <button class="btn btn-ghost btn-sm" @click="fetchQuotes">↻ 更新</button>
          <button class="btn btn-primary btn-sm" @click="openQuoteModal">⚙ 自訂追蹤指數</button>
        </div>
      </div>
      <div class="card-body">
        <div v-if="quotesLoading && !quotes.length" class="loading-center">
          <div class="spinner"></div>
        </div>
        <div v-else class="quotes-grid">
          <div v-for="q in quotes" :key="q.symbol" class="quote-card" @click="openQuoteUrl(q.symbol)" :title="'前往 Yahoo 股市查看 ' + q.symbol">
            <div class="flex justify-between items-start">
              <div class="quote-symbol">{{ q.symbol }}</div>
              <div v-if="q.change !== null && q.change !== 0" :class="['quote-arrow', q.change > 0 ? 'text-red' : 'text-green']">
                {{ q.change > 0 ? '⬆️' : '⬇️' }}
              </div>
            </div>
            <div class="quote-name">{{ q.name }}</div>
            <div class="flex justify-between items-end mt-4">
              <div class="quote-price" v-if="q.price !== null">
                {{ formatPrice(q.price) }}
              </div>
              <div class="quote-price text-muted" v-else>N/A</div>
              
              <div v-if="q.change !== null" :class="['quote-delta', q.change > 0 ? 'text-red' : q.change < 0 ? 'text-green' : 'text-muted']">
                {{ Math.abs(q.change).toFixed(q.price < 10 ? 4 : 2) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent tracking -->
    <div class="card mb-24">
      <div class="card-header">
        <h3>追蹤中的指數</h3>
        <router-link to="/tracking" class="btn btn-ghost btn-sm">查看全部 →</router-link>
      </div>
      <div v-if="trackingStore.loading" class="loading-center"><div class="spinner"></div></div>
      <div v-else-if="!trackingStore.items.length" style="padding:32px;text-align:center;color:var(--text-muted);">
        尚未追蹤任何指數 · <router-link to="/tracking" style="color:var(--accent)">立即新增</router-link>
      </div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>代碼</th><th>名稱</th><th>類別</th><th>目前價格</th><th>觸發門檻</th><th>狀態</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in trackingStore.items.slice(0, 6)" :key="item.id">
              <td><span class="fw-600 text-accent">{{ item.symbol }}</span></td>
              <td>{{ item.name }}</td>
              <td><span :class="['badge', categoryBadge(item.category)]">{{ item.category.toUpperCase() }}</span></td>
              <td>{{ item.current_price ? item.current_price.toLocaleString() : '—' }}</td>
              <td>
                <span v-if="item.trigger_price">
                  {{ item.trigger_direction === 'above' ? '↑' : '↓' }} {{ item.trigger_price }}
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td><span :class="['badge', item.is_active ? 'badge-green' : 'badge-red']">{{ item.is_active ? '啟用' : '停用' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Alert logs -->
    <div class="card">
      <div class="card-header">
        <h3>最近通知記錄</h3>
      </div>
      <div v-if="!trackingStore.alertLogs.length" style="padding:32px;text-align:center;color:var(--text-muted);">
        尚無通知記錄
      </div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr><th>時間</th><th>代碼</th><th>觸發價格</th><th>實際價格</th><th>通知方式</th><th>狀態</th></tr>
          </thead>
          <tbody>
            <tr v-for="log in trackingStore.alertLogs.slice(0, 10)" :key="log.id">
              <td class="text-sm text-muted">{{ formatDate(log.created_at) }}</td>
              <td class="fw-600">{{ log.symbol }}</td>
              <td>{{ log.trigger_price }}</td>
              <td>{{ log.current_price }}</td>
              <td><span class="badge badge-blue">{{ log.channel }}</span></td>
              <td><span :class="['badge', log.status === 'sent' ? 'badge-green' : 'badge-red']">{{ log.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <!-- Modal: 自訂追蹤指數 -->
    <Teleport to="body">
    <div v-if="showQuoteModal" class="modal-overlay" @click.self="showQuoteModal = false">
      <div class="modal quote-modal">
        <!-- Header -->
        <div class="modal-header">
          <h3>⚙ 自訂追蹤指數</h3>
          <button class="btn-icon" @click="showQuoteModal = false">✕</button>
        </div>

        <!-- Body: two columns -->
        <div class="modal-body quote-modal-body">

          <!-- LEFT: Browse & Add -->
          <div class="qm-left">
            <!-- Category Tabs -->
            <div class="cat-tabs">
              <button
                v-for="tab in categoryTabs" :key="tab.key"
                :class="['cat-tab', activeTab === tab.key ? 'cat-tab--active' : '']"
                @click="activeTab = tab.key; quoteSearch = ''"
              >{{ tab.label }}</button>
            </div>

            <!-- Search -->
            <div class="qm-search">
              <input
                type="text" class="input" v-model="quoteSearch"
                :placeholder="'搜尋 ' + currentTabLabel + ' 代碼或名稱...'"
              />
            </div>

            <!-- Symbol list -->
            <div v-if="symbolsLoading" class="loading-center" style="min-height:200px">
              <div class="spinner"></div>
            </div>
            <div v-else class="qm-symbol-list">
              <div
                v-for="item in filteredCurrentTab" :key="item.symbol"
                class="qm-symbol-row"
                :class="{ 'qm-symbol-row--selected': isSelected(item.symbol) }"
              >
                <div class="qm-sym-info">
                  <span class="fw-600 text-accent">{{ item.symbol }}</span>
                  <span class="text-muted qm-sym-name">{{ item.name }}</span>
                </div>
                <button
                  v-if="!isSelected(item.symbol)"
                  class="btn btn-ghost btn-sm text-green"
                  @click="addQuote(item)"
                >＋</button>
                <span v-else class="qm-added-badge">✔ 已加入</span>
              </div>
              <div v-if="!filteredCurrentTab.length" class="text-center text-muted p-24">無符合結果</div>
            </div>
          </div>

          <!-- RIGHT: Selected list -->
          <div class="qm-right">
            <div class="qm-right-header">
              <span class="fw-600">已追蹤指數</span>
              <span class="badge badge-blue">{{ selectedQuotes.length }}</span>
            </div>
            <div class="qm-selected-list">
              <div
                v-for="(item, idx) in selectedQuotes" :key="idx"
                class="qm-selected-row"
              >
                <div class="qm-sym-info">
                  <span class="fw-600">{{ item.symbol }}</span>
                  <span class="text-muted qm-sym-name">{{ item.name }}</span>
                </div>
                <button class="btn-icon text-red" @click="removeQuote(idx)" title="移除">✕</button>
              </div>
              <div v-if="!selectedQuotes.length" class="text-center text-muted p-24" style="font-size:0.85rem">尚未加入任何標的</div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showQuoteModal = false">取消</button>
          <button class="btn btn-primary" @click="saveQuotes" :disabled="savingQuotes">
            <span v-if="savingQuotes" class="spinner" style="width:12px;height:12px;"></span>
            儲存追蹤清單
          </button>
        </div>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { useTrackingStore } from '../stores/tracking'

const auth = useAuthStore()
const trackingStore = useTrackingStore()

// Remove local API_BASE declaration
const quotes = ref([])
const quotesLoading = ref(false)
const quotesLastUpdated = ref('')
let quotesTimer = null

const DEFAULT_SYMBOLS = [
  {"symbol": "SPY",     "name": "S&P 500 ETF"},
  {"symbol": "QQQ",     "name": "Nasdaq 100 ETF"},
  {"symbol": "VTI",     "name": "Total Market ETF"},
  {"symbol": "GLD",     "name": "Gold ETF"},
  {"symbol": "^VIX",    "name": "VIX 恐慌指數"},
  {"symbol": "CL=F",    "name": "原油期貨"},
  {"symbol": "0050.TW", "name": "元大台灣50"},
  {"symbol": "0056.TW", "name": "元大高股息"}
]

const showQuoteModal = ref(false)
const quoteSearch = ref('')
const symbolsLoading = ref(false)
const savingQuotes = ref(false)
const availableSymbols = ref({ tw_etf: [], us_etf: [], index: [] })
const selectedQuotes = ref([])
const activeTab = ref('us_etf')

const categoryTabs = [
  { key: 'us_etf', label: '美國ETF' },
  { key: 'tw_etf', label: '台灣ETF' },
  { key: 'index',  label: '指數/原物料' },
]

const currentTabLabel = computed(() => categoryTabs.find(t => t.key === activeTab.value)?.label || '')

const filteredCurrentTab = computed(() => {
  const q = quoteSearch.value.toLowerCase()
  const list = availableSymbols.value[activeTab.value] || []
  if (!q) return list
  return list.filter(item =>
    item.symbol.toLowerCase().includes(q) || item.name.toLowerCase().includes(q)
  )
})

function isSelected(symbol) {
  return selectedQuotes.value.some(q => q.symbol === symbol)
}

async function openQuoteModal() {
  selectedQuotes.value = [...(auth.profile?.dashboard_quotes || DEFAULT_SYMBOLS)]
  showQuoteModal.value = true
  if (availableSymbols.value.tw_etf.length === 0) {
    symbolsLoading.value = true
    try {
      const res = await axios.get(`${API_BASE}/api/market/symbols`)
      availableSymbols.value = res.data
    } catch (e) {
      console.error('Failed to load symbols', e)
    } finally {
      symbolsLoading.value = false
    }
  }
}

function addQuote(item) {
  if (!selectedQuotes.value.some(q => q.symbol === item.symbol)) {
    selectedQuotes.value.push({ symbol: item.symbol, name: item.name })
  }
}

function removeQuote(idx) {
  selectedQuotes.value.splice(idx, 1)
}

async function saveQuotes() {
  savingQuotes.value = true
  try {
    await auth.updateProfile({ dashboard_quotes: selectedQuotes.value })
    showQuoteModal.value = false
    await fetchQuotes()
  } catch (e) {
    console.error('Failed to save quotes', e)
    alert('儲存失敗，請重試')
  } finally {
    savingQuotes.value = false
  }
}

const activeCount = computed(() => trackingStore.items.filter(i => i.is_active).length)

function categoryBadge(cat) {
  const map = { vix: 'badge-red', oil: 'badge-yellow', us_etf: 'badge-blue', tw_etf: 'badge-purple', index: 'badge-blue', crypto: 'badge-yellow' }
  return map[cat] || 'badge-blue'
}

function formatDate(d) {
  return new Date(d).toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' })
}

function formatPrice(p) {
  if (p === null || p === undefined) return 'N/A'
  return parseFloat(p) >= 1000
    ? parseFloat(p).toLocaleString('en-US', { maximumFractionDigits: 2 })
    : parseFloat(p).toFixed(2)
}

async function fetchQuotes() {
  quotesLoading.value = true
  try {
    const metas = auth.profile?.dashboard_quotes || DEFAULT_SYMBOLS
    const res = await axios.post(`${API_BASE}/api/market/quotes`, metas)
    quotes.value = res.data
    quotesLastUpdated.value = new Date().toLocaleTimeString('zh-TW', { timeZone: 'Asia/Taipei' }) + ' 更新'
  } catch (e) {
    console.error('Quotes fetch failed', e)
  } finally {
    quotesLoading.value = false
  }
}

function openQuoteUrl(symbol) {
  let url = ''
  const upper = symbol.toUpperCase()
  // Pattern for Taiwan stocks/ETFs: 4-6 digits, optional letter (e.g., 00751B), optional suffix
  const isTaiwan = /^\d{4,6}[A-Z]?(\.TW|\.TWO)?$/.test(upper) || upper.endsWith('.TW') || upper.endsWith('.TWO')
  
  if (isTaiwan) {
    let finalSymbol = upper
    if (!upper.includes('.')) {
      finalSymbol = upper + '.TW' 
    }
    url = `https://tw.stock.yahoo.com/quote/${finalSymbol}`
  } else {
    url = `https://finance.yahoo.com/quote/${upper}`
  }
  window.open(url, '_blank')
}

onMounted(async () => {
  await trackingStore.fetchAll()
  await trackingStore.fetchAlertLogs()
  await fetchQuotes()
  // Auto-refresh quotes every 60 seconds
  quotesTimer = setInterval(fetchQuotes, 60_000)
})

onUnmounted(() => {
  if (quotesTimer) clearInterval(quotesTimer)
})
</script>

<style scoped>
.align-center { align-items: center; }

.quotes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.quote-card {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}
.quote-card:hover {
  border-color: var(--accent);
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.3);
  background: rgba(255, 255, 255, 0.05);
}

.quote-symbol {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--accent);
  letter-spacing: 0.02em;
}
.quote-name {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 3px 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.quote-price {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.quote-arrow {
  font-size: 1.2rem;
  line-height: 1;
}

.quote-delta {
  font-size: 0.9rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.text-red { color: #ff5252 !important; }
.text-green { color: #4caf50 !important; }
.justify-between { justify-content: space-between; }
.items-start { align-items: flex-start; }
.items-end { align-items: flex-end; }
.mt-4 { margin-top: 4px; }


/* ─── Quote Modal (duplicate removed — see global <style> block below) ─── */
</style>

<!-- Global (non-scoped) styles for Teleported modal overlay -->
<style>
.quote-modal {
  width: 860px;
  max-width: 96vw;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 24px 60px rgba(0,0,0,0.5);
}

.quote-modal-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  overflow: hidden;
  flex: 1;
  min-height: 0;
  padding: 16px 24px;
}

.cat-tabs { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.cat-tab {
  padding: 6px 18px;
  border-radius: 999px;
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.cat-tab:hover { border-color: var(--accent); color: var(--accent); }
.cat-tab--active { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 700; }

.qm-left { display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.qm-search { margin-bottom: 10px; }
.qm-symbol-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.qm-symbol-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 0.85rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.qm-symbol-row:last-child { border-bottom: none; }
.qm-symbol-row:hover { background: var(--bg-glass); }
.qm-symbol-row--selected { opacity: 0.55; }

.qm-sym-info { display: flex; align-items: baseline; gap: 8px; overflow: hidden; }
.qm-sym-name {
  font-size: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
  color: var(--text-muted);
}
.qm-added-badge { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; }

.qm-right {
  display: flex;
  flex-direction: column;
  border: 1.5px solid var(--accent);
  border-radius: var(--radius-sm);
  overflow: hidden;
  min-height: 0;
}
.qm-right-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-glass);
  flex-shrink: 0;
}
.qm-selected-list { flex: 1; overflow-y: auto; }
.qm-selected-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 0.85rem;
  border-bottom: 1px solid var(--border);
}
.qm-selected-row:last-child { border-bottom: none; }

.quote-modal .modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.quote-modal .modal-footer {
  padding: 14px 24px;
  border-top: 1px solid var(--border);
}
.quote-modal .btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--text-muted);
  font-size: 1rem;
  line-height: 1;
  transition: color 0.15s, background 0.15s;
}
.quote-modal .btn-icon:hover { background: var(--bg-glass); color: var(--text-primary); }
</style>

