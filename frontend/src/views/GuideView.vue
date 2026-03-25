<template>
  <div class="max-w-4xl mx-auto">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-[var(--text-primary)] mb-2">使用說明</h1>
      <p class="text-zinc-600 dark:text-zinc-400">瞭解 NEXUS 的主要功能與使用方式</p>
    </div>

    <!-- Guide Sections -->
    <div class="space-y-6">
      <!-- Overview Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-brand-500/10">
            <LayoutDashboard class="text-brand-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">總覽</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              查看投資組合的整體概況。包括：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>投資組合總值與各持倉合計</li>
              <li>投資報酬率（累積與年化）</li>
              <li>資產配置比例圖表</li>
              <li>近期績效走勢</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Tracking Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-blue-500/10">
            <TrendingUp class="text-blue-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">指數追蹤</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              建立與管理投資組合，追蹤持倉績效：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>新增投資組合與持倉位置</li>
              <li>記錄購入和成本基數</li>
              <li>實時監控持倉市值與報酬</li>
              <li>管理多個投資組合</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Backtest Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-purple-500/10">
            <RefreshCcw class="text-purple-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">回測管理</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              測試投資策略在歷史數據上的表現：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>選擇投資標的與時間範圍</li>
              <li>設定投資策略（定期定額 DCA、固定權重等）</li>
              <li>查看關鍵績效指標：</li>
              <ul class="list-circle list-inside ml-6 space-y-0.5 text-zinc-600 dark:text-zinc-400">
                <li><span class="font-semibold">累積報酬</span>：整個期間的總報酬率</li>
                <li><span class="font-semibold">年化報酬</span>：按年度換算的平均報酬</li>
                <li><span class="font-semibold">波動度</span>：投資風險指標</li>
                <li><span class="font-semibold">夏普比例</span>：風險調整後的報酬</li>
                <li><span class="font-semibold">最大回撤</span>：峰值到谷底的最大跌幅</li>
              </ul>
            </ul>
          </div>
        </div>
      </div>

      <!-- Optimize Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-amber-500/10">
            <Target class="text-amber-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">投資組合最佳化</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              使用馬可維茲理論找出最優資產配置：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>輸入候選標的與歷史數據期間</li>
              <li>選擇優化目標（最小風險或最大夏普比例）</li>
              <li>獲得最優權重配置建議</li>
              <li>檢視高效前緣曲線</li>
              <li>比較不同配置的預期風險與報酬</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Users Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-green-500/10">
            <Users class="text-green-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">使用者管理</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              管理系統帳戶與權限：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>查看與編輯個人檔案</li>
              <li>管理登入帳戶</li>
              <li>更新個人信息</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- LINE Notification Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-lg bg-rose-500/10">
            <MessageCircle class="text-rose-500" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">LINE 通知</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">
              設定 LINE 通知以接收市場警報與策略提醒：
            </p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li>綁定 LINE 帳號進行身份驗證</li>
              <li>設定價格警報通知</li>
              <li>接收回測與優化完成提醒</li>
              <li>市場開盤/收盤提醒</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Tips Section -->
      <div class="bg-gradient-to-r from-brand-500/5 to-blue-500/5 border border-brand-500/20 rounded-xl p-6">
        <h2 class="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Lightbulb class="text-brand-500" :size="20" />
          實用提示
        </h2>
        <ul class="space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
          <li>• <span class="font-semibold">首先追蹤持倉：</span> 在指數追蹤中添加您的投資持倉，系統會自動計算績效</li>
          <li>• <span class="font-semibold">回測策略：</span> 在實施新策略前，使用回測管理驗證其歷史表現</li>
          <li>• <span class="font-semibold">定期優化：</span> 定期運行投資組合最佳化，根據市場變化調整配置</li>
          <li>• <span class="font-semibold">啟用通知：</span> 通過 LINE 通知即時獲取重要市場動態和策略提醒</li>
          <li>• <span class="font-semibold">分析指標：</span> 重點關注夏普比例，以評估風險調整後的報酬質量</li>
        </ul>
      </div>

      <!-- Support Section -->
      <div class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 text-center">
        <h2 class="text-lg font-bold text-[var(--text-primary)] mb-2">需要協助？</h2>
        <p class="text-zinc-600 dark:text-zinc-400 mb-4">
          如有任何問題或建議，歡迎聯絡我們或查看相關文件
        </p>
        <div class="flex justify-center gap-4">
          <router-link 
            to="/users" 
            class="px-6 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg font-medium transition-colors"
          >
            返回用戶中心
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  LayoutDashboard,
  TrendingUp,
  RefreshCcw,
  Target,
  Users,
  MessageCircle,
  Lightbulb
} from 'lucide-vue-next'
</script>

<style scoped>
/* Custom scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}
</style>
