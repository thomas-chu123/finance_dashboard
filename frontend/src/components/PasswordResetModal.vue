<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-[var(--bg-primary)] rounded-lg shadow-lg max-w-md w-full mx-4">
      <!-- Header -->
      <div class="p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-semibold text-[var(--text-primary)]">重設密碼</h3>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <!-- Error Alert (if any) -->
        <div v-if="resetError" class="p-4 rounded-lg bg-red-500/20 border border-red-500/50">
          <p class="text-sm text-red-600 dark:text-red-400">
            ❌ {{ resetError }}
          </p>
        </div>

        <!-- User Info -->
        <div class="p-3 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
          <div class="text-xs text-[var(--text-secondary)] space-y-1">
            <div><strong>使用者:</strong> {{ user.display_name }}</div>
            <div><strong>信箱:</strong> {{ user.email }}</div>
          </div>
        </div>

        <!-- Warning -->
        <div class="p-3 rounded bg-blue-500/10 border border-blue-500/20">
          <p class="text-xs text-blue-600 dark:text-blue-400">
            ℹ️ 此操作將重設使用者密碼。新密碼將通過電子郵件发送給用戶。
          </p>
        </div>

        <!-- New Password -->
        <div>
          <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
            新密碼 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="newPassword"
            type="password"
            placeholder="輸入新密碼"
            class="w-full px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-blue-500"
          />
          <p class="text-xs text-[var(--text-secondary)] mt-1">
            至少 8 個字符，包含大小寫和數字
          </p>
        </div>

        <!-- Confirm Password -->
        <div>
          <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
            確認密碼 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="確認新密碼"
            class="w-full px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-blue-500"
          />
        </div>

        <!-- Password Match Warning -->
        <div v-if="passwordMismatch" class="p-3 rounded bg-red-500/10 border border-red-500/20">
          <p class="text-xs text-red-600 dark:text-red-400">
            ❌ 密碼不相符
          </p>
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
          @click="resetPassword"
          :disabled="!newPassword || !confirmPassword || passwordMismatch || isResetting"
          class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ isResetting ? '重設中...' : '重設密碼' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAdminStore } from '../stores/admin'

const props = defineProps({
  isOpen: Boolean,
  user: Object,
})

const emit = defineEmits(['close', 'reset'])

const admin = useAdminStore()

const newPassword = ref('')
const confirmPassword = ref('')
const isResetting = ref(false)
const resetError = ref(null)

const passwordMismatch = computed(() => {
  return newPassword.value && confirmPassword.value && newPassword.value !== confirmPassword.value
})

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    newPassword.value = ''
    confirmPassword.value = ''
    resetError.value = null
  }
})

const resetPassword = async () => {
  if (!props.user || !newPassword.value || passwordMismatch.value) return

  isResetting.value = true
  resetError.value = null
  try {
    const success = await admin.resetPasswordAPI(props.user.id, newPassword.value)
    if (success) {
      emit('reset')
      close()
    } else {
      resetError.value = admin.error || '密碼重設失敗，請稍後重試'
    }
  } catch (error) {
    console.error('密碼重設失敗:', error)
    resetError.value = error.message || '密碼重設失敗，請稍後重試'
  } finally {
    isResetting.value = false
  }
}

const close = () => {
  newPassword.value = ''
  confirmPassword.value = ''
  resetError.value = null
  emit('close')
}
</script>
