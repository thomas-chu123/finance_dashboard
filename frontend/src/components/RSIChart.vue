<template>
  <div class="w-full bg-[var(--bg-main)] rounded-xl border border-[var(--border-color)]" style="height: 400px;">
    <div ref="chartRef" class="w-full h-full"></div>
    <div v-if="isLoading" class="absolute inset-0 bg-black/20 rounded-xl flex items-center justify-center">
      <div class="text-zinc-400 text-sm font-bold">載入歷史數據中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  trackingId: {
    type: String,
    default: null
  },
  darkMode: {
    type: Boolean,
    default: true
  }
})

const chartRef = ref(null)
let chart = null
const isLoading = ref(false)
const historyData = ref(null)
const authStore = useAuthStore()

// 取得 API 基礎 URL（優先使用環境變數，否則使用相同域名）
const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin)

// 產生示例歷史資料（備用方案）
const generateSampleData = () => {
  const dates = []
  const prices = []
  const rsiValues = []
  
  const now = new Date()
  let priceBase = props.item.current_price || 100
  let rsiBase = 50
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' }))
    
    // 逼真的價格變動
    priceBase += (Math.random() - 0.48) * 2
    prices.push(Math.max(priceBase, 10).toFixed(2))
    
    // 逼真的 RSI 變動
    rsiBase = Math.max(10, Math.min(90, rsiBase + (Math.random() - 0.5) * 15))
    rsiValues.push(Math.round(rsiBase))
  }
  
  return { dates, prices, rsiValues }
}

// 數據初始化
let dates = []
let prices = []
let rsiValues = []

// 從 API 獲取真實的歷史 RSI 數據
const fetchHistoricalRSIData = async () => {
  if (!props.trackingId) {
    console.warn('❌ RSIChart: trackingId not provided, using sample data')
    return null
  }

  isLoading.value = true
  try {
    // 優先從 auth store 取得 token，否則從 localStorage 讀取舊 key
    const token = authStore.token || localStorage.getItem('fd_token')
    
    if (!token) {
      console.warn('❌ RSIChart: No auth token found (checked: fd_token, authStore.token), using sample data')
      console.debug('  authStore.token:', !!authStore.token)
      console.debug('  localStorage.fd_token:', !!localStorage.getItem('fd_token'))
      isLoading.value = false
      return null
    }

    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const url = `${API_BASE}/api/tracking/${props.trackingId}/rsi-history`
    console.log(`📊 RSIChart: Fetching RSI history from ${url}`)
    console.debug('  Token present:', !!token)
    console.debug('  trackingId:', props.trackingId)
    
    const response = await axios.get(url, { headers })
    
    if (response.data && response.data.dates && response.data.rsi_values && response.data.dates.length > 0) {
      console.log(`✅ RSIChart: Successfully fetched ${response.data.dates.length} days of RSI data`)
      return response.data
    } else {
      console.warn('❌ RSIChart: API response missing required fields or empty', {
        hasDates: !!response.data?.dates,
        hasRsiValues: !!response.data?.rsi_values,
        datesLength: response.data?.dates?.length || 0
      })
      return null
    }
  } catch (error) {
    console.error('❌ RSIChart: Failed to fetch RSI history:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    })
    return null
  } finally {
    isLoading.value = false
  }
}

const chartOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: props.darkMode ? '#1f2937' : '#ffffff',
    borderColor: props.darkMode ? '#374151' : '#e5e7eb',
    textStyle: {
      color: props.darkMode ? '#f3f4f6' : '#1f2937'
    }
  },
  legend: {
    data: ['價格', 'RSI'],
    textStyle: {
      color: props.darkMode ? '#d1d5db' : '#4b5563'
    },
    top: 10,
    left: 'center'
  },
  grid: [
    { left: '10%', right: '5%', top: '60px', height: '43%' },
    { left: '10%', right: '5%', top: '72%', height: '25%' }
  ],
  xAxis: [
    {
      type: 'category',
      data: dates,
      gridIndex: 0,
      boundaryGap: false,
      axisLabel: { color: props.darkMode ? '#9ca3af' : '#6b7280', interval: 5 },
      axisLine: { lineStyle: { color: props.darkMode ? '#374151' : '#e5e7eb' } }
    },
    {
      type: 'category',
      data: dates,
      gridIndex: 1,
      boundaryGap: false,
      axisLabel: { color: props.darkMode ? '#9ca3af' : '#6b7280', interval: 5 },
      axisLine: { lineStyle: { color: props.darkMode ? '#374151' : '#e5e7eb' } }
    }
  ],
  yAxis: [
    {
      type: 'value',
      gridIndex: 0,
      name: '價格 ($)',
      nameTextStyle: { color: props.darkMode ? '#9ca3af' : '#6b7280' },
      axisLabel: { color: props.darkMode ? '#9ca3af' : '#6b7280', formatter: '${value}' },
      axisLine: { lineStyle: { color: props.darkMode ? '#374151' : '#e5e7eb' } },
      splitLine: { lineStyle: { color: props.darkMode ? '#1f2937' : '#f3f4f6' } }
    },
    {
      type: 'value',
      gridIndex: 1,
      name: 'RSI',
      nameTextStyle: { color: props.darkMode ? '#9ca3af' : '#6b7280' },
      axisLabel: { color: props.darkMode ? '#9ca3af' : '#6b7280' },
      axisLine: { lineStyle: { color: props.darkMode ? '#374151' : '#e5e7eb' } },
      splitLine: { lineStyle: { color: props.darkMode ? '#1f2937' : '#f3f4f6' } },
      min: 0,
      max: 100
    }
  ],
  series: [
    {
      name: '價格',
      data: prices,
      type: 'line',
      xAxisIndex: 0,
      yAxisIndex: 0,
      smooth: true,
      itemStyle: { color: '#3b82f6' },
      lineStyle: { color: '#3b82f6', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0)' }
        ])
      },
      symbol: 'circle',
      symbolSize: 4
    },
    {
      name: 'RSI',
      data: rsiValues,
      type: 'line',
      xAxisIndex: 1,
      yAxisIndex: 1,
      smooth: true,
      itemStyle: { color: '#10b981' },
      lineStyle: { color: '#10b981', width: 2 },
      symbol: 'circle',
      symbolSize: 3
    }
  ]
}))

