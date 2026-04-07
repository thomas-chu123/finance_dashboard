<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-[var(--bg-main)] transition-colors duration-300 p-4">
    <div class="relative z-10 w-full max-w-md bg-[var(--bg-main)] sm:bg-transparent rounded-2xl p-6 sm:p-0 border border-[var(--border-color)] sm:border-none shadow-xl sm:shadow-none">
      <div class="text-center mb-10">
        <div class="flex justify-center mb-6">
          <div class="p-4 bg-[#00df81]/10 rounded-[1.25rem]">
            <Activity class="w-10 h-10 text-[#00df81]" :stroke-width="2" />
          </div>
        </div>
        <h1 class="text-[2rem] leading-tight font-bold bg-gradient-to-r from-[#00df81] to-[#38bdf8] bg-clip-text text-transparent pb-1 tracking-tight">NEXUS<br />Finance Dashboard</h1>
        <p class="text-[var(--text-secondary)] text-sm mt-3 font-medium tracking-wide">Investment Tracking & Backtesting</p>
      </div>

      <!-- Segmented Control for Tabs -->
      <div class="flex mb-8 p-1.5 bg-[var(--bg-sidebar)] rounded-2xl border border-[var(--border-color)]">
        <button :class="['flex-1 py-3 font-bold text-[15px] rounded-xl transition-all duration-200', mode === 'login' ? 'bg-[var(--bg-main)] text-[#00df81] shadow-sm border border-[var(--border-color)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]']" @click="mode = 'login'">登入</button>
        <button :class="['flex-1 py-3 font-bold text-[15px] rounded-xl transition-all duration-200', mode === 'register' ? 'bg-[var(--bg-main)] text-[#00df81] shadow-sm border border-[var(--border-color)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]']" @click="mode = 'register'">註冊</button>
      </div>

      <div v-if="error" class="bg-rose-500/10 text-rose-500 p-3 rounded-xl mb-6 text-sm font-bold border border-rose-500/20 flex items-center justify-center">{{ error }}</div>

      <form @submit.prevent="handleSubmit" class="flex flex-col">
        <div v-if="mode === 'register'" class="space-y-2 mb-6 text-left">
          <label class="block text-[13px] font-bold text-[var(--text-secondary)] ml-1">姓名</label>
          <input v-model="form.displayName" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-[15px] rounded-xl focus:ring-1 focus:ring-[#00df81] focus:border-[#00df81] block p-3.5 outline-none transition-all placeholder:text-[var(--text-secondary)]/50" placeholder="您的姓名" />
        </div>

        <div class="space-y-2 mb-6 text-left">
          <label class="block text-[13px] font-bold text-[var(--text-secondary)] ml-1">電子郵件</label>
          <input v-model="form.email" type="email" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-[15px] rounded-xl focus:ring-1 focus:ring-[#00df81] focus:border-[#00df81] block p-3.5 outline-none transition-all placeholder:text-[var(--text-secondary)]/50" placeholder="example@email.com" required />
        </div>

        <div class="space-y-2 mb-10 text-left">
          <label class="block text-[13px] font-bold text-[var(--text-secondary)] ml-1">密碼</label>
          <input v-model="form.password" type="password" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-[15px] rounded-xl focus:ring-1 focus:ring-[#00df81] focus:border-[#00df81] block p-3.5 outline-none transition-all placeholder:text-[var(--text-secondary)]/50" placeholder="••••••••" required minlength="6" />
        </div>

        <button type="submit" class="w-full flex h-[52px] items-center justify-center gap-2 bg-[#00df81] hover:bg-[#00c974] text-white font-bold text-[17px] rounded-2xl transition-all shadow-[0_4px_20px_rgba(0,223,129,0.35)] hover:shadow-[0_4px_25px_rgba(0,223,129,0.5)] select-none" :disabled="loading">
          <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
          {{ loading ? '處理中...' : (mode === 'login' ? '登入' : '註冊') }}
        </button>

        <!-- Divider -->
        <div class="flex items-center my-6">
          <div class="flex-1 h-[1px] bg-[var(--border-color)]"></div>
          <span class="px-3 text-xs font-bold text-[var(--text-secondary)]">或</span>
          <div class="flex-1 h-[1px] bg-[var(--border-color)]"></div>
        </div>

        <!-- Google OAuth Button -->
        <button 
          type="button"
          @click="handleGoogleSignIn"
          class="w-full flex h-[52px] items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-800 font-bold text-[17px] rounded-2xl transition-all border border-gray-300 shadow-sm hover:shadow-md select-none"
          :disabled="loading"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          使用 Google 登入
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Activity, Loader2 } from 'lucide-vue-next'
import oauthAPI from '../api/oauth'

const router = useRouter()
const route = useRoute()
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

async function handleGoogleSignIn() {
  error.value = ''
  loading.value = true
  try {
    console.log('Initiating Google sign-in...')
    
    // 獲取 Google 登入 URL
    const { login_url } = await oauthAPI.getGoogleLoginUrl()
    
    // 重定向到 Google OAuth 頁面
    window.location.href = login_url
  } catch (e) {
    console.error('Google sign-in failed:', e)
    error.value = e.response?.data?.detail || e.message || 'Google 登入失敗，請重試'
    loading.value = false
  }
}

// 處理 OAuth 回調（當用戶從 Google 重定向回來時）
onMounted(async () => {
  // 檢查是否有 OAuth 回調參數
  const code = route.query.code
  const state = route.query.state
  
  if (code && state) {
    console.log('Processing OAuth callback...')
    loading.value = true
    try {
      // 交換授權碼為 JWT
      const tokenData = await oauthAPI.handleGoogleCallback(code, state)
      
      // 儲存令牌和用戶信息
      localStorage.setItem('access_token', tokenData.access_token)
      localStorage.setItem('user_id', tokenData.user_id)
      localStorage.setItem('user_email', tokenData.email)
      
      // 更新 auth store
      auth.setUser(tokenData.user_id, tokenData.email, tokenData.display_name)
      
      // 清除 URL 中的查詢參數
      router.replace({ path: '/login' })
      
      // 如果是新用戶，顯示歡迎消息
      if (tokenData.is_new_user) {
        alert(`歡迎 ${tokenData.display_name}！帳號建立成功！`)
      }
      
      // 導航到首頁
      setTimeout(() => {
        router.push('/')
      }, 500)
    } catch (e) {
      console.error('OAuth callback failed:', e)
      error.value = e.response?.data?.detail || e.message || 'OAuth 認證失敗，請重試'
      loading.value = false
    }
  }
})

</script>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-30px); }
}

.animate-float {
  animation: float 8s ease-in-out infinite;
}

.animate-delay-\[-4s\] {
  animation-delay: -4s;
}
</style>
