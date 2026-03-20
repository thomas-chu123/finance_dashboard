<template>
  <div class="line-view">
    <div class="header-section">
      <h1 class="page-title">LINE 通知設定</h1>
      <p class="page-subtitle">透過 LINE 接收即時投資提醒，掌握市場脈動</p>
    </div>

    <div class="content-grid">
      <!-- Status Card -->
      <div class="card status-card" :class="{ bound: isBound }">
        <div class="card-header">
          <span class="icon">{{ isBound ? '✅' : '⏳' }}</span>
          <h3>目前狀態</h3>
        </div>
        <div class="status-content">
          <div v-if="isBound" class="status-badge bound">已綁定</div>
          <div v-else class="status-badge unbound">未綁定</div>
          <p v-if="isBound" class="status-text">
            您的帳號已成功連結至 LINE。您將會收到價格觸發通知。
          </p>
          <p v-else class="status-text">
            您尚未連結 LINE 帳號，請按照下方的步驟進行綁定。
          </p>
          <div v-if="isBound && auth.profile?.line_user_id" class="line-id-box">
            <span class="label">LINE User ID:</span>
            <span class="value">{{ auth.profile.line_user_id }}</span>
          </div>
        </div>
      </div>

      <!-- Binding Steps Card -->
      <div class="card steps-card">
        <div class="card-header">
          <span class="icon">🔗</span>
          <h3>綁定步驟</h3>
        </div>
        <div class="steps-content">
          <div class="step-item">
            <div class="step-num">1</div>
            <div class="step-desc">
              <strong>掃描 QR Code</strong>
              <p>使用手機 LINE 掃描右側 QR Code 加入「投資通知系統」好友。</p>
            </div>
          </div>
          <div class="step-item">
            <div class="step-num">2</div>
            <div class="step-desc">
              <strong>生成綁定碼</strong>
              <p>點擊下方的按鈕生成一組 6 位數的暫時性綁定碼。</p>
              <button 
                class="btn btn-primary btn-generate" 
                @click="generateCode" 
                :disabled="loadingCode"
              >
                {{ loadingCode ? '生成中...' : '生成綁定碼' }}
              </button>
            </div>
          </div>
          <div v-if="bindingCode" class="binding-code-display animate-fade-in">
            <div class="code-label">您的綁定碼（10 分鐘內有效）</div>
            <div class="code-value">{{ bindingCode }}</div>
          </div>
          <div class="step-item">
            <div class="step-num">3</div>
            <div class="step-desc">
              <strong>在 LINE 中輸入命令</strong>
              <p>在 LINE 聊天室中輸入：<code class="command-text">bind {{ bindingCode || 'XXXXXX' }}</code></p>
            </div>
          </div>
        </div>
      </div>

      <!-- QR Code Card -->
      <div class="card qrcode-card">
        <div class="card-header">
          <span class="icon">📷</span>
          <h3>掃描加入</h3>
        </div>
        <div class="qrcode-container">
          <img src="@/assets/finance_qrcode.png" alt="LINE QR Code" class="qrcode-img" />
          <p class="qrcode-hint">掃描上方 QR Code 加入好友</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const auth = useAuthStore()
const isBound = computed(() => !!auth.profile?.line_user_id)
const bindingCode = ref('')
const loadingCode = ref(false)

onMounted(async () => {
  if (!auth.profile) {
    await auth.fetchProfile()
  }
})

async function generateCode() {
  loadingCode.value = true
  try {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await axios.post(`${API_BASE_URL}/api/line/binding-code`, {}, {
      headers: { Authorization: `Bearer ${auth.token}` }
    })
    bindingCode.value = res.data.code
  } catch (err) {
    console.error('Failed to generate code:', err)
    alert('無法生成綁定碼，請稍後再試。')
  } finally {
    loadingCode.value = false
  }
}
</script>

<style scoped>
.line-view {
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  margin-bottom: 32px;
}

.page-title {
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: var(--text-muted);
  font-size: 1rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 24px;
}

.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border);
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.status-card.bound {
  border-left: 4px solid var(--success);
}

.status-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 16px;
}

.status-badge.bound {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.status-badge.unbound {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.status-text {
  color: var(--text-secondary);
  line-height: 1.6;
}

.line-id-box {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-app);
  border-radius: 8px;
  font-family: monospace;
  font-size: 0.85rem;
}

.line-id-box .label {
  color: var(--text-muted);
  margin-right: 8px;
}

.line-id-box .value {
  color: var(--purple);
}

.steps-card {
  grid-row: span 2;
}

.step-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.step-num {
  width: 28px;
  height: 28px;
  background: var(--purple-light);
  color: var(--purple);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.step-desc strong {
  display: block;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.step-desc p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
}

.btn-generate {
  margin-top: 12px;
  padding: 8px 16px;
}

.binding-code-display {
  background: linear-gradient(135deg, var(--purple) 0%, #6366f1 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  margin: 16px 0 24px 0;
}

.code-label {
  font-size: 0.8rem;
  opacity: 0.9;
  margin-bottom: 8px;
}

.code-value {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 4px;
}

.command-text {
  background: var(--bg-app);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--accent);
  font-weight: 600;
}

.qrcode-card {
  text-align: center;
}

.qrcode-container {
  padding: 12px;
}

.qrcode-img {
  width: 180px;
  height: 180px;
  margin-bottom: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.qrcode-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  .steps-card {
    grid-row: auto;
  }
}
</style>
