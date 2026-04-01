<template>
  <div class="mt-6 space-y-6">
    <div class="space-y-2">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">日誌查看</h2>
      <p class="text-[var(--text-secondary)]">實時查看系統、操作、應用日誌</p>
    </div>

    <!-- Tabs Navigation -->
    <div class="flex gap-2 border-b border-[var(--border-color)]">
      <button
        @click="activeTab = 'audit'"
        :class="[
          'px-4 py-2 font-medium text-sm transition-colors border-b-2',
          activeTab === 'audit'
            ? 'text-blue-600 border-blue-600 dark:text-blue-400 dark:border-blue-400'
            : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'
        ]"
      >
        操作日誌
      </button>
      <button
        @click="activeTab = 'system'"
        :class="[
          'px-4 py-2 font-medium text-sm transition-colors border-b-2',
          activeTab === 'system'
            ? 'text-blue-600 border-blue-600 dark:text-blue-400 dark:border-blue-400'
            : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'
        ]"
      >
        系統日誌
      </button>
      <button
        @click="activeTab = 'backend'"
        :class="[
          'px-4 py-2 font-medium text-sm transition-colors border-b-2',
          activeTab === 'backend'
            ? 'text-blue-600 border-blue-600 dark:text-blue-400 dark:border-blue-400'
            : 'text-[var(--text-secondary)] border-transparent hover:text-[var(--text-primary)]'
        ]"
      >
        應用日誌
      </button>
    </div>

    <!-- Audit Logs Tab -->
    <div v-if="activeTab === 'audit'">
      <LogViewer
        :logs="auditLogs"
        :loading="loading"
        :searchable="true"
        :filterable="false"
        @refresh="refreshAuditLogs"
      />
    </div>

    <!-- System Logs Tab -->
    <div v-if="activeTab === 'system'">
      <div class="mb-4">
        <select 
          v-model="systemLevelFilter"
          class="px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm"
        >
          <option value="">所有級別</option>
          <option value="DEBUG">DEBUG</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
      </div>
      <LogViewer
        :logs="systemLogs"
        :loading="loading"
        :searchable="false"
        :filterable="true"
        @refresh="refreshSystemLogs"
      />
    </div>

    <!-- Backend Logs Tab -->
    <div v-if="activeTab === 'backend'">
      <LogViewer
        :logs="backendLogsArray"
        :loading="loading"
        :searchable="true"
        :filterable="false"
        @refresh="refreshBackendLogs"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useAdminLogs } from '../composables/useAdmin'
import LogViewer from '../components/LogViewer.vue'

const {
  auditLogs,
  systemLogs,
  backendLogs,
  filteredAuditLogs,
  filteredSystemLogs,
  systemLevelFilter,
  loading,
  refreshAuditLogs,
  refreshSystemLogs,
  refreshBackendLogs,
} = useAdminLogs()

const activeTab = ref('audit')

const backendLogsArray = computed(() => {
  if (!backendLogs.value) return []
  return backendLogs.value.split('\n').filter(line => line.trim())
})

onMounted(() => {
  refreshAuditLogs()
})
</script>
