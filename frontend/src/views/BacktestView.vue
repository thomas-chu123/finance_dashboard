<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <h2 class="text-xl font-bold text-[var(--text-primary)]">回測管理</h2>
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 w-[calc(100%+2rem)] sm:w-auto">
        <!-- Tab 選擇 -->
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            activeTab === 'single' && !showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="activeTab = 'single'; showSaved = false">
          <BarChart3 class="w-4 h-4 mr-2" />單一回測
        </button>
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            activeTab === 'compare' && !showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="activeTab = 'compare'; showSaved = false">
          <Scale class="w-4 h-4 mr-2" />組合比較
        </button>
        <!-- 已儲存按鈕 -->
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = true; activeTab = 'single'; loadingSaved = true; loadSavedPortfolios()"
          :disabled="loadingSaved">
          <BarChart3 v-if="showSaved" class="w-4 h-4 mr-2" />
          <FolderOpen v-else class="w-4 h-4 mr-2" />
          已儲存
        </button>
      </div>
    </div>

    <!-- 組合比較 Tab -->
    <BacktestCompareTab
      v-if="activeTab === 'compare'"
      :saved-portfolios="savedPortfolios"
    />

    <!-- 單一回測 Tab -->
    <template v-if="activeTab === 'single'">

    <!-- Saved portfolios list -->
    <div v-if="showSaved">
      <!-- Back button -->
      <div class="mb-4">
        <button
          class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-lg transition-colors"
          @click="showSaved = false; results = null">
          <ArrowLeft class="w-4 h-4" />
          返回設定
        </button>
      </div>
      <div v-if="loadingSaved" style="padding:48px;text-align:center;color:var(--text-muted);">
        <div class="inline-flex items-center justify-center w-12 h-12 mx-auto mb-3 rounded-full bg-brand-500/10 animate-pulse">
          <FolderOpen class="w-6 h-6 text-brand-500" />
        </div>
        加載組合中...
      </div>
      <div v-else-if="!savedPortfolios.length" style="padding:48px;text-align:center;color:var(--text-muted);">
        <FolderOpen class="w-12 h-12 mx-auto text-gray-400 mb-3" />
        尚無已儲存的回測
      </div>
      <div v-else class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="p in paginatedSavedPortfolios" :key="p.id" class="glass-card">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
            <div>
              <div class="font-semibold text-[var(--text-primary)]">{{ p.name }}</div>
              <div class="text-sm text-muted">{{ p.start_date }} → {{ p.end_date }}</div>
            </div>
            <div class="flex items-center gap-2">
              <button class="flex items-center px-3 py-1.5 text-sm font-medium text-muted hover:text-brand-500 dark:hover:text-brand-400 transition-colors rounded-lg" @click="loadSaved(p)">載入</button>
              <button class="p-1.5 text-muted hover:text-rose-600 dark:hover:text-rose-400 transition-colors rounded-md hover:bg-rose-50 dark:hover:bg-rose-900/20" @click="deleteSaved(p.id)"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div v-if="p.results_json?.metrics" class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">CAGR</div>
                <div class="fw-600" :class="(p.results_json.metrics.cagr || 0) >= 0 ? 'text-rose-600' : 'text-brand-600'">{{ p.results_json.metrics.cagr }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-accent">{{ p.results_json.metrics.sharpe_ratio }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">MDD</div>
                <div class="fw-600 text-brand-600">{{ p.results_json.metrics.max_drawdown }}%</div>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">CAGR</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">MDD</div>
                <div class="fw-600 text-muted">--</div>
              </div>
            </div>
            <div class="mt-3">
              <div class="text-xs text-muted mb-2">組合資產</div>
              <div class="flex items-center gap-2" style="flex-wrap:wrap;">
                <span v-for="item in p.items" :key="item.symbol" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-500 text-white">
                  {{ item.symbol }} {{ item.weight }}%
                </span>
              </div>
            </div>
            <div class="mt-3">
              <button class="flex items-center justify-center px-4 py-2 text-sm font-medium bg-white text-zinc-900 border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-all w-full" @click="addToTracking(p.items)">
                <Activity class="w-4 h-4 mr-2" />一鍵加入追蹤
              </button>
            </div>
          </div>
          </div>
        </div>
        <!-- ✅ 分頁控件 -->
        <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4 border-t border-[var(--border-color)]">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-1.5 text-sm font-medium rounded-lg border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-sidebar)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            ← 上一頁
          </button>
          <span class="text-sm text-[var(--text-muted)]">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-sm font-medium rounded-lg border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-sidebar)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            下一頁 →
          </button>
        </div>
      </div>
    </div>

    <!-- Backtest runner -->
    <div v-else>
      <!-- Loaded notification -->
      <div v-if="currentLoadedPortfolioId" class="mb-6">
        <div class="flex items-center justify-between p-4 bg-brand-500/5 backdrop-blur-md border border-brand-500/20 rounded-2xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center text-white shadow-lg shadow-brand-500/20">
              <FolderOpen class="w-5 h-5" />
            </div>
            <div>
              <div class="text-[10px] sm:text-xs text-brand-600 font-bold uppercase tracking-widest opacity-80">已加載回測組合</div>
              <div class="text-xs sm:text-base font-bold text-[var(--text-primary)]">{{ loadedPortfolioName }}</div>
            </div>
          </div>
          <button
            class="p-2 text-muted hover:text-rose-600 transition-all rounded-xl hover:bg-rose-50 dark:hover:bg-rose-900/20"
            @click="currentLoadedPortfolioId = null; loadedPortfolioName = ''; loadedPortfolioType = null; saveName = ''">
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3" style="gap:12px;">
        <!-- Left: config -->
        <div>
          <div class="premium-card mb-4 min-h-[500px]">
            <div class="premium-header">
              <div class="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center">
                <Target class="w-5 h-5 text-brand-500" />
              </div>
              <h3 class="font-bold text-[var(--text-primary)]">配置資產</h3>
            </div>
            <div class="p-5">
              <div class="space-y-4">
                <!-- Symbol type tabs -->
                <div class="flex gap-2 overflow-x-auto scrollbar-none pb-1 premium-tab-container">
                  <button v-for="t in symbolTypes" :key="t.value"
                    :class="['premium-tab', symbolType === t.value ? 'active' : '']"
                    @click="symbolType = t.value; loadSymbols()">{{ t.label }}</button>
                </div>

                <!-- Quick symbol search -->
                <div class="relative">
                  <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400" :size="16" />
                  <input v-model="symbolSearch" type="text" 
                    class="w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all text-[var(--text-primary)]"
                    placeholder="搜尋及點選資產..." 
                    @keydown.enter="addSearchSymbol" />
                </div>

                <!-- Symbol list -->
                <div class="h-80 overflow-y-auto border border-[var(--border-color)] rounded-2xl bg-[var(--bg-sidebar)]/30 custom-scrollbar">
                  <div v-for="s in filteredSymbols.slice(0, 100)" :key="s.symbol"
                    :class="['px-4 py-3 cursor-pointer transition-all border-b border-[var(--border-color)] last:border-0 flex items-center justify-between hover:bg-brand-500/5', isSelected(s.symbol) ? 'bg-brand-500/10' : '']"
                    @click="toggleSymbol(s)">
                    <div class="flex flex-col min-w-0">
                      <span class="font-bold text-sm text-[var(--text-primary)] truncate">{{ s.symbol }}</span>
                      <span class="text-[10px] text-[var(--text-secondary)] font-medium truncate uppercase tracking-wider">{{ s.name }}</span>
                    </div>
                    <div class="w-6 h-6 rounded-full flex items-center justify-center transition-colors" :class="isSelected(s.symbol) ? 'bg-brand-500 text-white' : 'bg-brand-500/20 text-brand-600 dark:bg-brand-500/30 dark:text-brand-400'">
                      <Plus v-if="!isSelected(s.symbol)" class="w-3.5 h-3.5" />
                      <Check v-else class="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Date range + amount -->
          <div class="premium-card">
            <div class="premium-header">
              <div class="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center">
                <BarChart3 class="w-5 h-5 text-brand-500" />
              </div>
              <h3 class="font-bold text-[var(--text-primary)]">時間範圍與金額</h3>
            </div>
            <div class="p-5">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-1.5 mb-2 min-w-0">
                  <label class="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">開始日期</label>
                  <input v-model="btConfig.start_date" type="date" class="w-full max-w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 block p-2.5 transition-all" />
                </div>
                <div class="space-y-1.5 mb-2 min-w-0">
                  <label class="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">結束日期</label>
                  <input v-model="btConfig.end_date" type="date" class="w-full max-w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 block p-2.5 transition-all" />
                </div>
              </div>
              <div class="space-y-1.5 mt-2">
                <label class="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">初始金額 (USD)</label>
                <div class="relative">
                   <span class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400">$</span>
                   <input v-model.number="btConfig.initial_amount" type="number" class="w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 block p-2.5 pl-7 transition-all" />
                </div>
                <div class="text-[10px] text-[var(--text-secondary)] mt-2 italic">註：若包含台灣資產，系統將自動依歷史匯率換算為美金計價。</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: selected + weights -->
        <div>
          <div class="premium-card flex flex-col h-full overflow-hidden">
            <div class="premium-header">
              <div class="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center">
                <FolderOpen class="w-5 h-5 text-brand-500" />
              </div>
              <div class="flex-1 flex items-center justify-between">
                <h3 class="font-bold text-[var(--text-primary)]">已選資產 ({{ selectedItems.length }}/10)</h3>
                <div class="text-xs font-bold px-2 py-1 rounded-md" :class="Math.abs(totalWeight - 100) <= 0.5 ? 'bg-brand-500/10 text-brand-600' : 'bg-rose-500/10 text-rose-600'">
                  總權重: {{ totalWeight.toFixed(1) }}%
                </div>
              </div>
            </div>
            <div class="p-5 overflow-y-auto flex-1 custom-scrollbar">
              <div v-if="!selectedItems.length" style="color:var(--text-muted);font-size:0.875rem;padding:12px 0;">
                請從左側選擇資產
              </div>
              <div v-for="item in selectedItems" :key="item.symbol" class="p-4 bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl mb-3 shadow-sm">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-500 font-extrabold text-xs uppercase">
                      {{ item.symbol.substring(0, 2) }}
                    </div>
                    <div class="flex flex-col">
                      <div class="font-bold text-sm text-[var(--text-primary)] leading-tight">{{ item.symbol }}</div>
                      <div class="text-[10px] text-muted uppercase tracking-wider leading-tight">{{ item.name }}</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-4">
                    <span class="text-lg font-bold text-brand-500 dark:text-brand-400">{{ item.weight.toFixed(0) }}%</span>
                    <button class="p-1.5 text-muted hover:text-rose-600 dark:hover:text-rose-400 transition-all rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20" @click="removeSymbol(item.symbol)">
                      <X class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div class="w-full">
                  <input type="range" v-model.number="item.weight" min="0" max="100" step="0.1" class="weight-slider w-full h-1.5 bg-brand-500/20 dark:bg-brand-500/20 rounded-lg appearance-none cursor-pointer" />
                </div>
              </div>


              <!-- action buttons removed: now in independent card below -->
            </div>
          </div>
        </div>
      </div>

      <!-- ✅ Independent Action Card -->
      <div v-if="!showSaved" class="premium-card mt-3">
        <div class="premium-header">
          <div class="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center">
            <Play class="w-5 h-5 text-brand-500" />
          </div>
          <h3 class="font-bold text-[var(--text-primary)]">執行操作</h3>
        </div>
        <div class="p-5 flex flex-col gap-3">
          <!-- 平均分配 & 儲存組合 row -->
          <div class="flex gap-3">
            <button
              :disabled="selectedItems.length === 0"
              :class="[
                'flex-1 px-3 py-2 text-sm font-medium border rounded-lg transition-colors flex items-center justify-center gap-2',
                selectedItems.length === 0
                  ? 'border-[var(--border-color)] text-zinc-400 dark:text-zinc-600 bg-[var(--input-bg)] cursor-not-allowed opacity-50'
                  : 'border-[var(--border-color)] text-muted hover:text-brand-500 hover:border-brand-500 hover:bg-brand-500/10 dark:hover:text-brand-400 cursor-pointer'
              ]"
              @click="selectedItems.length > 0 && equalizeWeights()"
            >
              <Scale class="w-4 h-4" />平均分配
            </button>
            <button
              :disabled="selectedItems.length === 0"
              :class="[
                'flex-1 px-3 py-2 text-sm font-medium border rounded-lg transition-colors flex items-center justify-center gap-2',
                selectedItems.length === 0
                  ? 'border-[var(--border-color)] text-zinc-400 dark:text-zinc-600 bg-[var(--input-bg)] cursor-not-allowed opacity-50'
                  : 'border-[var(--border-color)] text-muted hover:text-brand-500 hover:border-brand-500 hover:bg-brand-500/10 dark:hover:text-brand-400 cursor-pointer'
              ]"
              @click="selectedItems.length > 0 && (showSaveModal = true)"
            >
              <Save class="w-4 h-4" />儲存組合
            </button>
          </div>

          <!-- Error message -->
          <div v-if="backtestError" class="p-3 text-sm text-red-800 rounded-lg bg-red-50 dark:bg-gray-800 dark:text-red-400">{{ backtestError }}</div>

          <!-- Progress bar -->
          <div v-if="runLoading" class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-3 shadow-sm animate-pulse">
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm fw-600 text-[var(--text-primary)]">
                <Play v-if="runProgress === 0 || runProgress === 100" class="w-4 h-4 mr-2 inline" /><Loader2 v-else class="w-4 h-4 mr-2 inline animate-spin" />{{ runProgress < 100 ? '正在計算結果...' : '計算完成！' }}
              </span>
              <span class="text-xs text-accent fw-700">{{ Math.floor(runProgress) }}%</span>
            </div>
            <div class="h-2 bg-[var(--bg-sidebar)] rounded-full overflow-hidden relative">
              <div class="h-full bg-brand-500 rounded-full transition-all duration-300" :style="{ width: runProgress + '%' }"></div>
            </div>
          </div>

          <!-- 執行回測 button -->
          <button
            v-else
            :disabled="runLoading || selectedItems.length === 0 || Math.abs(totalWeight - 100) > 0.5"
            :class="[
              'w-full py-3 px-4 font-bold rounded-xl transition-all flex items-center justify-center gap-2',
              (runLoading || selectedItems.length === 0 || Math.abs(totalWeight - 100) > 0.5)
                ? 'bg-[var(--border-color)] text-zinc-400 dark:text-zinc-600 cursor-not-allowed opacity-60'
                : 'bg-brand-500 hover:bg-brand-600 text-white shadow-lg shadow-brand-500/20 active:scale-95 cursor-pointer'
            ]"
            @click="runBacktest"
          >
            <Loader2 v-if="runLoading" class="w-4 h-4 animate-spin" />
            <Play v-else class="w-4 h-4 fill-current" />
            {{ runLoading ? '回測計算中...' : '執行回測' }}
          </button>
        </div>
      </div>

      <!-- Results -->
      <div v-if="results" class="mt-6 border-t border-[var(--border-color)] pt-6">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <h3 class="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
            回測結果 
            <span class="text-sm font-normal text-muted">({{ results.date_range?.start }} → {{ results.date_range?.end }})</span>
          </h3>
          <div class="flex items-center gap-3 w-full sm:w-auto">
            <button class="flex-1 sm:flex-none flex items-center justify-center px-4 py-2 text-sm font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-all shadow-sm" @click="addAllToTracking">
              <Activity class="w-4 h-4 mr-2" />加入追蹤
            </button>
            <button class="flex-1 sm:flex-none flex items-center justify-center px-4 py-2 text-sm font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-all shadow-sm" @click="showSaveModal = true">
              <Save class="w-4 h-4 mr-2" />儲存回測
            </button>
          </div>
        </div>

        <!-- Metrics -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <!-- CAGR -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">CAGR 年化報酬</div>
            <div :class="['text-xl font-bold', (results?.metrics?.cagr || 0) >= 0 ? 'text-rose-600' : 'text-brand-600']">
              {{ results?.metrics?.cagr ?? '--' }}{{ results?.metrics?.cagr !== undefined ? '%' : '' }}
            </div>
          </div>
          <!-- Sharpe -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">SHARPE RATIO</div>
            <div class="text-xl font-bold text-brand-500 dark:text-brand-400">{{ results?.metrics?.sharpe_ratio ?? '--' }}</div>
          </div>
          <!-- Sortino -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">SORTINO RATIO</div>
            <div class="text-xl font-bold text-teal-600 dark:text-teal-400">{{ results?.metrics?.sortino_ratio ?? '--' }}</div>
          </div>
          <!-- Beta -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">BETA</div>
            <div class="text-xl font-bold text-[var(--text-primary)]">{{ results?.metrics?.beta ?? '--' }}</div>
          </div>
          <!-- Max Drawdown -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">MAX DRAWDOWN</div>
            <div class="text-xl font-bold text-brand-600">{{ results?.metrics?.max_drawdown ?? '--' }}{{ results?.metrics?.max_drawdown !== undefined ? '%' : '' }}</div>
          </div>
          <!-- Volatility -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">VOLATILITY (STD)</div>
            <div class="text-xl font-bold text-[var(--text-primary)]">{{ results?.metrics?.annual_std ?? '--' }}{{ results?.metrics?.annual_std !== undefined ? '%' : '' }}</div>
          </div>
          <!-- VaR -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">VAR (95%)</div>
            <div class="text-xl font-bold text-orange-500">{{ results?.metrics?.var_95 ?? '--' }}{{ results?.metrics?.var_95 !== undefined ? '%' : '' }}</div>
          </div>
          <!-- Final Amount -->
          <div class="bg-[var(--bg-main)]/50 border border-[var(--border-color)] rounded-xl p-4 shadow-sm">
            <div class="text-[10px] text-muted uppercase tracking-widest mb-1 font-bold whitespace-nowrap">FINAL AMOUNT</div>
            <div class="text-xl font-bold text-rose-600">${{ (results?.metrics?.final_amount ?? 0).toLocaleString() }}</div>
            <div class="text-[10px] font-medium" :class="(results?.metrics?.total_return || 0) >= 0 ? 'text-rose-600' : 'text-brand-600'">
              RETURN: {{ results?.metrics?.total_return ?? '--' }}{{ results?.metrics?.total_return !== undefined ? '%' : '' }}
            </div>
          </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-12">
          <!-- Portfolio growth chart -->
          <div class="glass-card">
            <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between"><h3>資產成長曲線 (Portfolio Growth)</h3></div>
            <div class="p-3 sm:p-4" :style="{ height: isMobile ? '280px' : '400px' }">
              <v-chart :option="growthChartOption" autoresize style="height:100%;" />
            </div>
          </div>

          <!-- Annual returns -->
          <div class="glass-card">
            <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between"><h3>年度報酬率</h3></div>
            <div class="p-3 sm:p-4" style="height:260px;">
              <v-chart :option="annualReturnChartOption" autoresize style="height:100%;" />
            </div>
          </div>
        </div>

        <!-- Asset contributions -->
        <div class="glass-card mb-2">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between"><h3>各資產貢獻度</h3></div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left">
              <thead class="text-xs text-muted uppercase bg-[var(--bg-sidebar)]/50 border-b border-[var(--border-color)]">
                <tr class="text-muted"><th class="px-6 py-4 font-medium">代碼</th><th class="px-6 py-4 font-medium">名稱</th><th class="px-6 py-4 font-medium">權重</th><th class="px-6 py-4 font-medium">報酬貢獻 (USD)</th></tr>
              </thead>
              <tbody class="divide-y divide-[var(--border-color)]/20">
                <tr v-for="(contrib, symbol) in (results.asset_contributions || {})" :key="symbol">
                  <td class="px-6 py-4 fw-600 text-accent">{{ symbol }}</td>
                  <td class="px-6 py-4">{{ contrib.name }}</td>
                  <td class="px-6 py-4">{{ contrib.weight }}%</td>
                  <td class="px-6 py-4" :class="(contrib.return_contribution || 0) >= 0 ? 'text-rose-600 font-bold' : 'text-brand-600 font-bold'">
                    ${{ (contrib.return_contribution || 0).toLocaleString() }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Drawdown chart -->
        <div class="glass-card mb-6" v-if="results.drawdown_series">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
            <h3>回撤曲線 (Drawdown)</h3>
            <span class="text-sm text-muted">最大回撤：<span class="text-brand-600 fw-600">{{ results?.metrics?.max_drawdown ?? '--' }}%</span></span>
          </div>
          <div class="p-4 sm:p-6" style="height:240px;">
            <v-chart :option="drawdownChartOption" autoresize style="height:100%;" />
          </div>
        </div>

        <!-- Monthly Returns Heatmap -->
        <div class="glass-card mb-6" v-if="results.monthly_returns">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
            <h3>月度報酬率熱力圖</h3>
          </div>
          <div class="p-4 sm:p-6" style="height:320px;">
            <v-chart :option="monthlyReturnsHeatmapOption" autoresize style="height:100%;" />
          </div>
        </div>

        <!-- Correlation heatmap -->
        <div class="glass-card" v-if="results.correlation_matrix && results.available_symbols?.length > 1">
          <div class="p-4 border-b border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
            <h3>相關性熱力圖</h3>
            <span class="text-xs text-muted">1.0 = 完全正相關 · -1.0 = 完全負相關</span>
          </div>
          <div class="p-4 sm:p-6" style="height:320px;">
            <v-chart :option="correlationHeatmapOption" autoresize style="height:100%;" />
          </div>
        </div>
      </div>
    </div>

    <!-- Save modal -->
    <Transition name="fade">
      <div v-if="showSaveModal" class="fixed inset-0 bg-gray-900/50 dark:bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-[var(--bg-main)] rounded-xl shadow-xl w-full max-w-md overflow-hidden ring-1 ring-[var(--border-color)]">
          <div class="px-6 py-4 border-b border-[var(--border-color)] flex justify-between items-center font-semibold text-[var(--text-primary)]"><h3>儲存回測</h3><button class="text-muted hover:text-[var(--text-primary)] transition-colors" @click="showSaveModal = false"><X class="w-4 h-4" /></button></div>
          <div class="p-6">
            <div class="space-y-1 mb-4">
              <label class="block text-sm font-medium text-muted">回測名稱</label>
              <input v-model="saveName" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" placeholder="例: 台美混合 2020-2024" />
            </div>
          </div>
          <div class="px-6 py-4 bg-[var(--bg-sidebar)] flex justify-end gap-3">
            <button class="px-4 py-2 text-sm font-medium text-muted hover:bg-[var(--input-bg)] rounded-lg transition-colors border border-transparent" @click="showSaveModal = false">取消</button>
            <button class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition-colors shadow-sm" @click="saveBacktest">儲存</button>
          </div>
        </div>
      </div>
    </Transition>

    </template><!-- end single tab -->
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { useTrackingStore } from '../stores/tracking'
import { useBreakpoint } from '../composables/useBreakpoint'
import { FolderOpen, Trash2, Activity, BarChart3, Rocket, Play, Scale, Save, Check, X, Loader2, ArrowLeft, Search, Plus, Target } from 'lucide-vue-next'
import BacktestCompareTab from '../components/BacktestCompareTab.vue'

const auth = useAuthStore()
const trackingStore = useTrackingStore()
const { isMobile, isTablet, isDesktop } = useBreakpoint()

// Remove local API_BASE declaration
const activeTab = ref('single')  // 'single' | 'compare'
const showSaved = ref(false)
const savedPortfolios = ref([])
const loadingSaved = ref(false)
const currentPage = ref(1)  // 分頁: 當前頁
const pageSize = ref(6)     // 分頁: 每頁項目數
const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])
const results = ref(null)
const runLoading = ref(false)
const runProgress = ref(0)
const backtestError = ref('')
const showSaveModal = ref(false)
const saveName = ref('')
const currentLoadedPortfolioId = ref(null)
const loadedPortfolioName = ref('')  // ✅ 追蹤已加載的組合名稱
const loadedPortfolioType = ref(null) // ✅ 追蹤已加載的組合類型

