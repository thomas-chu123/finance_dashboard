<template>
  <div class="mt-6 space-y-6">
    <div class="space-y-2">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">系統監控</h2>
      <p class="text-[var(--text-secondary)]">查看系統統計和性能指標</p>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Users -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">總使用者數</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ statsOverview.total_users_count || 0 }}</div>
      </div>

      <!-- Active Users -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">活躍使用者（7天）</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ statsOverview.active_users_count || 0 }}</div>
      </div>

      <!-- Tracked Indices -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">追蹤標的物</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ statsOverview.tracked_indices_count || 0 }}</div>
      </div>

      <!-- Alerts Count -->
      <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
        <div class="text-sm text-[var(--text-secondary)] mb-2">已送出警報</div>
        <div v-if="loading" class="text-2xl font-bold text-[var(--text-primary)]">—</div>
        <div v-else class="text-2xl font-bold text-orange-600 dark:text-orange-400">{{ statsOverview.alerts_sent_count || 0 }}</div>
      </div>
    </div>

    <!-- User Statistics -->
    <div class="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <h3 class="font-semibold text-[var(--text-primary)] mb-4">新增使用者統計</h3>
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
      <h3 class="font-semibold text-[var(--text-primary)] mb-4">警報統計</h3>
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
