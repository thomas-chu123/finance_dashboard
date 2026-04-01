<template>
  <div class="mt-6 space-y-6">
    <div class="space-y-2">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">用戶管理</h2>
      <p class="text-[var(--text-secondary)]">編輯、刪除、修改密碼和管理員權限</p>
    </div>

    <!-- Search Bar -->
    <div class="flex gap-2">
      <input 
        v-model="searchQuery"
        type="text" 
        placeholder="搜尋用戶名稱或郵件..."
        class="flex-1 px-4 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-blue-500"
      />
      <button 
        @click="refreshUsers"
        class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
      >
        重新加載
      </button>
    </div>

    <!-- Users Table -->
    <div class="overflow-x-auto rounded-lg border border-[var(--border-color)]">
      <table class="w-full text-sm">
        <thead class="bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">用戶</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">郵件</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">權限</th>
            <th class="px-4 py-3 text-left font-semibold text-[var(--text-primary)]">創建時間</th>
            <th class="px-4 py-3 text-center font-semibold text-[var(--text-primary)]">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" class="border-b border-[var(--border-color)]">
            <td colspan="5" class="px-4 py-3 text-center text-[var(--text-secondary)]">
              加載中...
            </td>
          </tr>
          <tr v-else-if="filteredUsers.length === 0" class="border-b border-[var(--border-color)]">
            <td colspan="5" class="px-4 py-3 text-center text-[var(--text-secondary)]">
              沒有用戶
            </td>
          </tr>
          <tr v-for="user in filteredUsers" :key="user.id" class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)]">
            <td class="px-4 py-3 font-medium text-[var(--text-primary)]">{{ user.display_name || '未設定' }}</td>
            <td class="px-4 py-3 text-[var(--text-secondary)]">{{ user.email }}</td>
            <td class="px-4 py-3">
              <span v-if="user.is_admin" class="inline-block px-2 py-1 rounded bg-amber-500/20 text-amber-600 dark:text-amber-400 text-xs font-medium">
                管理員
              </span>
              <span v-else class="inline-block px-2 py-1 rounded bg-gray-500/20 text-gray-600 dark:text-gray-400 text-xs font-medium">
                普通用戶
              </span>
            </td>
            <td class="px-4 py-3 text-[var(--text-secondary)]">
              {{ formatDate(user.created_at) }}
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex justify-center gap-2">
                <button 
                  @click="openEditModal(user)"
                  class="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-600 hover:bg-blue-500/30 transition-colors"
                >
                  編輯
                </button>
                <button 
                  @click="openPasswordModal(user)"
                  class="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-600 hover:bg-yellow-500/30 transition-colors"
                >
                  密碼
                </button>
                <button 
                  @click="openDeleteModal(user)"
                  class="px-2 py-1 rounded text-xs bg-red-500/20 text-red-600 hover:bg-red-500/30 transition-colors"
                >
                  刪除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Modals -->
  <UserEditModal
    :is-open="showEditModal"
    :user="editingUser"
    @close="closeEditModal"
    @saved="handleEditSaved"
  />
  
  <UserDeleteConfirm
    :is-open="showDeleteModal"
    :user="editingUser"
    :tracking-count="0"
    @close="closeDeleteModal"
    @deleted="handleDeleted"
  />
  
  <PasswordResetModal
    :is-open="showPasswordModal"
    :user="editingUser"
    @close="closePasswordModal"
    @reset="handlePasswordReset"
  />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAdminUsers } from '../composables/useAdmin'
import UserEditModal from '../components/UserEditModal.vue'
import UserDeleteConfirm from '../components/UserDeleteConfirm.vue'
import PasswordResetModal from '../components/PasswordResetModal.vue'

const {
  filteredUsers,
  searchQuery,
  editingUser,
  showEditModal,
  showDeleteModal,
  showPasswordModal,
  loading,
  refreshUsers,
  openEditModal,
  closeEditModal,
  openDeleteModal,
  closeDeleteModal,
  openPasswordModal,
  closePasswordModal,
} = useAdminUsers()

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const handleEditSaved = async () => {
  await refreshUsers()
}

const handleDeleted = async () => {
  await refreshUsers()
}

const handlePasswordReset = () => {
  // 密碼重設成功後的操作（如果需要）
}

onMounted(() => {
  refreshUsers()
})
</script>
