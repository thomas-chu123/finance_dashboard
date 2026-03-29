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
        <div v-else class="min-w-[500px]">
          <div class="grid grid-cols-4 sm:grid-cols-7 p-4 bg-[var(--bg-sidebar)]/50 text-[10px] uppercase font-bold tracking-widest text-zinc-500 border-b border-[var(--border-color)]">
            <div class="col-span-1 sm:col-span-2 flex items-center gap-1">時間 <Clock :size="12" class="hidden sm:inline" /></div>
            <div class="col-span-1">代碼</div>
            <div class="col-span-1 hidden sm:block">觸發價</div>
            <div class="col-span-1">目前價</div>
            <div class="col-span-1">方式</div>
            <div class="col-span-1 hidden sm:block">狀態</div>
          </div>
          <div
            v-for="log in trackingStore.alertLogs"
            :key="log.id"
            class="grid grid-cols-4 sm:grid-cols-7 items-center p-4 border-b border-[var(--border-color)] hover:bg-[var(--bg-main)]/50 transition-colors"
          >
            <div class="col-span-1 sm:col-span-2 text-[10px] sm:text-[11px] text-zinc-500">{{ formatLogTime(log.created_at) }}</div>
            <div class="col-span-1 font-bold text-sm text-[var(--text-primary)]">{{ log.symbol }}</div>
            <div class="col-span-1 font-mono text-sm text-zinc-500 hidden sm:block">{{ log.trigger_price }}</div>
            <div class="col-span-1 font-mono text-sm text-[var(--text-primary)]">{{ log.current_price }}</div>
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

function formatLogTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    month: 'numeric', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
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
