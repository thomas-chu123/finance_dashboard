<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-[var(--bg-primary)] rounded-lg shadow-lg max-w-md w-full mx-4">
      <!-- Header -->
      <div class="p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-semibold text-[var(--text-primary)]">編輯使用者</h3>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <!-- Error Alert (if any) -->
        <div v-if="saveError" class="p-4 rounded-lg bg-red-500/20 border border-red-500/50">
          <p class="text-sm text-red-600 dark:text-red-400">
            ❌ {{ saveError }}
          </p>
        </div>

        <!-- Display Name -->
        <div>
          <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">
            名稱
          </label>
          <input
            v-model="formData.display_name"
            type="text"
            class="w-full px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-blue-500"
            placeholder="輸入名稱"
          />
        </div>

        <!-- Admin Status -->
        <div class="flex items-center gap-3">
          <input
            v-model="formData.is_admin"
            type="checkbox"
            id="is_admin"
            class="w-4 h-4 rounded border-[var(--border-color)] text-blue-600 focus:ring-0 cursor-pointer"
          />
          <label for="is_admin" class="text-sm font-medium text-[var(--text-primary)] cursor-pointer">
            管理員權限
          </label>
        </div>

        <!-- User Info -->
        <div class="p-3 rounded bg-[var(--bg-secondary)] border border-[var(--border-color)]">
          <div class="text-xs text-[var(--text-secondary)] space-y-1">
            <div><strong>ID:</strong> {{ user.id }}</div>
            <div><strong>信箱:</strong> {{ user.email }}</div>
            <div><strong>建立時間:</strong> {{ formatDate(user.created_at) }}</div>
          </div>
        </div>

        <!-- Warning -->
        <div v-if="isChangingAdminStatus" class="p-3 rounded bg-yellow-500/10 border border-yellow-500/20">
          <p class="text-xs text-yellow-600 dark:text-yellow-400">
            ⚠️ 您正在修改此用戶的管理員權限。請謹慎操作。
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
          @click="saveChanges"
          :disabled="isSaving"
          class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ isSaving ? '保存中...' : '保存' }}
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

const emit = defineEmits(['close', 'saved'])

const admin = useAdminStore()

const formData = ref({
  display_name: '',
  is_admin: false,
})

const isSaving = ref(false)
const originalAdminStatus = ref(false)
const saveError = ref(null)

const isChangingAdminStatus = computed(() => {
  return formData.value.is_admin !== originalAdminStatus.value
})

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(() => props.user, (newUser) => {
  if (newUser) {
    formData.value = {
      display_name: newUser.display_name || '',
      is_admin: newUser.is_admin || false,
    }
    originalAdminStatus.value = newUser.is_admin || false
    saveError.value = null
  }
}, { immediate: true })

const saveChanges = async () => {
  if (!props.user) return

  isSaving.value = true
  saveError.value = null
  try {
    // 更新用戶基本信息
    await admin.updateUserLocal(props.user.id, {
      display_name: formData.value.display_name,
    })

    // 如果改變了管理員狀態，發送到後端
    if (isChangingAdminStatus.value) {
      const updateData = {
        display_name: formData.value.display_name,
        is_admin: formData.value.is_admin,
      }
      await admin.updateUserAPI(props.user.id, updateData)
    } else {
      // 只更新名稱
      const updateData = {
        display_name: formData.value.display_name,
      }
      await admin.updateUserAPI(props.user.id, updateData)
    }

    emit('saved')
    close()
  } catch (error) {
    console.error('保存失敗:', error)
    saveError.value = error.message || '保存失敗，請稍後重試'
  } finally {
    isSaving.value = false
  }
}

const close = () => {
  emit('close')
}
</script>
