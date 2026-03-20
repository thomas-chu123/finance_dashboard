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
        <div class="profile-layout">
          <div class="profile-fields">
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">顯示姓名</label>
                <input v-model="profileForm.display_name" type="text" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label">LINE User ID</label>
                <div class="flex gap-8">
                  <input v-model="profileForm.line_user_id" type="text" class="form-control" placeholder="未連結" disabled />
                  <span v-if="profileForm.line_user_id" class="badge badge-green align-center flex">已綁定</span>
                </div>
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

            <!-- LINE Binding Logic integrated here -->
            <div class="line-binding-section mt-24">
              <h4 class="mb-12">🔗 LINE 帳號綁定</h4>
              <div class="flex gap-16 align-start wrap">
                <div class="binding-controls flex-1">
                  <div v-if="profileForm.line_user_id" class="mb-16">
                    <p class="text-sm text-green fw-600 mb-8">✅ 您的帳號已與 LINE 連結</p>
                    <button class="btn btn-danger btn-sm" @click="unlinkLine">🚫 解除綁定</button>
                  </div>
                  <div v-else>
                    <p class="text-sm text-muted mb-16">
                      點擊下方按鈕生成綁定碼，並在 LINE 聊天室輸入 <code>bind [綁定碼]</code>。
                    </p>
                    <button 
                      class="btn btn-outline btn-sm mb-16" 
                      @click="generateLineCode" 
                      :disabled="loadingCode"
                    >
                      {{ loadingCode ? '生成中...' : '✨ 生成綁定碼' }}
                    </button>
                  </div>
                  
                  <div v-if="lineBindingCode" class="binding-code-box animate-fade-in">
                    <div class="code-label">您的綁定碼：</div>
                    <div class="code-value">{{ lineBindingCode }}</div>
                    <div class="code-expiry">⏱️ 10 分鐘內有效</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="profile-sidebar">
            <div class="qrcode-card">
              <img src="@/assets/finance_qrcode.png" alt="LINE QR Code" class="qrcode-img" />
              <p class="text-xs text-muted text-center mt-8">掃描加入 LINE 投資通知系統</p>
            </div>
          </div>
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

const lineBindingCode = ref('')
const loadingCode = ref(false)

async function generateLineCode() {
  loadingCode.value = true
  try {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await axios.post(`${API_BASE_URL}/api/line/binding-code`, {}, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    lineBindingCode.value = res.data.code
  } catch (err) {
    console.error('Failed to generate code:', err)
    alert('無法生成綁定碼，請稍後再試。')
  } finally {
    loadingCode.value = false
  }
}

async function unlinkLine() {
  if (!confirm('確定要解除 LINE 帳號綁定嗎？解除後將無法接收 LINE 通知。')) return
  try {
    await auth.updateProfile({ line_user_id: null, notify_line: false })
    alert('LINE 帳號已解除綁定。')
  } catch (err) {
    alert('解除綁定失敗：' + (err.response?.data?.detail || err.message))
  }
}

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
.profile-layout {
  display: flex;
  gap: 32px;
}
.profile-fields {
  flex: 1;
}
.profile-sidebar {
  width: 200px;
  flex-shrink: 0;
}
.qrcode-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  background: var(--bg-app);
}
.qrcode-img {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 4px;
}
.binding-code-box {
  background: rgba(139, 92, 246, 0.1);
  border-radius: 8px;
  padding: 16px 24px;
  text-align: center;
  border: 1px dashed var(--purple);
  width: fit-content;
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.1);
}
.btn-outline {
  background: transparent;
  border: 1px solid var(--purple);
  color: var(--purple);
}
.btn-outline:hover {
  background: rgba(139, 92, 246, 0.1);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.2);
}
.code-label {
  font-size: 0.75rem;
  color: var(--purple);
  margin-bottom: 4px;
}
.code-value {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 2px;
  color: var(--purple);
}
.code-expiry {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 4px;
}
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
.wrap { flex-wrap: wrap; }
@media (max-width: 768px) {
  .profile-layout { flex-direction: column; }
  .profile-sidebar { width: 100%; order: -1; }
  .qrcode-img { width: 150px; margin: 0 auto; display: block; }
}
</style>
