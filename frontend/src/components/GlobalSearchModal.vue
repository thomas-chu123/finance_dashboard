<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-start justify-center pt-20">
      <!-- 背景 Backdrop -->
      <div 
        class="absolute inset-0 bg-black/50 backdrop-blur-sm" 
        @click="close"
      />
      
      <!-- Modal 容器 -->
      <div class="relative w-full max-w-2xl mx-4 bg-[var(--bg-primary)] rounded-lg shadow-2xl border border-[var(--border-color)] overflow-hidden">
        <!-- 搜尋輸入框區域 -->
        <div class="flex items-center px-4 py-3 border-b border-[var(--border-color)]">
          <Search :size="18" class="text-zinc-400 flex-shrink-0" />
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            placeholder="搜尋指數、基金代碼或名稱..."
            class="flex-1 ml-3 bg-transparent outline-none text-[var(--text-primary)] placeholder-zinc-500 font-medium"
            @keydown.arrow-down="moveDown"
            @keydown.arrow-up="moveUp"
            @keydown.enter="selectCurrent"
            @keydown.escape="close"
          />
          <button
            class="ml-2 px-3 py-1 text-xs font-semibold text-white bg-brand-500 hover:bg-brand-600 rounded transition-colors"
            @click="handleSearch"
            :disabled="!query.trim() || searchStore.isLoading"
          >
            搜尋
          </button>
        </div>
        
        <!-- 類別篩選 -->
        <div class="px-4 py-2 flex gap-2 border-b border-[var(--border-color)] overflow-x-auto">
          <button
            v-for="cat in searchStore.categories"
            :key="cat.value"
            :class="[
              'px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-colors',
              searchStore.selectedCategory === cat.value 
                ? 'bg-blue-600 text-white' 
                : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            ]"
            @click="searchStore.changeCategory(cat.value)"
          >
            {{ cat.label }}
          </button>
        </div>
        
        <!-- 搜尋結果區域 -->
        <div class="max-h-96 overflow-y-auto">
          <!-- 載入中 -->
          <div v-if="searchStore.isLoading" class="p-8 flex justify-center">
            <Loader2 class="animate-spin text-blue-500" :size="24" />
          </div>

          <!-- 錯誤提示 -->
          <div v-else-if="searchStore.error" class="p-4 text-center">
            <p class="text-sm text-red-500">{{ searchStore.error }}</p>
          </div>

          <!-- 空提示 -->
          <div v-else-if="!query" class="p-8 text-center text-[var(--text-secondary)]">
            <p class="text-sm">輸入關鍵字後按「搜尋」開始查詢</p>
            <p class="text-xs mt-2 text-zinc-500">支持符號、中文名稱或英文名稱</p>
          </div>

          <!-- 無結果 -->
          <div v-else-if="!searchStore.results.length" class="p-4 text-center text-[var(--text-secondary)]">
            <p class="text-sm">找不到相符的結果</p>
          </div>

          <!-- 搜尋結果清單 -->
          <template v-else>
            <button
              v-for="(item, idx) in searchStore.results"
              :key="item.symbol"
              :class="[
                'w-full px-4 py-3 border-b border-[var(--border-color)]/50 cursor-pointer transition-colors hover:bg-[var(--bg-secondary)]/50 text-left',
                selectedIndex === idx ? 'bg-blue-600/20 border-l-2 border-l-blue-600' : ''
              ]"
              @click="selectResult(item)"
              @mouseenter="selectedIndex = idx"
            >
              <div class="flex items-start justify-between">
                <!-- 左側：名稱資訊 -->
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-[var(--text-primary)]">
                    {{ item.name_zh }}
                    <span class="text-xs text-zinc-500 font-normal ml-1">{{ item.symbol }}</span>
                  </div>
                  <div class="text-xs text-zinc-500 mt-0.5 truncate">
                    {{ item.name_en }} · {{ getCategoryLabel(item.category) }}
                  </div>
                </div>

                <!-- 右側：價格資訊 -->
                <div v-if="item.price !== null" class="text-right ml-4 flex-shrink-0">
                  <div class="font-semibold text-[var(--text-primary)]">
                    ${{ formatPrice(item.price) }}
                  </div>
                  <div :class="[
                    'text-xs font-bold',
                    (item.change_pct || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  ]">
                    {{ formatChangePercent(item.change_pct) }}%
                  </div>
                </div>
                <div v-else class="text-right ml-4 flex-shrink-0">
                  <div class="text-xs text-zinc-500">N/A</div>
                </div>
              </div>
            </button>
          </template>
        </div>

        <!-- 頁腳：快捷鍵提示 -->
        <div class="px-4 py-2 bg-[var(--bg-secondary)]/50 text-xs text-zinc-500 flex justify-between border-t border-[var(--border-color)]">
          <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">↑↓</kbd> 導航</span>
          <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">Enter</kbd> 選擇</span>
          <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">Esc</kbd> 關閉</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, defineExpose, watch } from 'vue'
