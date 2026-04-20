<template>
  <div class="public-share-container">
    <!-- 載入狀態 -->
    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>載入投組數據中...</p>
    </div>

    <!-- 錯誤狀態 -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">❌</div>
      <h2>無法載入分享</h2>
      <p>{{ error }}</p>
      <router-link to="/backtest" class="btn-back">返回回測</router-link>
    </div>

    <!-- 成功狀態 -->
    <div v-else-if="share" class="share-content">
      <!-- 頂部資訊欄 -->
      <div class="share-header">
        <div class="header-left">
          <h1>{{ share.portfolio.name }}</h1>
          <div class="meta">
            <span class="meta-item">
              <strong>類型：</strong>
              <span :class="`badge badge-${share.portfolio.portfolio_type}`">
                {{ portfolioTypeLabel }}
              </span>
            </span>
            <span class="meta-item">
              <strong>分享者：</strong> {{ share.shared_by || '匿名用戶' }}
            </span>
            <span class="meta-item">
              <strong>建立時間：</strong> {{ formatDate(share.created_at) }}
            </span>
            <span v-if="share.portfolio.expires_at" class="meta-item">
              <strong>過期時間：</strong>
              <span :class="{ 'text-red-500': isExpired }">
                {{ formatDate(share.portfolio.expires_at) }}
              </span>
            </span>
          </div>
        </div>
        <div class="header-right">
          <div class="view-count">
            <span class="count-number">{{ share.view_count }}</span>
            <span class="count-label">瀏覽次數</span>
          </div>
        </div>
      </div>

      <!-- 分享描述 -->
      <div v-if="share.portfolio.share_description" class="share-description">
        <h3>分享者備註</h3>
        <p>{{ share.portfolio.share_description }}</p>
      </div>

      <!-- 投組詳情 -->
      <div class="portfolio-details">
        <div class="detail-section">
          <h2>投組配置</h2>

          <!-- 基本信息 -->
          <div class="info-grid">
            <div class="info-card">
              <label>初始金額</label>
              <div class="value">{{ formatCurrency(share.portfolio.initial_amount) }}</div>
            </div>
            <div class="info-card">
              <label>回測期間</label>
              <div class="value">
                {{ formatDate(share.portfolio.start_date) }} ~
                {{ formatDate(share.portfolio.end_date) }}
              </div>
            </div>
            <div v-if="share.portfolio.rebalance_frequency" class="info-card">
              <label>再平衡頻率</label>
              <div class="value">{{ share.portfolio.rebalance_frequency }}</div>
            </div>
          </div>

          <!-- 持倉表 -->
          <h3 style="margin-top: 2rem">持倉</h3>
          <div class="holdings-table">
            <table>
              <thead>
                <tr>
                  <th>代號</th>
                  <th>名稱</th>
                  <th>配置比例</th>
                  <th>初始金額</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in share.portfolio.items" :key="idx">
                  <td class="symbol">{{ item.symbol }}</td>
                  <td>{{ item.name || '-' }}</td>
                  <td class="weight">{{ (item.weight * 100).toFixed(1) }}%</td>
                  <td class="amount">
                    {{ formatCurrency((share.portfolio.initial_amount * item.weight) || 0) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 回測結果 -->
        <div v-if="share.portfolio.results_json" class="detail-section">
          <h2>回測結果</h2>

          <div class="results-grid">
            <div class="result-card">
              <label>年化報酬</label>
              <div :class="['value', { positive: share.portfolio.results_json.annual_return > 0 }]">
                {{ (share.portfolio.results_json.annual_return * 100).toFixed(2) }}%
              </div>
            </div>

            <div class="result-card">
              <label>波動度</label>
              <div class="value">{{ (share.portfolio.results_json.volatility * 100).toFixed(2) }}%</div>
            </div>

            <div class="result-card">
              <label>夏普比例</label>
              <div :class="['value', { positive: share.portfolio.results_json.sharpe_ratio > 0 }]">
                {{ share.portfolio.results_json.sharpe_ratio.toFixed(2) }}
              </div>
            </div>

            <div class="result-card">
              <label>最大回撤</label>
              <div :class="['value', { negative: share.portfolio.results_json.max_drawdown < 0 }]">
                {{ (share.portfolio.results_json.max_drawdown * 100).toFixed(2) }}%
              </div>
            </div>

            <div class="result-card">
              <label>終值</label>
              <div
                :class="[
                  'value',
                  { positive: share.portfolio.results_json.final_value > share.portfolio.initial_amount },
                ]"
              >
                {{ formatCurrency(share.portfolio.results_json.final_value) }}
              </div>
            </div>

            <div class="result-card">
              <label>總報酬</label>
              <div
                :class="[
                  'value',
                  { positive: share.portfolio.results_json.total_return > 0 },
                ]"
              >
                {{ (share.portfolio.results_json.total_return * 100).toFixed(2) }}%
              </div>
            </div>
          </div>
        </div>

        <!-- 圖表區域（可選） -->
        <div v-if="share.portfolio.chart_data" class="detail-section">
          <h2>歷史走勢</h2>
          <div class="chart-placeholder">
            <p>圖表載入中...</p>
          </div>
        </div>
      </div>

      <!-- 動作按鈕 -->
      <div class="share-actions">
        <button @click="copyShareLink" class="btn-primary">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          複製分享連結
        </button>

        <a
          :href="`https://twitter.com/intent/tweet?text=${encodeURIComponent('查看我的投資策略：' + currentUrl)}`"
          target="_blank"
          class="btn-secondary social"
          title="分享到 Twitter"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path
              d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2s9 5 20 5a9.5 9.5 0 00-9-5.5c4.75 2.25 7-7 7-7a4.5 4.5 0 01-4-4.5V3z"
            />
          </svg>
          分享到 Twitter
        </a>

        <a
          :href="`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(currentUrl)}`"
          target="_blank"
          class="btn-secondary social"
          title="分享到 Facebook"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M18 2h-3a6 6 0 00-6 6v3H7v4h2v8h4v-8h3l1-4h-4V8a1 1 0 011-1h3z" />
          </svg>
          分享到 Facebook
        </a>

        <router-link to="/backtest" class="btn-secondary">返回回測</router-link>
      </div>

      <!-- 免責聲明 -->
      <div class="disclaimer">
        <strong>⚠️ 免責聲明：</strong>
        此投資策略為分享者提供之參考資訊，過去表現不代表未來成果。投資涉及風險，請自行進行評估或諮詢專業投資顧問後再作決定。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getPublicShare } from '@/api/shares'