const symbolTypes = [
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'indices', label: '指數/原物料' },
  { value: 'crypto', label: '加密貨幣' },
  { value: 'funds', label: '共同基金' },
]

const btConfig = reactive({
  start_date: '2015-01-01',
  end_date: new Date().toISOString().split('T')[0],
  initial_amount: 100000,
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  return availableSymbols.value.filter(s =>
    !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
})

const totalWeight = computed(() => selectedItems.value.reduce((s, i) => s + (i.weight || 0), 0))

const benchmarkSymbol = computed(() => {
  const hasTaiwan = selectedItems.value.some(i => i.category === 'tw_etf')
  return hasTaiwan ? '0050' : 'SPY'
})

// ✅ 分頁計算：只渲染當前頁的項目
const paginatedSavedPortfolios = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = currentPage.value * pageSize.value
  return savedPortfolios.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(savedPortfolios.value.length / pageSize.value))

function isSelected(sym) { return selectedItems.value.some(i => i.symbol === sym) }

function toggleSymbol(s) {
  if (isSelected(s.symbol)) {
    removeSymbol(s.symbol)
  } else if (selectedItems.value.length < 10) {
    selectedItems.value.push({ ...s, weight: Math.floor(100 / (selectedItems.value.length + 1)) })
    equalizeWeights()
  }
}

