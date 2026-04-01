<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
    <div class="bg-[var(--bg-primary)] rounded-lg shadow-lg max-w-2xl w-full mx-4 my-8">
      <!-- Header -->
      <div class="p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-semibold text-[var(--text-primary)]">{{ job.job_name }}</h3>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-6 max-h-96 overflow-y-auto">
        <!-- Job Info -->
        <div class="space-y-3">
          <h4 class="font-semibold text-[var(--text-primary)] text-sm">基本資訊</h4>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">任務 ID</div>
              <div class="text-[var(--text-primary)] font-mono text-xs break-all">{{ job.job_id }}</div>
            </div>
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">排程</div>
              <div class="text-[var(--text-primary)] font-mono text-xs">{{ job.schedule_cron || '—' }}</div>
            </div>
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">狀態</div>
              <div class="text-[var(--text-primary)] font-mono text-xs">
                <span :class="{
                  'text-green-600 dark:text-green-400': job.is_enabled,
                  'text-gray-600 dark:text-gray-400': !job.is_enabled
                }">
                  {{ job.is_enabled ? '運行中' : '已暫停' }}
                </span>
              </div>
            </div>
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">當前狀態</div>
              <div class="text-[var(--text-primary)] font-mono text-xs">{{ job.status || '—' }}</div>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div v-if="job.description" class="space-y-2">
          <h4 class="font-semibold text-[var(--text-primary)] text-sm">描述</h4>
          <p class="text-sm text-[var(--text-secondary)] p-3 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
            {{ job.description }}
          </p>
        </div>

        <!-- Timing -->
        <div class="space-y-3">
          <h4 class="font-semibold text-[var(--text-primary)] text-sm">執行時間</h4>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">最後執行</div>
              <div class="text-[var(--text-primary)] text-xs">{{ formatDate(job.last_run_at) }}</div>
            </div>
            <div class="p-2 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <div class="text-[var(--text-secondary)] text-xs mb-1">下次執行</div>
              <div class="text-[var(--text-primary)] text-xs">{{ formatDate(job.next_run_at) }}</div>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="job.error_message" class="space-y-2">
          <h4 class="font-semibold text-[var(--text-primary)] text-sm">最後錯誤</h4>
          <p class="text-xs text-red-600 dark:text-red-400 p-3 rounded bg-red-500/10 border border-red-500/20 font-mono break-words">
            {{ job.error_message }}
          </p>
        </div>

        <!-- Recent Runs (Placeholder) -->
        <div class="space-y-3">
          <h4 class="font-semibold text-[var(--text-primary)] text-sm">最近執行歷史</h4>
          <div class="text-sm text-[var(--text-secondary)] p-3 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
            點擊「查看歷史」按鈕查看完整的執行紀錄。
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-[var(--border-color)] flex gap-2 justify-between">
        <div class="flex gap-2">
          <button
            @click="viewHistory"
            class="px-4 py-2 rounded border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors text-sm"
          >
            查看歷史
          </button>
        </div>
        <button
          @click="close"
          class="px-4 py-2 rounded border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
        >
          關閉
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  job: Object,
})

const emit = defineEmits(['close', 'viewHistory'])

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const viewHistory = () => {
  emit('viewHistory', props.job.job_id)
  close()
}

const close = () => {
  emit('close')
}
</script>
