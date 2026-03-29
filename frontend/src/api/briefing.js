import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 取得最新一次排程的 AI 早報摘要
 * @param {string} token - JWT token
 */
export async function fetchLatestBriefing(token) {
  return axios.get(`${API_BASE}/api/briefing/latest`, {
    headers: { Authorization: `Bearer ${token}` },
  })
}

/**
 * 手動觸發一次市場早報排程（背景執行）
 * @param {string} token - JWT token
 */
export async function triggerBriefing(token) {
  return axios.post(
    `${API_BASE}/api/briefing/trigger`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  )
}
