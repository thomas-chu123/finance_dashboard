import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * LRU 快取實現（最近最少使用）
 * 防止記憶體無限增長
 */
class LRUCache {
  constructor(maxSize = 50) {
    this.maxSize = maxSize
    this.cache = new Map()
  }

  get(key) {
    if (!this.cache.has(key)) return null
    // 移到末尾（標記為最近使用）
    const value = this.cache.get(key)
    this.cache.delete(key)
    this.cache.set(key, value)
    return value
  }

  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key)
    } else if (this.cache.size >= this.maxSize) {
      // 刪除最舊的（第一個）項目
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }
    this.cache.set(key, value)
  }

  clear() {
    this.cache.clear()
  }

  get size() {
    return this.cache.size
  }
}

/**
 * 建立通用的 debounce 函數
 * @param {Function} fn - 要 debounce 的函數
 * @param {number} delay - 延遲時間（毫秒）
 * @returns {Function} debounced 函數
 */
export function debounce(fn, delay = 500) {
  let timeoutId = null
  let lastArgs = null

  const debounced = async (...args) => {
    lastArgs = args
    clearTimeout(timeoutId)

    return new Promise((resolve, reject) => {
      timeoutId = setTimeout(async () => {
        try {
          const result = await fn(...lastArgs)
          resolve(result)
        } catch (err) {
          reject(err)
        }
      }, delay)
    })
  }

  /**
   * 立即取消 debounce
   */
  debounced.cancel = () => {
    clearTimeout(timeoutId)
    timeoutId = null
  }

  return debounced
}

// 建立搜尋快取（LRU）
const searchCache = new LRUCache(50)

/**
 * 搜尋符號/指數/基金
 * @param {string} query - 搜尋關鍵字
 * @param {string|null} category - 篩選類別 (可選)
 * @param {number} limit - 返回結果數量
 * @returns {Promise<Array>} 搜尋結果陣列
 */
export async function searchSymbols(query, category = null, limit = 15) {
  // 空查詢直接返回空結果
  if (!query || query.trim().length === 0) {
    return []
  }

  const cacheKey = `${query.trim()}:${category}:${limit}`

  // 檢查快取
  const cached = searchCache.get(cacheKey)
  if (cached) {
    return cached
  }

  try {
    const params = {
      q: query.trim(),
      limit: Math.min(limit, 50), // 最多 50
    }

    if (category) {
      params.category = category
    }

    const response = await axios.get(`${API_BASE}/api/market/search`, { params })
    const results = response.data.results || []

    // 存入快取
    searchCache.set(cacheKey, results)

    return results
  } catch (error) {
    console.error('[SearchAPI] Error searching symbols:', error)
    throw error
  }
}

/**
 * 建立 debounced 版本的搜尋函數
 * 自動 debounce 搜尋請求（500ms）
 */
export const searchSymbolsDebounced = debounce(searchSymbols, 200)

/**
 * 清空搜尋快取
 * 用於手動清理（如用戶登出時）
 */
export function clearSearchCache() {
  searchCache.clear()
}

/**
 * 獲取快取統計信息（用於調試）
 * @returns {Object} 快取統計
 */
export function getSearchCacheStats() {
  return {
    size: searchCache.size,
    maxSize: searchCache.maxSize,
  }
}