const route = useRoute()

const isLoading = ref(false)
const error = ref(null)
const share = ref(null)
const currentUrl = ref('')

const portfolioTypeLabel = computed(() => {
  const types = {
    backtest: '回測',
    optimize: '最佳化',
    monte_carlo: '蒙地卡羅模擬',
  }
  return types[share.value?.portfolio.portfolio_type] || share.value?.portfolio.portfolio_type
})

const isExpired = computed(() => {
  if (!share.value?.portfolio.expires_at) return false
  return new Date(share.value.portfolio.expires_at) < new Date()
})

const loadShare = async () => {
  try {
    isLoading.value = true
    error.value = null

    const shareKey = route.params.share_key
    const response = await getPublicShare(shareKey)

    share.value = response
    currentUrl.value = window.location.href
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const copyShareLink = async () => {
  try {
    await navigator.clipboard.writeText(currentUrl.value)
    alert('✅ 已複製分享連結到剪貼板')
  } catch {
    alert('❌ 複製失敗，請手動複製')
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

onMounted(() => {
  loadShare()
})
</script>

<style scoped>
.public-share-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
}

/* 載入和錯誤狀態 */
.loading,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 1rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid rgba(102, 126, 234, 0.1);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon {
  font-size: 3rem;
}

.error-state h2 {
  color: #dc2626;
  margin: 0;
}

.error-state p {
  color: #6b7280;
  margin: 0.5rem 0 1rem;
}

/* 頂部資訊欄 */
.share-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 1rem;
  margin-bottom: 2rem;
  border: 1px solid #e5e7eb;
}

.share-header h1 {
  margin: 0 0 1rem 0;
  font-size: 2rem;
  color: #1f2937;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
}

.meta-item strong {
  color: #374151;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-backtest {
  background: #bfdbfe;
  color: #1e40af;
}

.badge-optimize {
  background: #d1fae5;
  color: #065f46;
}

.badge-monte_carlo {
  background: #fce7f3;
  color: #831843;
}

.header-right {
  text-align: center;
}

.view-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.count-number {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
}

.count-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
}

/* 分享描述 */
.share-description {
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 1.5rem;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
}

.share-description h3 {
  margin-top: 0;
  color: #92400e;
}

.share-description p {
  margin: 0.5rem 0 0 0;
  color: #78350f;
  line-height: 1.6;
}

/* 詳情區域 */
.portfolio-details {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.detail-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid #e5e7eb;
}

.detail-section h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  color: #1f2937;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 1rem;
}

