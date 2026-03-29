<template>
  <div v-if="item" class="space-y-2">
    <!-- RSI 主卡片：整合目前 RSI + 閾值 + 狀態燈 -->
    <div :class="[
      'rounded-xl p-4 border',
      rsiStatusBg(item.current_rsi, item.rsi_below, item.rsi_above)
    ]">
      <div class="flex items-start justify-between">
        <!-- 左側：RSI 數值 -->
        <div>
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-1">目前 RSI</div>
          <div v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="flex items-baseline gap-1">
            <span :class="['text-3xl font-bold font-mono', getRSIColor(item.current_rsi)]">
              {{ item.current_rsi.toFixed(2) }}
            </span>
            <span class="text-xs font-bold text-zinc-500">%</span>
          </div>
          <div v-else class="text-2xl text-zinc-400 font-bold">--</div>
          <div class="mt-1 text-xs text-zinc-500">
            <span v-if="item.rsi_updated_at">更新: {{ formatTime(item.rsi_updated_at) }}</span>
          </div>
        </div>

        <!-- 右側：狀態燈 + 標籤 -->
        <div class="flex flex-col items-end gap-1">
          <div v-if="item.current_rsi !== null && item.current_rsi !== undefined">
            <span v-if="item.current_rsi < item.rsi_below"
              class="flex items-center gap-1 px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-full">
              <span class="w-2 h-2 rounded-full bg-white inline-block"></span>
              超賣信號
            </span>
            <span v-else-if="item.current_rsi > item.rsi_above"
              class="flex items-center gap-1 px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
              <span class="w-2 h-2 rounded-full bg-white inline-block"></span>
              超買信號
            </span>
            <span v-else
              class="flex items-center gap-1 px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">
              <span class="w-2 h-2 rounded-full bg-white inline-block"></span>
              正常
            </span>
          </div>
          <div class="text-xs text-zinc-500 mt-1">RSI {{ item.rsi_period ?? 14 }}日</div>
        </div>
      </div>

      <!-- 閾值資訊列 -->
      <div class="mt-3 pt-3 border-t border-zinc-200/30 dark:border-zinc-700/30 flex gap-4 text-xs">
        <div class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
          <span class="text-zinc-500">超賣閾值</span>
          <span class="font-bold font-mono text-red-500">{{ item.rsi_below ?? 30 }}</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span>
          <span class="text-zinc-500">超買閾值</span>
          <span class="font-bold font-mono text-green-500">{{ item.rsi_above ?? 70 }}</span>
        </div>
      </div>
    </div>

    <!-- 配置資訊 -->
    <div class="bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-xl p-3">
      <div class="text-sm font-bold text-[var(--text-primary)] mb-2">配置資訊</div>
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 text-sm">
        <div>
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">觸發模式</div>
          <div class="font-bold text-[var(--text-primary)]">{{ triggerModeLabel(item.trigger_mode) }}</div>
        </div>
        <div>
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">RSI 週期</div>
          <div class="font-bold text-[var(--text-primary)] font-mono">{{ item.rsi_period ?? 14 }} 天</div>
        </div>
        <div>
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">當前狀態</div>
          <div v-if="item.is_active" class="inline-block px-2 py-1 bg-green-500/20 text-green-600 dark:text-green-400 text-xs font-bold rounded">
            🟢 啟用
          </div>
          <div v-else class="inline-block px-2 py-1 bg-zinc-500/20 text-zinc-600 dark:text-zinc-400 text-xs font-bold rounded">
            ⚪ 停用
          </div>
        </div>
        <div>
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">通知方式</div>
          <div class="font-bold text-[var(--text-primary)] text-xs">{{ notifyChannelLabel(item.notify_channel) }}</div>
        </div>
      </div>
    </div>

    <!-- RSI 圖表 -->
    <RSIChart :item="item" :tracking-id="item?.id" :dark-mode="true" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RSIChart from './RSIChart.vue'

const props = defineProps({
  item: {
    type: Object,
    default: null
  }
})

function getRSIColor(rsi) {
  if (rsi < 30) return 'text-red-600 dark:text-red-400'
  if (rsi > 70) return 'text-green-600 dark:text-green-400'
  return 'text-blue-600 dark:text-blue-400'
}

// 根據 RSI 狀態決定卡片背景色
function rsiStatusBg(rsi, below, above) {
  if (rsi === null || rsi === undefined) return 'bg-[var(--bg-main)] border-[var(--border-color)]'
  if (rsi < (below ?? 30)) return 'bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30'
  if (rsi > (above ?? 70)) return 'bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30'
  return 'bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20'
}

function triggerModeLabel(mode) {
  const map = {
    price: '💰 價格',
    rsi: '📈 RSI',
    both: '⚡ 複合'
  }
  return map[mode] || mode
}

function notifyChannelLabel(ch) {
  const map = {
    email: '📧 Email',
    line: '💬 LINE',
    both: '📧💬 Email+LINE'
  }
  return map[ch] || ch
}

function formatTime(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diff = (now - date) / 1000
  
  if (diff < 60) return '剛剛'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前`
  return date.toLocaleDateString('zh-TW')
}
</script>

<style scoped>
/* Component styling using Tailwind classes */
</style>
