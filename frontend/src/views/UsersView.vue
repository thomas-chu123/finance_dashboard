<template>
  <div>
    <div class="flex-between mb-24">
      <h2>使用者管理</h2>
    </div>

    <!-- My profile -->
    <div class="card mb-24">
      <div class="card-header">
        <h3>我的設定</h3>
        <button class="btn btn-primary btn-sm" @click="saveProfile" :disabled="profileSaving">
          {{ profileSaving ? '儲存中...' : '💾 儲存' }}
        </button>
      </div>
      <div class="card-body">
        <div v-if="profileMsg" :class="['alert', profileMsg.ok ? 'alert-success' : 'alert-error']" style="margin-bottom:16px;">
          {{ profileMsg.text }}
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">顯示姓名</label>
            <input v-model="profileForm.display_name" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label class="form-label">LINE User ID</label>
            <input v-model="profileForm.line_user_id" type="text" class="form-control" placeholder="Uxxxxxxxxx..." />
          </div>
        </div>
        <div class="flex gap-24 mt-16">
          <label class="flex gap-8 align-center" style="cursor:pointer;">
            <label class="toggle">
              <input type="checkbox" v-model="profileForm.notify_email" />
              <span class="toggle-slider"></span>
            </label>
            <span class="text-sm fw-600">📧 Email 通知</span>
          </label>
          <label class="flex gap-8 align-center" style="cursor:pointer;">
            <label class="toggle">
              <input type="checkbox" v-model="profileForm.notify_line" />
              <span class="toggle-slider"></span>
            </label>
            <span class="text-sm fw-600">💬 LINE 通知</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Admin: user list (only if admin) -->
    <div v-if="auth.profile?.is_admin" class="card">
      <div class="card-header">
        <h3>所有使用者 <span class="badge badge-yellow" style="margin-left:8px;">管理員</span></h3>
        <button class="btn btn-ghost btn-sm" @click="loadUsers">🔄 重新整理</button>
      </div>
      <div v-if="usersLoading" class="loading-center"><div class="spinner"></div></div>
      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr><th>Email</th><th>姓名</th><th>LINE</th><th>Email通知</th><th>LINE通知</th><th>角色</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.email }}</td>
              <td>{{ u.display_name || '—' }}</td>
              <td><span v-if="u.line_user_id" class="badge badge-green">已設定</span><span v-else class="text-muted">—</span></td>
              <td><span :class="['badge', u.notify_email ? 'badge-green' : 'badge-red']">{{ u.notify_email ? '是' : '否' }}</span></td>
              <td><span :class="['badge', u.notify_line ? 'badge-green' : 'badge-red']">{{ u.notify_line ? '是' : '否' }}</span></td>
              <td><span :class="['badge', u.is_admin ? 'badge-yellow' : 'badge-blue']">{{ u.is_admin ? '管理員' : '一般' }}</span></td>
              <td>
                <button class="btn btn-ghost btn-sm" @click="toggleAdmin(u)" v-if="u.id !== auth.userId">
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
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const API_BASE = ''

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

<style scoped>
.align-center { align-items: center; }
</style>
