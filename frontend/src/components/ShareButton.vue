<template>
  <div class="share-button-container">
    <!-- 分享按鈕 -->
    <button
      @click="showShareModal = true"
      :disabled="isLoading"
      class="btn-share"
      title="分享此投組到社群"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C9.589 12.938 10 12.077 10 11.25c0-1.657-1.343-3-3-3s-3 1.343-3 3 1.343 3 3 3c.423 0 .815-.1 1.197-.292m9.457-5.966A9.967 9.967 0 1012 20.25m4.772-4.772a9.969 9.969 0 01-5.087 2.025" />
      </svg>
      分享
    </button>

    <!-- 分享模態框 -->
    <div v-if="showShareModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>分享投組</h2>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>

        <div class="modal-body">
          <!-- 進度步驟 -->
          <div class="steps">
            <div :class="['step', { active: step === 1, completed: step > 1 }]">
              <div class="step-num">1</div>
              <div>生成快照</div>
            </div>
            <div :class="['step', { active: step === 2, completed: step > 2 }]">
              <div class="step-num">2</div>
              <div>上傳到伺服器</div>
            </div>
            <div :class="['step', { active: step === 3, completed: step > 3 }]">
              <div class="step-num">3</div>
              <div>取得分享連結</div>
            </div>
          </div>

          <!-- Step 1: 配置 -->
          <div v-if="step === 1" class="step-content">
            <div class="form-group">
              <label>分享類型</label>
              <select v-model="shareConfig.share_type" class="form-control">
                <option value="snapshot">快照（建議）- 一旦建立就不再變更</option>
                <option value="public">實時 - 投組編輯後自動更新</option>
              </select>
            </div>

            <div class="form-group">
              <label>過期時間</label>
              <select v-model.number="shareConfig.expires_in_days" class="form-control">
                <option :value="7">7 天</option>
                <option :value="30">30 天（建議）</option>
                <option :value="90">90 天</option>
                <option :value="365">1 年</option>
                <option :value="null">永不過期</option>
              </select>
            </div>

            <div class="form-group">
              <label>分享描述（可選）</label>
              <textarea
                v-model="shareConfig.share_description"
                placeholder="例如：年化報酬 12.5%，夏普比例 0.95"
                class="form-control"
                rows="3"
              ></textarea>
            </div>

            <button @click="generateShare" :disabled="isLoading" class="btn-primary">
              <span v-if="!isLoading">下一步：生成分享</span>
              <span v-else>
                <span class="spinner"></span>
                正在生成...
              </span>
            </button>
          </div>

          <!-- Step 2: 進度 -->
          <div v-if="step === 2" class="step-content">
            <div class="progress-container">
              <div class="progress-text">正在生成分享...</div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <div class="progress-percent">{{ uploadProgress }}%</div>
            </div>
          </div>

          <!-- Step 3: 成功 -->
          <div v-if="step === 3 && shareResult" class="step-content success">
            <div class="success-icon">✓</div>
            <h3>分享成功！</h3>

            <div class="share-info">
              <div class="info-item">
                <label>分享短碼</label>
                <div class="share-key">{{ shareResult.share_key }}</div>
              </div>

              <div class="info-item">
                <label>分享連結</label>
                <div class="share-url-container">
                  <input
                    type="text"
                    :value="shareResult.share_url"
                    readonly
                    class="share-url"
                  />
                  <button @click="copyToClipboard" class="btn-copy">複製</button>
                </div>
              </div>

              <div v-if="shareResult.expires_at" class="info-item">
                <label>過期時間</label>
                <div>{{ formatDate(shareResult.expires_at) }}</div>
              </div>

              <div class="info-item">
                <label>瀏覽次數</label>
                <div>{{ shareResult.view_count }}</div>
              </div>
            </div>

            <!-- 社群分享按鈕 -->
            <div class="social-share-buttons">
              <a
                :href="`https://twitter.com/intent/tweet?text=查看我的投資策略：${shareResult.share_url}`"
                target="_blank"
                class="social-btn twitter"
                title="分享到 Twitter"
              >
                𝕏
              </a>
              <a
                :href="`https://www.facebook.com/sharer/sharer.php?u=${shareResult.share_url}`"
                target="_blank"
                class="social-btn facebook"
                title="分享到 Facebook"
              >
                f
              </a>
              <a
                :href="`https://line.me/R/msg/0?${encodeURIComponent(shareResult.share_url)}`"
                target="_blank"
                class="social-btn line"
                title="分享到 LINE"
              >
                LINE
              </a>
              <a
                :href="`mailto:?subject=查看我的投資策略&body=${shareResult.share_url}`"
                class="social-btn email"
                title="透過電郵分享"
              >
                ✉
              </a>
            </div>
          </div>

          <!-- 錯誤提示 -->
          <div v-if="error" class="error-message">
            <strong>❌ 錯誤：</strong> {{ error }}
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeModal" class="btn-secondary">
            {{ step === 3 ? '關閉' : '取消' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
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

const authStore = useAuthStore()
const showShareModal = ref(false)
const step = ref(1)
const isLoading = ref(false)
const uploadProgress = ref(0)
const error = ref(null)
const shareResult = ref(null)

const shareConfig = ref({
  share_type: 'snapshot',
  expires_in_days: 30,
  share_description: '',
})

const generateShare = async () => {
  try {
    error.value = null
    isLoading.value = true
    step.value = 2
    uploadProgress.value = 0

    // 模擬上傳進度
    const progressInterval = setInterval(() => {
      uploadProgress.value = Math.min(uploadProgress.value + Math.random() * 30, 90)
    }, 300)

    // 調用 API 生成分享
    const response = await sharePortfolio(props.portfolioId, {
      share_type: shareConfig.value.share_type,
      expires_in_days: shareConfig.value.expires_in_days,
      share_description: shareConfig.value.share_description,
    })

    clearInterval(progressInterval)
    uploadProgress.value = 100

    // 延遲顯示成功畫面
    await new Promise(resolve => setTimeout(resolve, 500))

    shareResult.value = response
    step.value = 3

    emit('share-success', response)
  } catch (err) {
    error.value = err.message || '分享失敗，請重試'
    step.value = 1
  } finally {
    isLoading.value = false
  }
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(shareResult.value.share_url)
    alert('✅ 已複製到剪貼板！')
  } catch (err) {
    alert('❌ 複製失敗，請手動複製')
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const closeModal = () => {
  showShareModal.value = false
  // 重置表單
  setTimeout(() => {
    step.value = 1
    error.value = null
    shareResult.value = null
    uploadProgress.value = 0
    shareConfig.value = {
      share_type: 'snapshot',
      expires_in_days: 30,
      share_description: '',
    }
  }, 300)
}
</script>

<style scoped>
.share-button-container {
  display: inline-block;
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
}

.btn-share:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-share:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-share svg {
  width: 1.25rem;
  height: 1.25rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(2rem);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.close-btn:hover {
  color: #1f2937;
}

.modal-body {
  padding: 2rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
}

/* Steps */
.steps {
  display: flex;
  justify-content: space-around;
  margin-bottom: 2rem;
  gap: 1rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #9ca3af;
  font-size: 0.875rem;
}

.step.active {
  color: #667eea;
}

.step.completed {
  color: #10b981;
}

.step-num {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  border: 2px solid currentColor;
}

.step.completed .step-num::after {
  content: '✓';
}

.step.completed .step-num {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.step-content {
  animation: fadeIn 0.3s ease;
}

/* Form */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.form-control {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Buttons */
.btn-primary,
.btn-secondary,
.btn-copy {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #667eea;
  color: white;
  width: 100%;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-copy {
  background: #f3f4f6;
  color: #374151;
  padding: 0.5rem 0.75rem;
  margin-left: 0.5rem;
}

.btn-copy:hover {
  background: #e5e7eb;
}

/* Progress */
.progress-container {
  text-align: center;
}

.progress-text {
  font-weight: 600;
  margin-bottom: 1rem;
  color: #374151;
}

.progress-bar {
  height: 0.5rem;
  background: #e5e7eb;
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.progress-percent {
  font-size: 0.875rem;
  color: #6b7280;
}

/* Success */
.success {
  text-align: center;
}

.success-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: scaleIn 0.5s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}

.success h3 {
  font-size: 1.5rem;
  color: #10b981;
  margin-bottom: 1.5rem;
}

/* Share Info */
.share-info {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  margin-bottom: 1rem;
  text-align: left;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item label {
  display: block;
  font-weight: 600;
  color: #6b7280;
  font-size: 0.75rem;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.share-key {
  font-family: monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #667eea;
  word-break: break-all;
}

.share-url-container {
  display: flex;
  gap: 0.5rem;
}

.share-url {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-family: monospace;
  background: white;
}

/* Social Share Buttons */
.social-share-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.social-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.3s ease;
  color: white;
}

.social-btn.twitter {
  background: #000;
}

.social-btn.twitter:hover {
  background: #333;
  transform: scale(1.1);
}

.social-btn.facebook {
  background: #1877f2;
}

.social-btn.facebook:hover {
  background: #0a66c2;
  transform: scale(1.1);
}

.social-btn.line {
  background: #00b900;
}

.social-btn.line:hover {
  background: #008000;
  transform: scale(1.1);
}

.social-btn.email {
  background: #ea4335;
}

.social-btn.email:hover {
  background: #d33425;
  transform: scale(1.1);
}

/* Spinner */
.spinner {
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Error */
.error-message {
  background: #fee;
  color: #c00;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-top: 1rem;
  font-size: 0.875rem;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .modal-content {
    background: #1f2937;
    color: #f3f4f6;
  }

  .modal-header {
    border-bottom-color: #374151;
  }

  .modal-header h2 {
    color: #f3f4f6;
  }

  .close-btn {
    color: #9ca3af;
  }

  .close-btn:hover {
    color: #f3f4f6;
  }

  .form-group label {
    color: #e5e7eb;
  }

  .form-control {
    background: #111827;
    border-color: #374151;
    color: #f3f4f6;
  }

  .form-control:focus {
    border-color: #667eea;
  }

  .success h3 {
    color: #10b981;
  }

  .share-info {
    background: #111827;
  }

  .info-item label {
    color: #9ca3af;
  }

  .share-url {
    background: #111827;
    border-color: #374151;
    color: #f3f4f6;
  }
}
</style>
