import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : window.location.origin)

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('fd_token') || null,
    userId: localStorage.getItem('fd_user_id') || null,
    email: localStorage.getItem('fd_email') || null,
    profile: null,
    profileLoadTime: 0, // 用於快取控制
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.profile?.is_admin ?? false,
    headers: (state) => ({ Authorization: `Bearer ${state.token}` }),
  },

  actions: {
    async login(email, password) {
      console.log(`Attempting login to: ${API_BASE}/api/auth/login`)
      try {
        const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password })
        console.log('Login request successful')
        this.token = res.data.access_token
        this.userId = res.data.user_id
        this.email = res.data.email
        localStorage.setItem('fd_token', this.token)
        localStorage.setItem('fd_user_id', this.userId)
        localStorage.setItem('fd_email', this.email)
        
        // 優化：延遲非關鍵初始化，並行化加載 admin API 和 profile
        // 不阻塞路由導航
        Promise.all([
          // 初始化 Admin API
          (async () => {
            try {
              const { setAuthToken } = await import('../api/admin-api.js')
              setAuthToken(this.token)
            } catch (e) {
              console.warn('[auth.login] Failed to initialize admin API:', e.message)
            }
          })(),
          // 非關鍵：後台加載個人資料
          this.fetchProfile()
        ]).catch(e => {
          console.warn('[auth.login] Background tasks error:', e.message)
        })
      } catch (error) {
        console.error('Login failed:', error.message)
        if (error.response) {
          console.error('Error Response:', error.response.status, error.response.data)
        } else if (error.request) {
          console.error('No response received (Request sent):', error.request)
        } else {
          console.error('Error setting up request:', error.message)
        }
        throw error
      }
    },

    async register(email, password, displayName) {
      await axios.post(`${API_BASE}/api/auth/register`, {
        email,
        password,
        display_name: displayName,
      })
    },

    async fetchProfile() {
      console.debug('[auth.fetchProfile] Starting...', { hasToken: !!this.token, apiBase: API_BASE })
      if (!this.token) {
        console.warn('[auth.fetchProfile] No token available, skipping profile fetch')
        return
      }
      
      // 優化：5 分鐘快取，避免頻繁查詢
      const now = Date.now()
      const CACHE_TTL = 5 * 60 * 1000 // 5 分鐘
      if (this.profile && (now - this.profileLoadTime) < CACHE_TTL) {
        console.debug('[auth.fetchProfile] Using cached profile (TTL: 5min)')
        return
      }
      
      try {
        console.debug('[auth.fetchProfile] Fetching from:', `${API_BASE}/api/users/me`)
        const res = await axios.get(`${API_BASE}/api/users/me`, { headers: this.headers })
        console.debug('[auth.fetchProfile] Profile loaded:', res.data)
        this.profile = res.data
        this.profileLoadTime = now
      } catch (e) {
        console.error('[auth.fetchProfile] Error:', e.message, e.response?.status, e.response?.data)
      }
    },

    async updateProfile(data) {
      const res = await axios.put(`${API_BASE}/api/users/me`, data, { headers: this.headers })
      this.profile = res.data
    },

    async toggleGlobalNotify() {
      if (!this.profile) return
      const current = this.profile.global_notify !== false // defaults to true
      const newValue = !current
      
      console.log(`[GlobalToggle] Switching from ${current} to ${newValue}`)
      
      // Optimitistic UI update for the bell
      this.profile.global_notify = newValue
      try {
        // 1. Also update all tracking items' is_active status
        console.log(`[GlobalToggle] Sending sync request to /api/tracking/toggle-all/status:`, { is_active: newValue })
        const syncRes = await axios.put(`${API_BASE}/api/tracking/toggle-all/status`, 
          { is_active: newValue },
          { headers: this.headers }
        )
        console.log(`[GlobalToggle] Sync response:`, syncRes.data)
        
        // 2. Update the user profile
        console.log(`[GlobalToggle] Updating user profile...`)
        await this.updateProfile({ global_notify: newValue })
        
        // 3. Refresh UI Page as requested
        console.log(`[GlobalToggle] Success! Refreshing page in 500ms...`)
        setTimeout(() => {
          window.location.reload()
        }, 500)
      } catch (e) {
        // Revert on failure
        this.profile.global_notify = current
        console.error('[GlobalToggle] Failed:', e)
        alert('切換通知狀態失敗，請稍後再試。')
      }
    },

    logout() {
      this.token = null
      this.userId = null
      this.email = null
      this.profile = null
      localStorage.removeItem('fd_token')
      localStorage.removeItem('fd_user_id')
      localStorage.removeItem('fd_email')
    },
  },
})

export const API_BASE_URL = API_BASE
