<template>
  <div class="p-6">
    <!-- 標題列 -->
    <div class="border-b border-[var(--border-color)] pb-4 mb-5 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <h3 class="font-bold text-lg text-[var(--text-primary)]">🤖 {{ $t('pages.briefing') }}</h3>
        <span v-if="briefingStore.sessionTime" class="text-[11px] font-medium text-brand-700 dark:text-brand-400 bg-brand-500/10 rounded-md px-2 py-0.5">
          {{ formattedSessionTime }}
        </span>
      </div>
      <button
        @click="handleRefresh"
        :disabled="refreshing || briefingStore.loading"
        class="p-1.5 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 disabled:opacity-40"
        :title="$t('briefing.refresh')"
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
        <p class="text-sm font-medium text-red-700 dark:text-red-400">{{ $t('briefing.loadFailed') }}</p>
        <p class="text-xs text-red-500 dark:text-red-500 mt-0.5">{{ briefingStore.error }}</p>
      </div>
    </div>

    <!-- 無資料 -->
    <div v-else-if="!briefingStore.items.length" class="py-10 text-center text-zinc-500 text-sm">
      <p class="text-2xl mb-2">📰</p>
      <p>{{ $t('briefing.empty') }}</p>
      <p class="text-xs mt-1">{{ $t('briefing.schedule') }}</p>
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
              {{ displaySymbol(item) }}
            </span>
            <span class="text-sm text-[var(--text-primary)] font-medium">{{ displayName(item) }}</span>
          </div>
          <!-- status badge -->
          <span
            v-if="item.status === 'failed'"
            class="shrink-0 text-[10px] px-1.5 py-0.5 rounded border border-red-400 dark:border-red-500 text-red-500 dark:text-red-400 font-medium"
          >{{ $t('briefing.generationFailed') }}</span>
        </div>

        <!-- AI 摘要 -->
        <div class="px-4 pb-3">
          <div
            v-if="item.summary_text"
            class="briefing-summary text-sm text-[var(--text-primary)] leading-relaxed"
            v-html="renderSummary(item.summary_text)"
          ></div>
          <p v-else class="text-sm text-zinc-400 italic">{{ $t('briefing.noSummary') }}</p>
        </div>

        <!-- 展開/收合新聞清單 -->
        <div v-if="item.news_json && item.news_json.length" class="border-t border-[var(--border-color)]">
          <button
            @click="toggleNews(item.symbol)"
            class="w-full flex items-center justify-between px-4 py-2 text-xs text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
          >
            <span>📰 {{ $t('briefing.relatedNews') }}（{{ item.news_json.length }} {{ $t('briefing.articles') }}）</span>
            <svg :class="['w-3 h-3 transition-transform', expandedSymbols.has(item.symbol) ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="expandedSymbols.has(item.symbol)" class="px-4 pb-3 space-y-2">
            <div v-for="(news, idx) in item.news_json" :key="idx" class="text-xs border-l-2 border-brand-300 dark:border-brand-700 pl-3">
              <a
                v-if="news.url"
                :href="news.url"
                target="_blank"
                rel="noopener noreferrer"
                class="font-medium text-brand-600 dark:text-brand-400 hover:underline line-clamp-1"
              >{{ news.title }}</a>
              <p v-else class="font-medium text-[var(--text-primary)] line-clamp-2">{{ news.title }}</p>
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
import { useLocale } from '../composables/useLocale'

const briefingStore = useBriefingStore()
const { locale, t } = useLocale()
const expandedSymbols = ref(new Set())
const refreshing = ref(false)

