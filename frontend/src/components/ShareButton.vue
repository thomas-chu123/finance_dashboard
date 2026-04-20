<template>
  <div class="share-button-container">
    <!-- 分享按鈕 - 直接觸發分享 -->
    <button
      @click="handleQuickShare"
      :disabled="isLoading"
      class="btn-share"
      title="分享此投組 (一鍵複製連結)"
    >
      <svg v-if="!isLoading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C9.589 12.938 10 12.077 10 11.25c0-1.657-1.343-3-3-3s-3 1.343-3 3 1.343 3 3 3c.423 0 .815-.1 1.197-.292m9.457-5.966A9.967 9.967 0 1012 20.25m4.772-4.772a9.969 9.969 0 01-5.087 2.025" />
      </svg>
      <span v-else class="spinner"></span>
      {{ isLoading ? '分享中...' : '分享' }}
    </button>

    <!-- 簡化的分享完成提示 -->
    <transition name="fade">
      <div v-if="showSuccessMessage" class="share-success-toast">
        ✓ 已複製分享連結到剪貼簿
      </div>
    </transition>

    <!-- 錯誤提示 -->
    <transition name="fade">
      <div v-if="showErrorMessage" class="share-error-toast">
        ✕ {{ errorMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { sharePortfolio } from '@/api/shares'

const props = defineProps({
  portfolioId: {
    type: String,
    required: true,
  },
  portfolioName: {
    type: String,
    default: 'Investment Portfolio',
  },
})

const emit = defineEmits(['share-success'])

const isLoading = ref(false)
const showSuccessMessage = ref(false)
const showErrorMessage = ref(false)
const errorMessage = ref('')

// 備用複製方案（用於舊瀏覽器或 API 不可用時）
const copyToClipboardFallback = (text) => {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  textarea.style.left = '-999999px'
  
  document.body.appendChild(textarea)
  textarea.select()
  
  const success = document.execCommand('copy')
  document.body.removeChild(textarea)
  
  if (!success) {
    throw new Error('execCommand copy failed')
  }
}

const handleQuickShare = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    showErrorMessage.value = false
    showSuccessMessage.value = false

    // 使用預設配置直接生成分享
    const response = await sharePortfolio(props.portfolioId, {
      share_type: 'snapshot',
      expires_in_days: 30,
      share_description: '',
    })

    // 複製分享連結到剪貼簿
    if (response.share_url) {
      try {
        // 嘗試使用現代 Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(response.share_url)
        } else {
          // 備用方案：使用舊式 execCommand
          copyToClipboardFallback(response.share_url)
        }
      } catch (clipboardErr) {
        console.warn('Clipboard API failed, using fallback method:', clipboardErr)
        try {
          copyToClipboardFallback(response.share_url)
        } catch (fallbackErr) {
          console.error('Fallback copy also failed:', fallbackErr)
          // 即使複製失敗，也顯示連結已生成
          errorMessage.value = `分享已生成，但無法自動複製連結。連結：${response.share_url}`
          showErrorMessage.value = true
          setTimeout(() => {
            showErrorMessage.value = false
          }, 5000)
          throw new Error('無法複製連結，但分享已成功生成')
        }
      }
      
      showSuccessMessage.value = true
      
      // 3 秒後隱藏成功訊息
      setTimeout(() => {
        showSuccessMessage.value = false
      }, 3000)

      // 觸發成功事件
      emit('share-success', response)
    }
  } catch (err) {
    // 解析錯誤消息
    let message = '分享失敗，請稍後重試'
    
    if (err.response?.data?.detail) {
      message = err.response.data.detail
    } else if (err.message) {
      message = err.message
    }
    
    // 檢查常見的認證錯誤
    if (message.includes('401') || message.includes('Not authenticated')) {
      message = '認證失敗，請重新登入'
    }
    
    console.error('Share error:', { status: err.response?.status, message, fullError: err })
    
    errorMessage.value = message
    showErrorMessage.value = true

    // 5 秒後隱藏錯誤訊息
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.share-button-container {
  display: inline-block;
  position: relative;
}

.btn-share {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-share:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-share:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.share-success-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #10b981;
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-weight: 500;
  z-index: 9999;
}

.share-error-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #ef4444;
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-weight: 500;
  z-index: 9999;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
