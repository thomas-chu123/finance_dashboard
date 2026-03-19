import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { useAuthStore } from './stores/auth'
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, ScatterChart, HeatmapChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent,
  ToolboxComponent,
  MarkLineComponent,
} from 'echarts/components'
import './assets/main.css'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  ScatterChart,
  HeatmapChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent,
  ToolboxComponent,
  MarkLineComponent,
])

// Global Console Interceptor for remote logging
const originalConsoleLog = console.log
const originalConsoleWarn = console.warn
const originalConsoleError = console.error

function sendLog(level, ...args) {
  try {
    const message = args.map(arg => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg))).join(' ')
    fetch('/api/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level: level,
        message: message,
        url: window.location.href,
        details: navigator.userAgent
      })
    }).catch(() => {})
  } catch (err) {
    // Ignore serialization errors
  }
}

console.log = function(...args) {
  originalConsoleLog.apply(console, args)
  sendLog('info', ...args)
}
console.warn = function(...args) {
  originalConsoleWarn.apply(console, args)
  sendLog('warn', ...args)
}
console.error = function(...args) {
  originalConsoleError.apply(console, args)
  sendLog('error', ...args)
}

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// Global Axios Interceptor for 401
const authStore = useAuthStore(pinia)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (authStore.token) {
        authStore.logout()
        alert('您的登入已過期或被登出，請重新登入！')
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

app.component('VChart', ECharts)
app.mount('#app')