function removeSymbol(sym) {
  selectedItems.value = selectedItems.value.filter(i => i.symbol !== sym)
  equalizeWeights()
  if (selectedItems.value.length === 0) {
    currentLoadedPortfolioId.value = null
    loadedPortfolioName.value = ''
    loadedPortfolioType.value = null
    saveName.value = ''
  }
}

function equalizeWeights() {
  if (!selectedItems.value.length) return
  const w = parseFloat((100 / selectedItems.value.length).toFixed(1))
  selectedItems.value.forEach((item, idx) => {
    item.weight = idx === selectedItems.value.length - 1 ? 100 - w * (selectedItems.value.length - 1) : w
  })
}

function adjustWeights(symbol, newWeight) {
  const item = selectedItems.value.find(i => i.symbol === symbol)
  if (!item) return
  
  // Basic logic: just update this one. 
  // For a better UX, we could adjust others proportionally, but let's keep it simple for now.
  item.weight = newWeight
}

function addSearchSymbol() {
  const sym = symbolSearch.value.trim().toUpperCase()
  if (!sym || isSelected(sym) || selectedItems.value.length >= 10) return
  selectedItems.value.push({ symbol: sym, name: sym, category: symbolType.value, weight: 0 })
  equalizeWeights()
  symbolSearch.value = ''
}

