import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8005/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

// 自動添加認證令牌
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * 建立投組分享快照
 * @param {string} portfolioId - 投組 ID
 * @param {object} config - 分享配置
 * @returns {Promise<object>} 分享結果
 */
export async function sharePortfolio(portfolioId, config) {
  try {
    const response = await apiClient.post(`/backtest/portfolio/${portfolioId}/share`, {
      share_type: config.share_type || 'snapshot',
      expires_in_days: config.expires_in_days || 30,
      share_description: config.share_description || '',
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || '分享失敗')
  }
}

/**
 * 取得公開分享快照（不需認證）
 * @param {string} shareKey - 分享短碼
 * @returns {Promise<object>} 分享數據
 */
export async function getPublicShare(shareKey) {
  try {
    const response = await axios.get(`${API_BASE_URL}/share/${shareKey}`)
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || '取得分享失敗')
  }
}

/**
 * 列出用戶的分享
 * @param {object} params - 查詢參數
 * @returns {Promise<array>} 分享列表
 */
export async function listUserShares(params = {}) {
  try {
    const response = await apiClient.get('/backtest/shares', { params })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || '取得分享列表失敗')
  }
}

/**
 * 取消分享
 * @param {string} shareKey - 分享短碼
 * @returns {Promise<void>}
 */
export async function deleteShare(shareKey) {
  try {
    await apiClient.delete(`/backtest/shares/${shareKey}`)
  } catch (error) {
    throw new Error(error.response?.data?.detail || '取消分享失敗')
  }
}

/**
 * 存檔分享（隱藏但不刪除）
 * @param {string} shareKey - 分享短碼
 * @param {boolean} isArchived - 是否存檔
 * @returns {Promise<object>}
 */
export async function archiveShare(shareKey, isArchived) {
  try {
    const response = await apiClient.patch(`/backtest/shares/${shareKey}`, {
      is_archived: isArchived,
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || '存檔分享失敗')
  }
}

export default apiClient
