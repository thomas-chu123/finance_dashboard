<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-[var(--bg-main)] transition-colors duration-300">
    <div class="relative z-10 w-full max-w-[420px] p-6">
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
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Activity, Loader2 } from 'lucide-vue-next'

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
