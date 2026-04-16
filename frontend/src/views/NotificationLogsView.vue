<template>
  <div>
    <div class="flex flex-row items-center justify-between gap-4 mb-6 sm:mb-12">
      <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)]">🔔 通知記錄</h2>
      <button
        class="btn btn-outline btn-sm flex items-center gap-2"
        @click="refresh"
        :disabled="loading"
      >
        <RefreshCcw :size="14" :class="loading ? 'animate-spin' : ''" />
        <span class="hidden sm:inline">重新整理</span>
      </button>
    </div>

    <div class="glass-card rounded-2xl overflow-hidden">
      <div class="p-6 border-b border-[var(--border-color)] flex items-center justify-between">
        <div class="flex items-center gap-3">
          <h3 class="font-bold text-lg text-[var(--text-primary)]">所有通知記錄</h3>
          <span class="px-2 py-0.5 bg-brand-500/10 text-brand-600 dark:text-brand-400 text-xs font-bold rounded-full">
            {{ trackingStore.alertLogs.length }} 筆
          </span>
        </div>
      </div>

      <div class="overflow-x-auto">
        <!-- 載入中 -->
        <div v-if="loading" class="p-12 flex justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500"></div>
        </div>

        <!-- 無資料 -->
        <div v-else-if="!trackingStore.alertLogs.length" class="p-4 py-16 text-center text-zinc-500">
          <Bell :size="40" class="mx-auto mb-3 opacity-30" />
          <p>尚無通知記錄</p>
        </div>

        <!-- 資料表格 -->
        <div v-else class="min-w-[600px]">
          <div class="grid grid-cols-5 sm:grid-cols-8 p-4 bg-[var(--bg-sidebar)]/50 text-[10px] uppercase font-bold tracking-widest text-zinc-500 border-b border-[var(--border-color)]">
            <div class="col-span-1 sm:col-span-2 flex items-center gap-1">時間 <Clock :size="12" class="hidden sm:inline" /></div>
            <div class="col-span-1">代碼</div>
            <div class="col-span-1 hidden sm:block">觸發價</div>
            <div class="col-span-1">目前價</div>
            <div class="col-span-1 hidden sm:block">觸發原因</div>
            <div class="col-span-1">方式</div>
            <div class="col-span-1 hidden sm:block">狀態</div>
          </div>
          
          <div v-for="log in trackingStore.alertLogs" :key="log.id">
            <!-- 主表格列 -->
            <div
              class="grid grid-cols-5 sm:grid-cols-8 items-center p-4 border-b border-[var(--border-color)] hover:bg-[var(--bg-main)]/50 transition-colors cursor-pointer"
              @click="toggleExpanded(log.id)"
            >
              <div class="col-span-1 sm:col-span-2 text-[10px] sm:text-[11px] text-zinc-500">{{ formatLogTime(log.created_at) }}</div>
              <div class="col-span-1 font-bold text-sm text-[var(--text-primary)]">{{ log.symbol }}</div>
              <div class="col-span-1 font-mono text-sm text-zinc-500 hidden sm:block">{{ log.trigger_price || '—' }}</div>
              <div class="col-span-1 font-mono text-sm text-[var(--text-primary)]">{{ log.current_price || '—' }}</div>
              
              <!-- 觸發原因徽章 -->
              <div class="col-span-1 hidden sm:block">
                <span :class="getTriggerReasonBadgeClass(log.trigger_reason)">
                  {{ getTriggerReasonLabel(log.trigger_reason) }}
                </span>
              </div>
              
              <div class="col-span-1">
                <span class="px-1.5 py-0.5 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[9px] sm:text-[10px] font-bold rounded uppercase tracking-wider">
                  {{ log.channel }}
                </span>
              </div>
              <div class="col-span-1 hidden sm:block">
                <span :class="['px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider', log.status === 'sent' ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400' : 'bg-rose-500/10 text-rose-600 dark:text-rose-400']">
                  {{ log.status }}
                </span>
              </div>
            </div>
            
            <!-- 詳情展開行 -->
            <div
              v-if="expandedLogId === log.id && (log.rsi_value !== null || log.trigger_details)"
              class="grid grid-cols-1 p-4 bg-zinc-50/50 dark:bg-zinc-900/50 border-b border-[var(--border-color)]"
            >
              <div class="space-y-3">
                <!-- RSI 資訊 -->
                <div v-if="log.rsi_value !== null" class="flex gap-4">
                  <div class="flex-1">
                    <p class="text-xs font-bold text-zinc-600 dark:text-zinc-400 uppercase">RSI 值</p>
                    <p class="text-lg font-mono font-bold text-[var(--text-primary)]">{{ log.rsi_value?.toFixed(2) }}</p>
                  </div>
                  <div class="flex-1" v-if="log.rsi_threshold">
                    <p class="text-xs font-bold text-zinc-600 dark:text-zinc-400 uppercase">觸發閾值</p>
                    <p class="text-lg font-mono font-bold text-orange-500">{{ log.rsi_threshold }}</p>
                  </div>
                  <div v-if="log.trigger_details?.rsi_period" class="flex-1">
                    <p class="text-xs font-bold text-zinc-600 dark:text-zinc-400 uppercase">計算週期</p>
                    <p class="text-lg font-mono font-bold text-[var(--text-primary)]">{{ log.trigger_details.rsi_period }}</p>
                  </div>
                </div>
                
                <!-- 觸發詳情 JSON -->
                <div v-if="log.trigger_details" class="p-3 bg-zinc-200/30 dark:bg-zinc-800/30 rounded border border-zinc-300/50 dark:border-zinc-700/50">
                  <p class="text-xs font-bold text-zinc-600 dark:text-zinc-400 uppercase mb-2">觸發詳情</p>
                  <pre class="text-[11px] text-zinc-700 dark:text-zinc-300 overflow-auto max-h-40">{{ JSON.stringify(log.trigger_details, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTrackingStore } from '../stores/tracking'
import { RefreshCcw, Clock, Bell } from 'lucide-vue-next'

const trackingStore = useTrackingStore()
const loading = ref(false)
const expandedLogId = ref(null)

const triggerReasonLabels = {
  'rsi_oversold': '超賣 (RSI < 30)',
  'rsi_overbought': '超買 (RSI > 70)',
  'price_alert_above': '上方價格',
  'price_alert_below': '下方價格',
  'price_and_rsi': '價格 + RSI',
  'dividend_ex_date': '除權息日',
  'dividend_payment_date': '股息配息',
  'high_dividend_yield': '高股息殖利率'
}

const triggerReasonColors = {
  'rsi_oversold': 'bg-green-500/10 text-green-600 dark:text-green-400',
  'rsi_overbought': 'bg-red-500/10 text-red-600 dark:text-red-400',
  'price_alert_above': 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  'price_alert_below': 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  'price_and_rsi': 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  'dividend_ex_date': 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  'dividend_payment_date': 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  'high_dividend_yield': 'bg-teal-500/10 text-teal-600 dark:text-teal-400'
}

function formatLogTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    month: 'numeric', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function getTriggerReasonLabel(reason) {
  return triggerReasonLabels[reason] || reason || '未知'
}

function getTriggerReasonBadgeClass(reason) {
  const baseClass = 'px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider'
  const colorClass = triggerReasonColors[reason] || 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400'
  return `${baseClass} ${colorClass}`
}

function toggleExpanded(logId) {
  expandedLogId.value = expandedLogId.value === logId ? null : logId
}

async function refresh() {
  loading.value = true
  try {
    await trackingStore.fetchAlertLogs()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
})
</script>
