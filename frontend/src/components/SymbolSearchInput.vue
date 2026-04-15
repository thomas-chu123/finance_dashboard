<template>
  <div class="relative w-full">
    <!-- 搜尋輸入框 -->
    <div class="relative">
      <input
        v-model="query"
        type="text"
        :placeholder="placeholder"
        :disabled="disabled"
        class="w-full px-3 py-2 rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:border-blue-500 transition-colors"
        @input="handleInput"
        @focus="showResults = true"
        @blur="handleBlur"
        @keydown.arrow-down="moveDown"
        @keydown.arrow-up="moveUp"
        @keydown.enter.prevent="selectCurrent"
        @keydown.escape="hideResults"
      />
      
      <!-- 清除按鈕 -->
      <button
        v-if="query && !disabled"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors"
        @click="clearSearch"
      >
        <X :size="16" />
      </button>
    </div>

    <!-- 搜尋結果下拉清單 -->
    <div
      v-if="showResults && query"
      class="absolute top-full left-0 right-0 mt-1 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-md shadow-lg z-40 max-h-64 overflow-y-auto"
    >
      <!-- 載入中 -->
      <div v-if="isLoading" class="p-3 flex justify-center">
        <Loader2 :size="16" class="animate-spin text-blue-500" />
      </div>

      <!-- 錯誤提示 -->
      <div v-else-if="error" class="p-3 text-center">
        <p class="text-xs text-red-500">{{ error }}</p>
      </div>

      <!-- 無結果 -->
      <div v-else-if="!results.length" class="p-3 text-center">
        <p class="text-xs text-[var(--text-secondary)]">無搜尋結果</p>
      </div>

      <!-- 結果清單 -->
      <template v-else>
        <button
          v-for="(item, idx) in results"
          :key="item.symbol"
          type="button"
          :class="[
            'w-full px-3 py-2 text-left text-sm border-b border-[var(--border-color)]/50 cursor-pointer transition-colors hover:bg-blue-600/10',
            selectedIndex === idx ? 'bg-blue-600/20' : ''
          ]"
          @click="selectResult(item)"
          @mouseenter="selectedIndex = idx"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-semibold text-[var(--text-primary)]">
                {{ item.name_zh }}
                <span class="text-xs text-zinc-500 font-normal ml-1">{{ item.symbol }}</span>
              </div>
              <div class="text-xs text-zinc-500 truncate">
                {{ item.name_en }}
              </div>
            </div>
            
            <!-- 價格資訊 -->
            <div v-if="item.price !== null" class="text-right text-xs ml-2 flex-shrink-0">
              <div class="font-semibold text-[var(--text-primary)]">
                ${{ formatPrice(item.price) }}
              </div>
              <div :class="[
                'font-bold',
                (item.change_pct || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              ]">
                {{ formatChangePercent(item.change_pct) }}%
              </div>
            </div>
          </div>
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { X, Loader2 } from 'lucide-vue-next'
import { searchSymbolsDebounced, clearSearchCache } from '../api/search'

const props = defineProps({
  placeholder: {
    type: String,
    default: '搜尋指數、基金代碼或名稱...'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  category: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select', 'change'])

// 狀態
const query = ref('')
const showResults = ref(false)
const results = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedIndex = ref(0)

/**
 * 格式化價格顯示
 */
function formatPrice(price) {
  if (!price) return 'N/A'
  if (price >= 1000) {
    return (price / 1000).toFixed(2) + 'K'
  }
  return price.toFixed(2)
}

/**
 * 格式化漲跌百分比
 */
function formatChangePercent(pct) {
  if (pct === null || pct === undefined) return '0.00'
  return (pct >= 0 ? '+' : '') + pct.toFixed(2)
}

/**
 * 處理輸入事件
 */
async function handleInput() {
  emit('change', query.value)
  selectedIndex.value = 0
  
  if (!query.value.trim()) {
    results.value = []
    error.value = null
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const data = await searchSymbolsDebounced(
      query.value,
      props.category || 'all'
    )
    results.value = data || []
  } catch (err) {
    error.value = err.message || '搜尋失敗'
    results.value = []
  } finally {
    isLoading.value = false
  }
}

/**
 * 清除搜尋
 */
function clearSearch() {
  query.value = ''
  results.value = []
  error.value = null
  selectedIndex.value = 0
}

/**
 * 隱藏結果
 */
function hideResults() {
  showResults.value = false
}

/**
 * 處理 Blur 事件（延遲，讓 click 事件先執行）
 */
function handleBlur() {
  setTimeout(() => {
    showResults.value = false
  }, 100)
}

/**
 * 向下移動選擇
 */
function moveDown() {
  if (results.value.length > 0) {
    selectedIndex.value = (selectedIndex.value + 1) % results.value.length
  }
}

/**
 * 向上移動選擇
 */
function moveUp() {
  if (results.value.length > 0) {
    selectedIndex.value = selectedIndex.value === 0 
      ? results.value.length - 1 
      : selectedIndex.value - 1
  }
}

/**
 * 選擇當前高亮的結果
 */
function selectCurrent() {
  if (results.value.length > 0 && selectedIndex.value < results.value.length) {
    selectResult(results.value[selectedIndex.value])
  }
}

/**
 * 選擇搜尋結果
 */
function selectResult(item) {
  emit('select', item)
  query.value = item.symbol
  showResults.value = false
}

// 監聽 category prop 改變，清除快取
watch(() => props.category, () => {
  clearSearchCache()
  if (query.value) {
    handleInput()
  }
})
</script>

<style scoped>
/* Scrollbar 樣式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgb(113 113 122 / 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(113 113 122 / 0.5);
}
</style>
