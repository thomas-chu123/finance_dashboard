import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 獲取 Google 登入 URL
 * @returns {Promise} { login_url, state }
 */
export async function getGoogleLoginUrl() {
  const response = await axios.get(`${API_BASE}/api/auth/oauth/google/login-url`)
  return response.data
}

/**
 * 處理 Google OAuth 回調
 * @param {string} code - Authorization code from Google
 * @param {string} state - State parameter for CSRF protection
 * @returns {Promise} { access_token, user_id, email, display_name, is_new_user }
 */
export async function handleGoogleCallback(code, state) {
  const response = await axios.post(`${API_BASE}/api/auth/oauth/google/callback`, {
    code,
    state,
  })
  return response.data
}

/**
 * 交換 Google ID Token 以獲取用戶信息
 * @param {string} idToken - Google ID token from Google Sign-In
 * @returns {Promise} 用戶信息 { access_token, user_id, email, display_name, is_new_user }
 */
export async function exchangeGoogleToken(idToken) {
  const response = await axios.post(`${API_BASE}/api/auth/oauth/google/token-exchange`, {
    id_token: idToken,
  })
  return response.data
}

export default {
  getGoogleLoginUrl,
  handleGoogleCallback,
  exchangeGoogleToken,
}
