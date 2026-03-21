<template>
  <div class="max-w-4xl mx-auto">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">LINE 通知設定</h1>
      <p class="text-gray-500 dark:text-gray-400">透過 LINE 接收即時投資提醒，掌握市場脈動</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Status Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-[var(--border-color)] shadow-sm transition-all hover:shadow-md" :class="{ 'border-l-4 border-l-emerald-500': isBound }">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-gray-900 dark:text-white flex items-center justify-between">
          <span class="icon"><CheckCircle2 v-if="isBound" class="w-5 h-5 text-emerald-500" /><Loader2 v-else class="w-5 h-5 text-amber-500 animate-spin" /></span>
          <h3>目前狀態</h3>
        </div>
        <div class="p-6">
          <div v-if="isBound" class="inline-block px-4 py-1.5 rounded-full text-sm font-semibold bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400 mb-4">已綁定</div>
          <div v-else class="inline-block px-4 py-1.5 rounded-full text-sm font-semibold bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-500 mb-4">未綁定</div>
          <p v-if="isBound" class="text-gray-600 dark:text-gray-400 leading-relaxed">
            您的帳號已成功連結至 LINE。您將會收到價格觸發通知。
          </p>
          <p v-else class="text-gray-600 dark:text-gray-400 leading-relaxed">
            您尚未連結 LINE 帳號，請按照下方的步驟進行綁定。
          </p>
          <div v-if="isBound && auth.profile?.line_user_id" class="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg font-mono text-sm">
            <span class="text-gray-500 dark:text-gray-400 mr-2">LINE User ID:</span>
            <span class="text-indigo-600 dark:text-indigo-400 break-all">{{ auth.profile.line_user_id }}</span>
          </div>
        </div>
      </div>

      <!-- Binding Steps Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-[var(--border-color)] shadow-sm transition-all hover:shadow-md md:row-span-2">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-gray-900 dark:text-white flex items-center justify-between">
          <LinkIcon class="w-5 h-5 text-gray-500 font-semibold" />
          <h3>綁定步驟</h3>
        </div>
        <div class="p-6">
          <div class="flex gap-4 mb-6">
            <div class="w-7 h-7 shrink-0 bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400 rounded-full flex items-center justify-center font-bold">1</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              <strong class="block mb-1 text-gray-900 dark:text-white text-base">掃描 QR Code</strong>
              <p class="m-0 text-gray-600 dark:text-gray-400 mt-1">使用手機 LINE 掃描右側 QR Code 加入「投資通知系統」好友。</p>
            </div>
          </div>
          <div class="flex gap-4 mb-6">
            <div class="w-7 h-7 shrink-0 bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400 rounded-full flex items-center justify-center font-bold">2</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              <strong class="block mb-1 text-gray-900 dark:text-white text-base">生成綁定碼</strong>
              <p class="m-0 text-gray-600 dark:text-gray-400 mt-1">點擊下方的按鈕生成一組 6 位數的暫時性綁定碼。</p>
              <button 
                class="px-4 py-2 mt-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm" 
                @click="generateCode" 
                :disabled="loadingCode"
              >
                {{ loadingCode ? '生成中...' : '生成綁定碼' }}
              </button>
            </div>
          </div>
          <div v-if="bindingCode" class="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white p-5 rounded-xl text-center my-4 animate-[fadeIn_0.4s_ease-out]">
            <div class="text-xs opacity-90 mb-2">您的綁定碼（10 分鐘內有效）</div>
            <div class="text-3xl font-extrabold tracking-[0.25em]">{{ bindingCode }}</div>
            <p style="font-size: 0.85rem; margin-top: 12px; opacity: 0.8;">請掃描右側 QR Code，將自動帶入綁定指令</p>
          </div>
          <div class="flex gap-4 mb-6">
            <div class="w-7 h-7 shrink-0 bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400 rounded-full flex items-center justify-center font-bold">3</div>
            <div class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
              <strong class="block mb-1 text-gray-900 dark:text-white text-base">在 LINE 中輸入命令</strong>
              <p class="m-0 text-gray-600 dark:text-gray-400 mt-1">在 LINE 聊天室中輸入：<code class="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded text-indigo-600 dark:text-indigo-400 font-semibold">bind {{ bindingCode || 'XXXXXX' }}</code></p>
            </div>
          </div>
        </div>
      </div>

      <!-- QR Code Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-[var(--border-color)] shadow-sm transition-all hover:shadow-md text-center">
        <div class="p-4 border-b border-[var(--border-color)] font-semibold text-gray-900 dark:text-white flex items-center justify-between">
          <QrCode class="w-5 h-5 text-gray-500 font-semibold" />
          <h3>掃描加入與綁定</h3>
        </div>
        <div class="p-4 flex flex-col items-center">
          <qrcode-vue
            v-if="qrCodeUrl"
            :value="qrCodeUrl"
            :size="200"
            level="M"
            class="mb-3 border-4 border-white rounded-lg shadow-sm"
          />
          <div v-else class="w-[200px] h-[200px] mb-3 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
            <p>請先點擊左側「生成綁定碼」</p>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400 text-center">使用 LINE 掃描，加入好友並自動預填綁定指令</p>
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
import { CheckCircle2, Loader2, Link as LinkIcon, QrCode } from 'lucide-vue-next'

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
