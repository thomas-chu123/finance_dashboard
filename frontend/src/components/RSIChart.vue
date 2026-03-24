<template>
  <div class="w-full h-full min-h-[400px] bg-[var(--bg-main)] rounded-xl border border-[var(--border-color)]">
    <div ref="chartRef" class="w-full h-full"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  darkMode: {
    type: Boolean,
    default: true
  }
})

const chartRef = ref(null)
let chart = null

// Generate sample historical data
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
    
    // Realistic price movement
    priceBase += (Math.random() - 0.48) * 2
    prices.push(Math.max(priceBase, 10).toFixed(2))
    
    // Realistic RSI movement
    rsiBase = Math.max(10, Math.min(90, rsiBase + (Math.random() - 0.5) * 15))
    rsiValues.push(Math.round(rsiBase))
  }
  
  return { dates, prices, rsiValues }
}

const { dates, prices, rsiValues } = generateSampleData()

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
    { left: '10%', right: '5%', top: '60px', height: '55%' },
    { left: '10%', right: '5%', top: '62%', height: '30%' }
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

onMounted(() => {
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
</script>

<style scoped>
/* Component styles */
</style>
