<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-start justify-center pt-20">
      <!-- 背景 Backdrop -->
      <div 
        class="absolute inset-0 bg-black/50 backdrop-blur-sm" 
        @click="close"
      />
      
      <!-- Modal 容器 -->
      <div class="relative w-full max-w-2xl mx-4 bg-[var(--bg-primary)] rounded-lg shadow-2xl border border-[var(--border-color)] overflow-hidden" @click.stop>
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
            @keydown.enter="handleEnterKey"
            @keydown.escape="close"
            @compositionstart="handleCompositionStart"
            @compositionend="handleCompositionEnd"
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

          <!-- 空提示（用戶還沒輸入或已修改搜尋詞但還沒按搜尋） -->
          <div v-else-if="!query || !hasSearched" class="p-8 text-center text-[var(--text-secondary)]">
            <p class="text-sm">輸入關鍵字後按「搜尋」開始查詢</p>
            <p class="text-xs mt-2 text-zinc-500">支持符號、中文名稱或英文名稱</p>
          </div>

          <!-- 無結果（用戶已按搜尋，但沒有結果） -->
          <div v-else-if="hasSearched && !searchStore.results.length" class="p-4 text-center text-[var(--text-secondary)]">
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

        <!-- 頁腳：快捷鍵提示 + 關閉按鈕 -->
        <div class="px-4 py-2 bg-[var(--bg-secondary)]/50 text-xs text-zinc-500 flex justify-between items-center border-t border-[var(--border-color)]">
          <div class="flex gap-2">
            <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">↑↓</kbd> 導航</span>
            <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">Enter</kbd> 選擇</span>
            <span><kbd class="inline-block px-1.5 py-0.5 bg-brand-500 rounded text-white font-mono text-xs">Esc</kbd> 關閉</span>
          </div>
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
const isComposing = ref(false)
const hasSearched = ref(false)  // 標記用戶是否已按過搜尋按鈕或 Enter（區分輸入中 vs 無結果）
let justCompletedComposition = false  // 標記剛完成 composition，300ms 內忽略 Enter

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
  hasSearched.value = false  // 重置搜尋狀態
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
  
  hasSearched.value = true  // 標記已搜尋
  
  console.log('[GlobalSearchModal] handleSearch 觸發', {
    query: query.value,
    category: searchStore.selectedCategory,
    timestamp: new Date().toISOString()
  })
  
  selectedIndex.value = 0
  await searchStore.performSearch(
    query.value,
    searchStore.selectedCategory
  )
}

/**
 * 處理 Enter 鍵按下
 * - 如果有搜尋結果且高亮了項目，則選擇該項目
 * - 否則觸發搜尋
 */
function handleEnterKey(e) {
  console.log('[GlobalSearchModal] Enter 鍵按下', {
    isComposing: isComposing.value,
    justCompletedComposition: justCompletedComposition,
    query: query.value,
    resultsCount: searchStore.results.length,
    selectedIndex: selectedIndex.value,
    timestamp: new Date().toISOString(),
    eventType: e.type,
    key: e.key
  })

  // 如果正在進行中文輸入組合，忽略 Enter 鍵
  if (isComposing.value) {
    console.log('[GlobalSearchModal] 正在進行中文輸入，忽略 Enter 鍵')
    e.preventDefault()
    return
  }

  // 如果剛剛完成 composition，忽略此 Enter 鍵（應該是 IME 確認鍵）
  if (justCompletedComposition) {
    console.log('[GlobalSearchModal] 剛剛完成 composition，忽略 Enter 鍵（這是 IME 確認鍵）')
    e.preventDefault()
    justCompletedComposition = false  // 重置標記
    return
  }

  e.preventDefault()

  // 檢查是否有搜尋結果
  if (searchStore.results.length > 0 && selectedIndex.value < searchStore.results.length) {
    console.log('[GlobalSearchModal] 有搜尋結果，執行 selectCurrent', {
      selectedItem: searchStore.results[selectedIndex.value].symbol,
      selectedIndex: selectedIndex.value
    })
    selectResult(searchStore.results[selectedIndex.value])
  } else {
    console.log('[GlobalSearchModal] 沒有搜尋結果或未選中項目，執行 handleSearch')
    await handleSearch()
  }
}

/**
 * 處理中文輸入開始
 */
function handleCompositionStart() {
  console.log('[GlobalSearchModal] 中文輸入開始 (compositionstart)', {
    timestamp: new Date().toISOString()
  })
  isComposing.value = true
}

/**
 * 處理中文輸入結束
 */
function handleCompositionEnd() {
  console.log('[GlobalSearchModal] 中文輸入結束 (compositionend)', {
    query: query.value,
    timestamp: new Date().toISOString()
  })
  isComposing.value = false
  
  // 設置標記：剛剛完成 composition，接下來的 Enter 鍵應該被忽略（這是 IME 確認鍵）
  justCompletedComposition = true
  
  // 300ms 後重置標記，允許用戶正常使用 Enter 鍵選擇搜尋結果
  setTimeout(() => {
    justCompletedComposition = false
    console.log('[GlobalSearchModal] 重置 justCompletedComposition 標記')
  }, 300)
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
 * 選擇搜尋結果
 * 發出 'select' 事件給父組件
 * 注意：不自動關閉視窗，由用戶手動按 ESC 或點擊背景關閉
 */
function selectResult(item) {
  console.log('[GlobalSearchModal] 選擇搜尋結果', {
    symbol: item.symbol,
    name: item.name_zh,
    timestamp: new Date().toISOString()
  })
  emit('select', item)
  // 不關閉視窗 - 用戶可以繼續搜尋或按 ESC/點擊背景關閉
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

// 當搜尋詞改變時，清空舊結果和錯誤提示
// 只有按「搜尋」按鈕或 Enter 時才會執行新搜尋
watch(query, (newVal) => {
  if (newVal !== searchStore.query) {
    // 搜尋詞已改變，清空舊結果
    searchStore.results = []
    searchStore.error = null
    selectedIndex.value = 0
    hasSearched.value = false  // 重置搜尋狀態（用戶在輸入新詞，還沒按搜尋）
    
    console.log('[GlobalSearchModal] 搜尋詞改變，清空舊結果', {
      oldQuery: searchStore.query,
      newQuery: newVal,
      hasSearched: hasSearched.value,
      timestamp: new Date().toISOString()
    })
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
