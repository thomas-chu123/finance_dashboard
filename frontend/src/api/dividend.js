import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 取得指定月份的除權息日曆
 * @param {string} token - JWT token
 * @param {number} year  - 西元年
 * @param {number} month - 月份 1-12
 */
export const fetchDividendCalendar = (token, year, month) =>
  axios.get(`${API_BASE}/api/dividend/calendar`, {
    params: { year, month },
    headers: { Authorization: `Bearer ${token}` },
  })

/**
 * 取得未來 N 天內的除權息清單
 * @param {string} token - JWT token
 * @param {number} days  - 天數（預設 30）
 */
export const fetchUpcomingDividends = (token, days = 30) =>
  axios.get(`${API_BASE}/api/dividend/upcoming`, {
    params: { days },
    headers: { Authorization: `Bearer ${token}` },
  })
