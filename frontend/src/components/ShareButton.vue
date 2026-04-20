<template>
  <div class="share-button-container">
    <!-- 分享按鈕 - 直接觸發分享 -->
    <button
      @click="handleQuickShare"
      :disabled="isLoading"
      class="btn-share"
      title="分享此投組"
    >
      <svg v-if="!isLoading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C9.589 12.938 10 12.077 10 11.25c0-1.657-1.343-3-3-3s-3 1.343-3 3 1.343 3 3 3c.423 0 .815-.1 1.197-.292m9.457-5.966A9.967 9.967 0 1012 20.25m4.772-4.772a9.969 9.969 0 01-5.087 2.025" />
      </svg>
      <span v-else class="spinner"></span>
      {{ isLoading ? '分享中...' : '分享' }}
    </button>

    <!-- 分享連結模態窗口 (用於 Safari 或 clipboard API 失敗) -->
    <transition name="fade">
      <div v-if="showShareModal" class="share-modal-overlay" @click="closeModal">
        <div class="share-modal" @click.stop>
          <div class="share-modal-header">
            <h3>分享連結已生成</h3>
            <button class="modal-close" @click="closeModal">&times;</button>
          </div>
          
          <div class="share-modal-body">
            <p class="share-hint">點擊下方連結複製，或手動複製：</p>
            
            <div class="share-link-container">
              <input 
                v-model="shareUrl" 
                type="text" 
                class="share-link-input" 
                readonly
                ref="linkInput"
              />
              <button class="btn-copy" @click="copyFromModal">
                {{ copyButtonText }}
              </button>
            </div>
            
            <p class="share-url-display">
              {{ shareUrl }}
            </p>
          </div>
          
          <div class="share-modal-footer">
            <button class="btn-close" @click="closeModal">完成</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 成功提示 -->
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
const showShareModal = ref(false)
const shareUrl = ref('')
const copyButtonText = ref('複製')
const linkInput = ref(null)

// 嘗試使用 Clipboard API 複製
const tryClipboardCopy = async (text) => {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      console.warn('Clipboard API failed:', err)
      return false
    }
  }
  return false
}

// 備用複製方案（同步上下文）
const tryExecCommandCopy = () => {
  try {
    if (linkInput.value) {
      linkInput.value.select()
      const success = document.execCommand('copy')
      if (success) {
        return true
      }
    }
  } catch (err) {
    console.error('execCommand failed:', err)
  }
  return false
}

// 從模態框複製
const copyFromModal = async () => {
  if (await tryClipboardCopy(shareUrl.value)) {
    copyButtonText.value = '已複製 ✓'
    setTimeout(() => {
      copyButtonText.value = '複製'
    }, 2000)
  } else if (tryExecCommandCopy()) {
    copyButtonText.value = '已複製 ✓'
    setTimeout(() => {
      copyButtonText.value = '複製'
    }, 2000)
  } else {
    copyButtonText.value = '複製失敗'
    setTimeout(() => {
      copyButtonText.value = '複製'
    }, 2000)
  }
}

const closeModal = () => {
  showShareModal.value = false
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

    // 嘗試複製分享連結到剪貼簿
    if (response.share_url) {
      shareUrl.value = response.share_url
      
      // 首先嘗試直接複製
      const clipboardSuccess = await tryClipboardCopy(response.share_url)
      
      if (clipboardSuccess) {
        // Clipboard API 成功
        showSuccessMessage.value = true
        setTimeout(() => {
          showSuccessMessage.value = false
        }, 3000)
        emit('share-success', response)
      } else {
        // Clipboard API 失敗，顯示模態框讓用戶手動複製
        showShareModal.value = true
        emit('share-success', response)
      }
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

/* 模態窗口樣式 */
.share-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.share-modal {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  overflow: hidden;
}

.share-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.share-modal-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #1f2937;
}

.share-modal-body {
  padding: 1.5rem;
}

.share-hint {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.share-link-container {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.share-link-input {
  flex: 1;
  padding: 0.625rem 0.875rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-family: monospace;
  color: #1f2937;
}

.share-link-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-copy {
  padding: 0.625rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.btn-copy:hover {
  background: #5568d3;
}

.btn-copy:active {
  background: #4c5fc7;
}

.share-url-display {
  padding: 0.875rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  color: #6b7280;
  word-break: break-all;
  margin: 0;
  font-family: monospace;
}

.share-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-close {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #1f2937;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-close:hover {
  background: #d1d5db;
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
