<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-[var(--bg-secondary)] transition-colors duration-300 p-4">
    <div class="relative z-10 w-full max-w-[420px] bg-[var(--bg-primary)] rounded-[24px] p-10 border border-[var(--border-color)] shadow-[0_10px_25px_rgba(0,0,0,0.05)] text-center">
      <!-- Brand Header -->
      <div class="mb-8">
        <div class="w-14 h-14 bg-[#00D084] rounded-full flex justify-center items-center mx-auto mb-4 text-white text-2xl font-bold shadow-[0_4px_12px_rgba(0,208,132,0.2)]">N</div>
        <h1 class="m-0 text-[28px] font-bold tracking-wider text-[#00D084]">NEXUS</h1>
        <p class="mt-1 text-[var(--text-secondary)] text-sm font-medium">Finance Dashboard</p>
      </div>

      <!-- Tab Group (Segmented Control) -->
      <div class="flex bg-[var(--bg-sidebar)] p-1 rounded-xl mb-7.5 border border-[var(--border-color)]">
        <button 
          :class="['flex-1 py-2.5 text-[15px] font-semibold rounded-lg transition-all duration-300', mode === 'login' ? 'bg-[var(--bg-primary)] text-[#00D084] shadow-[0_2px_8px_rgba(0,0,0,0.05)] border border-[var(--border-color)]' : 'text-[var(--text-secondary)] hover:text-[#00D084]']" 
          @click="mode = 'login'"
        >登入</button>
        <button 
          :class="['flex-1 py-2.5 text-[15px] font-semibold rounded-lg transition-all duration-300', mode === 'register' ? 'bg-[var(--bg-primary)] text-[#00D084] shadow-[0_2px_8px_rgba(0,0,0,0.05)] border border-[var(--border-color)]' : 'text-[var(--text-secondary)] hover:text-[#00D084]']" 
          @click="mode = 'register'"
        >註冊</button>
      </div>

      <div v-if="error" class="bg-rose-500/10 text-rose-500 p-3 rounded-xl mb-6 text-sm font-bold border border-rose-500/20 flex items-center justify-center text-center">{{ error }}</div>

      <form @submit.prevent="handleSubmit" class="flex flex-col">
        <div v-if="mode === 'register'" class="mb-5 text-left">
          <label class="block text-sm font-semibold mb-2 text-[var(--text-primary)]">姓名</label>
          <input v-model="form.displayName" type="text" class="w-full p-3 border-[1.5px] border-[var(--border-color)] rounded-xl text-base box-border transition-all bg-[var(--input-bg)] outline-none focus:border-[#00D084] focus:shadow-[0_0_0_4px_rgba(0,208,132,0.1)] text-[var(--text-primary)]" placeholder="您的姓名" />
        </div>

        <div class="mb-5 text-left">
          <label class="block text-sm font-semibold mb-2 text-[var(--text-primary)]">電子郵件</label>
          <input v-model="form.email" type="email" class="w-full p-3 border-[1.5px] border-[var(--border-color)] rounded-xl text-base box-border transition-all bg-[var(--input-bg)] outline-none focus:border-[#00D084] focus:shadow-[0_0_0_4px_rgba(0,208,132,0.1)] text-[var(--text-primary)]" placeholder="example@email.com" required />
        </div>

        <div class="mb-8 text-left">
          <label class="block text-sm font-semibold mb-2 text-[var(--text-primary)]">密碼</label>
          <input v-model="form.password" type="password" class="w-full p-3 border-[1.5px] border-[var(--border-color)] rounded-xl text-base box-border transition-all bg-[var(--input-bg)] outline-none focus:border-[#00D084] focus:shadow-[0_0_0_4px_rgba(0,208,132,0.1)] text-[var(--text-primary)]" placeholder="••••••••" required minlength="6" />
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

      <div class="mt-5 text-[13px] text-[var(--text-secondary)]">
        <button @click="showForgotPassword = true" class="text-[#00D084] no-underline hover:underline bg-none border-none cursor-pointer p-0">忘記密碼？</button>
      </div>
    </div>

    <!-- Forgot Password Modal -->
    <ForgotPasswordModal 
      :isOpen="showForgotPassword" 
      @close="showForgotPassword = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Activity, Loader2 } from 'lucide-vue-next'
import axios from 'axios'
import oauthAPI from '../api/oauth'
import ForgotPasswordModal from '../components/ForgotPasswordModal.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const mode = ref('login')
const loading = ref(false)
const error = ref('')
const showForgotPassword = ref(false)
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
    console.log('Code:', code.substring(0, 30) + '...')
    console.log('State:', state.substring(0, 30) + '...')
    loading.value = true
    try {
      // 呼叫後端的新端點進行完整的 OAuth 交換
      // 使用 GET 請求，將參數作為查詢參數傳遞
      const tokenData = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || ''}/api/auth/oauth/google/complete-callback`,
        {
          params: { code, state }
        }
      )
      
      console.log('OAuth exchange successful:', tokenData.data)
      
      // 儲存令牌和用戶信息
      localStorage.setItem('access_token', tokenData.data.access_token)
      localStorage.setItem('user_id', tokenData.data.user_id)
      localStorage.setItem('user_email', tokenData.data.email)
      
      // 更新 auth store
      auth.setUser(tokenData.data.user_id, tokenData.data.email, tokenData.data.display_name)
      
      // 清除 URL 中的查詢參數
      router.replace({ path: '/login' })
      
      // 如果是新用戶，顯示歡迎消息
      if (tokenData.data.is_new_user) {
        alert(`歡迎 ${tokenData.data.display_name}！帳號建立成功！`)
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
/* Keeping original scoped styles in case needed, but mostly relying on the refined utility classes */
</style>