async function loadSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest/symbols`, { headers: auth.headers })
    const data = res.data
    if (symbolType.value === 'us_etf') availableSymbols.value = data.us_etf || []
    else if (symbolType.value === 'tw_etf') availableSymbols.value = data.tw_etf || []
    else if (symbolType.value === 'crypto') {
      availableSymbols.value = (data.indices || []).filter(s => s.category === 'crypto')
    }
    else if (symbolType.value === 'funds') {
      availableSymbols.value = data.funds || []
    }
    else availableSymbols.value = (data.indices || []).filter(s => s.category !== 'crypto')
  } catch (e) { console.error('Symbol load failed', e) }
}

async function runBacktest() {
  backtestError.value = ''
  
  // ✅ 驗證日期是否有效
  if (!btConfig.start_date || !btConfig.end_date) {
    backtestError.value = '請設置回測起始日期和結束日期'
    return
  }
  
  runLoading.value = true
  runProgress.value = 0
  results.value = null

  // Progress simulation
  const progressInterval = setInterval(() => {
    if (runProgress.value < 20) {
      runProgress.value += 2 // Fast start
    } else if (runProgress.value < 85) {
      runProgress.value += 0.5 // Normal slow
    } else if (runProgress.value < 98) {
      runProgress.value += 0.1 // Crawl
    }
  }, 100)

  try {
    const res = await axios.post(`${API_BASE}/api/backtest/run`, {
      items: selectedItems.value.map(i => ({ symbol: i.symbol, name: i.name, weight: i.weight, category: i.category })),
      start_date: btConfig.start_date,
      end_date: btConfig.end_date,
      initial_amount: btConfig.initial_amount,
    }, { headers: auth.headers })
    
    clearInterval(progressInterval)
    runProgress.value = 100
    
    // Give a moment for the 100% state to be visible
    await new Promise(r => setTimeout(r, 400))
    console.log('[DEBUG] Backtest results:', res.data)
    results.value = res.data
    
    // Auto-save if it's a loaded portfolio
    if (currentLoadedPortfolioId.value && saveName.value) {
      try {
        await axios.post(`${API_BASE}/api/backtest/save`, {
          id: currentLoadedPortfolioId.value,
          name: saveName.value,
          items: selectedItems.value,
          start_date: btConfig.start_date,
          end_date: btConfig.end_date,
          initial_amount: btConfig.initial_amount,
          results_json: results.value,
        }, { headers: auth.headers })
        await loadSavedPortfolios()
      } catch (saveErr) {
        console.error('[DEBUG] Auto-save failed:', saveErr)
      }
    }
  } catch (e) {
    clearInterval(progressInterval)
    console.error('[DEBUG] Backtest error:', e)
    backtestError.value = e.response?.data?.detail || e.message
  } finally {
    runLoading.value = false
    runProgress.value = 0
  }
}

const growthChartOption = computed(() => {
  if (!results.value?.portfolio_value_series) return {}
  const dates = Object.keys(results.value.portfolio_value_series)
  const values = dates.map(d => parseFloat(results.value.portfolio_value_series[d]))

  const series = [{ 
    name: '投資組合',
    data: values, 
    type: 'line', 
    smooth: true, 
    symbol: 'none', 
    lineStyle: { color: '#2563eb', width: 2.5 }, 
    areaStyle: { 
      color: { 
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1, 
        colorStops: [
          { offset: 0, color: 'rgba(37, 99, 235, 0.2)' }, 
          { offset: 1, color: 'rgba(37, 99, 235, 0)' }
        ] 
      } 
    } 
  }]

  const benchmarkLabel = `參考曲線-${benchmarkSymbol.value}`

  // Add benchmark if available
  if (results.value?.benchmark_value_series && Object.keys(results.value.benchmark_value_series).length > 0) {
    const bmData = results.value.benchmark_value_series
    const initialAmt = results.value?.metrics?.initial_amount || 0
    if (initialAmt > 0) {
      const bmValues = dates.map(d => {
        const val = bmData[d] || 1
        return parseFloat((val * initialAmt).toFixed(2))
      })
      series.push({
        name: benchmarkLabel,
        data: bmValues,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2, type: 'solid' }
      })
    }
  }

  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e', fontFamily: 'Inter, sans-serif' },
    grid: { left: 80, right: 40, top: 40, bottom: 80 }, 
    legend: { 
      show: true, 
      bottom: '2%', 
      left: 'center', 
      orient: 'horizontal',
      icon: 'roundRect',
      data: [
        { name: '投資組合', textStyle: { color: '#2563eb', fontWeight: 'bold' } },
        { name: benchmarkLabel, textStyle: { color: '#10b981', fontWeight: 'bold' } }
      ]
    },
    xAxis: { 
      type: 'category', 
      name: 'Year',
      nameLocation: 'middle',
      nameGap: 35,
      data: dates, 
      axisLabel: {
          fontSize: 10,
          color: '#8b949e',
          interval: Math.floor(dates.length / 8),
          formatter: (value) => value.substring(0, 7)
        }, 
      axisLine: { lineStyle: { color: 'transparent' } },
      splitLine: { show: false }
    },
    yAxis: { 
      type: 'value', // Changed back to value for better tick density ($150k etc)
      scale: true,
      name: 'Portfolio Balance ($)',
      nameLocation: 'middle',
      nameGap: 60,
      splitNumber: 8, // More ticks
      axisLabel: { 
        formatter: v => '$' + v.toLocaleString(), 
        color: '#8b949e' 
      },
      axisLine: { lineStyle: { color: '#30363d', width: 1 } },
      splitLine: { lineStyle: { color: '#2d333b', type: 'solid' } },
      minorTick: { show: false },
      minorSplitLine: { show: false }
    },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => {
      let html = `${p[0].axisValue}<br/>`
      p.forEach(s => { html += `${s.marker} ${s.seriesName}: $${parseFloat(s.value).toLocaleString()}<br/>` })
      return html
    }},
    series: series
  }
})

const annualReturnChartOption = computed(() => {
  if (!results.value?.annual_returns) return {}
  const years = Object.keys(results.value.annual_returns)
  const vals = years.map(y => (results.value.annual_returns[y] * 100).toFixed(2))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#e6edf3' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: years, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } },
    yAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } } },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${p[0].axisValue}: ${p[0].value}%` },
    series: [{
      data: vals.map(v => ({ value: v, itemStyle: { color: parseFloat(v) >= 0 ? '#f85149' : '#3fb950' } })),
      type: 'bar', barMaxWidth: 40,
    }]
  }
})

