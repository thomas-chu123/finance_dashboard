<template>
  <div v-if="show" class="space-y-4 p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl">
    <!-- RSI Period Selection -->
    <div>
      <label class="block text-sm font-bold text-[var(--text-primary)] mb-2">
        <span class="flex items-center">
          <span class="text-base mr-2">📊</span>
          RSI 週期 (天數)
        </span>
      </label>
      <div class="flex gap-2 items-center">
        <input
          v-model.number="period"
          type="range"
          min="7"
          max="50"
          step="1"
          class="flex-1 h-2 bg-[var(--border-color)] rounded-lg appearance-none cursor-pointer accent-brand-500"
        />
        <div class="w-16 px-3 py-2 bg-[var(--bg-main)] border border-[var(--border-color)] rounded-lg text-center font-bold text-[var(--text-primary)] text-sm">
          {{ period }}
        </div>
      </div>
      <p class="mt-1 text-xs text-zinc-500">
        標準值：14 天 (較敏感: 7-9, 一般: 14, 較遲鈍: 21-50)
      </p>
    </div>

    <!-- RSI Oversold Threshold -->
    <div>
      <label class="block text-sm font-bold text-[var(--text-primary)] mb-2">
        <span class="flex items-center">
          <span class="text-red-500 text-base mr-2">🔴</span>
          超賣閾值 (低於)
        </span>
      </label>
      <div class="flex gap-2 items-center">
        <input
          v-model.number="rsiBelow"
          type="range"
          min="5"
          max="50"
          step="1"
          class="flex-1 h-2 bg-[var(--border-color)] rounded-lg appearance-none cursor-pointer accent-red-500"
        />
        <div class="w-16 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-center font-bold text-red-600 dark:text-red-400 text-sm">
          {{ rsiBelow }}
        </div>
      </div>
      <p class="mt-1 text-xs text-zinc-500">
        RSI 低於此值時視為超賣狀態 (標準: 30)
      </p>
    </div>

    <!-- RSI Overbought Threshold -->
    <div>
      <label class="block text-sm font-bold text-[var(--text-primary)] mb-2">
        <span class="flex items-center">
          <span class="text-green-500 text-base mr-2">🟢</span>
          超買閾值 (高於)
        </span>
      </label>
      <div class="flex gap-2 items-center">
        <input
          v-model.number="rsiAbove"
          type="range"
          min="50"
          max="95"
          step="1"
          class="flex-1 h-2 bg-[var(--border-color)] rounded-lg appearance-none cursor-pointer accent-green-500"
        />
        <div class="w-16 px-3 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-center font-bold text-green-600 dark:text-green-400 text-sm">
          {{ rsiAbove }}
        </div>
      </div>
      <p class="mt-1 text-xs text-zinc-500">
        RSI 高於此值時視為超買狀態 (標準: 70)
      </p>
    </div>

    <!-- Validation Info -->
    <div v-if="validationError" class="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-600 dark:text-red-400 font-bold">
      ❌ {{ validationError }}
    </div>

    <div v-if="!validationError && rsiBelow < rsiAbove" class="p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-sm text-green-600 dark:text-green-400 font-bold">
      ✅ RSI 參數有效
    </div>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  period: {
    type: Number,
    default: 14
  },
  rsiBelow: {
    type: Number,
    default: 30
  },
  rsiAbove: {
    type: Number,
    default: 70
  }
})

const emit = defineEmits(['update:period', 'update:rsiBelow', 'update:rsiAbove'])

// Local state with watchers
const period = ref(props.period)
const rsiBelow = ref(props.rsiBelow)
const rsiAbove = ref(props.rsiAbove)

watch(() => props.period, (newVal) => { period.value = newVal })
watch(() => props.rsiBelow, (newVal) => { rsiBelow.value = newVal })
watch(() => props.rsiAbove, (newVal) => { rsiAbove.value = newVal })

watch(period, (newVal) => emit('update:period', newVal))
watch(rsiBelow, (newVal) => emit('update:rsiBelow', newVal))
watch(rsiAbove, (newVal) => emit('update:rsiAbove', newVal))

const validationError = computed(() => {
  if (rsiBelow.value >= rsiAbove.value) {
    return `超賣閾值 (${rsiBelow.value}) 必須低於超買閾值 (${rsiAbove.value})`
  }
  if (period.value < 7 || period.value > 50) {
    return 'RSI 週期必須介於 7-50 天之間'
  }
  return ''
})
</script>

<style scoped>
/* Component styling using Tailwind classes */
input[type="range"] {
  -webkit-appearance: slider-horizontal;
}
</style>
