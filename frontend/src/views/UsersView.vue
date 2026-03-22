<template>
  <div>
    <div class="flex-between mb-24">
      <h2 class="text-[var(--text-primary)]">使用者管理</h2>
    </div>

    <!-- My profile -->
    <div class="glass-card mb-6">
      <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
        <h3>我的設定</h3>
        <button class="btn btn-primary btn-sm" @click="saveProfile" :disabled="profileSaving">
          <template v-if="profileSaving">
            <Loader2 class="w-4 h-4 mr-2 inline animate-spin" />儲存中...
          </template>
          <template v-else>
            <Save class="w-4 h-4 mr-2 inline" />儲存
          </template>
        </button>
      </div>
      <div class="p-4 sm:p-6">
        <div v-if="profileMsg" :class="['p-4 mb-4 text-sm rounded-lg', profileMsg.ok ? 'bg-brand-500/10 text-brand-500 border border-brand-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20']" style="margin-bottom:16px;">
          {{ profileMsg.text }}
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-1 mb-4">
            <label class="block text-sm font-medium text-[var(--text-muted)]">顯示姓名</label>
            <input v-model="profileForm.display_name" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" />
          </div>
          <div class="space-y-1 mb-4">
            <label class="block text-sm font-medium text-[var(--text-muted)]">LINE User ID</label>
            <div class="flex items-center gap-2">
              <input v-model="profileForm.line_user_id" type="text" class="flex-1 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" placeholder="未連結" disabled />
              <span v-if="profileForm.line_user_id" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-500/10 text-brand-500 border border-brand-500/20 whitespace-nowrap">已綁定</span>
            </div>
          </div>
        </div>
        
        <div class="flex gap-8 mt-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="profileForm.notify_email" class="w-5 h-5 cursor-pointer accent-brand-500" />
            <span class="text-sm font-medium text-[var(--text-primary)] flex items-center">
              <Mail class="w-4 h-4 mr-1.5" />Email 通知
            </span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="profileForm.notify_line" class="w-5 h-5 cursor-pointer accent-brand-500" />
            <span class="text-sm font-medium text-[var(--text-primary)] flex items-center">
              <MessageCircle class="w-4 h-4 mr-1.5" />LINE 通知
            </span>
          </label>
        </div>
      </div>
    </div>

    <!-- Admin: user list (only if admin) -->
    <div v-if="auth.profile?.is_admin" class="glass-card">
      <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
        <h3>所有使用者 <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20" style="margin-left:8px;">管理員</span></h3>
        <button class="flex items-center px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="loadUsers"><RefreshCw class="w-4 h-4 mr-2" />重新整理</button>
      </div>
      <div v-if="usersLoading" class="flex justify-center items-center p-12"><Loader2 class="w-8 h-8 text-brand-500 animate-spin" /></div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm text-left">
          <thead class="text-xs text-[var(--text-muted)] uppercase bg-[var(--input-bg)] border-b border-[var(--border-color)]">
            <tr><th class="px-6 py-4 font-medium">Email</th><th class="px-6 py-4 font-medium">姓名</th><th class="px-6 py-4 font-medium">LINE</th><th class="px-6 py-4 font-medium">Email通知</th><th class="px-6 py-4 font-medium">LINE通知</th><th class="px-6 py-4 font-medium">角色</th><th class="px-6 py-4 font-medium">操作</th></tr>
          </thead>
          <tbody class="divide-y border-[var(--border-color)]">
            <tr v-for="u in users" :key="u.id" class="text-[var(--text-primary)] hover:bg-[var(--input-bg)]">
              <td class="px-6 py-4">{{ u.email }}</td>
              <td class="px-6 py-4">{{ u.display_name || '—' }}</td>
              <td class="px-6 py-4"><span v-if="u.line_user_id" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-500/10 text-brand-500 border border-brand-500/20">已設定</span><span v-else class="text-[var(--text-muted)]">—</span></td>
              <td class="px-6 py-4"><span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', u.notify_email ? 'bg-brand-500/10 text-brand-500 border border-brand-500/20' : 'bg-rose-500/10 text-rose-500 border border-rose-500/20']">{{ u.notify_email ? '是' : '否' }}</span></td>
              <td class="px-6 py-4"><span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', u.notify_line ? 'bg-brand-500/10 text-brand-500 border border-brand-500/20' : 'bg-rose-500/10 text-rose-500 border border-rose-500/20']">{{ u.notify_line ? '是' : '否' }}</span></td>
              <td class="px-6 py-4"><span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', u.is_admin ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' : 'bg-blue-500/10 text-blue-500 border border-blue-500/20']">{{ u.is_admin ? '管理員' : '一般' }}</span></td>
              <td class="px-6 py-4">
                <button class="flex items-center px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="toggleAdmin(u)" v-if="u.id !== auth.userId">
                  {{ u.is_admin ? '撤銷管理員' : '設為管理員' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { Save, Mail, MessageCircle, RefreshCw, Loader2 } from 'lucide-vue-next'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'

const auth = useAuthStore()
// Remove local API_BASE declaration

const profileForm = reactive({
  display_name: '',
  line_user_id: '',
  notify_email: true,
  notify_line: false,
})
const profileSaving = ref(false)
const profileMsg = ref(null)

const users = ref([])
const usersLoading = ref(false)

function syncProfile() {
  if (auth.profile) {
    profileForm.display_name = auth.profile.display_name || ''
    profileForm.line_user_id = auth.profile.line_user_id || ''
    profileForm.notify_email = auth.profile.notify_email ?? true
    profileForm.notify_line = auth.profile.notify_line ?? false
  }
}

watch(() => auth.profile, syncProfile, { immediate: true })

async function saveProfile() {
  profileSaving.value = true
  profileMsg.value = null
  try {
    await auth.updateProfile({ ...profileForm })
    profileMsg.value = { ok: true, text: '個人設定已儲存！' }
    setTimeout(() => { profileMsg.value = null }, 3000)
  } catch (e) {
    profileMsg.value = { ok: false, text: e.response?.data?.detail || e.message }
  } finally {
    profileSaving.value = false
  }
}

async function loadUsers() {
  if (!auth.profile?.is_admin) return
  usersLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/users`, { headers: auth.headers })
    users.value = res.data
  } finally {
    usersLoading.value = false
  }
}

async function toggleAdmin(u) {
  if (!confirm(`確定${u.is_admin ? '撤銷' : '設定'} ${u.email} 的管理員權限？`)) return
  try {
    await axios.put(`${API_BASE}/api/users/${u.id}/admin`, { is_admin: !u.is_admin }, { headers: auth.headers })
    await loadUsers()
  } catch (e) { alert('操作失敗: ' + (e.response?.data?.detail || e.message)) }
}

onMounted(async () => {
  if (!auth.profile) await auth.fetchProfile()
  syncProfile()
  await loadUsers()
})
</script>