const drawdownChartOption = computed(() => {
  if (!results.value?.drawdown_series) return {}
  const dates = Object.keys(results.value.drawdown_series)
  const vals = dates.map(d => parseFloat(results.value.drawdown_series[d].toFixed(2)))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#e6edf3' },
    grid: { left: 60, right: 20, top: 10, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        fontSize: 10,
        color: '#8b949e',
        interval: Math.floor(dates.length / 6),
        formatter: (value) => value.substring(0, 7)
      },
      axisLine: { lineStyle: { color: '#30363d' } }
    },
    yAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#8b949e' }, splitLine: { lineStyle: { color: '#21262d' } }, max: 0 },
    tooltip: { trigger: 'axis', backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${p[0].axisValue}<br/>回撤：${p[0].value}%` },
    series: [{
      data: vals, type: 'line', smooth: true, symbol: 'none',
      lineStyle: { color: '#3fb950', width: 1.5 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(63,185,80,0.4)' }, { offset: 1, color: 'rgba(63,185,80,0.02)' }] } }
    }]
  }
})

const correlationHeatmapOption = computed(() => {
  if (!results.value?.correlation_matrix || !results.value?.available_symbols) return {}
  const syms = results.value.available_symbols
  const matrix = results.value.correlation_matrix
  // Build [x, y, value] triples
  const data = []
  syms.forEach((rowSym, yi) => {
    syms.forEach((colSym, xi) => {
      const val = (matrix[rowSym]?.[colSym] ?? 0)
      data.push([xi, yi, parseFloat(val.toFixed(3))])
    })
  })
  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e' },
    grid: { left: 70, right: 80, top: 20, bottom: 70 },
    xAxis: { type: 'category', data: syms, axisLabel: { color: '#8b949e', rotate: 30 }, axisLine: { lineStyle: { color: '#30363d' } } },
    yAxis: { type: 'category', data: syms, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } } },
    visualMap: {
      min: -1, max: 1, calculable: true, orient: 'vertical', right: 0, top: 'center',
      inRange: { color: ['#f85149', '#21262d', '#3fb950'] },
      textStyle: { color: '#8b949e' }, precision: 2
    },
    tooltip: { backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${syms[p.value[1]]} vs ${syms[p.value[0]]}<br/>相關係數：${p.value[2]}` },
    series: [{ type: 'heatmap', data, label: { show: syms.length <= 6, color: '#e6edf3', fontSize: 11 } }]
  }
})

