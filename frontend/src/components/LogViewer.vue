<template>
  <div class="space-y-3">
    <!-- Controls -->
    <div class="flex gap-2 flex-wrap">
      <input 
        v-if="showSearch"
        v-model="searchQuery" 
        type="text"
        placeholder="搜尋..."
        class="flex-1 px-3 py-2 rounded border border-gray-600 bg-gray-900 text-white placeholder-gray-500 text-sm"
      />
      <select 
        v-if="showLevelFilter"
        v-model="selectedLevel"
        class="px-3 py-2 rounded border border-gray-600 bg-gray-900 text-white text-sm"
      >
        <option value="" class="bg-gray-800">所有級別</option>
        <option value="DEBUG" class="bg-gray-800">DEBUG</option>
        <option value="INFO" class="bg-gray-800">INFO</option>
        <option value="WARNING" class="bg-gray-800">WARNING</option>
        <option value="ERROR" class="bg-gray-800">ERROR</option>
      </select>
      <button
        @click="refresh"
        class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors text-sm"
      >
        重新加載
      </button>
    </div>

    <!-- Log Viewer -->
    <div class="rounded-lg border border-[var(--border-color)] overflow-hidden">
      <!-- Header -->
      <div class="bg-gray-900 border-b border-gray-700 p-2 flex justify-between items-center">
        <span class="text-xs text-gray-400">{{ filteredLogs.length }} 筆記錄</span>
        <div class="flex gap-1">
          <button
            @click="scrollToTop"
            class="px-2 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 transition-colors text-gray-300"
            title="回到頂部"
          >
            ↑
          </button>
          <button
            @click="scrollToBottom"
            class="px-2 py-1 rounded text-xs bg-gray-800 hover:bg-gray-700 transition-colors text-gray-300"
            title="跳到底部"
          >
            ↓
          </button>
        </div>
      </div>

      <!-- Logs -->
      <div ref="logContainer" class="max-h-96 overflow-y-auto bg-black text-white">
        <div v-if="loading" class="p-4 text-center text-gray-400 text-sm">
          加載中...
        </div>
        <div v-else-if="filteredLogs.length === 0" class="p-4 text-center text-gray-400 text-sm">
          沒有日誌
        </div>
        <div v-for="(log, idx) in filteredLogs" :key="idx" class="border-b border-gray-700 text-xs hover:bg-gray-900 transition-colors">
          <!-- If log is object with level property -->
          <div v-if="typeof log === 'object' && log.level" class="p-3 space-y-1">
            <div class="flex items-center gap-2">
              <span class="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                :class="{
                  'bg-red-600 text-white': log.level === 'ERROR',
                  'bg-yellow-600 text-white': log.level === 'WARNING',
                  'bg-blue-600 text-white': log.level === 'INFO',
                  'bg-gray-600 text-white': log.level === 'DEBUG'
                }"
              >
                {{ log.level }}
              </span>
              <span class="text-gray-400 text-xs">{{ log.component }}</span>
              <span class="text-gray-400 text-xs ml-auto">{{ formatDate(log.created_at) }}</span>
            </div>
            <p class="text-white text-xs">{{ log.message }}</p>
          </div>
          <!-- If log is simple string -->
          <div v-else class="p-3 text-white font-mono text-xs whitespace-pre-wrap break-words" v-html="convertAnsiToHtml(log)">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import AnsiToHtml from 'ansi-to-html'

const props = defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  searchable: {
    type: Boolean,
    default: true,
  },
  filterable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['refresh'])

const logContainer = ref(null)
const searchQuery = ref('')
const selectedLevel = ref('')

// 初始化 ANSI 轉 HTML 轉換器（黑色背景，高對比顏色）
const ansiConverter = new AnsiToHtml({
  fg: '#ffffff',  // 前景色：白
  bg: '#000000',  // 背景色：黑
  newline: true,
  escapeXml: true,
  colors: {
    0: '#808080',   // 黑 → 深灰
    1: '#ff4444',   // 紅
    2: '#44ff44',   // 綠
    3: '#ffff00',   // 黃
    4: '#4444ff',   // 藍
    5: '#ff44ff',   // 洋紅
    6: '#44ffff',   // 青
    7: '#ffffff',   // 白
    8: '#aaaaaa',   // 亮黑
    9: '#ff6666',   // 亮紅
    10: '#66ff66',  // 亮綠
    11: '#ffff66',  // 亮黃
    12: '#6666ff',  // 亮藍
    13: '#ff66ff',  // 亮洋紅
    14: '#66ffff',  // 亮青
    15: '#ffffff',  // 亮白
  }
})

const convertAnsiToHtml = (text) => {
  if (!text || typeof text !== 'string') return ''
  try {
    return ansiConverter.toHtml(text)
  } catch (e) {
    console.warn('ANSI 轉換失敗:', e)
    return text
  }
}

const showSearch = computed(() => props.searchable && props.logs.some(log => typeof log === 'string'))
const showLevelFilter = computed(() => props.filterable && props.logs.some(log => typeof log === 'object' && log.level))

const filteredLogs = computed(() => {
  let result = props.logs

  // 搜尋過濾
  if (searchQuery.value && showSearch.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(log => 
      typeof log === 'string' 
        ? log.toLowerCase().includes(query)
        : (log.message?.toLowerCase().includes(query) || log.component?.toLowerCase().includes(query))
    )
  }

  // 級別過濾
  if (selectedLevel.value && showLevelFilter.value) {
    result = result.filter(log => typeof log === 'object' && log.level === selectedLevel.value)
  }

  return result
})

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const scrollToTop = async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = 0
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

const refresh = () => {
  emit('refresh')
}
</script>