.detail-section h3 {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-size: 1.125rem;
  color: #374151;
}

/* 資訊網格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.info-card {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.info-card label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.info-card .value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

/* 持倉表 */
.holdings-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

thead {
  background: #f3f4f6;
  border-bottom: 2px solid #e5e7eb;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
}

td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

tbody tr:hover {
  background: #f9fafb;
}

.symbol {
  font-weight: 600;
  color: #667eea;
  font-family: monospace;
}

.weight,
.amount {
  text-align: right;
}

/* 結果網格 */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.result-card {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.result-card label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.result-card .value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.result-card .value.positive {
  color: #10b981;
}

.result-card .value.negative {
  color: #dc2626;
}

/* 圖表區域 */
.chart-placeholder {
  background: #f3f4f6;
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 3rem;
  text-align: center;
  color: #6b7280;
}

/* 動作按鈕 */
.share-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin: 2rem 0;
  justify-content: center;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
  transform: translateY(-2px);
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
  transform: translateY(-2px);
}

.btn-secondary.social {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 0.75rem 1rem;
}

.btn-secondary.social:hover {
  opacity: 0.9;
}

.btn-primary svg,
.btn-secondary svg {
  width: 1.25rem;
  height: 1.25rem;
}

/* 免責聲明 */
.disclaimer {
  background: #fef3c7;
  border-left: 4px solid #dc2626;
  padding: 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #78350f;
  line-height: 1.6;
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .share-header {
    background: rgba(102, 126, 234, 0.1);
    border-color: #374151;
  }

  .share-header h1 {
    color: #f3f4f6;
  }

  .meta-item strong {
    color: #e5e7eb;
  }

  .detail-section {
    background: #1f2937;
    border-color: #374151;
  }

  .detail-section h2 {
    color: #f3f4f6;
    border-bottom-color: #374151;
  }

  .detail-section h3 {
    color: #e5e7eb;
  }

  .info-card {
    background: #111827;
    border-color: #374151;
  }

  .info-card .value {
    color: #f3f4f6;
  }

  thead {
    background: #111827;
    border-bottom-color: #374151;
  }

  th {
    color: #e5e7eb;
  }

  td {
    border-bottom-color: #374151;
  }

  tbody tr:hover {
    background: #111827;
  }

  .result-card {
    background: #111827;
    border-color: #374151;
  }

  .result-card .value {
    color: #f3f4f6;
  }
}

@media (max-width: 768px) {
  .public-share-container {
    padding: 1rem;
  }

  .share-header {
    flex-direction: column;
    gap: 1.5rem;
  }

  .header-right {
    align-self: flex-start;
  }

  .meta {
    flex-direction: column;
    gap: 0.75rem;
  }

  .share-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}
</style>
