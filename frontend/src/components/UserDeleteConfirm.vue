<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-[var(--bg-primary)] rounded-lg shadow-lg max-w-md w-full mx-4">
      <!-- Header -->
      <div class="p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-semibold text-red-600 dark:text-red-400">刪除使用者</h3>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <!-- Warning Alert -->
        <div class="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
          <p class="text-sm text-red-600 dark:text-red-400 font-medium mb-2">
            ⚠️ 警告：此操作不可恢復
          </p>
          <p class="text-xs text-red-600/80 dark:text-red-400/80">
            刪除此使用者將永久移除他們的帳戶以及所有相關數據。
          </p>
        </div>

        <!-- User Info -->
        <div class="p-3 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
          <div class="text-sm text-[var(--text-primary)] space-y-1">
            <div><strong>名稱:</strong> {{ user.display_name }}</div>
            <div><strong>信箱:</strong> {{ user.email }}</div>
          </div>
        </div>

        <!-- Cascade Delete Info -->
        <div class="p-3 rounded bg-yellow-500/10 border border-yellow-500/20">
          <p class="text-xs font-semibold text-yellow-600 dark:text-yellow-400 mb-2">
            將級聯刪除以下數據：
          </p>
          <ul class="text-xs text-yellow-600/80 dark:text-yellow-400/80 space-y-1 ml-4">
            <li>✓ 投資組合追蹤 ({{ trackingCount }})</li>
            <li>✓ 持倉記錄</li>
            <li>✓ 回測結果</li>
            <li>✓ 優化結果</li>
            <li>✓ 警報日誌</li>
            <li>✓ 通知日誌</li>
            <li>✓ 用戶偏好設定</li>
          </ul>
        </div>

        <!-- Confirmation -->
        <div>
          <label class="text-xs font-medium text-[var(--text-primary)] block mb-2">
            請輸入使用者名稱以確認（{{ user.display_name }}）
          </label>
          <input
            v-model="confirmText"
            type="text"
            placeholder="輸入名稱確認"
            class="w-full px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-red-500"
          />
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-[var(--border-color)] flex gap-2 justify-end">
        <button
          @click="close"
          class="px-4 py-2 rounded border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
        >
          取消
        </button>
        <button
          @click="confirmDelete"
          :disabled="confirmText !== user.display_name || isDeleting"
          class="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
        >
          {{ isDeleting ? '刪除中...' : '確認刪除' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  isOpen: Boolean,
  user: Object,
  trackingCount: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'deleted'])

const auth = useAuthStore()
const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : window.location.origin)

const confirmText = ref('')
const isDeleting = ref(false)

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    confirmText.value = ''
  }
})

const confirmDelete = async () => {
  if (!props.user || confirmText.value !== props.user.display_name) return

  isDeleting.value = true
  try {
    await axios.delete(`${API_BASE}/api/admin/users/${props.user.id}`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })

    emit('deleted')
    close()
  } catch (error) {
    console.error('刪除失敗:', error)
    alert('刪除失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    isDeleting.value = false
  }
}

const close = () => {
  confirmText.value = ''
  emit('close')
}
</script>
