import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from './auth'

export const useTrackingStore = defineStore('tracking', {
  state: () => ({
    items: [],
    alertLogs: [],
    rsiData: {}, // { [id]: { current_rsi, status, updated_at, ... } }
    loading: false,
  }),

  actions: {
    _headers() {
      return useAuthStore().headers
    },

    async fetchAll() {
      this.loading = true
      try {
        const res = await axios.get(`${API_BASE}/api/tracking`, { headers: this._headers() })
        this.items = res.data
      } finally {
        this.loading = false
      }
    },

    async create(data) {
      const res = await axios.post(`${API_BASE}/api/tracking`, data, { headers: this._headers() })
      this.items.unshift(res.data)
      return res.data
    },

    async update(id, data) {
      const res = await axios.put(`${API_BASE}/api/tracking/${id}`, data, { headers: this._headers() })
      const idx = this.items.findIndex((i) => i.id === id)
      if (idx !== -1) this.items[idx] = res.data
      return res.data
    },

    async remove(id) {
      await axios.delete(`${API_BASE}/api/tracking/${id}`, { headers: this._headers() })
      this.items = this.items.filter((i) => i.id !== id)
    },

    async addFromBacktest(symbols, names, categories) {
      const res = await axios.post(
        `${API_BASE}/api/tracking/from-backtest`,
        { symbols, names, categories },
        { headers: this._headers() }
      )
      await this.fetchAll()
      return res.data
    },

    async fetchAlertLogs() {
      const res = await axios.get(`${API_BASE}/api/tracking/alerts`, { headers: this._headers() })
      this.alertLogs = res.data
    },

    async fetchRSIData(id) {
      try {
        const res = await axios.get(
          `${API_BASE}/api/tracking/${id}/rsi-data`,
          { headers: this._headers() }
        )
        this.rsiData[id] = res.data
        return res.data
      } catch (e) {
        console.error(`Failed to fetch RSI data for tracking ${id}:`, e)
        throw e
      }
    },
  },
})
