<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <div class="flex items-center gap-3 mb-2">
      <div class="p-2 bg-brand-500/10 rounded-lg group-hover:bg-brand-500/20 transition-colors">
        <MessageCircle class="w-6 h-6 text-brand-500" />
      </div>
      <div>
        <h1 class="text-2xl font-bold text-[var(--text-primary)]">LINE 通知設定</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">透過 LINE 接收即時投資提醒，掌握市場脈動</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Status Card -->
      <div class="glass-card rounded-2xl overflow-hidden transition-all shadow-sm hover:shadow-md" :class="{ 'border-l-4 border-l-brand-500': isBound }">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center gap-2 bg-[var(--bg-sidebar)]/50">
          <CheckCircle2 v-if="isBound" class="w-5 h-5 text-brand-500" />
          <Loader2 v-else class="w-5 h-5 text-amber-500 animate-spin" />
          <h3>目前狀態</h3>
        </div>
        <div class="p-6">
          <span v-if="isBound" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-500/10 text-brand-500 border border-brand-500/20">
            <CheckCircle2 class="w-3.5 h-3.5" />已綁定
          </span>
          <div v-else class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-amber-500/10 text-amber-500 mb-4 gap-1.5 border border-amber-500/20">
            <div class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></div>未綁定
          </div>
          <p v-if="isBound" class="text-[var(--text-muted)] text-sm leading-relaxed">
            您的帳號已成功連結至 LINE。您將會收到價格觸發通知。
          </p>
          <p v-else class="text-[var(--text-muted)] text-sm leading-relaxed">
            您尚未連結 LINE 帳號，請按照右側的步驟進行綁定。
          </p>
          
          <div v-if="isBound && auth.profile?.line_user_id" class="mt-6 p-3 bg-[var(--bg-main)]/50 rounded-xl font-mono text-xs flex items-center overflow-x-auto border border-[var(--border-color)] shadow-inner">
            <span class="text-[var(--text-muted)] mr-2 shrink-0 select-none font-sans font-medium text-sm">LINE User ID:</span>
            <span class="text-brand-500 whitespace-nowrap font-bold select-all tracking-wide flex-1 break-all min-w-0">{{ auth.profile.line_user_id }}</span>
          </div>
        </div>
      </div>

      <!-- Binding Steps Card -->
      <div class="glass-card rounded-2xl overflow-hidden transition-all shadow-sm hover:shadow-md md:row-span-2">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center gap-2 bg-[var(--bg-sidebar)]/50">
          <LinkIcon class="w-5 h-5 text-brand-500" />
          <h3>綁定步驟</h3>
        </div>
        <div class="p-6">
          <div class="flex gap-4 mb-8">
            <div class="w-8 h-8 shrink-0 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center font-bold shadow-sm border border-brand-500/20">1</div>
            <div class="text-sm text-[var(--text-muted)] leading-relaxed pt-1">
              <strong class="block mb-1 text-[var(--text-primary)] text-base">掃描 QR Code</strong>
              <p class="m-0 mt-1">使用手機 LINE 掃描左下角的 QR Code 加入「投資通知系統」為好友。</p>
            </div>
          </div>
          <div class="flex gap-4 mb-8">
            <div class="w-8 h-8 shrink-0 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center font-bold shadow-sm border border-brand-500/20">2</div>
            <div class="text-sm text-[var(--text-muted)] leading-relaxed pt-1">
              <strong class="block mb-1 text-[var(--text-primary)] text-base">生成綁定碼</strong>
              <p class="m-0 mt-1 mb-3">點擊下方按鈕，系統將生成一組 6 位數暫時綁定碼。</p>
              <button 
                class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold rounded-lg transition-all shadow-sm hover:shadow active:scale-95 flex items-center gap-2" 
                @click="generateCode" 
                :disabled="loadingCode"
              >
                <Loader2 v-if="loadingCode" class="w-4 h-4 animate-spin" />
                <RefreshCcw v-else class="w-4 h-4" />
                {{ loadingCode ? '生成中...' : '生成綁定碼' }}
              </button>
            </div>
          </div>
          
          <div v-if="bindingCode" class="ml-12 mb-8 bg-gradient-to-br from-brand-500 to-brand-700 text-white p-5 rounded-2xl text-center animate-[fadeIn_0.4s_ease-out] shadow-md border border-brand-400/30 relative overflow-hidden">
            <div class="absolute inset-0 bg-white/5 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] opacity-20"></div>
            <div class="relative z-10">
              <div class="text-[10px] font-bold tracking-widest text-brand-100 uppercase mb-2">專屬綁定碼（10 分鐘有效）</div>
              <div class="text-3xl font-black tracking-[0.25em] font-mono drop-shadow-sm select-all">{{ bindingCode }}</div>
            </div>
          </div>

          <div class="flex gap-4">
            <div class="w-8 h-8 shrink-0 bg-brand-500/10 text-brand-500 rounded-full flex items-center justify-center font-bold shadow-sm border border-brand-500/20">3</div>
            <div class="text-sm text-[var(--text-muted)] leading-relaxed pt-1">
              <strong class="block mb-1 text-[var(--text-primary)] text-base">在 LINE 輸入指令</strong>
              <p class="m-0 mt-1">在 LINE 聊天室中傳送：<br/>
                <code class="inline-block mt-2 bg-[var(--input-bg)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg text-brand-500 font-mono text-sm shadow-inner select-all">bind {{ bindingCode || 'XXXXXX' }}</code>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- QR Code Card -->
      <div class="glass-card rounded-2xl overflow-hidden transition-all shadow-sm hover:shadow-md text-center">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center gap-2 bg-[var(--bg-sidebar)]/50">
          <QrCode class="w-5 h-5 text-brand-500" />
          <h3>掃描加入與綁定</h3>
        </div>
        <div class="p-8 flex flex-col items-center justify-center">
          <qrcode-vue
            v-if="qrCodeUrl"
            :value="qrCodeUrl"
            :size="180"
            level="M"
            class="mb-6 border-[6px] border-white rounded-xl shadow-sm bg-white"
          />
          <div v-else class="w-[180px] h-[180px] mb-6 border-2 border-dashed border-[var(--border-color)] rounded-xl flex items-center justify-center bg-[var(--bg-main)]/50 text-sm text-[var(--text-muted)]">
            <div class="flex flex-col items-center gap-2">
              <div class="p-1.5 bg-brand-500/10 rounded-lg">
                <Bell class="w-4 h-4 text-brand-500" />
              </div>
              <span class="font-medium text-[var(--text-muted)]">請先生成綁定碼</span>
            </div>
          </div>
          <p class="text-[13px] text-[var(--text-muted)] max-w-[220px] leading-relaxed">
            掃描 QR Code 開啟 LINE，將自動為您帶入綁定指令。
          </p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore, API_BASE_URL } from '../stores/auth'
import axios from 'axios'
import QrcodeVue from 'qrcode.vue'
import { CheckCircle2, Loader2, Link as LinkIcon, QrCode, RefreshCcw, MessageCircle } from 'lucide-vue-next'

const auth = useAuthStore()
const isBound = computed(() => !!auth.profile?.line_user_id)
const bindingCode = ref('')
const loadingCode = ref(false)

const qrCodeUrl = computed(() => {
  if (!bindingCode.value) return ''
  const botBasicId = '@295pqnho'
  // Format: https://line.me/R/oaMessage/{bot_id}/?{message}
  return `https://line.me/R/oaMessage/${botBasicId}/?bind%20${bindingCode.value}`
})

onMounted(async () => {
  if (!auth.profile) {
    await auth.fetchProfile()
  }
  
  // Auto-generate code if not bound as requested by user
  if (!isBound.value && !bindingCode.value) {
    generateCode()
  }

  // Start polling
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

let pollInterval = null

function startPolling() {
  stopPolling()
  pollInterval = setInterval(async () => {
    if (!isBound.value) {
      await auth.fetchProfile()
    } else {
      stopPolling()
    }
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function generateCode() {
  loadingCode.value = true
  try {
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
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
