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

        <button type="submit" class="w-full p-3.5 bg-[#00D084] hover:bg-[#00b372] text-white rounded-xl text-base font-semibold cursor-pointer transition-all mt-2 shadow-[0_4px_15px_rgba(0,208,132,0.2)] hover:-translate-y-[1px] active:translate-y-0 flex items-center justify-center" :disabled="loading"><Loader2 v-if="loading" class="w-5 h-5 animate-spin mr-2" />{{ loading ? '處理中...' : (mode === 'login' ? '登入系統' : '註冊帳號') }}</button>
      </form>

      <div class="mt-5 text-[13px] text-[var(--text-secondary)]">
        <a href="#" class="text-[#00D084] no-underline hover:underline">忘記密碼？</a>
      </div>
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
/* Keeping original scoped styles in case needed, but mostly relying on the refined utility classes */
</style>
