<template>
  <div class="space-y-4">
    <!-- Trigger Mode Selection -->
    <div>
      <label class="block text-sm font-bold text-[var(--text-primary)] mb-3">
        <span class="flex items-center">
          <span class="text-base mr-2">⚙️</span>
          觸發模式
        </span>
      </label>
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="mode in triggerModes"
          :key="mode.value"
          type="button"
          @click="emit('update:modelValue', mode.value)"
          :class="[
            'p-3 rounded-xl font-bold text-sm transition-all border-2',
            modelValue === mode.value
              ? `${mode.activeClass} border-transparent shadow-lg`
              : 'bg-[var(--bg-main)] border-[var(--border-color)] text-zinc-500 hover:border-brand-500 hover:text-brand-500'
          ]"
        >
          <div class="flex items-center justify-center gap-1.5">
            <span>{{ mode.icon }}</span>
            <span>{{ mode.label }}</span>
          </div>
        </button>
      </div>
      <p class="mt-2 text-xs text-zinc-500 leading-relaxed">
        {{ modeDescriptions[modelValue] }}
      </p>
    </div>

    <!-- Mode-Specific Info -->
    <div v-if="needsRSI" class="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
      <div class="flex gap-2">
        <span class="text-blue-500 font-bold">💡</span>
        <div class="flex-1 text-sm text-blue-600 dark:text-blue-400">
          <span class="font-bold">{{ modeInfoLabels[modelValue] }}：</span>
          需要設定 RSI 超賣 (低於) 和超買 (高於) 閾值
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'price',
    validator: (v) => ['price', 'rsi', 'both', 'either'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue'])

const triggerModes = [
  {
    value: 'price',
    label: '價格觸發',
    icon: '💰',
    activeClass: 'bg-yellow-500 text-white'
  },
  {
    value: 'rsi',
    label: 'RSI 指標',
    icon: '📈',
    activeClass: 'bg-blue-500 text-white'
  },
  {
    value: 'both',
    label: '價格及 RSI',
    icon: '⚡',
    activeClass: 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
  },
  {
    value: 'either',
    label: '價格或 RSI',
    icon: '🔀',
    activeClass: 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white'
  }
]

const modeDescriptions = {
  price:  '當前價格突破或跌破設定的觸發價格時發送警報 (傳統模式)',
  rsi:    '當 RSI 指數進入超賣 (<30) 或超買 (>70) 區域時發送警報',
  both:   '當價格觸發條件「且」RSI 條件同時滿足時發送警報 (更精確的信號)',
  either: '當價格觸發條件「或」RSI 條件任一滿足時發送警報 (更靈敏的信號)'
}

const modeInfoLabels = {
  rsi:    'RSI 觸發模式',
  both:   '價格及 RSI 模式',
  either: '價格或 RSI 模式'
}

// RSI 相關模式都需要設定 RSI 閾值
const needsRSI = computed(() => ['rsi', 'both', 'either'].includes(props.modelValue))
</script>

<style scoped>
/* Component styling using Tailwind classes */
</style>