const monthlyReturnsHeatmapOption = computed(() => {
  if (!results.value?.monthly_returns) return {}
  const mr = results.value.monthly_returns
  const years_raw = mr.years || []
  const years = years_raw.map(String)
  const months = mr.months || []
  const data = []
  const heatmap_raw = mr.data || []
  
  years.forEach((year, xIndex) => {
    months.forEach((month, yIndex) => {
      try {
        // Handle both 2D (matrix) and potentially 1D/broken data
        const row = heatmap_raw[xIndex]
        if (!row) return
        
        const val = row[yIndex]
        if (val !== null && val !== undefined && !isNaN(val)) {
          // backend uses ratio, frontend heatmap wants % value or ratio?
          // The previous code did parseFloat((val * 100).toFixed(2))
          data.push([xIndex, yIndex, parseFloat((val * 100).toFixed(2))])
        }
      } catch (err) {
        console.error(`[DEBUG] Heatmap compute error at ${xIndex},${yIndex}`, err)
      }
    })
  })

  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#8b949e' },
    grid: { left: 50, right: 20, top: 20, bottom: 100 },
    xAxis: { type: 'category', data: years, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } }, splitArea: { show: true } },
    yAxis: { type: 'category', data: months, axisLabel: { color: '#8b949e' }, axisLine: { lineStyle: { color: '#30363d' } }, splitArea: { show: true } },
    visualMap: {
      min: -15, max: 15, calculable: true, orient: 'horizontal', left: 'center', bottom: 20,
      inRange: { color: ['#3fb950', '#161b22', '#f85149'] },
      textStyle: { color: '#8b949e' }, formatter: v => v + '%'
    },
    tooltip: { backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' }, formatter: p => `${years[p.value[0]]} ${months[p.value[1]]}<br/>報酬：${p.value[2]}%` },
    series: [{ 
      type: 'heatmap', 
      data, 
      label: { show: true, color: '#e6edf3', fontSize: 10, formatter: p => p.value[2] + '%' },
      itemStyle: { borderColor: '#0d1117', borderWidth: 1 }
    }]
  }
})

