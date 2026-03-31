import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'
import { fetchDividendCalendar, fetchUpcomingDividends } from '../api/dividend'

export const useDividendStore = defineStore('dividend', () => {
  const auth = useAuthStore()

  const currentYear = ref(new Date().getFullYear())
  const currentMonth = ref(new Date().getMonth() + 1)
  const calendarItems = ref([])
  const upcomingItems = ref([])
  const loading = ref(false)
  const error = ref(null)

  /** 依日期分組：{ 'YYYY-MM-DD': [item, ...] } */
  const calendarByDate = computed(() => {
    const map = {}
    for (const item of calendarItems.value) {
      if (!map[item.ex_date]) map[item.ex_date] = []
      map[item.ex_date].push(item)
    }
    return map
  })

  async function loadCalendar(year, month) {
    loading.value = true
    error.value = null
    try {
      const res = await fetchDividendCalendar(auth.token, year, month)
      calendarItems.value = res.data
      currentYear.value = year
      currentMonth.value = month
    } catch (e) {
      error.value = e?.response?.data?.detail || '載入失敗'
    } finally {
      loading.value = false
    }
  }

  async function loadUpcoming(days = 30) {
    try {
      const res = await fetchUpcomingDividends(auth.token, days)
      upcomingItems.value = res.data
    } catch (e) {
      error.value = e?.response?.data?.detail || '載入失敗'
    }
  }

  function prevMonth() {
    if (currentMonth.value === 1) {
      loadCalendar(currentYear.value - 1, 12)
    } else {
      loadCalendar(currentYear.value, currentMonth.value - 1)
    }
  }

  function nextMonth() {
    if (currentMonth.value === 12) {
      loadCalendar(currentYear.value + 1, 1)
    } else {
      loadCalendar(currentYear.value, currentMonth.value + 1)
    }
  }

  return {
    currentYear,
    currentMonth,
    calendarItems,
    upcomingItems,
    loading,
    error,
    calendarByDate,
    loadCalendar,
    loadUpcoming,
    prevMonth,
    nextMonth,
  }
})
