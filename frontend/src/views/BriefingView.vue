<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-[var(--text-primary)]">AI 市場早報</h1>
      <p class="text-sm text-zinc-500 mt-1">由 {{ briefingStore.provider || 'AI' }} 自動生成，每日 08:00 / 13:00 / 18:00 更新</p>
    </div>
    <AIDailyBriefing />
  </div>
</template>

<script setup>
import { useBriefingStore } from '../stores/briefing'
import AIDailyBriefing from '../components/AIDailyBriefing.vue'

const briefingStore = useBriefingStore()
</script>
