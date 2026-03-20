<template>
  <div>
    <div class="flex-between mb-24">
      <h2>指數追蹤管理</h2>
      <button class="btn btn-primary" @click="showAddModal = true">＋ 新增追蹤</button>
    </div>

    <!-- Filter tabs -->
    <div class="flex-between mb-16 align-end">
      <div class="category-tabs">
        <button v-for="cat in categories" :key="cat.value"
          :class="['cat-tab', { active: activeCategory === cat.value }]"
          @click="activeCategory = cat.value">
          {{ cat.label }}
        </button>
      </div>
      <div>
        <button class="btn btn-ghost btn-sm" @click="fetchFundamentals" :disabled="loadingFundamentals">
          <span v-if="loadingFundamentals" class="spinner" style="width:14px;height:14px;"></span>
          {{ loadingFundamentals ? '載入中...' : '📊 載入台股基本面數據' }}
        </button>
      </div>
    </div>

    <!-- Fundamentals Dashboard (Optional) -->
    <div v-if="Object.keys(fundamentalsData).length > 0" class="card mb-24" style="border-left: 3px solid var(--purple);">
      <div class="card-header">
        <h3>台股基本面 (TWSE)</h3>
        <button class="btn btn-ghost btn-sm" @click="fundamentalsData = {}">✕</button>
      </div>
      <div class="card-body">
        <div class="grid-4" style="gap:16px;">
          <div v-for="(data, sym) in fundamentalsData" :key="sym" class="stat-card" style="padding:16px;">
            <div class="flex-between mb-8">
              <span class="fw-600">{{ sym }}</span>
              <span class="text-xs text-muted">{{ data.name }}</span>
            </div>
            <div class="grid-3 text-sm">
              <div>
                <div class="text-muted text-xs">本益比</div>
                <div class="fw-600">{{ data.pe_ratio }}</div>
              </div>
              <div>
                <div class="text-muted text-xs">殖利率</div>
                <div class="fw-600 text-green">{{ data.dividend_yield }}%</div>
              </div>
              <div>
                <div class="text-muted text-xs">淨值比</div>
                <div class="fw-600">{{ data.pb_ratio }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <div v-if="trackingStore.loading" class="loading-center"><div class="spinner"></div></div>
      <div v-else-if="!filteredItems.length" style="padding:48px;text-align:center;color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:12px;">📭</div>
        <div>此類別尚無追蹤項目</div>
      </div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>代碼</th><th>名稱</th><th>類別</th><th>目前價格</th>
              <th>觸發方向</th><th>觸發價格</th><th>通知方式</th><th>狀態</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td><span class="fw-600 text-accent">{{ item.symbol }}</span></td>
              <td>{{ item.name }}</td>
              <td><span :class="['badge', categoryBadge(item.category)]">{{ item.category.toUpperCase() }}</span></td>
              <td>
                <span v-if="item.current_price" class="fw-600">{{ item.current_price.toLocaleString() }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <span v-if="item.trigger_direction" :class="item.trigger_direction === 'above' ? 'text-green' : 'text-red'">
                  {{ item.trigger_direction === 'above' ? '↑ 突破' : '↓ 跌破' }}
                </span>
              </td>
              <td>{{ item.trigger_price || '—' }}</td>
              <td>
                <span class="badge badge-blue">{{ channelLabel(item.notify_channel) }}</span>
              </td>
              <td>
                <label class="toggle">
                  <input type="checkbox" :checked="item.is_active" @change="toggleActive(item)" />
                  <span class="toggle-slider"></span>
                </label>
              </td>
              <td>
                <div class="flex gap-8">
                  <button class="btn btn-ghost btn-sm" @click="openEdit(item)">✏️</button>
                  <button class="btn btn-ghost btn-sm" :disabled="testingId === item.id" @click="testAlert(item)" title="测試通知">
                    <span v-if="testingId === item.id" class="spinner" style="width:12px;height:12px;"></span>
                    <span v-else>🔔</span>
                  </button>
                  <button class="btn btn-danger btn-sm" @click="confirmDelete(item)">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Modal -->
    <Transition name="fade">
      <div v-if="showAddModal" class="modal-overlay">
        <div class="modal slide-up-enter-active">
          <div class="modal-header">
            <h3>{{ editItem ? '修改追蹤' : '新增追蹤指數' }}</h3>
            <button class="modal-close" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="modalError" class="alert alert-error">{{ modalError }}</div>

            <div class="form-group">
              <label class="form-label">類別</label>
              <select v-model="form.category" class="form-control" @change="symbolSearch = ''; form.symbol = ''; form.name = ''; currentPrice = null">
                <option value="vix">VIX (波動指數)</option>
                <option value="oil">石油期貨</option>
                <option value="us_etf">美國 ETF</option>
                <option value="tw_etf">台灣 ETF</option>
                <option value="index">大盤指數</option>
                <option value="crypto">加密貨幣</option>
                <option value="exchange">匯率</option>
              </select>
            </div>
            
            <div v-if="currentPrice !== null || fetchingPrice" class="mb-16">
              <span class="text-xs text-muted">目前價格: </span>
              <span v-if="fetchingPrice" class="spinner" style="width:12px;height:12px;display:inline-block;vertical-align:middle;"></span>
              <span v-else class="fw-600 text-accent">{{ currentPrice.toLocaleString() }}</span>
            </div>

            <div class="form-group" style="position:relative;">
              <label class="form-label">代碼 / Symbol</label>
              <div class="input-with-dropdown">
                <input v-model="symbolSearch" type="text" class="form-control" 
                  placeholder="輸入或選擇代碼..." :disabled="!!editItem"
                  @input="onSymbolInput" @focus="showSymbolDropdown = true" />
                
                <div v-if="showSymbolDropdown && filteredSymbols.length" class="dropdown-list">
                  <div v-for="s in filteredSymbols" :key="s.symbol" class="dropdown-item" @click="selectSymbol(s)">
                    <span class="fw-600">{{ s.symbol }}</span>
                    <span class="text-xs text-muted" style="margin-left:8px;">{{ s.name }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">名稱</label>
              <input v-model="form.name" type="text" class="form-control" placeholder="例: 元大台灣50" />
            </div>

            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">觸發方向</label>
                <select v-model="form.trigger_direction" class="form-control" style="height: 38px;">
                  <option value="above">↑ 突破 (漲到)</option>
                  <option value="below">↓ 跌破 (跌到)</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">觸發價格</label>
                <input v-model.number="form.trigger_price" type="number" step="0.01" class="form-control" placeholder="選填" style="height: 38px;" />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">通知方式</label>
              <select v-model="form.notify_channel" class="form-control">
                <option value="email">📧 Email</option>
                <option value="line">💬 LINE</option>
                <option value="both">📧💬 Email + LINE</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">備註 (選填)</label>
              <input v-model="form.notes" type="text" class="form-control" placeholder="備注..." />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="closeModal">取消</button>
            <button class="btn btn-primary" @click="handleSave" :disabled="saving">
              {{ saving ? '儲存中...' : (editItem ? '更新' : '新增') }}
            </button>
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
const showAddModal = ref(false)
const editItem = ref(null)
const saving = ref(false)
const modalError = ref('')
const activeCategory = ref('all')

const fundamentalsData = ref({})
const loadingFundamentals = ref(false)

const categories = [
  { value: 'all', label: '全部' },
  { value: 'vix', label: 'VIX' },
  { value: 'oil', label: '石油' },
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'index', label: '指數' },
  { value: 'exchange', label: '匯率' },
]

const form = reactive({
  symbol: '', name: '', category: 'us_etf',
  trigger_direction: 'below', trigger_price: null,
  notify_channel: 'email', notes: ''
})

const availableSymbols = ref({ tw_etf: [], us_etf: [], index: [] })
const symbolSearch = ref('')
const showSymbolDropdown = ref(false)
const currentPrice = ref(null)
const fetchingPrice = ref(false)

// Close dropdown when clicking outside
if (typeof window !== 'undefined') {
  window.addEventListener('click', (e) => {
    if (!e.target.closest('.input-with-dropdown')) {
      showSymbolDropdown.value = false
    }
  })
}

const allSymbols = computed(() => {
  const list = []
  const cat = form.category
  if (cat === 'tw_etf') {
    availableSymbols.value.tw_etf.forEach(s => list.push({ ...s, type: 'tw_etf' }))
  } else if (cat === 'us_etf') {
    availableSymbols.value.us_etf.forEach(s => list.push({ ...s, type: 'us_etf' }))
  } else if (['index', 'vix', 'oil', 'crypto'].includes(cat)) {
    // Filter index list by category
    const indices = availableSymbols.value.index || []
    indices.filter(s => s.category === cat).forEach(s => list.push({ ...s, type: 'index' }))
  } else {
    // Fallback or other
    availableSymbols.value.us_etf.forEach(s => list.push({ ...s, type: 'us_etf' }))
  }
  return list
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  if (!q) return allSymbols.value.slice(0, 10)
  return allSymbols.value.filter(s => 
    s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  ).slice(0, 15)
})

async function fetchAvailableSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/market/symbols`, { headers: auth.headers })
    availableSymbols.value = res.data
  } catch (e) {
    console.error('Failed to fetch symbols:', e)
  }
}

async function fetchPrice(symbol, category) {
  if (!symbol) return
  fetchingPrice.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/market/quotes?symbols=${symbol}`, { headers: auth.headers })
    if (res.data && res.data[0]) {
      currentPrice.value = res.data[0].price
    }
  } catch (e) {
    console.error('Failed to fetch price:', e)
    currentPrice.value = null
  } finally {
    fetchingPrice.value = false
  }
}