import { Search, Loader2 } from 'lucide-vue-next'
import { useSearchStore } from '../stores/useSearchStore'

const searchStore = useSearchStore()

// 狀態
const isOpen = ref(false)
const inputRef = ref(null)
const query = ref('')
const selectedIndex = ref(0)

/**
 * 格式化價格顯示
 * @param {number} price - 價格
 * @returns {string} 格式化後的價格
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
 * @param {number} pct - 百分比
 * @returns {string} 格式化後的百分比
 */
function formatChangePercent(pct) {
  if (pct === null || pct === undefined) return '0.00'
  return (pct >= 0 ? '+' : '') + pct.toFixed(2)
}

/**
 * 獲取類別標籤
 */
function getCategoryLabel(category) {
  const cat = searchStore.categories.find(c => c.value === category)
  return cat?.label || category || '其他'
}

/**
 * 打開 Modal
 */
async function open() {
  isOpen.value = true
  query.value = ''
  selectedIndex.value = 0
  searchStore.reset()
  
  await nextTick()
  inputRef.value?.focus()
}

/**
 * 關閉 Modal
 */
function close() {
  isOpen.value = false
  query.value = ''
  selectedIndex.value = 0
}

/**
 * 處理搜尋觸發（取代實時搜尋）
 * 只在用戶按 ENTER 或點擊搜尋按鈕時觸發
 */
async function handleSearch() {
  if (!query.value.trim()) {
    return
  }
  
  selectedIndex.value = 0
  await searchStore.performSearch(
    query.value,
    searchStore.selectedCategory
  )
}

/**
 * 向下移動選擇
 */
function moveDown(e) {
  e.preventDefault()
  if (searchStore.results.length > 0) {
    selectedIndex.value = (selectedIndex.value + 1) % searchStore.results.length
  }
}

/**
 * 向上移動選擇
 */
function moveUp(e) {
  e.preventDefault()
  if (searchStore.results.length > 0) {
    selectedIndex.value = selectedIndex.value === 0 
      ? searchStore.results.length - 1 
      : selectedIndex.value - 1
  }
}

/**
 * 選擇當前高亮的結果
 */
function selectCurrent(e) {
  e.preventDefault()
  if (searchStore.results.length > 0 && selectedIndex.value < searchStore.results.length) {
    selectResult(searchStore.results[selectedIndex.value])
  }
}

/**
 * 選擇搜尋結果
 * 發出 'select' 事件給父組件
 */
function selectResult(item) {
  emit('select', item)
  close()
}

// 當 isOpen 改變時，監聽全局快捷鍵
watch(isOpen, (newVal) => {
  if (!newVal) return

  function handleKeydown(e) {
    // ESC 關閉
    if (e.key === 'Escape') {
      e.preventDefault()
      close()
    }
  }

  if (newVal) {
    window.addEventListener('keydown', handleKeydown)
  }

  return () => {
    window.removeEventListener('keydown', handleKeydown)
  }
})

// 定義導出的方法
const emit = defineEmits(['select'])

defineExpose({
  open,
  close,
})
</script>

<style scoped>
/* Scrollbar 樣式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgb(113 113 122 / 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(113 113 122 / 0.5);
}
</style>
