<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">指數追蹤管理</h2>
      <button class="flex items-center justify-center px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white dark:text-black text-sm font-bold rounded-xl transition-all shadow-lg shadow-emerald-500/20" @click="showAddModal = true">
        <Plus class="w-4 h-4 mr-2" />
        新增追蹤
      </button>
    </div>

    <!-- Filter tabs -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex flex-wrap gap-2">
        <button v-for="cat in categories" :key="cat.value"
          :class="['px-4 py-1.5 rounded-full text-sm font-bold transition-colors border', activeCategory === cat.value ? 'bg-emerald-500 border-emerald-500 text-white dark:text-black shadow-sm' : 'bg-transparent border-[var(--border-color)] text-zinc-500 hover:border-emerald-500 hover:text-emerald-500']"
          @click="activeCategory = cat.value">
          {{ cat.label }}
        </button>
      </div>
      <div>
        <button class="flex items-center px-3 py-1.5 text-sm font-bold text-zinc-500 hover:text-[var(--text-primary)] transition-colors" @click="fetchFundamentals" :disabled="loadingFundamentals">
          <Loader2 v-if="loadingFundamentals" class="w-4 h-4 mr-2 animate-spin text-emerald-500" />
          <BarChart2 v-else class="w-4 h-4 mr-2" />
          {{ loadingFundamentals ? '載入中...' : '載入台股基本面數據' }}
        </button>
      </div>
    </div>

    <!-- Fundamentals Dashboard (Optional) -->
    <div v-if="Object.keys(fundamentalsData).length > 0" class="glass-card border-l-4 border-emerald-500">
      <div class="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-bold text-[var(--text-primary)] flex items-center">
          <TrendingUp class="w-5 h-5 mr-2 text-emerald-500" />
          台股基本面 (TWSE)
        </h3>
        <button class="p-1 text-zinc-500 hover:text-zinc-900 dark:hover:text-white rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors" @click="fundamentalsData = {}">
          <X class="w-5 h-5" />
        </button>
      </div>
      <div class="p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="(data, sym) in fundamentalsData" :key="sym" class="bg-white dark:bg-zinc-900/50 rounded-xl p-4 border border-[var(--border-color)]/50 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <span class="font-bold text-[var(--text-primary)] text-sm tracking-tight">{{ sym }}</span>
            <span class="text-xs text-zinc-500 truncate max-w-[100px]">{{ data.name }}</span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-sm">
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">本益比</div>
              <div class="font-bold font-mono text-[var(--text-primary)]">{{ data.pe_ratio }}</div>
            </div>
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">殖利率</div>
              <div class="font-bold font-mono text-emerald-600 dark:text-emerald-400">{{ data.dividend_yield }}%</div>
            </div>
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">淨值比</div>
              <div class="font-bold font-mono text-[var(--text-primary)]">{{ data.pb_ratio }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card rounded-2xl overflow-hidden">
      <div v-if="trackingStore.loading" class="flex justify-center items-center py-20">
        <Loader2 class="w-8 h-8 text-emerald-500 animate-spin" />
      </div>
      <div v-else-if="!filteredItems.length" class="py-20 text-center text-zinc-500">
        <div class="text-4xl mb-4 opacity-50">📭</div>
        <div class="text-lg">此類別尚無追蹤項目</div>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="text-[10px] text-zinc-500 uppercase font-bold tracking-widest bg-zinc-50 dark:bg-zinc-900/30 border-b border-[var(--border-color)]">
            <tr class="text-xs text-zinc-500 dark:text-zinc-400 border-b border-[var(--border-color)]">
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">代碼</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">名稱</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">類別</th>
              <th class="px-4 py-4 text-right font-medium whitespace-nowrap">目前價格</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">觸發規則</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">通知方式</th>
              <th class="px-4 py-4 text-center font-medium whitespace-nowrap">狀態</th>
              <th class="px-4 py-4 text-center font-medium whitespace-nowrap">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border-color)]">
            <tr v-for="item in filteredItems" :key="item.id" class="hover:bg-zinc-100 dark:hover:bg-zinc-800/30 transition-colors">
              <td class="px-4 py-4">
                <span class="font-bold text-sm tracking-tight text-emerald-600 dark:text-emerald-400">{{ item.symbol }}</span>
              </td>
              <td class="px-4 py-4 text-sm text-[var(--text-primary)] font-medium">{{ item.name }}</td>
              <td class="px-4 py-4 whitespace-nowrap">
                <span :class="['px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider whitespace-nowrap', categoryBadgeInfo(item.category).class]">
                  {{ categoryBadgeInfo(item.category).label }}
                </span>
              </td>
              <td class="px-4 py-4 text-right">
                <span v-if="item.current_price" class="font-mono text-sm font-bold text-[var(--text-primary)]">{{ item.current_price.toLocaleString() }}</span>
                <span v-else class="text-zinc-500">—</span>
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center space-x-2">
                  <span v-if="item.trigger_direction" :class="['flex items-center text-[11px] font-bold tracking-wider uppercase', item.trigger_direction === 'above' ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400']">
                    <TrendingUp v-if="item.trigger_direction === 'above'" class="w-3 h-3 mr-1" />
                    <TrendingDown v-else class="w-3 h-3 mr-1" />
                    {{ item.trigger_direction === 'above' ? '突破' : '跌破' }}
                  </span>
                  <span class="font-mono text-sm font-bold text-[var(--text-primary)]">{{ item.trigger_price || '—' }}</span>
                </div>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider whitespace-nowrap bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-[var(--border-color)]">
                  <Mail v-if="item.notify_channel === 'email' || item.notify_channel === 'both'" class="w-3 h-3 mr-1" />
                  <MessageCircle v-if="item.notify_channel === 'line' || item.notify_channel === 'both'" class="w-3 h-3 mr-1" :class="{'ml-1': item.notify_channel==='both'}" />
                  {{ channelLabel(item.notify_channel) }}
                </span>
              </td>
              <td class="px-4 py-4 text-center">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" :checked="item.is_active" @change="toggleActive(item)" class="sr-only peer">
                  <div class="w-9 h-5 bg-zinc-300 peer-focus:outline-none rounded-full peer dark:bg-zinc-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-zinc-600 peer-checked:bg-emerald-500"></div>
                </label>
              </td>
              <td class="px-4 py-4 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button class="p-1.5 text-zinc-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors rounded-md hover:bg-emerald-50 dark:hover:bg-zinc-800" @click="openEdit(item)" title="編輯">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button class="p-1.5 text-zinc-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors rounded-md hover:bg-amber-50 dark:hover:bg-zinc-800" :disabled="testingId === item.id" @click="testAlert(item)" title="测試通知">
                    <Loader2 v-if="testingId === item.id" class="w-4 h-4 animate-spin" />
                    <Bell v-else class="w-4 h-4" />
                  </button>
                  <button class="p-1.5 text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors rounded-md hover:bg-rose-50 dark:hover:bg-zinc-800" @click="confirmDelete(item)" title="刪除">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
        <div class="fixed inset-0 bg-zinc-900/60 backdrop-blur-sm transition-opacity" @click="closeModal"></div>
        
        <div class="relative bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden ring-2 ring-emerald-500/50 dark:ring-emerald-500/30">
          <div class="px-6 py-4 border-b border-[var(--border-color)] flex items-center justify-between bg-zinc-50/50 dark:bg-zinc-900/50">
            <h3 class="text-lg font-bold tracking-tight text-[var(--text-primary)] flex items-center">
              <PlusCircle v-if="!editItem" class="w-5 h-5 mr-2 text-emerald-500" />
              <Edit2 v-else class="w-5 h-5 mr-2 text-emerald-500" />
              {{ editItem ? '修改追蹤' : '新增追蹤指數' }}
            </h3>
            <button class="text-zinc-400 hover:text-zinc-500 dark:hover:text-zinc-300 transition-colors" @click="closeModal">
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="p-6 space-y-4 max-h-[calc(100vh-10rem)] overflow-y-auto">
            <div v-if="modalError" class="p-3 text-sm text-rose-600 bg-rose-50 dark:bg-rose-500/10 dark:text-rose-400 rounded-lg flex items-start">
              <AlertCircle class="w-4 h-4 mr-2 mt-0.5 shrink-0" />
              {{ modalError }}
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">類別</label>
              <select v-model="form.category" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3" @change="symbolSearch = ''; form.symbol = ''; form.name = ''; currentPrice = null">
                <option value="vix">VIX (波動指數)</option>
                <option value="oil">石油期貨</option>
                <option value="us_etf">美國 ETF</option>
                <option value="tw_etf">台灣 ETF</option>
                <option value="index">大盤指數</option>
                <option value="crypto">加密貨幣</option>
                <option value="exchange">匯率</option>
              </select>
            </div>
            
            <div v-if="currentPrice !== null || fetchingPrice" class="flex items-center p-3 bg-zinc-50 dark:bg-zinc-900/50 border border-[var(--border-color)] rounded-lg">
              <span class="text-sm font-medium text-zinc-500 dark:text-zinc-400 mr-2">目前價格: </span>
              <Loader2 v-if="fetchingPrice" class="w-4 h-4 text-emerald-500 animate-spin" />
              <span v-else class="text-lg font-bold tracking-tight text-[var(--text-primary)]">{{ currentPrice.toLocaleString() }}</span>
            </div>

            <div class="relative">
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">代碼 / Symbol</label>
              <div class="relative input-with-dropdown">
                <input v-model="symbolSearch" type="text" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3" 
                  placeholder="輸入或選擇代碼..." :disabled="!!editItem"
                  @input="onSymbolInput" @focus="showSymbolDropdown = true" />
                
                <div v-if="showSymbolDropdown && filteredSymbols.length" class="absolute z-10 w-full mt-1 bg-white dark:bg-zinc-900 border border-[var(--border-color)] rounded-lg shadow-lg max-h-60 overflow-auto">
                  <div v-for="s in filteredSymbols" :key="s.symbol" class="px-4 py-2 hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer border-b border-[var(--border-color)] last:border-0" @click="selectSymbol(s)">
                    <div class="font-bold text-[var(--text-primary)]">{{ s.symbol }}</div>
                    <div class="text-xs font-medium text-zinc-500 dark:text-zinc-400 truncate">{{ s.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">名稱</label>
              <input v-model="form.name" type="text" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3" placeholder="例: 元大台灣50" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">觸發方向</label>
                <select v-model="form.trigger_direction" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3">
                  <option value="above" class="text-rose-600 font-bold">↑ 突破 (漲到)</option>
                  <option value="below" class="text-emerald-600 font-bold">↓ 跌破 (跌到)</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">觸發價格</label>
                <input v-model.number="form.trigger_price" type="number" step="0.01" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3" placeholder="選填" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">通知方式</label>
              <select v-model="form.notify_channel" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3">
                <option value="email">📧 Email</option>
                <option value="line">💬 LINE</option>
                <option value="both">📧💬 Email + LINE</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">備註 (選填)</label>
              <input v-model="form.notes" type="text" class="w-full h-10 bg-white dark:bg-zinc-900 border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block px-3" placeholder="備注..." />
            </div>
          </div>
          
          <div class="px-6 py-4 border-t border-[var(--border-color)] bg-zinc-50/50 dark:bg-zinc-900/50 flex justify-end space-x-3">
            <button class="px-4 py-2 text-sm font-bold text-zinc-600 dark:text-zinc-400 hover:text-[var(--text-primary)] hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors border border-transparent" @click="closeModal">取消</button>
            <button class="flex items-center justify-center px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white dark:text-black text-sm font-bold rounded-lg transition-all shadow-lg shadow-emerald-500/20" @click="handleSave" :disabled="saving">
              <Loader2 v-if="saving" class="w-4 h-4 mr-2 animate-spin" />
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
import {
  Plus, Loader2, BarChart2, TrendingUp, X, ArrowUpRight, ArrowDownRight,
  Mail, MessageCircle, Edit2, Bell, Trash2, PlusCircle, AlertCircle
} from 'lucide-vue-next'
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
  } else if (['index', 'vix', 'oil', 'crypto', 'exchange'].includes(cat)) {
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

function categoryBadgeInfo(cat) {
  const map = {
    vix: { label: 'VIX', class: 'bg-rose-500 text-white border border-rose-600' },
    oil: { label: '石油', class: 'bg-amber-500 text-white border border-amber-600' },
    us_etf: { label: '美股', class: 'bg-blue-500 text-white border border-blue-600' },
    tw_etf: { label: '台股', class: 'bg-purple-500 text-white border border-purple-600' },
    index: { label: '大盤', class: 'bg-violet-500 text-white border border-violet-600' },
    crypto: { label: '加密', class: 'bg-emerald-500 text-white border border-emerald-600' },
    exchange: { label: '匯率', class: 'bg-cyan-500 text-white border border-cyan-600' }
  }
  return map[cat] || { label: cat.toUpperCase(), class: 'bg-zinc-500 text-white border border-zinc-600' }
}

function channelLabel(ch) {
  const map = { email: 'Email', line: 'LINE', both: 'Email + LINE' }
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
/* Removed old scoped styling; using global Tailwind CSS classes now */
</style>
