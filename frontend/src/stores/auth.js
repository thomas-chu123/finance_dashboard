import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : window.location.origin)

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('fd_token') || null,
    userId: localStorage.getItem('fd_user_id') || null,
    email: localStorage.getItem('fd_email') || null,
    profile: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
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
        await this.fetchProfile()
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
      try {
        console.debug('[auth.fetchProfile] Fetching from:', `${API_BASE}/api/users/me?_t=${Date.now()}`)
        const res = await axios.get(`${API_BASE}/api/users/me?_t=${Date.now()}`, { headers: this.headers })
        console.debug('[auth.fetchProfile] Profile loaded:', res.data)
        this.profile = res.data
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
      
      // Optimitistic UI update for the bell
      this.profile.global_notify = newValue
      try {
        // 1. Also update all tracking items' is_active status
        await axios.put(`${API_BASE}/api/tracking/toggle-all/status`, 
          { is_active: newValue },
          { headers: this.headers }
        )
        
        // 2. Update the user profile
        await this.updateProfile({ global_notify: newValue })
        
        // 3. Refresh UI Page as requested
        window.location.reload()
      } catch (e) {
        // Revert on failure
        this.profile.global_notify = current
        console.error('Failed to toggle global_notify', e)
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
