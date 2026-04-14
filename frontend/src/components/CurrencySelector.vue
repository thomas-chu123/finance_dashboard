<template>
  <div class="flex items-center gap-2 bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-lg p-2">
    <span class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">計價:</span>
    
    <button
      v-for="curr in ['USD', 'TWD']"
      :key="curr"
      @click="preference.setDisplayCurrency(curr)"
      :class="{
        'bg-brand-500 text-white': preference.displayCurrency === curr,
        'bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]': preference.displayCurrency !== curr,
      }"
      class="px-3 py-1.5 rounded-md text-sm font-bold transition-all"
    >
      {{ curr }}
    </button>

    <!-- 幣值提示icon（可選，如需進階提示時使用） -->
    <div v-if="showHint" class="flex items-center gap-1 ml-auto text-xs text-[var(--text-secondary)]">
      <span v-if="preference.displayCurrency === 'TWD'" class="text-amber-500">
        ※ 已按匯率轉換
      </span>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import { usePreferenceStore } from '@/stores/preference'

defineProps({
  showHint: {
    type: Boolean,
    default: false
  }
})

const preference = usePreferenceStore()
</script>

<style scoped>
button {
  font-weight: 600;
  transition: all 0.2s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:active {
  transform: translateY(0);
}
</style>
