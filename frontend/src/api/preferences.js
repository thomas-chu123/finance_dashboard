import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : window.location.origin)

/**
 * 用戶偏好設置 API 模塊
 * 提供與後端偏好設置端點的交互
 */
const preferencesAPI = {
  /**
   * 獲取用戶偏好設置
   * @param {string} token - JWT 認證令牌
   * @returns {Promise<Object>} 偏好設置對象（包含 card_order 等）
   */
  async getPreferences(token) {
    try {
      const response = await axios.get(
        `${API_BASE}/api/users/preferences`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      return response.data
    } catch (error) {
      console.error('Failed to get preferences:', error)
      throw error
    }
  },

  /**
   * 更新用戶偏好設置
   * @param {string} token - JWT 認證令牌
   * @param {Object} preferences - 偏好設置對象（例如：{ card_order: [...] }）
   * @returns {Promise<Object>} 更新後的偏好設置
   */
  async updatePreferences(token, preferences) {
    try {
      const response = await axios.put(
        `${API_BASE}/api/users/preferences`,
        preferences,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      return response.data
    } catch (error) {
      console.error('Failed to update preferences:', error)
      throw error
    }
  },

  /**
   * 更新卡片順序
   * @param {string} token - JWT 認證令牌
   * @param {Array<string>} cardOrder - 卡片 ID 陣列
   * @returns {Promise<Object>} 更新結果
   */
  async updateCardOrder(token, cardOrder) {
    return this.updatePreferences(token, { card_order: cardOrder })
  },

  /**
   * 重置偏好設置為默認值
   * @param {string} token - JWT 認證令牌
   * @returns {Promise<Object>} 重置後的偏好設置
   */
  async resetPreferences(token) {
    try {
      const response = await axios.post(
        `${API_BASE}/api/users/preferences/reset`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      return response.data
    } catch (error) {
      console.error('Failed to reset preferences:', error)
      throw error
    }
  }
}

export default preferencesAPI
