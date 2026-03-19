<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="glow glow-1"></div>
      <div class="glow glow-2"></div>
    </div>

    <div class="login-card">
      <div class="login-logo">
        <div class="logo-icon">📊</div>
        <h1 class="logo-text">Finance Dashboard</h1>
        <p class="logo-sub">Investment Tracking & Backtesting</p>
      </div>

      <div class="tabs">
        <button :class="['tab', { active: mode === 'login' }]" @click="mode = 'login'">登入</button>
        <button :class="['tab', { active: mode === 'register' }]" @click="mode = 'register'">註冊</button>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div v-if="mode === 'register'" class="form-group">
          <label class="form-label">姓名</label>
          <input v-model="form.displayName" type="text" class="form-control" placeholder="您的姓名" />
        </div>

        <div class="form-group">
          <label class="form-label">電子郵件</label>
          <input v-model="form.email" type="email" class="form-control" placeholder="example@email.com" required />
        </div>

        <div class="form-group">
          <label class="form-label">密碼</label>
          <input v-model="form.password" type="password" class="form-control" placeholder="••••••••" required minlength="6" />
        </div>

        <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:16px;height:16px;"></span>
          {{ loading ? '處理中...' : (mode === 'login' ? '登入' : '建立帳號') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref('login')
const loading = ref(false)
const error = ref('')
const form = reactive({ email: '', password: '', displayName: '' })

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.email, form.password)
      router.push('/')
    } else {
      await auth.register(form.email, form.password, form.displayName)
      mode.value = 'login'
      error.value = ''
      alert('帳號建立成功，請登入！')
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '操作失敗'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg { position: absolute; inset: 0; }

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
  animation: float 8s ease-in-out infinite;
}

.glow-1 {
  width: 500px;
  height: 500px;
  background: var(--accent);
  top: -100px;
  left: -100px;
}

.glow-2 {
  width: 400px;
  height: 400px;
  background: var(--purple);
  bottom: -100px;
  right: -100px;
  animation-delay: -4s;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-30px); }
}

.login-card {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px;
  width: 100%;
  max-width: 420px;
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
}

.login-logo { text-align: center; margin-bottom: 28px; }
.logo-icon { font-size: 2.5rem; margin-bottom: 8px; }
.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-sub { color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; }

.tabs { display: flex; gap: 0; margin-bottom: 24px; border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.tab {
  flex: 1;
  padding: 9px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.tab.active { background: var(--accent); color: white; }

.login-form { display: flex; flex-direction: column; gap: 0; }
.w-full { width: 100%; justify-content: center; margin-top: 8px; }
</style>
