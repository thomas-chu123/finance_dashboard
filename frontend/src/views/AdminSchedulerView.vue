<template>
  <div class="mt-6 space-y-6">
    <div class="space-y-2">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">時程表管理</h2>
      <p class="text-[var(--text-secondary)]">管理系統任務、暫停/恢復、立即執行</p>
    </div>

    <!-- Scheduler Jobs Table -->
    <div class="overflow-x-auto rounded-lg border border-[var(--border-color)]">
      <table class="w-full text-sm">
        <thead class="bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">任務名稱</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">描述</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">排程</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">狀態</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">最後執行</th>
            <th class="px-4 py-3 text-center font-semibold text-[var(--text-primary)]">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" class="border-b border-[var(--border-color)]">
            <td colspan="6" class="px-4 py-3 text-center text-[var(--text-secondary)]">
              加載中...
            </td>
          </tr>
          <tr v-else-if="jobs.length === 0" class="border-b border-[var(--border-color)]">
            <td colspan="6" class="px-4 py-3 text-center text-[var(--text-secondary)]">
              沒有任務
            </td>
          </tr>
          <tr v-for="job in jobs" :key="job.job_id" class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)]">
            <td class="px-4 py-3 font-medium text-[var(--text-primary)] cursor-pointer hover:text-blue-600" @click="openJobDetail(job)">
              {{ job.job_name }}
            </td>
            <td class="px-4 py-3 text-[var(--text-secondary)] text-xs max-w-xs truncate">{{ job.description || '—' }}</td>
            <td class="px-4 py-3 text-[var(--text-secondary)] text-xs">{{ job.schedule_cron || '—' }}</td>
            <td class="px-4 py-3">
              <span v-if="job.is_enabled" class="inline-block px-2 py-1 rounded bg-green-500/20 text-green-600 dark:text-green-400 text-xs font-medium">
                運行中
              </span>
              <span v-else class="inline-block px-2 py-1 rounded bg-gray-500/20 text-gray-600 dark:text-gray-400 text-xs font-medium">
                已暫停
              </span>
            </td>
            <td class="px-4 py-3 text-[var(--text-secondary)] text-xs">
              {{ formatDate(job.last_run_at) }}
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex justify-center gap-2">
                <button 
                  v-if="job.is_enabled"
                  @click="pauseJob(job.job_id)"
                  class="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-600 hover:bg-yellow-500/30 transition-colors"
                >
                  暫停
                </button>
                <button 
                  v-else
                  @click="resumeJob(job.job_id)"
                  class="px-2 py-1 rounded text-xs bg-green-500/20 text-green-600 hover:bg-green-500/30 transition-colors"
                >
                  恢復
                </button>
                <button 
                  @click="executeJob(job.job_id)"
                  class="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-600 hover:bg-blue-500/30 transition-colors"
                >
                  執行
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Reload Button -->
    <div class="flex justify-center">
      <button
        @click="refreshJobs"
        class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
      >
        重新加載任務
      </button>
    </div>
  </div>

  <!-- Job Detail Modal -->
  <SchedulerJobDetail
    :is-open="showJobDetail"
    :job="selectedJob"
    @close="closeJobDetail"
    @viewHistory="openJobHistory"
  />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAdminScheduler } from '../composables/useAdmin'
import SchedulerJobDetail from '../components/SchedulerJobDetail.vue'

const {
  jobs,
  selectedJob,
  showJobDetail,
  loading,
  openJobDetail,
  closeJobDetail,
  openJobHistory,
  refreshJobs,
  pauseJob,
  resumeJob,
  executeJob,
} = useAdminScheduler()

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  refreshJobs()
})
</script>
