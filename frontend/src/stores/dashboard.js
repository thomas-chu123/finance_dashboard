import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : window.location.origin)

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    // 卡片順序 ID 陣列
    cardOrder: [
      'ai-briefing',
      'market-ticker',
      'tracking-table',
      'status-sidebar'
    ],
    
    // 標記是否正在保存
    isSaving: false,
    saveError: null,
  }),

  getters: {
    // 取得排序後的卡片清單
    orderedCards: (state) => state.cardOrder,
  },

  actions: {
    /**
     * 移動卡片位置
     * @param {number} fromIndex - 來源位置
     * @param {number} toIndex - 目標位置
     */
    moveCard(fromIndex, toIndex) {
      if (fromIndex < 0 || toIndex < 0) return
      if (fromIndex >= this.cardOrder.length || toIndex >= this.cardOrder.length) return
      
      const card = this.cardOrder[fromIndex]
      this.cardOrder.splice(fromIndex, 1)
      this.cardOrder.splice(toIndex, 0, card)
    },

    /**
     * 交換兩個卡片位置
     * @param {number} index1 - 第一個卡片位置
     * @param {number} index2 - 第二個卡片位置
     */
    swapCards(index1, index2) {
      if (index1 < 0 || index2 < 0) return
      if (index1 >= this.cardOrder.length || index2 >= this.cardOrder.length) return
      
      [this.cardOrder[index1], this.cardOrder[index2]] = [this.cardOrder[index2], this.cardOrder[index1]]
    },

    /**
     * 從本地存儲加載卡片順序
     * 如果本地存儲中有保存的順序，則使用；否則使用默認順序
     */
    loadFromLocalStorage() {
      try {
        const saved = localStorage.getItem('dashboard_card_order')
        if (saved) {
          const parsed = JSON.parse(saved)
          if (Array.isArray(parsed) && parsed.length > 0) {
            this.cardOrder = parsed
            return true
          }
        }
      } catch (e) {
        console.warn('Failed to load from localStorage:', e)
      }
      return false
    },

    /**
     * 將卡片順序保存到本地存儲
     */
    saveToLocalStorage() {
      localStorage.setItem('dashboard_card_order', JSON.stringify(this.cardOrder))
    },

    /**
     * 從後端加載卡片順序
     * @param {string} token - JWT token
     * @returns {boolean} 是否成功加載
     */
    async loadCardOrder(token) {
      if (!token) {
        console.warn('No token provided for loadCardOrder')
        return this.loadFromLocalStorage()
      }
      
      try {
        const response = await axios.get(
          `${API_BASE}/api/users/preferences`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        if (response.data?.card_order && Array.isArray(response.data.card_order)) {
          this.cardOrder = response.data.card_order
          console.log('Loaded card order from server:', this.cardOrder)
          this.saveToLocalStorage()
          return true
        }
      } catch (error) {
        console.warn('Failed to load card order from server:', error.message)
      }
      
      // 失敗時回退到本地存儲
      return this.loadFromLocalStorage()
    },

    /**
     * 將卡片順序保存到後端
     * @param {string} token - JWT token
     */
    async saveCardOrder(token) {
      if (this.isSaving) return
      
      this.isSaving = true
      this.saveError = null
      
      try {
        await axios.put(
          `${API_BASE}/api/users/preferences`,
          { card_order: this.cardOrder },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        // 同時保存到本地存儲作為備份
        this.saveToLocalStorage()
      } catch (error) {
        console.error('Failed to save card order:', error)
        this.saveError = error.message
        // 失敗時至少保存到本地存儲
        this.saveToLocalStorage()
      } finally {
        this.isSaving = false
      }
    },

    /**
     * 重置為默認順序
     */
    resetToDefault() {
      this.cardOrder = [
        'market-ticker',
        'tracking-table',
        'status-sidebar'
      ]
      localStorage.removeItem('dashboard_card_order')
    }
  }
})
