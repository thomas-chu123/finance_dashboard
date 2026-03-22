<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">投資總覽</h2>
      <div class="flex items-center gap-2">
        <span v-if="quotesLoading" class="text-xs text-zinc-500 animate-pulse">載入中...</span>
        <span v-else class="text-xs text-zinc-500">{{ quotesLastUpdated }}</span>
        <button class="p-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800" @click="fetchQuotes" title="重新整理">
          <RefreshCcw :size="16" />
        </button>
        <button @click="openQuoteModal" class="bg-[var(--input-bg)] text-[var(--text-primary)] border border-[var(--border-color)] text-xs font-bold py-2 px-3 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-1">
          <Settings :size="14" /> 自訂指數
        </button>
      </div>
    </div>

    <!-- Market Overview Ticker -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-2">
      <div v-for="(q, idx) in quotes" :key="q.symbol" 
           @click="handleQuoteClick($event, q.symbol)" 
           class="glass-card p-3.5 rounded-xl flex items-center justify-between cursor-grab active:cursor-grabbing hover:border-brand-500/50 transition-all group"
           draggable="true"
           @dragstart="handleQuoteDragStart($event, idx)"
           @dragend="handleQuoteDragEnd($event)"
           @dragenter="handleQuoteDragEnter($event, idx)"
           @dragover="handleQuoteDragOver($event)"
           @dragleave="handleQuoteDragLeave($event)"
           @drop="handleQuoteDropTarget($event, idx)"
           :class="{'drag-over': quoteDragOverIndex === idx && isQuoteDragging}"
      >
        <div class="flex flex-col pr-3 overflow-hidden">
          <span class="text-xs font-bold text-[var(--text-primary)] group-hover:text-brand-600 dark:group-hover:text-brand-400 truncate">{{ q.name }}</span>
          <span class="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mt-0.5">{{ q.symbol }}</span>
        </div>
        <div class="flex flex-col items-end shrink-0">
          <span v-if="q.price !== null" class="text-sm font-bold font-mono text-[var(--text-primary)]">{{ formatPrice(q.price) }}</span>
          <span v-else class="text-sm font-bold font-mono text-zinc-400">N/A</span>
          
          <span v-if="q.change !== null" :class="[
            'text-[11px] font-bold flex items-center gap-0.5 mt-0.5',
            q.change > 0 ? 'text-rose-600 dark:text-rose-400' : q.change < 0 ? 'text-brand-600 dark:text-brand-400' : 'text-zinc-500'
          ]">
            <TrendingUp v-if="q.change > 0" :size="12" />
            <TrendingDown v-if="q.change < 0" :size="12" />
            <Minus v-if="q.change === 0" :size="12" />
            {{ Math.abs(q.change).toFixed(q.price < 10 ? 4 : 2) }}
          </span>
        </div>
      </div>
      <template v-if="quotesLoading && !quotes.length">
        <div v-for="i in 6" :key="i" class="glass-card p-3.5 rounded-xl animate-pulse h-[60px]"></div>
      </template>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6">
      
      <!-- Main Content Area - Draggable Cards (v-for driven by cardOrder) -->
      <div class="xl:col-span-3 space-y-6">

        <template v-for="cardId in mainContentCards" :key="cardId">

          <!-- Tracking Table Card -->
          <div
            v-if="cardId === 'tracking-table'"
            class="glass-card rounded-2xl overflow-hidden cursor-grab active:cursor-grabbing transition-all"
            draggable="true"
            @dragstart="handleDragStart($event, getCardIndex(cardId))"
            @dragend="handleDragEnd($event)"
            @dragenter="handleDragEnter($event, getCardIndex(cardId))"
            @dragover="handleDragOver($event)"
            @dragleave="handleDragLeave($event)"
            @drop="handleCardDrop($event, getCardIndex(cardId))"
            :class="{ 'drag-over': dragOverIndex === getCardIndex(cardId) && isDragging }"
            data-card-id="tracking-table"
          >
            <div class="p-6 border-b border-[var(--border-color)] flex items-center justify-between">
              <h3 class="font-bold text-lg text-[var(--text-primary)]">📊 追蹤中的指數</h3>
              <router-link to="/tracking" class="text-xs text-brand-600 dark:text-brand-400 font-bold hover:underline flex items-center gap-1">
                查看全部 <ChevronRight :size="14" />
              </router-link>
            </div>
            <div class="overflow-x-auto">
              <div v-if="trackingStore.loading" class="p-12 flex justify-center"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div></div>
              <div v-else-if="!trackingStore.items.length" class="p-4 py-12 text-left text-zinc-500">
                尚未追蹤任何指數 · <router-link to="/tracking" class="text-brand-500 hover:underline">立即新增</router-link>
              </div>
              <div v-else class="min-w-[600px]">
                <div class="grid grid-cols-6 p-4 bg-[var(--bg-sidebar)]/50 text-[10px] uppercase font-bold tracking-widest text-zinc-500 border-b border-[var(--border-color)]">
                  <div class="col-span-1">代碼</div>
                  <div class="col-span-2">名稱 / 類別</div>
                  <div class="col-span-1">目前價格</div>
                  <div class="col-span-1">觸發門檻</div>
                  <div class="col-span-1">狀態</div>
                </div>
                <div v-for="item in trackingStore.items.slice(0, 6)" :key="item.id" class="grid grid-cols-6 items-center p-4 border-b border-[var(--border-color)] hover:bg-[var(--bg-main)]/50 transition-colors">
                  <div class="col-span-1 font-bold text-sm tracking-tight text-brand-600 dark:text-brand-400">{{ item.symbol }}</div>
                  <div class="col-span-2 flex flex-col">
                    <span class="text-sm text-[var(--text-primary)] truncate pr-2">{{ item.name }}</span>
                    <span class="text-[10px] text-zinc-500 uppercase mt-0.5">{{ item.category }}</span>
                  </div>
                  <div class="col-span-1 font-mono text-sm text-[var(--text-primary)]">{{ item.current_price ? item.current_price.toLocaleString() : '—' }}</div>
                  <div class="col-span-1 font-mono text-sm text-[var(--text-primary)]">
                    <span v-if="item.trigger_price">
                      <TrendingUp v-if="item.trigger_direction === 'above'" :size="12" class="inline text-rose-500 mb-0.5" />
                      <TrendingDown v-else :size="12" class="inline text-brand-500 mb-0.5" />
                      {{ item.trigger_price }}
                    </span>
                    <span v-else class="text-zinc-500">—</span>
                  </div>
                  <div class="col-span-1">
                    <span :class="['px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider', item.is_active ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400']">
                      {{ item.is_active ? '啟用' : '停用' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Alert Logs Card -->
          <div
            v-if="cardId === 'alert-logs'"
            class="glass-card rounded-2xl overflow-hidden cursor-grab active:cursor-grabbing transition-all"
            draggable="true"
            @dragstart="handleDragStart($event, getCardIndex(cardId))"
            @dragend="handleDragEnd($event)"
            @dragenter="handleDragEnter($event, getCardIndex(cardId))"
            @dragover="handleDragOver($event)"
            @dragleave="handleDragLeave($event)"
            @drop="handleCardDrop($event, getCardIndex(cardId))"
            :class="{ 'drag-over': dragOverIndex === getCardIndex(cardId) && isDragging }"
            data-card-id="alert-logs"
          >
            <div class="p-6 border-b border-[var(--border-color)] flex items-center justify-between">
              <h3 class="font-bold text-lg text-[var(--text-primary)]">🔔 最近通知記錄</h3>
            </div>
            <div class="overflow-x-auto">
              <div v-if="!trackingStore.alertLogs.length" class="p-4 py-12 text-left text-zinc-500">尚無通知記錄</div>
              <div v-else class="min-w-[600px]">
                <div class="grid grid-cols-7 p-4 bg-[var(--bg-sidebar)]/50 text-[10px] uppercase font-bold tracking-widest text-zinc-500 border-b border-[var(--border-color)]">
                  <div class="col-span-2 flex items-center gap-1">時間 <Clock :size="12" /></div>
                  <div class="col-span-1">代碼</div>
                  <div class="col-span-1">觸發價</div>
                  <div class="col-span-1">實際價</div>
                  <div class="col-span-1">方式</div>
                  <div class="col-span-1">狀態</div>
                </div>
                <div v-for="log in trackingStore.alertLogs.slice(0, 8)" :key="log.id" class="grid grid-cols-7 items-center p-4 border-b border-[var(--border-color)] hover:bg-[var(--bg-main)]/50 transition-colors">
                  <div class="col-span-2 text-[11px] text-zinc-500">{{ formatDate(log.created_at) }}</div>
                  <div class="col-span-1 font-bold text-sm text-[var(--text-primary)]">{{ log.symbol }}</div>
                  <div class="col-span-1 font-mono text-sm text-zinc-500">{{ log.trigger_price }}</div>
                  <div class="col-span-1 font-mono text-sm text-[var(--text-primary)]">{{ log.current_price }}</div>
                  <div class="col-span-1">
                    <span class="px-2 py-0.5 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded uppercase tracking-wider">{{ log.channel }}</span>
                  </div>
                  <div class="col-span-1">
                    <span :class="['px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider', log.status === 'sent' ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400']">
                      {{ log.status }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </template>
      </div>

      <!-- Sidebar Widgets - Draggable -->
      <div class="space-y-6">
        
        <!-- System Status Card (Draggable) -->
        <div 
          v-if="dashboardStore.cardOrder.includes('status-sidebar')"
          class="glass-card rounded-2xl p-6 bg-gradient-to-br from-brand-500/5 to-transparent border-brand-500/20 cursor-grab active:cursor-grabbing transition-all"
          draggable="true"
          @dragstart="handleDragStart($event, getCardIndex('status-sidebar'))"
          @dragend="handleDragEnd($event)"
          @dragenter="handleDragEnter($event, getCardIndex('status-sidebar'))"
          @dragover="handleDragOver($event)"
          @dragleave="handleDragLeave($event)"
          @drop="handleCardDrop($event, getCardIndex('status-sidebar'))"
          :class="{ 'opacity-50': isDragging && dragOverIndex === getCardIndex('status-sidebar') }"
          data-card-id="status-sidebar"
        >
          <h3 class="text-sm font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-widest mb-6 flex items-center gap-2">
            <Activity :size="16" /> 系統運作狀態
          </h3>
          
          <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="flex flex-col gap-1 p-4 bg-[var(--input-bg)] rounded-xl border border-[var(--border-color)]">
              <span class="text-xs text-zinc-500 font-bold">追蹤數量</span>
              <span class="text-2xl font-bold font-mono text-[var(--text-primary)]">{{ trackingStore.items.length }}</span>
              <span class="text-[10px] text-brand-500 font-bold">{{ activeCount }} 啟用中</span>
            </div>
            <div class="flex flex-col gap-1 p-4 bg-[var(--input-bg)] rounded-xl border border-[var(--border-color)]">
              <span class="text-xs text-zinc-500 font-bold">通知記錄</span>
              <span class="text-2xl font-bold font-mono text-[var(--text-primary)]">{{ trackingStore.alertLogs.length }}</span>
              <span class="text-[10px] text-zinc-400 font-bold">近 50 筆</span>
            </div>
          </div>

          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-[var(--input-bg)] rounded-lg border border-[var(--border-color)]">
              <div class="flex items-center gap-2">
                <Mail :size="16" class="text-zinc-400" />
                <span class="text-sm font-bold text-[var(--text-primary)]">Email 通知</span>
              </div>
              <span :class="['text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded', auth.profile?.notify_email ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400' : 'bg-zinc-200 dark:bg-zinc-800 text-zinc-500']">
                {{ auth.profile?.notify_email ? '已啟用' : '停用' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-[var(--input-bg)] rounded-lg border border-[var(--border-color)]">
              <div class="flex items-center gap-2">
                <MessageCircle :size="16" class="text-zinc-400" />
                <span class="text-sm font-bold text-[var(--text-primary)]">LINE 通知</span>
              </div>
              <span :class="['text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded', auth.profile?.notify_line ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400' : 'bg-zinc-200 dark:bg-zinc-800 text-zinc-500']">
                {{ auth.profile?.notify_line ? '已啟用' : '停用' }}
              </span>
            </div>
          </div>
          
          <router-link to="/line" class="block w-full mt-6 py-3 border border-[var(--border-color)] rounded-xl text-xs font-bold text-center text-zinc-500 dark:text-zinc-400 hover:bg-[var(--input-bg)] transition-colors">
            前往設定通知
          </router-link>
        </div>

      </div>
    </div>

    <!-- Modal: 自訂追蹤指數 -->
    <Teleport to="body">
    <div v-if="showQuoteModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showQuoteModal = false">
      <div class="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-2xl shadow-2xl w-[860px] max-w-[96vw] max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 px-6 border-b border-[var(--border-color)] shrink-0">
          <h3 class="font-bold text-lg text-[var(--text-primary)] flex items-center gap-2"><Settings :size="18" /> 自訂追蹤指數</h3>
          <button class="p-1 rounded-md text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-[var(--text-primary)] transition-colors" @click="showQuoteModal = false">
            <X :size="18" />
          </button>
        </div>

        <!-- Body: two columns -->
        <div class="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-3 gap-6 p-6 min-h-0">

          <!-- LEFT: Browse & Add -->
          <div class="md:col-span-2 flex flex-col min-h-0">
            <!-- Category Tabs -->
            <div class="flex gap-2 mb-4 flex-wrap">
              <button
                v-for="tab in categoryTabs" :key="tab.key"
                :class="['px-4 py-1.5 rounded-full border text-sm font-bold transition-colors', activeTab === tab.key ? 'bg-brand-500 border-brand-500 text-white' : 'border-[var(--border-color)] text-zinc-500 hover:border-brand-500 hover:text-brand-500']"
                @click="activeTab = tab.key; quoteSearch = ''"
              >{{ tab.label }}</button>
            </div>

            <!-- Search -->
            <div class="mb-3 relative">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" :size="14" />
              <input
                type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" v-model="quoteSearch"
                :placeholder="'搜尋 ' + currentTabLabel + ' 代碼或名稱...'"
              />
            </div>

            <!-- Symbol list -->
            <div v-if="symbolsLoading" class="flex-1 flex items-center justify-center min-h-[200px] border border-[var(--border-color)] rounded-xl">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div>
            </div>
            <div v-else class="flex-1 overflow-y-auto border border-[var(--border-color)] rounded-xl custom-scrollbar bg-[var(--bg-sidebar)]/50">
              <div
                v-for="item in filteredCurrentTab" :key="item.symbol"
                class="flex justify-between items-center p-3 text-sm border-b border-[var(--border-color)] hover:bg-[var(--bg-main)]/50 transition-colors"
                :class="{ 'opacity-50': isSelected(item.symbol) }"
              >
                <div class="flex items-baseline gap-2 overflow-hidden pr-2">
                  <span class="font-bold text-brand-600 dark:text-brand-400 shrink-0">{{ item.symbol }}</span>
                  <span class="text-xs text-zinc-500 truncate max-w-[200px]">{{ item.name }}</span>
                </div>
                <button
                  v-if="!isSelected(item.symbol)"
                  class="p-1 rounded text-brand-600 hover:bg-brand-500/10 font-bold shrink-0"
                  @click="addQuote(item)"
                ><Plus :size="16" /></button>
                <span v-else class="text-xs text-zinc-500 font-bold shrink-0 flex items-center gap-1"><Check :size="16" />已加入</span>
              </div>
              <div v-if="!filteredCurrentTab.length" class="text-center text-zinc-500 p-8 text-sm">無符合結果</div>
            </div>
          </div>

          <!-- RIGHT: Selected list -->
          <div class="md:col-span-1 flex flex-col border border-brand-500/30 rounded-xl overflow-hidden min-h-0">
            <div class="flex items-center justify-between p-3 border-b border-[var(--border-color)] bg-brand-500/5 shrink-0">
              <span class="font-bold text-sm text-[var(--text-primary)]">已追蹤指數</span>
              <span class="bg-brand-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">{{ selectedQuotes.length }}</span>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar bg-[var(--bg-sidebar)]/50">
              <div
                v-for="(item, idx) in selectedQuotes" :key="idx"
                class="flex justify-between items-center p-3 text-sm border-b border-[var(--border-color)] group"
              >
                <div class="flex flex-col overflow-hidden pr-2">
                  <span class="font-bold text-[var(--text-primary)]">{{ item.symbol }}</span>
                  <span class="text-[10px] text-zinc-500 truncate">{{ item.name }}</span>
                </div>
                <button class="text-rose-400 hover:text-rose-600 p-1 opacity-50 group-hover:opacity-100 transition-opacity" @click="removeQuote(idx)" title="移除">
                  <X :size="14" />
                </button>
              </div>
              <div v-if="!selectedQuotes.length" class="text-center text-zinc-500 p-8 text-xs">尚未加入任何標的</div>
            </div>
            <div class="text-[10px] text-zinc-400 p-2 text-center bg-[var(--bg-main)]/30 border-t border-[var(--border-color)]">
              💡 提示：您可以在首頁直接拖曳卡片來變更順序
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 px-6 border-t border-[var(--border-color)] flex items-center justify-end gap-3 bg-[var(--bg-header)] shrink-0">
          <button class="px-4 py-2 text-sm font-bold text-zinc-500 hover:text-[var(--text-primary)] transition-colors" @click="showQuoteModal = false">取消</button>
          <button class="px-6 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-brand-500/20 flex items-center gap-2" @click="saveQuotes" :disabled="savingQuotes">
            <div v-if="savingQuotes" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
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
import { useDashboardStore } from '../stores/dashboard'
import { useDragDrop } from '../composables/useDragDrop'
import preferencesAPI from '../api/preferences'
import {
  TrendingUp, TrendingDown, Minus, RefreshCcw, Settings, ChevronRight, X, Clock, Activity, Mail, MessageCircle, Search, Plus, Check
} from 'lucide-vue-next'

const auth = useAuthStore()
const trackingStore = useTrackingStore()
const dashboardStore = useDashboardStore()

// Main dashboard cards drag & drop
const { handleDragStart, handleDragEnd, handleDragEnter, handleDragOver, handleDragLeave, handleDrop, dragOverIndex, isDragging } = useDragDrop()

// Quote cards drag & drop
const {
  handleDragStart: handleQuoteDragStart,
  handleDragEnd: _handleQuoteDragEnd,
  handleDragEnter: handleQuoteDragEnter,
  handleDragOver: handleQuoteDragOver,
  handleDragLeave: handleQuoteDragLeave,
  handleDrop: handleQuoteLocalDrop,
  dragOverIndex: quoteDragOverIndex,
  isDragging: isQuoteDragging
} = useDragDrop()

// Prevent click navigation immediately after a drag
let lastQuoteDragEndTime = 0
function handleQuoteDragEnd(event) {
  _handleQuoteDragEnd(event)
  lastQuoteDragEndTime = Date.now()
}

function handleQuoteClick(event, symbol) {
  // If drag ended less than 200ms ago, it was a drag, not a click
  if (Date.now() - lastQuoteDragEndTime < 200) {
    event.preventDefault()
    return
  }
  openQuoteUrl(symbol)
}

async function handleQuoteDropTarget(event, toIndex) {
  const result = handleQuoteLocalDrop(event, toIndex)
  if (result) {
    const { fromIndex, toIndex: finalToIndex } = result
    
    // Update local UI immediately
    const item = quotes.value.splice(fromIndex, 1)[0]
    quotes.value.splice(finalToIndex, 0, item)
    
    // Sync to backend profile
    if (auth.token) {
      const profileQuotes = [...(auth.profile?.dashboard_quotes || DEFAULT_SYMBOLS)]
      const pItem = profileQuotes.splice(fromIndex, 1)[0]
      profileQuotes.splice(finalToIndex, 0, pItem)
      
      try {
        await auth.updateProfile({ dashboard_quotes: profileQuotes })
      } catch (e) {
        console.error('Failed to save quote order:', e)
      }
    }
  }
}

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
  // 加載卡片順序
  dashboardStore.loadFromLocalStorage()
  if (auth.token) {
    try {
      await dashboardStore.loadCardOrder(auth.token)
    } catch (e) {
      console.warn('Failed to load card order from server, using local storage')
    }
  }
  
  await trackingStore.fetchAll()
  await trackingStore.fetchAlertLogs()
  await fetchQuotes()
  quotesTimer = setInterval(fetchQuotes, 60_000)
})

onUnmounted(() => {
  if (quotesTimer) clearInterval(quotesTimer)
})

/**
 * 處理卡片拖放完成
 * @param {Event} event - 拖放事件
 * @param {number} toIndex - 放置目標索引
 */
async function handleCardDrop(event, toIndex) {
  const result = handleDrop(event, toIndex)
  if (result) {
    dashboardStore.moveCard(result.fromIndex, result.toIndex)
    
    // 保存到後端
    if (auth.token) {
      try {
        await dashboardStore.saveCardOrder(auth.token)
      } catch (e) {
        console.error('Failed to save card order:', e)
      }
    }
  }
}

/**
 * 主要內容區的卡片 ID 清單，依 cardOrder 排序（排除 sidebar）
 * Bug 1 修正：透過 computed 讓 v-for 能響應 cardOrder 的變化
 */
const MAIN_CARD_IDS = ['tracking-table', 'alert-logs']
const mainContentCards = computed(() =>
  dashboardStore.cardOrder.filter(id => MAIN_CARD_IDS.includes(id))
)

/**
 * 取得卡片在 cardOrder 中的真實索引（供 moveCard 使用）
 */
function getCardIndex(cardId) {
  return dashboardStore.cardOrder.indexOf(cardId)
}
</script>

<style scoped>
/* 拖放視覺反饋樣式 */
.drag-over {
  border: 2px solid rgb(var(--color-brand-500)) !important;
  background-color: rgb(59 130 246 / 0.05) !important;
}

/* 拖動中的卡片透明度 */
.dragging {
  opacity: 0.5;
}
</style>
