<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-[var(--bg-primary)] rounded-2xl shadow-lg max-w-md w-full border border-[var(--border-color)]">
      <!-- Header -->
      <div class="p-6 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-semibold text-[var(--text-primary)]">重設密碼</h3>
        <p class="text-sm text-[var(--text-secondary)] mt-1">輸入您的信箱以重設密碼</p>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <!-- Success Alert -->
        <div v-if="successMessage" class="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
          <p class="text-sm text-green-600 dark:text-green-400">
            ✅ {{ successMessage }}
          </p>
        </div>

        <!-- Error Alert -->
        <div v-if="errorMessage" class="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20">
          <p class="text-sm text-rose-600 dark:text-rose-400">
            ❌ {{ errorMessage }}
          </p>
        </div>

        <!-- Step 1: Email -->
        <div v-if="currentStep === 'email'">
          <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
            電子郵件 <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="email"
            type="email"
            placeholder="example@email.com"
            class="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[#00D084] focus:shadow-[0_0_0_3px_rgba(0,208,132,0.1)]"
            :disabled="isLoading"
          />
        </div>

        <!-- Step 2: New Password -->
        <div v-if="currentStep === 'password'">
          <div class="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] mb-4">
            <div class="text-xs text-[var(--text-secondary)]">
              <strong>重設帳號:</strong> {{ email }}
            </div>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
              新密碼 <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="newPassword"
              type="password"
              placeholder="輸入新密碼（至少6個字符）"
              minlength="6"
              class="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[#00D084] focus:shadow-[0_0_0_3px_rgba(0,208,132,0.1)]"
              :disabled="isLoading"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
              確認密碼 <span class="text-rose-500">*</span>
            </label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="確認新密碼"
              minlength="6"
              class="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-[#00D084] focus:shadow-[0_0_0_3px_rgba(0,208,132,0.1)]"
              :disabled="isLoading"
            />
          </div>

          <!-- Password Mismatch Warning -->
          <div v-if="passwordMismatch" class="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
            <p class="text-xs text-rose-600 dark:text-rose-400">
              ❌ 密碼不相符
            </p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-[var(--border-color)] flex gap-3 justify-end">
        <button
          @click="close"
          class="px-4 py-2 rounded-lg border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors font-medium text-sm"
          :disabled="isLoading"
        >
          取消
        </button>
        <button
          v-if="currentStep === 'email'"
          @click="sendResetEmail"
          :disabled="!email || isLoading"
          class="px-4 py-2 rounded-lg bg-[#00D084] text-white hover:bg-[#00c974] disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
        >
          {{ isLoading ? '發送中...' : '發送重設連結' }}
        </button>
        <button
          v-if="currentStep === 'password'"
          @click="resetPassword"
          :disabled="!newPassword || !confirmPassword || passwordMismatch || isLoading"
          class="px-4 py-2 rounded-lg bg-[#00D084] text-white hover:bg-[#00c974] disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
        >
          {{ isLoading ? '重設中...' : '重設密碼' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  isOpen: Boolean,
})

const emit = defineEmits(['close'])

const auth = useAuthStore()
const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const currentStep = ref('email')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const passwordMismatch = computed(() => {
  return newPassword.value && confirmPassword.value && newPassword.value !== confirmPassword.value
})

async function sendResetEmail() {
  if (!email.value) return

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''
    await axios.post(`${apiBase}/api/auth/forgot-password`, { email: email.value })

    successMessage.value = '重設連結已發送到您的信箱，請檢查您的郵件'
    currentStep.value = 'password'
    
    // 3秒後自動轉到密碼重設步驟
    setTimeout(() => {
      currentStep.value = 'password'
    }, 1500)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '無法發送重設連結，請檢查信箱是否正確'
    console.error('Forgot password error:', error)
  } finally {
    isLoading.value = false
  }
}

async function resetPassword() {
  if (!email.value || !newPassword.value || passwordMismatch.value) return

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const apiBase = import.meta.env.VITE_API_BASE_URL || ''
    await axios.post(`${apiBase}/api/auth/reset-password`, {
      email: email.value,
      new_password: newPassword.value,
    })

    successMessage.value = '密碼已成功重設，請使用新密碼登入'
    
    setTimeout(() => {
      close()
    }, 2000)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || '密碼重設失敗，請稍後重試'
    console.error('Reset password error:', error)
  } finally {
    isLoading.value = false
  }
}

function close() {
  email.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  currentStep.value = 'email'
  errorMessage.value = ''
  successMessage.value = ''
  emit('close')
}
</script>
