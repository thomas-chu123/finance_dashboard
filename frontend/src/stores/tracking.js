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
      const auth = useAuthStore()
      const headers = auth.headers
      console.log('[TrackingStore] Using headers:', {
        hasToken: !!auth.token,
        userId: auth.userId,
        isLoggedIn: auth.isLoggedIn,
        authorizationHeader: headers.Authorization ? headers.Authorization.substring(0, 20) + '...' : 'none'
      })
      return headers
    },

    async fetchAll() {
      this.loading = true
      try {
        const headers = this._headers()
        if (!headers.Authorization || headers.Authorization === 'Bearer null') {
          throw new Error('Not authenticated - no valid token found')
        }
        
        console.log('[TrackingStore] Fetching all tracking items...')
        const res = await axios.get(`${API_BASE}/api/tracking`, { headers })
        console.log('[TrackingStore] Received', res.data.length, 'tracking items')
        
        // Ensure category field exists for backward compatibility
        this.items = (res.data || []).map(item => ({
          ...item,
          category: item.category || 'us_etf' // Default to us_etf if missing
        }))
        
        console.log('[TrackingStore] After normalization:', this.items.length, 'items')
        return this.items
      } catch (e) {
        console.error('[TrackingStore] Error fetching tracking items:', e)
        this.items = []
        throw e
      } finally {
        this.loading = false
      }
    },

    async create(data) {
      try {
        console.log('[TrackingStore.create] Creating with data:', { symbol: data.symbol, name: data.name, trigger_mode: data.trigger_mode })
        const res = await axios.post(`${API_BASE}/api/tracking`, data, { headers: this._headers() })
        console.log('[TrackingStore.create] Response:', res.data)
        const newItem = {
          ...res.data,
          category: res.data.category || data.category || 'us_etf'
        }
        this.items.unshift(newItem)
        console.log('[TrackingStore] Created new item:', newItem.id, newItem.symbol)
        return newItem
      } catch (e) {
        console.error('[TrackingStore.create] Error:', {
          message: e.message,
          status: e.response?.status,
          detail: e.response?.data?.detail,
          data: e.response?.data
        })
        throw e
      }
    },

    async update(id, data) {
      const res = await axios.put(`${API_BASE}/api/tracking/${id}`, data, { headers: this._headers() })
      const updatedItem = {
        ...res.data,
        category: res.data.category || data.category || this.items.find(i => i.id === id)?.category || 'us_etf'
      }
      const idx = this.items.findIndex((i) => i.id === id)
      if (idx !== -1) {
        this.items[idx] = updatedItem
        console.log('[TrackingStore] Updated item:', id)
      }
      return updatedItem
    },

    async remove(id) {
      await axios.delete(`${API_BASE}/api/tracking/${id}`, { headers: this._headers() })
      const itemName = this.items.find(i => i.id === id)?.symbol || id
      this.items = this.items.filter((i) => i.id !== id)
      console.log('[TrackingStore] Removed item:', itemName)
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
      try {
        console.log('[TrackingStore] Fetching alert logs...')
        const res = await axios.get(`${API_BASE}/api/tracking/alerts`, { headers: this._headers() })
        this.alertLogs = res.data
        console.log('[TrackingStore] Alert logs loaded:', this.alertLogs.length, 'logs')
        return this.alertLogs
      } catch (e) {
        console.error('[TrackingStore] Failed to fetch alert logs:', e)
        this.alertLogs = []
        throw e
      }
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
