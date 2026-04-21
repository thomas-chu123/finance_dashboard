import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8005/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

// 自動添加認證令牌
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('fd_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * 上傳結果圖像（Backtest/Optimize/MonteCarlo PNG）
 * @param {FormData} formData - 包含 file、result_type、portfolio_id 的表單數據
 * @returns {Promise<object>} 包含 image_hash 和 share_url 的響應
 */
export async function uploadResultImage(formData) {
  try {
    const response = await apiClient.post('/backtest/share/image/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || '上傳圖像失敗')
  }
}

/**
 * 獲取無認證分享圖像（直接訪問）
 * @param {string} imageHash - 圖像哈希值
 * @returns {string} 圖像 URL
 */
export function getSharedImageUrl(imageHash) {
  return `${API_BASE_URL}/backtest/share/image/${imageHash}`
}

export default apiClient
