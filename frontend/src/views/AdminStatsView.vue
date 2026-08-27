<template>
  <div class="mt-6 space-y-6">
    <div class="space-y-2">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">{{ $t('pages.stats') }}</h2>
      <p class="text-[var(--text-secondary)]">{{ $t('admin.statsDescription') }}</p>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Users -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">{{ $t('admin.totalUsers') }}</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ statsOverview.total_users_count || 0 }}</div>
      </div>

      <!-- Active Users -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">{{ $t('admin.activeUsers') }}</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ statsOverview.active_users_count || 0 }}</div>
      </div>

      <!-- Tracked Indices -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">{{ $t('admin.trackedAssets') }}</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ statsOverview.tracked_indices_count || 0 }}</div>
      </div>

      <!-- Alerts Count -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">{{ $t('admin.alertsSent') }}</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-orange-600 dark:text-orange-400">{{ statsOverview.alerts_sent_count || 0 }}</div>
      </div>
    </div>

    <!-- User Statistics -->
    <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <h3 class="font-semibold text-[var(--text-primary)] mb-4">{{ $t('admin.newUsers') }}</h3>
      <div v-if="loading" class="text-center text-[var(--text-secondary)]">加載中...</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="p-3 rounded bg-[var(--bg-primary)] border border-[var(--border-color)]">
          <div class="text-xs text-[var(--text-secondary)] mb-1">今日</div>
          <div class="text-2xl font-bold text-[var(--text-primary)]">{{ userStats.today || 0 }}</div>
        </div>
        <div class="p-3 rounded bg-[var(--bg-primary)] border border-[var(--border-color)]">
          <div class="text-xs text-[var(--text-secondary)] mb-1">本週</div>
          <div class="text-2xl font-bold text-[var(--text-primary)]">{{ userStats.week || 0 }}</div>
        </div>
        <div class="p-3 rounded bg-[var(--bg-primary)] border border-[var(--border-color)]">
          <div class="text-xs text-[var(--text-secondary)] mb-1">本月</div>
          <div class="text-2xl font-bold text-[var(--text-primary)]">{{ userStats.month || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- Alert Statistics -->
    <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <h3 class="font-semibold text-[var(--text-primary)] mb-4">{{ $t('admin.alertStats') }}</h3>
      <div v-if="loading" class="text-center text-[var(--text-secondary)]">加載中...</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-3 rounded bg-[var(--bg-primary)] border border-[var(--border-color)]">
          <div class="text-sm text-[var(--text-secondary)] mb-2">已送出</div>
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">{{ alertStats.sent_count || 0 }}</div>
        </div>
        <div class="p-3 rounded bg-[var(--bg-primary)] border border-[var(--border-color)]">
          <div class="text-sm text-[var(--text-secondary)] mb-2">失敗</div>
          <div class="text-2xl font-bold text-red-600 dark:text-red-400">{{ alertStats.failed_count || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- Refresh Button -->
    <div class="flex justify-center">
      <button
        @click="refreshStats"
        class="px-6 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
      >
        重新加載統計
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAdminStats } from '../composables/useAdmin'

const {
  statsOverview,
  userStats,
  alertStats,
  loading,
  refreshStats,
} = useAdminStats()

onMounted(() => {
  refreshStats()
})
</script>
