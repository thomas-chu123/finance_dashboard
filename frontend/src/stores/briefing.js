import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import { fetchLatestBriefing, triggerBriefing } from '../api/briefing'

export const useBriefingStore = defineStore('briefing', {
  state: () => ({
    items: [],
    sessionTime: null,
    provider: null,
    loading: false,
    error: null,
    _lastFetched: 0,  // timestamp ms，用於 TTL 快取
  }),

  actions: {
    /**
     * 從後端載入最新一次排程早報
     */
    async fetchLatestBriefing({ force = false, silent = false } = {}) {
      const authStore = useAuthStore()
      if (!authStore.token) return

      // 5 分鐘內已有資料且非強制刷新，直接跳過
      const TTL_MS = 5 * 60 * 1000
      if (!force && this.items.length > 0 && Date.now() - this._lastFetched < TTL_MS) return

      if (!silent) {
        this.loading = true
        this.error = null
      }

      try {
        const resp = await fetchLatestBriefing(authStore.token)
        this.sessionTime = resp.data.session_time
        this.provider = resp.data.provider || null
        this.items = resp.data.items || []
        this._lastFetched = Date.now()
      } catch (err) {
        if (!silent) {
          this.error = err?.response?.data?.detail || '載入 AI 早報失敗'
        }
        console.error('[BriefingStore]', err)
      } finally {
        if (!silent) {
          this.loading = false
        }
      }
    },

    /**
     * 手動觸發早報排程，並以 polling 等待新結果出現。
     * 後端 /trigger 回傳觸發時的 session_time，前端每 5 秒輪測
     * /latest，直到 session_time >= 觸發時間（最多等 90 秒）。
     */
    async triggerRefresh() {
      const authStore = useAuthStore()
      if (!authStore.token) return

      let newSessionTime = null
      try {
        const resp = await triggerBriefing(authStore.token)
        newSessionTime = resp.data?.session_time ?? null
      } catch (err) {
        console.error('[BriefingStore] trigger failed:', err)
        return
      }

      const POLL_INTERVAL = 5000
      const MAX_POLLS = 18  // 最多 90 秒

      if (!newSessionTime) {
        // Fallback：無 session_time 可比較時，延遲一次強制拉取
        await new Promise(r => setTimeout(r, POLL_INTERVAL))
        await this.fetchLatestBriefing({ force: true })
        return
      }

      // Polling：每 5 秒查詢，直到 latest session_time >= 觸發時間
      for (let i = 0; i < MAX_POLLS; i++) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL))
        await this.fetchLatestBriefing({ force: true, silent: true })
        if (this.sessionTime && new Date(this.sessionTime) >= new Date(newSessionTime)) break
      }
    },
  },
})
