<template>
  <div class="share-image-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加載圖像...</p>
    </div>

    <!-- Success State -->
    <div v-else-if="imageUrl" class="success-state">
      <div class="image-wrapper">
        <img :src="imageUrl" :alt="`${resultType} 分享圖像`" class="shared-image" @error="onImageError" />
      </div>
      <div class="actions">
        <button @click="downloadImage" class="btn-download">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          下載圖像
        </button>
        <button @click="copyLink" class="btn-share">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.658 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          複製連結
        </button>
      </div>
      <div v-if="copied" class="copied-message">✓ 已複製連結</div>
    </div>

    <!-- Error State -->
    <div v-else class="error-state">
      <div class="error-icon">⚠️</div>
      <h2>無法加載圖像</h2>
      <p>{{ errorMessage }}</p>
      <p class="help-text">圖像可能已過期（30 天）或不存在。請重新生成分享。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const imageHash = route.params.imageHash
const loading = ref(true)
const imageUrl = ref(null)
const errorMessage = ref('')
const copied = ref(false)

const resultType = computed(() => {
  // 從 URL 推斷結果類型（可選）
  return 'backtest' // 默認值，可以從路由參數獲取
})

const loadImage = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    const apiBase = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8005' : window.location.origin)
    imageUrl.value = `${apiBase}/api/backtest/share/image/${imageHash}`
    // 讓 <img> 的 @error handler 處理載入失敗
    loading.value = false
  } catch (err) {
    loading.value = false
    errorMessage.value = err.message || '無法加載圖像，請確認連結正確。'
    imageUrl.value = null
  }
}

const onImageError = () => {
  imageUrl.value = null
  errorMessage.value = '圖像不存在或已過期（30天）'
}

const downloadImage = async () => {
  try {
    const response = await fetch(imageUrl.value)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${resultType.value}_${imageHash}.png`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('Download failed:', err)
  }
}

const copyLink = async () => {
  try {
    const url = window.location.href
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(url)
    } else {
      // 備用方案
      const input = document.createElement('input')
      input.value = url
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
    }
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}

onMounted(() => {
  loadImage()
})
</script>

<style scoped>
.share-image-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.loading-state,
.error-state,
.success-state {
  text-align: center;
  color: white;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.success-state {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.1);
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  color: #1f2937;
}

.image-wrapper {
  margin-bottom: 2rem;
  text-align: center;
}

.shared-image {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-download,
.btn-share {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-download {
  background: #667eea;
  color: white;
}

.btn-download:hover {
  background: #5568d3;
}

.btn-share {
  background: #f3f4f6;
  color: #1f2937;
}

.btn-share:hover {
  background: #e5e7eb;
}

.copied-message {
  margin-top: 1rem;
  color: #10b981;
  font-weight: 600;
  font-size: 0.875rem;
}

.error-state {
  background: white;
  border-radius: 1rem;
  padding: 3rem 2rem;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.1);
  max-width: 28rem;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-state h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.error-state p {
  color: #6b7280;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.help-text {
  font-size: 0.875rem;
  color: #9ca3af;
}
</style>
