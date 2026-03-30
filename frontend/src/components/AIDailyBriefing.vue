<template>
  <div class="p-6">
    <!-- 標題列 -->
    <div class="border-b border-[var(--border-color)] pb-4 mb-5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <h3 class="font-bold text-lg text-[var(--text-primary)]">🤖 AI 市場早報</h3>
        <span v-if="briefingStore.sessionTime" class="text-[11px] font-medium text-brand-700 dark:text-brand-400 bg-brand-500/10 rounded-md px-2 py-0.5">
          {{ formattedSessionTime }}
        </span>
      </div>
      <button
        @click="handleRefresh"
        :disabled="refreshing || briefingStore.loading"
        class="p-1.5 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-40"
        title="手動刷新早報"
      >
        <svg :class="['w-4 h-4', (refreshing || briefingStore.loading) ? 'animate-spin' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="briefingStore.loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-800 h-24"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="briefingStore.error" class="flex items-start gap-2 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <span class="text-red-500 text-lg">⚠️</span>
      <div>
        <p class="text-sm font-medium text-red-700 dark:text-red-400">早報載入失敗</p>
        <p class="text-xs text-red-500 dark:text-red-500 mt-0.5">{{ briefingStore.error }}</p>
      </div>
    </div>

    <!-- 無資料 -->
    <div v-else-if="!briefingStore.items.length" class="py-10 text-center text-zinc-500 text-sm">
      <p class="text-2xl mb-2">📰</p>
      <p>尚無早報資料</p>
      <p class="text-xs mt-1">排程於每日 08:00、13:00、18:00 自動生成</p>
    </div>

    <!-- 早報列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="item in briefingStore.items"
        :key="item.symbol"
        class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-main)]/50 overflow-hidden"
      >
        <!-- Symbol header -->
        <div class="flex items-start justify-between gap-3 p-4">
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-xs font-bold px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-700 dark:text-brand-400 uppercase tracking-wider">
              {{ item.symbol }}
            </span>
            <span class="text-sm text-[var(--text-primary)] font-medium">{{ item.symbol_name }}</span>
          </div>
          <!-- status badge -->
          <span
            v-if="item.status === 'failed'"
            class="shrink-0 text-[10px] px-1.5 py-0.5 rounded border border-red-400 dark:border-red-500 text-red-500 dark:text-red-400 font-medium"
          >生成失敗</span>
        </div>

        <!-- AI 摘要 -->
        <div class="px-4 pb-3">
          <p
            v-if="item.summary_text"
            class="text-sm text-[var(--text-primary)] leading-relaxed"
            v-html="renderSummary(item.summary_text)"
          ></p>
          <p v-else class="text-sm text-zinc-400 italic">無摘要</p>
        </div>

        <!-- 展開/收合新聞清單 -->
        <div v-if="item.news_json && item.news_json.length" class="border-t border-[var(--border-color)]">
          <button
            @click="toggleNews(item.symbol)"
            class="w-full flex items-center justify-between px-4 py-2 text-xs text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
          >
            <span>📰 相關新聞（{{ item.news_json.length }} 則）</span>
            <svg :class="['w-3 h-3 transition-transform', expandedSymbols.has(item.symbol) ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="expandedSymbols.has(item.symbol)" class="px-4 pb-3 space-y-2">
            <div v-for="(news, idx) in item.news_json" :key="idx" class="text-xs border-l-2 border-brand-300 dark:border-brand-700 pl-3">
              <a
                :href="news.url"
                target="_blank"
                rel="noopener noreferrer"
                class="font-medium text-brand-600 dark:text-brand-400 hover:underline line-clamp-1"
              >{{ news.title }}</a>
              <p class="text-zinc-500 mt-0.5 line-clamp-2">{{ news.description?.slice(0, 80) }}{{ news.description?.length > 80 ? '...' : '' }}</p>
              <p v-if="news.published_date" class="text-zinc-400 mt-0.5">{{ news.published_date }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBriefingStore } from '../stores/briefing'

const briefingStore = useBriefingStore()
const expandedSymbols = ref(new Set())
const refreshing = ref(false)

const formattedSessionTime = computed(() => {
  if (!briefingStore.sessionTime) return ''
  const d = new Date(briefingStore.sessionTime)
  return d.toLocaleString('zh-TW', {
    timeZone: 'Asia/Taipei',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
})

function toggleNews(symbol) {
  if (expandedSymbols.value.has(symbol)) {
    expandedSymbols.value.delete(symbol)
  } else {
    expandedSymbols.value.add(symbol)
  }
  // 觸發響應性更新
  expandedSymbols.value = new Set(expandedSymbols.value)
}

/** 安全轉義 HTML 特殊字元 */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 將 summary_text 中的編號引用 [N] 轉為可點擊超連結上標。
 * 格式預期：文字[1]文字[2]\n\n參考來源：\n[1] url1\n[2] url2
 */
function renderSummary(text) {
  if (!text) return ''

  const REFS_HEADER = '\n\n參考來源：\n'
  const sepIdx = text.indexOf(REFS_HEADER)
  let mainText = text
  const refMap = {}

  if (sepIdx !== -1) {
    mainText = text.slice(0, sepIdx)
    const refLines = text.slice(sepIdx + REFS_HEADER.length).split('\n')
    for (const line of refLines) {
      const m = line.match(/^\[(\d+)\]\s+(https?:\/\/\S+)$/)
      if (m) refMap[m[1]] = m[2]
    }
  }

  // 先 escape 主文 HTML，再將 [N] 插入超連結
  const html = escapeHtml(mainText).replace(/\[(\d+)\]/g, (_, n) => {
    const url = refMap[n]
    if (!url) return `[${n}]`
    return `<sup><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="text-brand-500 hover:text-brand-400">[${n}]</a></sup>`
  })

  return html
}

async function handleRefresh() {
  refreshing.value = true
  try {
    await briefingStore.triggerRefresh()
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  briefingStore.fetchLatestBriefing()
})
</script>
