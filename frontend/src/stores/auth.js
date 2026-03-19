import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.DEV
  ? ''
  : `${window.location.protocol}//${window.location.hostname}:8005`

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
      const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password })
      this.token = res.data.access_token
      this.userId = res.data.user_id
      this.email = res.data.email
      localStorage.setItem('fd_token', this.token)
      localStorage.setItem('fd_user_id', this.userId)
      localStorage.setItem('fd_email', this.email)
      await this.fetchProfile()
    },

    async register(email, password, displayName) {
      await axios.post(`${API_BASE}/api/auth/register`, {
        email,
        password,
        display_name: displayName,
      })
    },

    async fetchProfile() {
      if (!this.token) return
      try {
        const res = await axios.get(`${API_BASE}/api/users/me`, { headers: this.headers })
        this.profile = res.data
      } catch (e) {
        console.error('Profile fetch failed', e)
      }
    },

    async updateProfile(data) {
      const res = await axios.put(`${API_BASE}/api/users/me`, data, { headers: this.headers })
      this.profile = res.data
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