function selectSymbol(s) {
  form.symbol = s.symbol
  form.name = s.name
  symbolSearch.value = s.symbol
  showSymbolDropdown.value = false
  fetchPrice(s.symbol, form.category)
}

function onSymbolInput() {
  form.symbol = symbolSearch.value
  showSymbolDropdown.value = true
  // Try to find if it matches exactly
  const match = allSymbols.value.find(s => s.symbol.toLowerCase() === symbolSearch.value.toLowerCase())
  if (match) {
    form.name = match.name
    fetchPrice(match.symbol, form.category)
  }
}


const filteredItems = computed(() =>
  activeCategory.value === 'all'
    ? trackingStore.items
    : trackingStore.items.filter(i => i.category === activeCategory.value)
)

function categoryBadge(cat) {
  const map = { vix: 'badge-red', oil: 'badge-yellow', us_etf: 'badge-blue', tw_etf: 'badge-purple', index: 'badge-blue', crypto: 'badge-yellow', exchange: 'badge-green' }
  return map[cat] || 'badge-blue'
}

function channelLabel(ch) {
  const map = { email: '📧 Email', line: '💬 LINE', both: '📧💬 兩者' }
  return map[ch] || ch
}

function openEdit(item) {
  editItem.value = item
  symbolSearch.value = item.symbol
  currentPrice.value = item.current_price
  Object.assign(form, {
    symbol: item.symbol, name: item.name, category: item.category,
    trigger_direction: item.trigger_direction || 'below',
    trigger_price: item.trigger_price, notify_channel: item.notify_channel,
    notes: item.notes || ''
  })
  showAddModal.value = true
}

