<template>
  <div v-if="item" class="space-y-4">
    <!-- RSI Value Card -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <!-- Current RSI -->
      <div class="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-bold text-zinc-500 uppercase tracking-widest">目前 RSI</span>
          <span class="text-2xl">📈</span>
        </div>
        <div v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="flex items-baseline gap-2">
          <div :class="[
            'text-4xl font-bold font-mono',
            getRSIColor(item.current_rsi)
          ]">
            {{ item.current_rsi.toFixed(2) }}
          </div>
          <div class="text-xs font-bold text-zinc-500 uppercase">%</div>
        </div>
        <div v-else class="text-2xl text-zinc-400 font-bold">
          --
        </div>
        <div class="mt-3 text-xs text-zinc-500">
          <span v-if="item.rsi_updated_at" class="block">
            更新: {{ formatTime(item.rsi_updated_at) }}
          </span>
          <span v-else class="block text-zinc-400">尚未計算</span>
        </div>
      </div>

      <!-- Oversold Zone -->
      <div class="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-bold text-zinc-500 uppercase tracking-widest">超賣區</span>
          <span class="text-2xl">🔴</span>
        </div>
        <div class="flex flex-col gap-2">
          <div>
            <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">閾值</div>
            <div class="text-2xl font-bold text-red-600 dark:text-red-400">
              {{ item.rsi_below ?? '--' }}
            </div>
          </div>
          <div v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="mt-2 pt-2 border-t border-red-500/20">
            <span v-if="item.current_rsi < item.rsi_below" class="inline-block px-2 py-1 bg-red-500 text-white text-xs font-bold rounded">
              ⚠️ 超賣信號
            </span>
            <span v-else class="inline-block px-2 py-1 bg-zinc-500/30 text-zinc-600 dark:text-zinc-400 text-xs font-bold rounded">
              ✅ 正常
            </span>
          </div>
        </div>
      </div>

      <!-- Overbought Zone -->
      <div class="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-bold text-zinc-500 uppercase tracking-widest">超買區</span>
          <span class="text-2xl">🟢</span>
        </div>
        <div class="flex flex-col gap-2">
          <div>
            <div class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1">閾值</div>
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ item.rsi_above ?? '--' }}
            </div>
          </div>
          <div v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="mt-2 pt-2 border-t border-green-500/20">
            <span v-if="item.current_rsi > item.rsi_above" class="inline-block px-2 py-1 bg-green-500 text-white text-xs font-bold rounded">
              ⚠️ 超買信號
            </span>
            <span v-else class="inline-block px-2 py-1 bg-zinc-500/30 text-zinc-600 dark:text-zinc-400 text-xs font-bold rounded">
              ✅ 正常
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- RSI Gauge/Progress Bar -->
    <div class="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-xl p-4">
      <div class="text-sm font-bold text-[var(--text-primary)] mb-3">RSI 指數分佈</div>
      <div class="space-y-2">
        <!-- Oversold Zone (0-30) -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="font-bold text-red-600">超賣</span>
            <span class="text-zinc-500">0</span>
            <span class="text-zinc-500">{{ item.rsi_below ?? 30 }}</span>
          </div>
          <div class="h-2 bg-[var(--border-color)] rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-red-600 to-orange-500" :style="{ width: item.rsi_below ? `${item.rsi_below}%` : '30%' }"></div>
          </div>
        </div>

        <!-- Normal Zone (30-70) -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="font-bold text-blue-600">正常</span>
            <span class="text-zinc-500">{{ item.rsi_below ?? 30 }}</span>
            <span class="text-zinc-500">{{ item.rsi_above ?? 70 }}</span>
          </div>
          <div class="h-2 bg-[var(--border-color)] rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-blue-500 to-cyan-500" :style="{ width: item.rsi_above && item.rsi_below ? `${item.rsi_above - item.rsi_below}%` : '40%', marginLeft: item.rsi_below ? `${item.rsi_below}%` : '30%' }"></div>
          </div>
        </div>

        <!-- Overbought Zone (70-100) -->
        <div>
          <div class="flex justify-between text-xs mb-1">
            <span class="font-bold text-green-600">超買</span>
            <span class="text-zinc-500">{{ item.rsi_above ?? 70 }}</span>
            <span class="text-zinc-500">100</span>
          </div>
          <div class="h-2 bg-[var(--border-color)] rounded-full overflow-hidden">
            <div class="h-full bg-gradient-to-r from-green-500 to-emerald-600" :style="{ width: item.rsi_above ? `${100 - item.rsi_above}%` : '30%' }"></div>
          </div>
        </div>
      </div>

      <!-- Current Position Indicator -->
      <div v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="mt-4 pt-4 border-t border-[var(--border-color)]">
        <div class="flex items-center gap-2">
          <div class="flex-1 h-3 bg-[var(--border-color)] rounded-full overflow-hidden relative">
            <div :class="['h-full transition-all duration-300', getRSIGaugeColor(item.current_rsi)]" :style="{ width: `${Math.min(100, Math.max(0, item.current_rsi))}%` }"></div>
            <div class="absolute top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[var(--text-primary)] opacity-70" :style="{ left: `${Math.min(100, Math.max(0, item.current_rsi))}%` }"></div>
          </div>
          <span class="text-sm font-bold font-mono" :class="getRSIColor(item.current_rsi)">
            {{ item.current_rsi.toFixed(1) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Configuration Info -->
    <div class="bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-xl p-4">
      <div class="text-sm font-bold text-[var(--text-primary)] mb-3">配置資訊</div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
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

    <!-- RSI Chart -->
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

function getRSIGaugeColor(rsi) {
  if (rsi < 30) return 'bg-gradient-to-r from-red-600 to-orange-500'
  if (rsi > 70) return 'bg-gradient-to-r from-green-500 to-emerald-600'
  return 'bg-gradient-to-r from-blue-500 to-cyan-500'
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
