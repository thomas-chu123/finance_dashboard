import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSearchStore } from '../../frontend/src/stores/useSearchStore'
import * as searchAPI from '../../frontend/src/api/search'

describe('Search Functionality - Unit Tests', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSearchStore()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // ============================================================
  // Search Store Tests
  // ============================================================

  describe('useSearchStore - State & Initialization', () => {
    it('初始化時應有正確的默認狀態', () => {
      expect(store.query).toBe('')
      expect(store.results).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.selectedCategory).toBe('all')
      expect(store.error).toBe(null)
    })

    it('應有 7 個可用的搜尋類別', () => {
      expect(store.categories).toHaveLength(7)
      const categoryValues = store.categories.map(c => c.value)
      expect(categoryValues).toContain('all')
      expect(categoryValues).toContain('taiwan_etf')
      expect(categoryValues).toContain('us_etf')
    })
  })

  describe('useSearchStore - changeCategory', () => {
    it('應能更改選中的類別', () => {
      store.changeCategory('taiwan_etf')
      expect(store.selectedCategory).toBe('taiwan_etf')
    })

    it('changeCategory 應接受有效的類別值', () => {
      const validCategories = ['all', 'taiwan_etf', 'us_etf', 'fund', 'index', 'vix', 'futures']
      
      validCategories.forEach(cat => {
        store.changeCategory(cat)
        expect(store.selectedCategory).toBe(cat)
      })
    })
  })

  describe('useSearchStore - reset', () => {
    it('應能重置搜尋狀態', () => {
      store.query = 'test'
      store.results = [{ symbol: 'VTI' }]
      store.isLoading = true
      store.error = 'some error'
      store.selectedCategory = 'us_etf'

      store.reset()

      expect(store.query).toBe('')
      expect(store.results).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe(null)
      expect(store.selectedCategory).toBe('all')
    })
  })

  // ============================================================
  // Search API Tests
  // ============================================================

  describe('Search API - LRUCache', () => {
    it('LRUCache 應能存儲和檢索值', () => {
      const cache = new searchAPI.LRUCache(5)
      cache.set('key1', 'value1')
      
      expect(cache.get('key1')).toBe('value1')
    })

    it('LRUCache 應遵守最大容量限制', () => {
      const cache = new searchAPI.LRUCache(3)
      
      cache.set('key1', 'value1')
      cache.set('key2', 'value2')
      cache.set('key3', 'value3')
      cache.set('key4', 'value4') // 應移除最舊的 key1
      
      expect(cache.get('key1')).toBeUndefined()
      expect(cache.get('key4')).toBe('value4')
    })

    it('LRUCache.clear() 應清除所有緩存', () => {
      const cache = new searchAPI.LRUCache(5)
      cache.set('key1', 'value1')
      cache.set('key2', 'value2')
      
      cache.clear()
      
      expect(cache.get('key1')).toBeUndefined()
      expect(cache.get('key2')).toBeUndefined()
    })
  })

  describe('Search API - debounce', () => {
    it('debounce 應延遲函數執行', async () => {
      const mockFn = vi.fn()
      const debouncedFn = searchAPI.debounce(mockFn, 100)

      debouncedFn('arg1')
      debouncedFn('arg2')
      debouncedFn('arg3')

      // 立即檢查不應執行
      expect(mockFn).not.toHaveBeenCalled()

      // 等待延遲後應只執行一次，且使用最後一次調用的參數
      await new Promise(resolve => setTimeout(resolve, 150))
      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('arg3')
    })

    it('debounce 返回的函數應有 cancel 方法', () => {
      const mockFn = vi.fn()
      const debouncedFn = searchAPI.debounce(mockFn, 100)

      debouncedFn('arg')
      debouncedFn.cancel()

      // cancel 後應不執行函數
      expect(mockFn).not.toHaveBeenCalled()
    })
  })

  // ============================================================
  // Search Performance Tests
  // ============================================================

  describe('Search Performance', () => {
    it('搜尋應在 200ms 內返回結果', async () => {
      const mockResults = [
        { symbol: 'VTI', name_zh: '美股整體市場', name_en: 'US Total Market', price: 250.50, change_pct: 2.5 }
      ]

      // Mock API 調用
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)

      const startTime = Date.now()
      await store.performSearch('VTI', 'all')
      const endTime = Date.now()

      expect(endTime - startTime).toBeLessThan(200)
      expect(store.results).toHaveLength(1)
    })
  })

  // ============================================================
  // Edge Cases & Error Handling
  // ============================================================

  describe('Search - Edge Cases', () => {
    it('空查詢應返回空結果', async () => {
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue([])

      store.query = ''
      await store.performSearch('', 'all')

      expect(store.results).toEqual([])
    })

    it('應能處理搜尋 API 錯誤', async () => {
      vi.spyOn(searchAPI, 'searchSymbols').mockRejectedValue(new Error('Network error'))

      await store.performSearch('test', 'all')

      expect(store.error).toBeTruthy()
      expect(store.isLoading).toBe(false)
    })

    it('應能處理特殊字符搜尋', async () => {
      const mockResults = [
        { symbol: 'ETF-US', name_zh: '美國 ETF', name_en: 'US ETF', price: 100, change_pct: 1 }
      ]

      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)

      await store.performSearch('ETF-US', 'all')

      expect(store.results).toHaveLength(1)
      expect(store.results[0].symbol).toBe('ETF-US')
    })

    it('應能處理長搜尋查詢', async () => {
      const longQuery = 'a'.repeat(500)
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue([])

      await store.performSearch(longQuery, 'all')

      // 應不崩潰，返回空結果
      expect(store.results).toEqual([])
      expect(store.error).toBeNull()
    })
  })

  // ============================================================
  // Category Filtering Tests
  // ============================================================

  describe('Search - Category Filtering', () => {
    beforeEach(() => {
      const mockResults = [
        { symbol: '0050', category: 'taiwan_etf', name_zh: '台灣 50', name_en: 'Taiwan 50' },
        { symbol: 'VTI', category: 'us_etf', name_zh: '美股整體市場', name_en: 'US Total Market' },
        { symbol: 'BND', category: 'us_etf', name_zh: '美國債券', name_en: 'US Bonds' }
      ]
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)
    })

    it('應能依類別篩選搜尋結果', async () => {
      await store.performSearch('', 'taiwan_etf')
      expect(store.selectedCategory).toBe('taiwan_etf')
    })

    it('「all」類別應返回所有結果', async () => {
      await store.performSearch('', 'all')
      expect(store.results).toHaveLength(3)
    })

    it('特定類別應只返回該類別的結果', async () => {
      // 模擬後端根據類別篩選
      vi.spyOn(searchAPI, 'searchSymbols')
        .mockImplementation((query, category) => {
          if (category === 'us_etf') {
            return Promise.resolve([
              { symbol: 'VTI', category: 'us_etf', name_zh: '美股整體市場', name_en: 'US Total Market' },
              { symbol: 'BND', category: 'us_etf', name_zh: '美國債券', name_en: 'US Bonds' }
            ])
          }
          return Promise.resolve([])
        })

      await store.performSearch('', 'us_etf')
      expect(store.results).toHaveLength(2)
      expect(store.results.every(r => r.category === 'us_etf')).toBe(true)
    })
  })

  // ============================================================
  // Multi-language Support Tests
  // ============================================================

  describe('Search - Multi-language Support', () => {
    it('應能搜尋中文名稱', async () => {
      const mockResults = [
        { symbol: '0050', name_zh: '台灣 50', name_en: 'Taiwan 50', category: 'taiwan_etf', price: 100 }
      ]
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)

      await store.performSearch('台灣', 'all')
      expect(store.results).toHaveLength(1)
    })

    it('應能搜尋英文名稱', async () => {
      const mockResults = [
        { symbol: 'VTI', name_zh: '美股整體市場', name_en: 'US Total Market', category: 'us_etf', price: 250 }
      ]
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)

      await store.performSearch('Total Market', 'all')
      expect(store.results).toHaveLength(1)
    })

    it('應能搜尋符號代碼', async () => {
      const mockResults = [
        { symbol: 'VTI', name_zh: '美股整體市場', name_en: 'US Total Market', category: 'us_etf', price: 250 }
      ]
      vi.spyOn(searchAPI, 'searchSymbols').mockResolvedValue(mockResults)

      await store.performSearch('VTI', 'all')
      expect(store.results).toHaveLength(1)
      expect(store.results[0].symbol).toBe('VTI')
    })
  })
})
