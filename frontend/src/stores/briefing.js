import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import { fetchLatestBriefing, triggerBriefing } from '../api/briefing'

export const useBriefingStore = defineStore('briefing', {
  state: () => ({
    items: [],
    sessionTime: null,
    loading: false,
    error: null,
  }),

  actions: {
    /**
     * 從後端載入最新一次排程早報
     */
    async fetchLatestBriefing() {
      const authStore = useAuthStore()
      if (!authStore.token) return

      this.loading = true
      this.error = null

      try {
        const resp = await fetchLatestBriefing(authStore.token)
        this.sessionTime = resp.data.session_time
        this.items = resp.data.items || []
      } catch (err) {
        this.error = err?.response?.data?.detail || '載入 AI 早報失敗'
        console.error('[BriefingStore]', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * 手動觸發早報排程，然後重新拉取結果
     */
    async triggerRefresh() {
      const authStore = useAuthStore()
      if (!authStore.token) return

      try {
        await triggerBriefing(authStore.token)
      } catch (err) {
        console.error('[BriefingStore] trigger failed:', err)
      }
      // 背景排程需要時間，等 3 秒後重新拉取
      setTimeout(() => this.fetchLatestBriefing(), 3000)
    },
  },
})