const formattedSessionTime = computed(() => {
  if (!briefingStore.sessionTime) return ''
  const d = new Date(briefingStore.sessionTime)
  return d.toLocaleString(locale.value, {
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

function displaySymbol(item) {
  if (item.symbol === 'AI_WEEK') return t('briefing.thisWeek')
  if (item.symbol === 'AI_TW_FCST') return t('briefing.taiwanStocks')
  return item.symbol
}

function displayName(item) {
  if (item.symbol === 'AI_WEEK') return t('briefing.weeklyMarketEvents')
  if (item.symbol === 'AI_TW_FCST') return t('briefing.taiwanMarketForecast')
  return item.symbol_name || item.symbol
}

/** 安全轉義 HTML 特殊字元 */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function decodeBasicEntities(str) {
  return str
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/g, "'")
}

function normalizeSummaryText(text) {
  return decodeBasicEntities(String(text))
    .replace(/\r\n?/g, '\n')
    .replace(/<\s*br\s*\/?\s*>/gi, '\n')
    .replace(/<\s*(strong|b)\b[^>]*>/gi, '**')
    .replace(/<\s*\/\s*(strong|b)\s*>/gi, '**')
    .replace(/<\s*(em|i)\b[^>]*>/gi, '*')
    .replace(/<\s*\/\s*(em|i)\s*>/gi, '*')
    .replace(/<\s*h[1-6]\b[^>]*>/gi, '\n**')
    .replace(/<\s*\/\s*h[1-6]\s*>/gi, '**\n')
    .replace(/<\s*\/\s*(p|div|li|tr|h[1-6]|section|article)\s*>/gi, '\n')
    .replace(/<\s*(p|div|li|tr|h[1-6]|section|article|ul|ol|table|tbody|thead)\b[^>]*>/gi, '\n')
    .replace(/<\s*\/?\s*(td|th)\b[^>]*>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/\\\((.*?)\\\)/g, '$1')
    .replace(/\$\s*([^$]+?)\s*\$/g, '$1')
    .replace(/\\text\{([^}]+)\}/g, '$1')
    .replace(/\\approx/g, '約')
    .replace(/\\times/g, 'x')
    .replace(/\\div/g, '/')
    .replace(/\\rightarrow/g, '->')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\s*---+\s*/g, '\n')
    .replace(/\s+([#]{2,6}\s+)/g, '\n$1')
    .replace(/([^\n])(\s*#{2,6}\s+)/g, '$1\n$2')
    .replace(/\s+(?=\d+\.\s*(?:事件|Step|步驟|預測|開盤|收盤|結論|總結)[：:])/g, '\n')
    .replace(/\s+(?=\d+\.\s*事件\s*[：:])/g, '\n')
    .replace(/\s+(?=[*]\s*(?:\*\*)?[\u4e00-\u9fffA-Za-z0-9^$（(][^*\n]{1,60}(?:\*\*)?\s*[：:])/g, '\n')
    .replace(/\s+(?=【[^】]{1,24}】)/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function renderInlineMarkdown(text, refMap) {
  let html = escapeHtml(text)

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/(?<!\*)\*([^*\n]{2,80})\*(?!\*)/g, '<strong>$1</strong>')
  html = html.replace(/\[(\d+)\]/g, (_, n) => {
    const url = refMap[n]
    if (!url) return `[${n}]`
    return `<sup><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="text-brand-500 hover:text-brand-400">[${n}]</a></sup>`
  })

  return html
}

function classifyLine(line) {
  if (/^\d+\.\s*/.test(line)) return 'numbered'
  if (/^[*]\s+/.test(line)) return 'bullet'
  if (/^#{2,6}\s*/.test(line)) return 'heading'
  if (/^【[^】]{1,24}】/.test(line)) return 'heading'
  if (/^(?:Step\s*\d+|步驟\s*\d+|分析步驟|預測台股|開盤預測|收盤預測|總結|結論)[：:\s]/i.test(line)) return 'heading'
  return 'paragraph'
}

function renderSummaryBlocks(mainText, refMap) {
  const normalized = normalizeSummaryText(mainText)
  if (!normalized) return ''

  const lines = normalized
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)

  return lines.map((rawLine) => {
    const type = classifyLine(rawLine)
    const line = rawLine.replace(/^#{2,6}\s*/, '')

    if (type === 'numbered') {
      const m = line.match(/^(\d+\.)\s*(.*)$/)
      return `<div class="briefing-list-item"><span class="briefing-marker">${m?.[1] || ''}</span><div>${renderInlineMarkdown(m?.[2] || line, refMap)}</div></div>`
    }

    if (type === 'bullet') {
      return `<div class="briefing-list-item briefing-bullet"><span class="briefing-marker">•</span><div>${renderInlineMarkdown(line.replace(/^[*]\s+/, ''), refMap)}</div></div>`
    }

    if (type === 'heading') {
      return `<div class="briefing-heading">${renderInlineMarkdown(line, refMap)}</div>`
    }

    return `<p>${renderInlineMarkdown(line, refMap)}</p>`
  }).join('')
}

/**
 * 將 summary_text 中的編號引用 [N] 轉為可點擊超連結上標。
 * 同時清理模型輸出的 HTML/Markdown 標記，並轉成可讀段落與縮排清單。
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

  return renderSummaryBlocks(mainText, refMap)
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

<style scoped>
.briefing-summary {
  overflow-wrap: anywhere;
}

.briefing-summary :deep(p) {
  margin: 0 0 0.65rem;
}

.briefing-summary :deep(strong) {
  font-weight: 700;
  color: var(--text-primary);
}

.briefing-summary :deep(.briefing-heading) {
  margin: 0.85rem 0 0.45rem;
  font-weight: 700;
  color: var(--text-primary);
}

.briefing-summary :deep(.briefing-heading:first-child) {
  margin-top: 0;
}

.briefing-summary :deep(.briefing-list-item) {
  display: grid;
  grid-template-columns: 2.2rem minmax(0, 1fr);
  gap: 0.35rem;
  margin: 0.55rem 0;
  padding-left: 0.25rem;
}

.briefing-summary :deep(.briefing-bullet) {
  grid-template-columns: 1.2rem minmax(0, 1fr);
  margin-left: 1rem;
}

.briefing-summary :deep(.briefing-marker) {
  color: var(--text-muted);
  font-weight: 700;
  text-align: right;
}
</style>
