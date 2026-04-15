import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { searchSymbolsDebounced, clearSearchCache } from '../api/search'

export const useSearchStore = defineStore('search', () => {
  // 狀態
  const query = ref('')
  const results = ref([])
  const isLoading = ref(false)
  const selectedCategory = ref(null)
  const error = ref(null)

  // 搜尋類別清單
  const categories = [
    { label: '全部', value: null },
    { label: '台灣 ETF', value: 'tw_etf' },
    { label: '美股 ETF', value: 'us_etf' },
    { label: '基金', value: 'fund' },
    { label: '指數', value: 'index' },
    { label: 'VIX', value: 'vix' },
    { label: '期貨', value: 'oil' },
  ]

  /**
   * 執行搜尋
   * @param {string} q - 搜尋關鍵字
   * @param {string|null} category - 篩選類別
   */
  const performSearch = async (q, category = null) => {
    // 清空之前的結果
    if (!q || q.trim().length === 0) {
      results.value = []
      query.value = q
      return
    }

    query.value = q
    selectedCategory.value = category

    isLoading.value = true
    error.value = null

    try {
      const searchResults = await searchSymbolsDebounced(q, category, 15)
      results.value = searchResults || []
    } catch (err) {
      error.value = err?.response?.data?.detail || '搜尋失敗'
      console.error('[SearchStore] Search error:', err)
      results.value = []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重置搜尋
   */
  const reset = () => {
    query.value = ''
    results.value = []
    selectedCategory.value = null
    error.value = null
    isLoading.value = false
    clearSearchCache()
  }

  /**
   * 更改類別篩選並重新搜尋
   * @param {string|null} category - 新的篩選類別
   */
  const changeCategory = async (category) => {
    selectedCategory.value = category
    if (query.value.trim()) {
      await performSearch(query.value, category)
    }
  }

  /**
   * 計算選中類別的標籤
   */
  const selectedCategoryLabel = computed(() => {
    const cat = categories.find(c => c.value === selectedCategory.value)
    return cat?.label || '全部'
  })

  return {
    // 狀態
    query,
    results,
    isLoading,
    selectedCategory,
    error,
    categories,

    // 計算屬性
    selectedCategoryLabel,

    // 方法
    performSearch,
    reset,
    changeCategory,
  }
})