onMounted(async () => {
  // 嘗試從 API 獲取真實數據
  const data = await fetchHistoricalRSIData()
  
  if (data && data.dates && data.rsi_values && data.dates.length > 0) {
    // 使用真實的 RSI 數據
    historyData.value = data
    dates = data.dates
    rsiValues = data.rsi_values

    // 優先使用後端回傳的真實收盤價，若無則用模擬資料
    if (data.prices && data.prices.length === data.dates.length) {
      prices = data.prices.map(p => parseFloat(p).toFixed(2))
      console.log(`✅ 使用真實價格數據 (${prices.length} 天)`)
    } else {
      let priceBase = props.item.current_price || 100
      for (let i = 0; i < dates.length; i++) {
        priceBase += (Math.random() - 0.48) * 2
        prices.push(Math.max(priceBase, 10).toFixed(2))
      }
      console.warn('⚠️ 後端未回傳價格資料，使用模擬價格')
    }
    
    console.log(`✅ 使用真實 RSI 歷史數據 (${data.dates.length} 天)`)
  } else {
    // 備用：使用隨機生成的示例數據
    const sampleData = generateSampleData()
    dates = sampleData.dates
    prices = sampleData.prices
    rsiValues = sampleData.rsiValues
    console.warn(`⚠️ 使用示例數據 (無法獲取歷史 RSI)`)
  }
  
  // 初始化圖表
  if (chartRef.value) {
    chart = echarts.init(chartRef.value, props.darkMode ? 'dark' : 'light')
    chart.setOption(chartOption.value)
    
    window.addEventListener('resize', () => {
      chart?.resize()
    })
  }
})

watch(() => props.darkMode, () => {
  if (chart) {
    chart.dispose()
    chart = echarts.init(chartRef.value, props.darkMode ? 'dark' : 'light')
    chart.setOption(chartOption.value)
  }
})

watch(() => props.item?.id, async (newId) => {
  if (newId && props.trackingId) {
    // 當 item 改變時，重新獲取歷史數據
    const data = await fetchHistoricalRSIData()
    if (data && data.dates && data.rsi_values) {
      historyData.value = data
      dates = data.dates
      rsiValues = data.rsi_values

      // 使用真實價格或模擬價格
      if (data.prices && data.prices.length === data.dates.length) {
        prices = data.prices.map(p => parseFloat(p).toFixed(2))
      } else {
        prices = []
        let priceBase = props.item.current_price || 100
        for (let i = 0; i < dates.length; i++) {
          priceBase += (Math.random() - 0.48) * 2
          prices.push(Math.max(priceBase, 10).toFixed(2))
        }
      }

      // 更新圖表
      if (chart) {
        chart.setOption(chartOption.value)
      }
    }
  }
})
</script>

<style scoped>
/* Component styles */
</style>