function closeModal() {
  showAddModal.value = false
  editItem.value = null
  modalError.value = ''
  symbolSearch.value = ''
  currentPrice.value = null
  Object.assign(form, { symbol: '', name: '', category: 'us_etf', trigger_direction: 'below', trigger_price: null, notify_channel: 'email', notes: '' })
}

async function handleSave() {
  if (!form.symbol || !form.name) { modalError.value = '請填寫代碼和名稱'; return }
  saving.value = true
  modalError.value = ''
  try {
    const data = { ...form }
    if (!data.trigger_price) delete data.trigger_price
    if (editItem.value) {
      await trackingStore.update(editItem.value.id, data)
    } else {
      await trackingStore.create(data)
    }
    closeModal()
  } catch (e) {
    modalError.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}

async function toggleActive(item) {
  await trackingStore.update(item.id, { is_active: !item.is_active })
}

async function confirmDelete(item) {
  if (confirm(`確定刪除追蹤「${item.name}」?`)) {
    await trackingStore.remove(item.id)
  }
}

const testingId = ref(null)

async function testAlert(item) {
  testingId.value = item.id
  try {
    const res = await axios.post(
      `${API_BASE}/api/tracking/${item.id}/test-alert`,
      {},
      { headers: auth.headers }
    )
    const r = res.data.results
    const parts = []
    if (r.email) parts.push(`Email: ${r.email}`)
    if (r.line) parts.push(`LINE: ${r.line}`)
    alert(`测試通知已發送！\n${parts.join('\n')}`)
  } catch (e) {
    alert('發送失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    testingId.value = null
  }
}

async function fetchFundamentals() {
  const twSymbols = trackingStore.items
    .filter(i => i.category === 'tw_etf' || i.symbol.endsWith('.TW') || i.symbol.endsWith('.TWO'))
    .map(i => i.symbol)
    
  if (twSymbols.length === 0) {
    alert("您的追蹤清單中目前沒有台灣ETF或台股代碼 (需要設定類別為台股ETF或是附帶.TW)。")
    return
  }

  loadingFundamentals.value = true
  try {
    const params = new URLSearchParams()
    twSymbols.forEach(s => params.append('symbols', s))
    const res = await axios.get(`${API_BASE}/api/fundamentals/tw?${params.toString()}`, { headers: auth.headers })
    fundamentalsData.value = res.data
  } catch (e) {
    alert('載入基本面失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    loadingFundamentals.value = false
  }
}

onMounted(async () => {
  trackingStore.fetchAll()
  fetchAvailableSymbols()
})
</script>

<style scoped>
.align-end { align-items: flex-end; }
.category-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.cat-tab {
  padding: 6px 16px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: transparent;
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.cat-tab:hover { color: var(--text-primary); border-color: var(--accent); }
.cat-tab.active { background: var(--accent); color: white; border-color: var(--accent); }

.input-with-dropdown { position: relative; }
.dropdown-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: var(--shadow);
}
.dropdown-item {
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.dropdown-item:last-child { border-bottom: none; }
.dropdown-item:hover { background: var(--bg-glass); }
</style>
