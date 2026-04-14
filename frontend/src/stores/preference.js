import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePreferenceStore = defineStore('preference', () => {
  // 從 localStorage 讀取幣值選擇，預設為 TWD
  const displayCurrency = ref(
    localStorage.getItem('displayCurrency') || 'TWD'
  )

  /**
   * 設置顯示幣值
   * @param {string} currency - 'USD' 或 'TWD'
   */
  const setDisplayCurrency = (currency) => {
    if (!['USD', 'TWD'].includes(currency)) {
      console.warn(`Invalid currency: ${currency}, using TWD`)
      return
    }
    displayCurrency.value = currency
    localStorage.setItem('displayCurrency', currency)
  }

  /**
   * 在 USD 和 TWD 之間切換
   */
  const toggleCurrency = () => {
    const newCurrency = displayCurrency.value === 'USD' ? 'TWD' : 'USD'
    setDisplayCurrency(newCurrency)
  }

  return {
    displayCurrency,
    setDisplayCurrency,
    toggleCurrency
  }
})
