<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)]">投資組合最佳化</h2>
        <div class="text-xs sm:text-sm text-[var(--text-muted)]">基於 Markowitz 效率前緣理論尋找最佳權重分配</div>
      </div>
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 w-[calc(100%+2rem)] sm:w-auto">
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            !showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = false">
          <Dna class="w-4 h-4 mr-2" />開始最佳化
        </button>
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = true; loadingSaved = true; loadSavedPortfolios()"
          :disabled="loadingSaved">
          <FolderOpen class="w-4 h-4 mr-2" />
          已儲存 {{ loadingSaved ? '(加載中...)' : '' }}
        </button>
      </div>
    </div>

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
        尚無已儲存的優化組合
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
            <div v-if="p.results_json?.max_sharpe" class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-accent">{{ p.results_json.max_sharpe.sharpe.toFixed(4) }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">Return</div>
                <div class="fw-600 text-rose-600">{{ (p.results_json.max_sharpe.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-muted">Volatility</div>
                <div class="fw-600 text-brand-600">{{ (p.results_json.max_sharpe.volatility * 100).toFixed(2) }}%</div>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">Sharpe</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">Return</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">Volatility</div>
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

    <!-- Optimization Config -->
    <div v-if="!showSaved">
      <!-- Loaded notification (Same as BacktestView) -->
      <div v-if="loadedPortfolioId" class="mb-6">
        <div class="flex items-center justify-between p-4 bg-brand-500/5 backdrop-blur-md border border-brand-500/20 rounded-2xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center text-white shadow-lg shadow-brand-500/20">
              <FolderOpen class="w-5 h-5" />
            </div>
            <div>
              <div class="text-[10px] sm:text-xs text-brand-600 font-bold uppercase tracking-widest opacity-80">已加載優化組合</div>
              <div class="text-xs sm:text-base font-bold text-[var(--text-primary)]">{{ loadedPortfolioName }}</div>
            </div>
          </div>
          <button
            class="p-2 text-muted hover:text-rose-600 transition-all rounded-xl hover:bg-rose-50 dark:hover:bg-rose-900/20"
            @click="loadedPortfolioId = null; loadedPortfolioName = ''; loadedPortfolioType = null; saveName = ''">
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <!-- Left: Asset selection -->
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

      <!-- Date range -->
        <div class="premium-card">
          <div class="p-5">
            <!-- 幣值選擇器 -->
            <div class="mb-4">
              <CurrencySelector :show-hint="true" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1.5 mb-2 min-w-0">
                <label class="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">最佳化分析起點</label>
                <input v-model="optConfig.start_date" type="date" class="w-full max-w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 block p-2.5 transition-all" />
              </div>
              <div class="space-y-1.5 mb-2 min-w-0">
                <label class="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">結束日期</label>
                <input v-model="optConfig.end_date" type="date" class="w-full max-w-full bg-[var(--bg-sidebar)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 block p-2.5 transition-all" />
              </div>
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
              <div class="text-xs font-bold px-2 py-1 rounded-md" :class="totalWeight === 100 ? 'bg-brand-500/10 text-brand-600' : 'bg-rose-500/10 text-rose-600'">
                總權重: {{ totalWeight }}%
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
                  <span class="text-lg font-bold text-brand-500 dark:text-brand-400">{{ Math.round(item.weight) }}%</span>
                  <button class="p-1.5 text-muted hover:text-rose-600 dark:hover:text-rose-400 transition-all rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20" @click="removeSymbol(item.symbol)">
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div class="w-full">
                <input type="range" v-model.number="item.weight" min="0" max="100" step="1" @input="adjustWeights(item.symbol, item.weight)" class="weight-slider w-full h-1.5 bg-brand-500/20 dark:bg-brand-500/20 rounded-lg appearance-none cursor-pointer" />
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

        <!-- 開始優化 button -->
        <button
          :disabled="runLoading || selectedItems.length < 2 || totalWeight !== 100"
          :class="[
            'w-full py-3 px-4 font-bold rounded-xl transition-all flex items-center justify-center gap-2',
            (runLoading || selectedItems.length < 2 || totalWeight !== 100)
              ? 'bg-[var(--border-color)] text-zinc-400 dark:text-zinc-600 cursor-not-allowed opacity-60'
              : 'bg-brand-500 hover:bg-brand-600 text-white shadow-lg shadow-brand-500/20 active:scale-95 cursor-pointer'
          ]"
          @click="runOptimization"
        >
          <Loader2 v-if="runLoading" class="w-4 h-4 animate-spin" />
          <Play v-else class="w-4 h-4 fill-current" />
          {{ runLoading ? '優化計算中...' : '開始優化' }}
        </button>
      </div>
    </div>
  </div>

    <!-- Optimization Results -->
    <div v-if="!showSaved && results" id="optimize-results-chart" class="mt-6 space-y-6">
      <h3 class="mb-2">最佳化分析結果</h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        <!-- Max Sharpe Portfolio -->
        <div class="glass-card" style="border: 3px solid #f85149;">
          <div class="p-4 border-b-2 border-[#f85149] font-semibold text-[var(--text-primary)] flex items-center justify-between" style="background:rgba(248, 81, 73, 0.08);">
            <div class="optimize-header w-full">
              <h3 class="text-brand-500"><Trophy class="w-5 h-5 mr-2 inline" />最大夏普值組合 (Max Sharpe)</h3>
              <button class="px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="exportToBacktest(results.max_sharpe)">使用此權重回測</button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <div>
                <div class="text-xs text-[var(--text-muted)]">預期年化報酬</div>
                <div class="fw-600 text-rose-600">{{ (results.max_sharpe.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">年化波動率</div>
                <div class="font-semibold text-[var(--text-primary)]">{{ (results.max_sharpe.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">夏普值</div>
                <div class="fw-600 text-accent">{{ results.max_sharpe.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div :style="{ height: isMobile ? '200px' : '250px' }">
              <v-chart :option="maxSharpePieOption" autoresize />
            </div>
          </div>
        </div>

        <!-- Min Volatility Portfolio -->
        <div class="glass-card" style="border: 3px solid #3fb950;">
          <div class="p-4 border-b-2 border-[#3fb950] font-semibold text-[var(--text-primary)] flex items-center justify-between" style="background:rgba(63, 185, 80, 0.12);">
             <div class="optimize-header w-full">
              <h3 class="text-brand-600"><Shield class="w-5 h-5 mr-2 inline" />最小波動率組合 (Min Volatility)</h3>
              <button class="px-3 py-1.5 text-sm font-medium text-[var(--text-muted)] hover:text-brand-500 transition-colors rounded-lg" @click="exportToBacktest(results.min_volatility)">使用此權重回測</button>
            </div>
          </div>
          <div class="p-3 sm:p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <div>
                <div class="text-xs text-[var(--text-muted)]">預期年化報酬</div>
                <div class="fw-600 text-rose-600">{{ (results.min_volatility.return * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">年化波動率</div>
                <div class="font-semibold text-[var(--text-primary)]">{{ (results.min_volatility.volatility * 100).toFixed(2) }}%</div>
              </div>
              <div>
                <div class="text-xs text-[var(--text-muted)]">夏普值</div>
                <div class="fw-600 text-accent">{{ results.min_volatility.sharpe.toFixed(3) }}</div>
              </div>
            </div>
            <div :style="{ height: isMobile ? '200px' : '250px' }">
              <v-chart :option="minVolPieOption" autoresize />
            </div>
          </div>
        </div>
      </div>

      <!-- Efficient Frontier Chart -->
      <div class="glass-card mb-2">
        <div class="p-4 border-b-2 border-[var(--border-color)] font-semibold text-[var(--text-primary)] flex items-center justify-between">
          <h3>效率前緣 (Efficient Frontier)</h3>
          <span class="text-sm text-[var(--text-muted)]">顯示在相同風險下能產生的最高預期報酬</span>
        </div>
        <div class="p-3 sm:p-4" :style="{ height: isMobile ? '280px' : '380px' }">
          <v-chart :option="efficientFrontierOption" autoresize />
        </div>
      </div>

      <!-- Share Image Button -->
      <div class="flex justify-center mt-4">
        <ShareImageButton
          result-type="optimize"
          capture-selector="#optimize-results-chart"
          @share-success="onImageShareSuccess"
        />
      </div>

    </div>

    <!-- Save modal -->
    <Transition name="fade">
      <div v-if="showSaveModal" class="fixed inset-0 bg-gray-900/50 dark:bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-[var(--bg-main)] rounded-xl shadow-xl w-full max-w-md overflow-hidden ring-1 ring-[var(--border-color)]">
          <div class="px-6 py-4 border-b border-[var(--border-color)] flex justify-between items-center font-semibold text-[var(--text-primary)]"><h3>儲存最佳化方案</h3><button class="text-muted hover:text-[var(--text-primary)] transition-colors" @click="showSaveModal = false"><X class="w-4 h-4" /></button></div>
          <div class="p-6">
            <div class="space-y-1 mb-4">
              <label class="block text-sm font-medium text-muted">方案名稱</label>
              <input v-model="saveName" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" placeholder="例: 股債80/20最優組合" />
            </div>
            <div v-if="saveError" class="p-3 mb-4 text-sm text-red-600 rounded-lg bg-red-50 dark:bg-red-900/20">{{ saveError }}</div>
          </div>
          <div class="px-6 py-4 bg-[var(--bg-sidebar)] flex justify-end gap-3">
            <button class="px-4 py-2 text-sm font-medium text-muted hover:bg-[var(--input-bg)] rounded-lg transition-colors border border-transparent" @click="showSaveModal = false; saveName = ''">取消</button>
            <button class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition-colors shadow-sm" @click="saveOptimization" :disabled="savingOptimization">
              <Loader2 v-if="savingOptimization" class="w-4 h-4 mr-2 inline animate-spin" />
              <span v-else>儲存</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Trophy, Shield, Dna, X, Check, Loader2, FolderOpen, Trash2, ArrowLeft, Save, Search, Plus, Target, Scale, Play } from 'lucide-vue-next'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { usePreferenceStore } from '../stores/preference'
import { useBreakpoint } from '../composables/useBreakpoint'
import CurrencySelector from '../components/CurrencySelector.vue'
import ShareImageButton from '../components/ShareImageButton.vue'

const auth = useAuthStore()
const router = useRouter()
const preference = usePreferenceStore()
const { isMobile, isTablet, isDesktop } = useBreakpoint()
// Remove local API_BASE declaration

const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])
const results = ref(null)
const runLoading = ref(false)
const optError = ref('')
const showSaved = ref(false)
const savedPortfolios = ref([])
const loadingSaved = ref(false)
const currentPage = ref(1)  // 分頁: 當前頁
const pageSize = ref(6)     // 分頁: 每頁項目數
const showSaveModal = ref(false)
const saveName = ref('')
const savingOptimization = ref(false)
const saveError = ref('')
const loadedPortfolioId = ref(null)  // 追蹤載入的組合 ID，用於自動儲存
const loadedPortfolioName = ref('')  // 追蹤載入的組合名稱
const loadedPortfolioType = ref(null)  // 追蹤載入的組合類型（backtest/optimize/monte_carlo）
const customPortfolioPerf = ref(null)  // 自定義權重組合的性能指標
const calcPerfLoading = ref(false)  // 計算性能中的加載狀態

const symbolTypes = [
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'indices', label: '指數/原物料' },
  { value: 'crypto', label: '加密貨幣' },
  { value: 'funds', label: '共同基金' },
]

const optConfig = reactive({
  start_date: '2015-01-01', // Optimization needs slightly longer history ideally
  end_date: new Date().toISOString().split('T')[0]
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  return availableSymbols.value.filter(s =>
    !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
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
}

function addSearchSymbol() {
  const sym = symbolSearch.value.trim().toUpperCase()
  if (!sym || isSelected(sym) || selectedItems.value.length >= 10) return
  selectedItems.value.push({ symbol: sym, name: sym, category: symbolType.value, weight: Math.floor(100 / (selectedItems.value.length + 1)) })
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

async function runOptimization() {
  optError.value = ''
  runLoading.value = true
  results.value = null
  customPortfolioPerf.value = null
  
  // ✅ 驗證日期是否有效
  if (!optConfig.start_date || !optConfig.end_date) {
    optError.value = '請設置回測起始日期和結束日期'
    runLoading.value = false
    return
  }
  
  try {
    const res = await axios.post(`${API_BASE}/api/optimize`, {
      symbols: selectedItems.value.map(i => i.symbol),
      start_date: optConfig.start_date,
      end_date: optConfig.end_date,
      display_currency: preference.displayCurrency,
    }, { headers: auth.headers })
    results.value = res.data.results
    
    // ✅ 優化完成後計算自定義組合性能（顯示目前權重在圖上的位置）
    await calculateCustomPortfolioPerf()
    
    // ✅ 如果是從載入的組合執行，自動儲存結果
    if (loadedPortfolioId.value) {
      await autoSaveOptimization()
    }
  } catch (e) {
    optError.value = e.response?.data?.detail || e.message
  } finally {
    runLoading.value = false
  }
}

// ✅ 均勻分配權重（整數百分比）
function equalizeWeights() {
  if (!selectedItems.value.length) return
  const baseWeight = Math.floor(100 / selectedItems.value.length)
  const remainder = 100 % selectedItems.value.length
  
  selectedItems.value.forEach((item, idx) => {
    item.weight = idx < remainder ? baseWeight + 1 : baseWeight
  })
}

// ✅ 調整權重（整數百分比，無需歸一化）
function adjustWeights(symbol, newWeight) {
  const item = selectedItems.value.find(i => i.symbol === symbol)
  if (!item) return
  item.weight = Math.max(0, Math.round(newWeight))
  
  // ✅ 權重變化時計算自定義組合的性能（如果已經運行過優化）
  if (results.value && totalWeight.value > 0) {
    calculateCustomPortfolioPerf()
  }
}

// ✅ 計算自定義權重組合的性能指標（用於圖表上的點）
async function calculateCustomPortfolioPerf() {
  if (!optConfig.start_date || !optConfig.end_date || selectedItems.value.length < 2) {
    customPortfolioPerf.value = null
    return
  }

  calcPerfLoading.value = true
  try {
    const weights = {}
    selectedItems.value.forEach(item => {
      weights[item.symbol] = item.weight
    })

    const res = await axios.post(`${API_BASE}/api/optimize/calculate-custom-portfolio`, {
      symbols: selectedItems.value.map(i => i.symbol),
      weights: weights,
      start_date: optConfig.start_date,
      end_date: optConfig.end_date,
      display_currency: preference.displayCurrency,
    }, { headers: auth.headers })

    customPortfolioPerf.value = res.data.portfolio
  } catch (e) {
    console.error('計算組合性能失敗:', e)
    customPortfolioPerf.value = null
  } finally {
    calcPerfLoading.value = false
  }
}

function createPieOption(portfolioData) {
  if (!portfolioData) return {}
  const data = Object.entries(portfolioData.weights)
    .filter(([sym, w]) => w > 0.01) // ignore weights less than 0.01%
    .map(([sym, w]) => ({ name: sym, value: w.toFixed(2) }))
  
  return {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(22, 27, 34, 0.9)', borderColor: 'rgba(48, 54, 61, 0.8)', textStyle: { color: '#e6edf3' }, formatter: '{b}: {c}%' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: 'transparent', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{c}%', color: 'inherit' },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: data
      }
    ]
  }
}

const totalWeight = computed(() => selectedItems.value.reduce((s, i) => s + (i.weight || 0), 0))

const maxSharpePieOption = computed(() => createPieOption(results.value?.max_sharpe))
const minVolPieOption = computed(() => createPieOption(results.value?.min_volatility))

const efficientFrontierOption = computed(() => {
  if (!results.value?.efficient_frontier) return {}
  
  // Format [x(vol), y(ret)]
  const v_list = results.value.efficient_frontier.volatilities
  const r_list = results.value.efficient_frontier.returns
  const frontierPoints = v_list.map((v, idx) => [
    (v * 100).toFixed(2), 
    (r_list[idx] * 100).toFixed(2)
  ])

  const maxSharpeInfo = results.value.max_sharpe
  const minVolInfo = results.value.min_volatility

  const maxSharpePoint = [
    (maxSharpeInfo.volatility * 100).toFixed(2), 
    (maxSharpeInfo.return * 100).toFixed(2)
  ]
  const minVolPoint = [
    (minVolInfo.volatility * 100).toFixed(2), 
    (minVolInfo.return * 100).toFixed(2)
  ]

  const assetPoints = (results.value.asset_points || []).map(p => ({
    name: p.symbol,
    value: [(p.volatility * 100).toFixed(2), (p.return * 100).toFixed(2)]
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(22, 27, 34, 0.9)', 
      borderColor: 'rgba(48, 54, 61, 0.8)', 
      textStyle: { color: '#e6edf3' },
      formatter: p => `風險 (波動率): ${p[0].value[0]}%<br/>預期報酬: ${p[0].value[1]}%` 
    },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { 
      type: 'value', 
      name: '風險 (年化波動率 %)',
      nameLocation: 'middle',
      nameGap: 25,
      axisLabel: { color: '#8b949e', show: !isMobile.value },
      splitLine: { lineStyle: { color: 'rgba(139, 148, 158, 0.1)' } },
      scale: true
    },
    yAxis: { 
      type: 'value', 
      name: '預期報酬 (%)',
      nameLocation: 'middle',
      nameGap: 40,
      axisLabel: { color: '#8b949e', show: !isMobile.value },
      splitLine: { lineStyle: { color: 'rgba(139, 148, 158, 0.1)' } },
      scale: true
    },
    visualMap: {
      type: 'continuous',
      dimension: 2, 
      min: 0,
      max: 2, 
      calculable: true,
      orient: 'vertical',
      right: 0,
      top: 'center',
      inRange: { color: ['#1f6feb', '#58a6ff', '#3fb950', '#f85149'] },
      textStyle: { color: '#8b949e' },
      show: false 
    },
    series: [
      {
        name: '效率前緣',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#58a6ff' },
        data: frontierPoints
      },
      {
        name: '個別資產',
        type: 'scatter',
        symbolSize: 8,
        itemStyle: { color: '#8b949e', opacity: 0.6 },
        label: { 
          show: true, 
          position: 'right', 
          color: '#8b949e', 
          fontSize: 10, 
          formatter: '{b}',
          distance: 5
        },
        data: assetPoints,
        tooltip: { formatter: p => `資產: ${p.name}<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      {
        name: 'Max Sharpe 圓圈',
        type: 'scatter',
        symbolSize: 17.5,
        itemStyle: { 
          color: 'transparent', 
          borderColor: '#f85149', 
          borderWidth: 2,
          opacity: 0.8
        },
        label: { show: false },
        data: [maxSharpePoint],
        tooltip: { show: false }
      },
      {
        name: 'Max Sharpe',
        type: 'scatter',
        symbolSize: 14,
        itemStyle: { color: '#f85149', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'top',
          color: '#f85149',
          fontWeight: 'bold',
          formatter: '🏆 Max Sharpe',
          distance: 10
        },
        data: [maxSharpePoint],
        tooltip: { formatter: p => `🏆 最大夏普點<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      {
        name: 'Min Volatility 圓圈',
        type: 'scatter',
        symbolSize: 17.5,
        itemStyle: { 
          color: 'transparent', 
          borderColor: '#3fb950', 
          borderWidth: 2,
          opacity: 0.8
        },
        label: { show: false },
        data: [minVolPoint],
        tooltip: { show: false }
      },
      {
        name: 'Min Volatility',
        type: 'scatter',
        symbolSize: 14,
        itemStyle: { color: '#3fb950', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'bottom',
          color: '#3fb950',
          fontWeight: 'bold',
          formatter: '🛡️ Min Vol',
          distance: 10
        },
        data: [minVolPoint],
        tooltip: { formatter: p => `🛡️ 最小波動點<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%` }
      },
      // ✅ 自定義組合點（使用者手動調整的權重）
      customPortfolioPerf.value ? {
        name: '您的投資組合',
        type: 'scatter',
        symbolSize: 16,
        itemStyle: { color: '#a371f7', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'left',
          color: '#a371f7',
          fontWeight: 'bold',
          formatter: '📊 您的組合',
          distance: 10
        },
        data: [[
          (customPortfolioPerf.value.volatility).toFixed(2),
          (customPortfolioPerf.value.return).toFixed(2)
        ]],
        tooltip: { formatter: p => `📊 您的投資組合<br/>波動: ${p.value[0]}%<br/>報酬: ${p.value[1]}%<br/>夏普比: ${customPortfolioPerf.value.sharpe_ratio.toFixed(4)}` }
      } : null
    ].filter(s => s !== null)
  }
})

function exportToBacktest(portfolioData) {
  // Store configured weights into sessionStorage to pass to backtest view
  const items = selectedItems.value.map(item => ({
    symbol: item.symbol,
    name: item.name,
    category: item.category,
    weight: portfolioData.weights[item.symbol] || 0
  })).filter(i => i.weight > 0.01)

  const preset = {
    items,
    start_date: optConfig.start_date,
    end_date: optConfig.end_date
  }
  
  sessionStorage.setItem('backtest_preset', JSON.stringify(preset))
  router.push('/backtest')
}

async function loadSavedPortfolios() {
  try {
    // ✅ 改為讀取 /api/backtest，顯示所有類型的組合（backtest, optimize, monte_carlo）
    // 這樣 OptimizeView 可以加載任何功能保存的組合
    const res = await axios.get(`${API_BASE}/api/backtest`, { headers: auth.headers })
    savedPortfolios.value = res.data
    currentPage.value = 1  // ✅ 重置分頁到第一頁
  } catch (e) { console.error('Load saved failed', e) }
  finally {
    loadingSaved.value = false
  }
}

async function deleteSaved(id) {
  if (!confirm('確定刪除此優化結果？')) return
  try {
    saveError.value = ''
    // ✅ 改為使用 /api/backtest 刪除組合
    await axios.delete(`${API_BASE}/api/backtest/${id}`, { headers: auth.headers })
    await loadSavedPortfolios()
  } catch (e) { console.error('Delete failed', e) }
}

function loadSaved(p) {
  // ✅ 優先從 results_json 中恢復所有資產（包括權重為 0 的資產）
  // 這樣可以恢復完整的優化組合，而不是只加載儲存的資產
  if (p.results_json && p.results_json.max_sharpe && p.results_json.max_sharpe.weights) {
    const weights = p.results_json.max_sharpe.weights
    selectedItems.value = Object.entries(weights).map(([symbol, weight]) => ({
      symbol,
      name: symbol,
      weight: weight || 0,
      category: p.items?.[0]?.category || 'us_etf'  // 從已儲存的資產推斷類別
    }))
  } else {
    // ✅ 後備方案：使用儲存的 items（如果沒有結果數據）
    selectedItems.value = p.items.map(i => ({ ...i }))
  }
  
  // ✅ 檢查日期有效性：如果為 null（如 Monte Carlo 等不需要日期的類型），設置默認值
  if (p.start_date && p.end_date) {
    optConfig.start_date = p.start_date
    optConfig.end_date = p.end_date
  } else {
    // 如果沒有日期，使用默認值 (2015-01-01)
    optConfig.start_date = '2015-01-01'
    optConfig.end_date = new Date().toISOString().split('T')[0]
  }
  
  // Only restore results if valid results_json exists
  results.value = (p.results_json && p.results_json.max_sharpe) ? p.results_json : null
  // ✅ 記錄載入的組合 ID 用於自動儲存
  loadedPortfolioId.value = p.id
  loadedPortfolioName.value = p.name
  saveName.value = p.name // ✅ 同步儲存名稱以便快速儲存
  loadedPortfolioType.value = p.portfolio_type  // ✅ 記錄組合類型
  // Switch to config panel immediately
  showSaved.value = false
}

// ✅ 自動儲存：當從已載入組合執行優化時自動保存結果
async function autoSaveOptimization() {
  try {
    console.log('[OptimizeView] Auto-saving optimization results...')
    // ✅ 直接使用用戶設定的權重
    const itemsToSave = selectedItems.value.map(item => {
      return { ...item, weight: item.weight || 0 }
    })
    
    // ✅ 自動儲存：以同名覆蓋原組合，無需增加後綴
    const response = await axios.post(`${API_BASE}/api/optimize/save`, {
      id: loadedPortfolioId.value,  // ✅ 傳遞 id 以執行 upsert
      name: loadedPortfolioName.value,  // ✅ 同名覆蓋，不增加後綴
      items: itemsToSave,  // ✅ 傳遞計算後的權重
      start_date: optConfig.start_date,
      end_date: optConfig.end_date,
      results_json: results.value,
    }, { headers: auth.headers })
    console.log('[OptimizeView] Auto-save successful:', response.data)
    // ✅ 自動儲存成功：自動刷新側邊欄列表(無需用戶手動操作)
    await loadSavedPortfolios()
  } catch (e) {
    console.error('[OptimizeView] Auto-save failed:', e.message, e.response?.data)
    // 不中斷用戶，允許手動儲存
  }
}

async function saveOptimization() {
  if (!saveName.value.trim()) return
  saveError.value = ''
  savingOptimization.value = true
  try {
    // ✅ 直接使用用戶設定的權重
    const itemsToSave = selectedItems.value.map(item => {
      return { ...item, weight: item.weight || 0 }
    })
    
    // ✅ 檢查名稱是否改變：同名時更新，異名時另存新檔
    let portfolioId = null
    if (loadedPortfolioId.value && saveName.value === loadedPortfolioName.value) {
      // 同名：詢問用戶是否覆蓋
      const confirmed = confirm(`確定要更新「${saveName.value}」嗎？`)
      if (!confirmed) {
        savingOptimization.value = false
        return
      }
      portfolioId = loadedPortfolioId.value
    } else if (loadedPortfolioId.value && saveName.value !== loadedPortfolioName.value) {
      // 異名：詢問用戶是新增還是覆蓋
      const response = confirm(
        `您已加載的優化結果為「${loadedPortfolioName.value}」，現在儲存為「${saveName.value}」。\n\n` +
        `點擊【確定】另存新檔\n` +
        `點擊【取消】返回修改名稱`
      )
      if (!response) {
        savingOptimization.value = false
        return
      }
      // 不傳遞 portfolioId，建立新組合
      portfolioId = null
    }
    // else: 未加載任何組合，新增新組合（portfolioId = null）

    await axios.post(`${API_BASE}/api/optimize/save`, {
      id: portfolioId,
      name: saveName.value,
      items: itemsToSave,  // ✅ 傳遞計算後的權重
      start_date: optConfig.start_date,
      end_date: optConfig.end_date,
      results_json: results.value,
    }, { headers: auth.headers })
    showSaveModal.value = false
    // 如果建立了新組合，重置名稱；如果覆蓋，保持不變
    if (!portfolioId) saveName.value = ''
    // 重置載入的組合（如果覆蓋更新，需要重新加載以獲取最新時間戳等元數據）
    loadedPortfolioId.value = null
    loadedPortfolioName.value = ''
    // ✅ 重新加載側邊欄列表
    await loadSavedPortfolios()
    alert('最佳化方案已儲存！')
  } catch (e) { 
    saveError.value = e.response?.data?.detail || e.message 
  } finally {
    savingOptimization.value = false
  }
}

onMounted(async () => {
  try {
    await loadSymbols()
    console.log('[OptimizeView] Symbols loaded successfully')
  } catch (error) {
    console.error('[OptimizeView] Failed to load symbols:', error)
  }
})

function onImageShareSuccess(shareResult) {
  console.log('圖形分享成功:', shareResult)
}

// ✅ 監聽權重變化，防抖計算組合性能（僅在有結果時）
let perfCalculationTimer = null
watch(
  () => selectedItems.value.map(i => i.weight).join(','),
  () => {
    if (!results.value || selectedItems.value.length < 2) {
      customPortfolioPerf.value = null
      return
    }
    
    // 防抖：延遲 500ms 後計算
    clearTimeout(perfCalculationTimer)
    perfCalculationTimer = setTimeout(() => {
      calculateCustomPortfolioPerf()
    }, 500)
  },
  { immediate: false }
)
</script>

<style scoped>
.optimize-header {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
}

.symbol-item {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  width: 100% !important;
}
</style>


