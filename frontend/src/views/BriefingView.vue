<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-[var(--text-primary)]">{{ $t('pages.briefing') }}</h1>
      <p class="text-sm text-zinc-500 mt-1">{{ $t('briefing.description') }}</p>
    </div>
    <AIDailyBriefing />
  </div>
</template>

<script setup>
import { useBriefingStore } from '../stores/briefing'
import AIDailyBriefing from '../components/AIDailyBriefing.vue'

const briefingStore = useBriefingStore()
</script>