async function loadSavedPortfolios() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest`, { headers: auth.headers })
    savedPortfolios.value = res.data
    currentPage.value = 1  // ✅ 重置分頁到第一頁
  } catch (e) { console.error('Load saved failed', e) }
  finally {
    loadingSaved.value = false
  }
}

async function deleteSaved(id) {
  if (!confirm('確定刪除此回測？')) return
  await axios.delete(`${API_BASE}/api/backtest/${id}`, { headers: auth.headers })
  await loadSavedPortfolios()
}

function loadSaved(p) {
  showSaved.value = false
  selectedItems.value = p.items.map(i => ({ ...i }))
  btConfig.start_date = p.start_date || '2015-01-01'
  btConfig.end_date = p.end_date || new Date().toISOString().split('T')[0]
  btConfig.initial_amount = p.initial_amount || 100000
  results.value = p.results_json
  currentLoadedPortfolioId.value = p.id
  loadedPortfolioName.value = p.name  // ✅ 記錄已加載的組合名稱
  saveName.value = p.name
  loadedPortfolioType.value = p.portfolio_type // ✅ 紀錄類別
  
  // ✅ 如果 load 的組合沒有 metrics，自動執行重新計算
  if (!p.results_json?.metrics) {
    console.log('[DEBUG] Missing metrics, auto-running backtest...');
    // 延遲一點點執行以確保 UI 已經切換
    setTimeout(() => {
      runBacktest();
    }, 100);
  }
}

async function saveBacktest() {
  if (!saveName.value.trim()) return
  try {
    // ✅ 檢查名稱是否改變：同名時更新，異名時另存新檔
    let portfolioId = null
    if (currentLoadedPortfolioId.value && saveName.value === loadedPortfolioName.value) {
      // 同名：詢問用戶是否覆蓋
      const confirmed = confirm(`確定要更新「${saveName.value}」嗎？`)
      if (!confirmed) return
      portfolioId = currentLoadedPortfolioId.value
    } else if (currentLoadedPortfolioId.value && saveName.value !== loadedPortfolioName.value) {
      // 異名：詢問用戶是新增還是覆蓋
      const response = confirm(
        `您已加載的回測為「${loadedPortfolioName.value}」，現在儲存為「${saveName.value}」。\n\n` +
        `點擊【確定】另存新檔\n` +
        `點擊【取消】返回修改名稱`
      )
      if (!response) return
      // 不傳遞 portfolioId，建立新組合
      portfolioId = null
    }
    // else: 未加載任何組合，新增新組合（portfolioId = null）

    await axios.post(`${API_BASE}/api/backtest/save`, {
      id: portfolioId,
      name: saveName.value,
      items: selectedItems.value,
      start_date: btConfig.start_date,
      end_date: btConfig.end_date,
      initial_amount: btConfig.initial_amount,
      results_json: results.value,
    }, { headers: auth.headers })
    showSaveModal.value = false
    // 如果建立了新組合，重置名稱；如果覆蓋，保持不變
    if (!portfolioId) saveName.value = ''
    await loadSavedPortfolios()
    alert('回測已儲存！')
  } catch (e) { alert('儲存失敗: ' + (e.response?.data?.detail || e.message)) }
}

async function addAllToTracking() {
  const symbols = selectedItems.value.map(i => i.symbol)
  const names = selectedItems.value.map(i => i.name)
  const categories = selectedItems.value.map(i => i.category)
  await trackingStore.addFromBacktest(symbols, names, categories)
  alert(`已將 ${symbols.length} 個資產加入追蹤！`)
}

async function addToTracking(items) {
  await trackingStore.addFromBacktest(items.map(i => i.symbol), items.map(i => i.name || i.symbol), items.map(i => i.category || 'us_etf'))
  alert('已加入追蹤！')
}

onMounted(async () => {
  await loadSymbols()
  await loadSavedPortfolios()

  const presetStr = sessionStorage.getItem('backtest_preset')
  if (presetStr) {
    try {
      const preset = JSON.parse(presetStr)
      selectedItems.value = preset.items
      btConfig.start_date = preset.start_date || '2015-01-01'
      btConfig.end_date = preset.end_date || new Date().toISOString().split('T')[0]
      sessionStorage.removeItem('backtest_preset') // clean up
      
      // Auto run backtest if valid
      if (selectedItems.value.length > 0) {
        // Ensure total weight is approx 100 before running automatically
        const total = selectedItems.value.reduce((s, i) => s + i.weight, 0)
        if (Math.abs(total - 100) < 0.5) {
            setTimeout(() => runBacktest(), 500) // slight delay to let UI render
        }
      }
    } catch (e) {
      console.error('Failed to parse preset', e)
    }
  }
})
</script>

<style scoped>
.backtest-header {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 0.5rem !important;
}

.symbol-item {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  width: 100% !important;
}

.metrics-grid {
  display: grid !important;
  grid-template-columns: repeat(2, 1fr) !important;
  gap: 1rem !important;
}

@media (min-width: 1024px) {
  .metrics-grid {
    grid-template-columns: repeat(4, 1fr) !important;
  }
}
</style>


