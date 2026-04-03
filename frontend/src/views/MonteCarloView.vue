<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div>
        <h2 class="text-xl font-bold text-[var(--text-primary)]">蒙地卡羅模擬 (Monte Carlo Simulation)</h2>
        <div class="text-xs sm:text-sm text-[var(--text-secondary)]">基於歷史數據進行 10,000 次隨機路徑模擬，預測長期投資組合的成功率與分佈。</div>
      </div>
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 w-[calc(100%+2rem)] sm:w-auto">
        <button
          :class="['flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all shadow-sm border whitespace-nowrap',
            !showSaved
              ? 'bg-brand-500 border-brand-500 text-white'
              : 'bg-[var(--bg-sidebar)] border-[var(--border-color)] text-muted hover:text-[var(--text-primary)]']"
          @click="showSaved = false">
          <Dice5 class="w-4 h-4 mr-2" />開始模擬
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
          @click="showSaved = false">
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
        尚無已儲存的模擬組合
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
            <div v-if="p.items" class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">初始金額</div>
                <div class="fw-600 text-rose-600">${{ (p.initial_amount || 0).toLocaleString() }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">年數</div>
                <div class="fw-600 text-brand-600">{{ p.years || '--' }}</div>
              </div>
              <div>
                <div class="text-xs text-muted">模擬次數</div>
                <div class="fw-600 text-accent">{{ (p.simulations || 0).toLocaleString() }}</div>
              </div>
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3" style="gap:12px;">
              <div>
                <div class="text-xs text-muted">初始金額</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">年數</div>
                <div class="fw-600 text-muted">--</div>
              </div>
              <div>
                <div class="text-xs text-muted">模擬次數</div>
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

    <!-- Configuration Panel -->
    <div v-if="!showSaved" class="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
      <!-- Asset Selection -->
      <div class="lg:col-span-1 space-y-4">
        <div class="glass-card h-full flex flex-col">
          <div class="p-4 border-b border-[var(--border-color)]">
            <h3 class="font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Target class="w-4 h-4 text-brand-500" />
              配置資產權重
            </h3>
          </div>
          <div class="p-4 flex-1 flex flex-col space-y-4">
            <!-- Asset Selection UI (Simplified version of OptimizeView) -->
            <div class="space-y-3">
              <div class="flex gap-2 overflow-x-auto scrollbar-none pb-1">
                <button v-for="t in symbolTypes" :key="t.value"
                  :class="['px-3 py-1.5 text-xs font-medium rounded-full border transition-colors whitespace-nowrap', symbolType === t.value ? 'bg-brand-500 text-white border-brand-500' : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-color)] hover:bg-[var(--input-bg)]']"
                  @click="symbolType = t.value; loadSymbols()">{{ t.label }}</button>
              </div>
              
              <div class="relative">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" :size="14" />
                <input v-model="symbolSearch" type="text" 
                  class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]"
                  placeholder="搜尋及點選資產..." />
              </div>

              <div class="h-48 overflow-y-auto border border-[var(--border-color)] rounded-xl bg-[var(--bg-main)]/50 custom-scrollbar">
                <div v-for="s in filteredSymbols.slice(0, 100)" :key="s.symbol"
                  :class="['px-3 py-2 cursor-pointer transition-all border-b border-[var(--border-color)] last:border-0 flex items-center justify-between', isSelected(s.symbol) ? 'bg-brand-500/10' : 'hover:bg-[var(--input-bg)]']"
                  @click="toggleSymbol(s)">
                  <div class="flex flex-col min-w-0">
                    <span class="font-bold text-xs text-[var(--text-primary)] truncate">{{ s.symbol }}</span>
                    <span class="text-[10px] text-[var(--text-secondary)] truncate">{{ s.name }}</span>
                  </div>
                  <Plus v-if="!isSelected(s.symbol)" class="w-3 h-3 text-zinc-400" />
                  <Check v-else class="w-3 h-3 text-brand-500" />
                </div>
              </div>
            </div>

            <!-- Selected Assets Weights -->
            <div class="space-y-3 overflow-y-auto pr-1" style="max-height: 300px;">
              <div v-for="item in selectedItems" :key="item.symbol" class="p-3 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)] space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-[var(--text-primary)]">{{ item.symbol }}</span>
                  <button @click="removeSymbol(item.symbol)" class="text-zinc-400 hover:text-rose-500 transition-colors">
                    <X class="w-3 h-3" />
                  </button>
                </div>
                <div class="flex items-center gap-3">
                  <input type="range" v-model.number="item.weight" min="0" max="100" step="5" class="weight-slider flex-1 h-1.5 bg-brand-500/20 dark:bg-brand-500/20 rounded-lg appearance-none cursor-pointer" />
                  <span class="text-xs font-mono font-bold w-14 text-right rounded px-2 py-1 bg-brand-500/10 dark:bg-brand-500/10 text-brand-500">{{ item.weight }}<span class="ml-0.5">%</span></span>
                </div>
              </div>
            </div>

            <div v-if="totalWeight !== 100" class="text-[10px] text-amber-500 font-medium">
              ⚠️ 當前權重總和為 {{ totalWeight }}% (需為 100%)
            </div>
          </div>
        </div>
      </div>

      <!-- Simulation Parameters -->
      <div class="lg:col-span-1 space-y-4">
        <div class="glass-card h-full flex flex-col">
          <div class="p-4 border-b border-[var(--border-color)]">
            <h3 class="font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Dice5 class="w-4 h-4 text-brand-500" />
              模擬參數設定
            </h3>
          </div>
          <div class="p-6 space-y-6 flex-1 overflow-y-auto">
            <div class="space-y-4">
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">初始金額 (USD/TWD)</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <input v-model.number="config.initial_amount" type="number" 
                    class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2.5 pl-8 pr-4 text-sm font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">模擬年數</label>
                  <input v-model.number="config.years" type="number" 
                    class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2.5 px-4 text-sm font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">模擬次數</label>
                  <select v-model.number="config.simulations" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2.5 px-4 text-sm font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)] h-10">
                    <option :value="1000">1,000 次</option>
                    <option :value="5000">5,000 次</option>
                    <option :value="10000">10,000 次</option>
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">年投入金額 (+)</label>
                  <input v-model.number="config.annual_contribution" type="number" 
                    class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2.5 px-4 text-sm font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">年取百分比 (%)</label>
                  <div class="relative">
                    <input v-model.number="config.annual_withdrawal" type="number" step="0.1"
                      class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2.5 pr-8 pl-4 text-sm font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500">%</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="pt-6 border-t border-[var(--border-color)] space-y-4">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-[var(--text-primary)]">考慮通膨影響</label>
                <label class="flex items-center cursor-pointer gap-2">
                  <input type="checkbox" v-model="config.adjust_for_inflation" class="w-5 h-5 rounded accent-brand-500 cursor-pointer" />
                </label>
              </div>
              
              <div v-if="config.adjust_for_inflation" class="grid grid-cols-2 gap-4 animate-in fade-in slide-in-from-top-2">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-widest">平均通膨率</label>
                  <div class="relative">
                    <input v-model.number="config.inflation_mean" type="number" step="0.01"
                      class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2 px-3 text-xs font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-[10px]">%</span>
                  </div>
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-widest">通膨波動度</label>
                  <div class="relative">
                    <input v-model.number="config.inflation_std" type="number" step="0.01"
                      class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg py-2 px-3 text-xs font-bold focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]" />
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-[10px]">%</span>
                  </div>
                </div>
              </div>
            </div>

            <button 
              @click="runSimulation"
              :disabled="loading || selectedItems.length === 0 || totalWeight !== 100"
              class="w-full bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-brand-500/20 transition-all active:scale-95 flex items-center justify-center gap-2">
              <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
              <Play v-else class="w-4 h-4 fill-current" />
              {{ loading ? '模擬運算中...' : '開始模擬分析' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Quick Summary Stats (Visible after run) -->
      <div class="lg:col-span-1">
        <div v-if="results" class="space-y-4 animate-in fade-in slide-in-from-right-4 duration-500">
          <div class="glass-card bg-brand-500/10 border-brand-500/20">
            <div class="p-6 text-center">
              <h4 class="text-xs font-bold text-brand-600 uppercase tracking-widest mb-1">投資成功率</h4>
              <div class="text-5xl font-black text-brand-500 tracking-tighter">
                {{ (results.summary.success_rate * 100).toFixed(1) }}<span class="text-2xl">%</span>
              </div>
              <p class="text-[10px] text-brand-600 font-medium mt-2">模擬達成保本目標 (終值 ≥ 初始投入) 的比例</p>
            </div>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="glass-card p-4">
              <h4 class="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-widest mb-1">預期中位數</h4>
              <div class="text-lg font-bold text-[var(--text-primary)] truncate">
                ${{ formatNumber(results.summary.median_end_balance) }}
              </div>
              <div class="text-[10px] text-zinc-500">第 50 百分位數</div>
            </div>
            <div class="glass-card p-4">
              <h4 class="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-widest mb-1">最悲觀情況</h4>
              <div class="text-lg font-bold text-rose-500 truncate">
                ${{ formatNumber(results.summary.p10_end_balance) }}
              </div>
              <div class="text-[10px] text-zinc-500">第 10 百分位數 (P10)</div>
            </div>
          </div>

          <div class="glass-card p-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-brand-500/10 dark:bg-brand-500/20 flex items-center justify-center">
                <History class="w-5 h-5 text-brand-500" />
              </div>
              <div>
                <h4 class="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-widest">樣本數據範圍</h4>
                <div class="text-sm font-bold text-[var(--text-primary)]">
                  使用過去 {{ results.history_years }} 年歷史數據
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Initial Placeholder -->
        <div v-else class="glass-card h-full flex flex-col items-center justify-center p-8 text-center bg-zinc-50/50 dark:bg-zinc-900/50 border-dashed">
          <div class="w-16 h-16 rounded-2xl bg-brand-500/10 dark:bg-brand-500/20 flex items-center justify-center mb-4">
            <BarChart3 class="w-8 h-8 text-brand-500" />
          </div>
          <h3 class="text-sm font-bold text-[var(--text-primary)] mb-2">準備開始模擬</h3>
          <p class="text-xs text-[var(--text-secondary)] leading-relaxed">
            請在左側選擇資產權重並設定模擬參數，系統將為您預測未來資產分佈狀況。
          </p>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div v-if="results && !showSaved" class="grid grid-cols-1 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <div class="glass-card overflow-hidden">
        <div class="p-4 border-b border-[var(--border-color)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h3 class="font-semibold text-[var(--text-primary)] text-sm">資產增長隨機路徑百分位 (Percentile Paths)</h3>
          <div class="flex flex-wrap items-center gap-3 sm:gap-4">
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-brand-500"></span>
              <span class="text-[10px] font-bold text-[var(--text-secondary)]">P50 (中位數)</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-full bg-zinc-400"></span>
              <span class="text-[10px] font-bold text-[var(--text-secondary)]">P10 - P90 區間</span>
            </div>
          </div>
        </div>
        <div class="p-4 h-[300px] sm:h-[400px] md:h-[450px]">
          <v-chart :option="pathChartOption" autoresize />
        </div>
      </div>
    </div>
    
    <div v-if="error && !showSaved" class="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-500 text-sm flex items-center gap-3">
      <AlertTriangle class="w-5 h-5 flex-shrink-0" />
      {{ error }}
    </div>

    <!-- Save button -->
    <div v-if="results && !showSaved" class="flex gap-3 mt-8 justify-center mb-8">
      <button class="flex items-center justify-center px-6 py-3 text-sm font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-all shadow-sm" @click="showSaveModal = true">
        <Save class="w-4 h-4 mr-2" />儲存模擬結果
      </button>
    </div>

    <!-- Save modal -->
    <Transition name="fade">
      <div v-if="showSaveModal" class="fixed inset-0 bg-gray-900/50 dark:bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-[var(--bg-main)] rounded-xl shadow-xl w-full max-w-md overflow-hidden ring-1 ring-[var(--border-color)]">
          <div class="px-6 py-4 border-b border-[var(--border-color)] flex justify-between items-center font-semibold text-[var(--text-primary)]"><h3>儲存模擬結果</h3><button class="text-muted hover:text-[var(--text-primary)] transition-colors" @click="showSaveModal = false"><X class="w-4 h-4" /></button></div>
          <div class="p-6">
            <div class="space-y-1 mb-4">
              <label class="block text-sm font-medium text-muted">結果名稱</label>
              <input v-model="saveName" type="text" class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2.5" placeholder="例: 保守型30年退休規劃" />
            </div>
            <div v-if="saveError" class="p-3 mb-4 text-sm text-red-600 rounded-lg bg-red-50 dark:bg-red-900/20">{{ saveError }}</div>
          </div>
          <div class="px-6 py-4 bg-[var(--bg-sidebar)] flex justify-end gap-3">
            <button class="px-4 py-2 text-sm font-medium text-muted hover:bg-[var(--input-bg)] rounded-lg transition-colors border border-transparent" @click="showSaveModal = false; saveName = ''">取消</button>
            <button class="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium rounded-lg transition-colors shadow-sm" @click="saveMonteCarloSimulation" :disabled="savingSimulation">
              <Loader2 v-if="savingSimulation" class="w-4 h-4 mr-2 inline animate-spin" />
              <span v-else>儲存</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { 
  Target, Search, Plus, Check, X, Dice5, Play, 
  Loader2, BarChart3, AlertTriangle, History, FolderOpen, Trash2, ArrowLeft, Save
} from 'lucide-vue-next'

const auth = useAuthStore()

// State
const loading = ref(false)
const error = ref('')
const results = ref(null)
const showSaved = ref(false)
const savedPortfolios = ref([])
const loadingSaved = ref(false)
const currentPage = ref(1)  // 分頁: 當前頁
const pageSize = ref(6)     // 分頁: 每頁項目數
const showSaveModal = ref(false)
const saveName = ref('')
const savingSimulation = ref(false)
const saveError = ref('')
const loadedPortfolioId = ref(null)  // 追蹤載入的組合 ID，用於自動儲存
const loadedPortfolioName = ref('')  // 追蹤載入的組合名稱

const config = reactive({
  initial_amount: 100000,
  years: 30,
  simulations: 10000,
  annual_contribution: 0,
  annual_withdrawal: 4,
  inflation_mean: 3.0,
  inflation_std: 1.0,
  adjust_for_inflation: true
})

// Asset Selection
const symbolSearch = ref('')
const symbolType = ref('us_etf')
const availableSymbols = ref([])
const selectedItems = ref([])

const symbolTypes = [
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'indices', label: '指數/原物料' },
]

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  return availableSymbols.value.filter(s =>
    !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
})

const totalWeight = computed(() => selectedItems.value.reduce((sum, item) => sum + item.weight, 0))

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
    selectedItems.value.push({ ...s, weight: 0 })
    // Auto-distribute weights equally among all items
    const count = selectedItems.value.length
    const equalWeight = Math.round((100 / count) * 100) / 100 // 四捨五入到2位小數
    selectedItems.value.forEach(item => {
      item.weight = equalWeight
    })
  }
}

function removeSymbol(sym) {
  selectedItems.value = selectedItems.value.filter(i => i.symbol !== sym)
  // Re-distribute weights equally among remaining items
  if (selectedItems.value.length > 0) {
    const count = selectedItems.value.length
    const equalWeight = Math.round((100 / count) * 100) / 100
    selectedItems.value.forEach(item => {
      item.weight = equalWeight
    })
  }
}

async function loadSymbols() {
  try {
    const res = await axios.get(`${API_BASE}/api/backtest/symbols`, { headers: auth.headers })
    const data = res.data
    if (symbolType.value === 'us_etf') availableSymbols.value = data.us_etf || []
    else if (symbolType.value === 'tw_etf') availableSymbols.value = data.tw_etf || []
    else availableSymbols.value = data.indices || []
  } catch (e) { console.error('Symbol load failed', e) }
}

async function runSimulation() {
  error.value = ''
  loading.value = true
  results.value = null
  
  try {
    const payload = {
      assets: selectedItems.value.map(item => ({
        symbol: item.symbol,
        weight: item.weight / 100
      })),
      ...config
    }
    
    // Scale percentages for backend API (backend expects 0.03 for 3%)
    if (payload.adjust_for_inflation) {
      payload.inflation_mean = payload.inflation_mean / 100
      payload.inflation_std = payload.inflation_std / 100
    } else {
      payload.inflation_mean = 0
      payload.inflation_std = 0
    }
    
    const res = await axios.post(`${API_BASE}/api/monte-carlo/run`, payload, { headers: auth.headers })
    results.value = res.data
    
    // ✅ 如果是從載入的組合執行，自動儲存結果
    if (loadedPortfolioId.value) {
      await autoSaveMonteCarloSimulation()
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '模擬分析執行失敗，請稍後再試。'
    console.error('Simulation failed:', err)
  } finally {
    loading.value = false
  }
}

// Chart Options
const pathChartOption = computed(() => {
  if (!results.value) return {}
  
  const years = Array.from({ length: config.years + 1 }, (_, i) => `${i}Y`)
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#e4e4e7',
      textStyle: { color: '#09090b', fontSize: 12 },
      formatter: (params) => {
        let res = `<div class="font-bold mb-1">${params[0].axisValue}</div>`
        params.forEach(p => {
          res += `<div class="flex items-center justify-between gap-4">
            <span class="flex items-center gap-1.5 text-zinc-500">
              <span class="w-2 h-2 rounded-full" style="background-color: ${p.color}"></span>
              ${p.seriesName}
            </span>
            <span class="font-bold">$${formatNumber(p.value)}</span>
          </div>`
        })
        return res
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '4%', containLabel: true },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: { lineStyle: { color: '#f4f4f5' } },
      axisLabel: { color: '#71717a', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { 
        color: '#71717a', 
        fontSize: 10,
        formatter: (value) => `$${formatNumber(value)}`
      },
      splitLine: { lineStyle: { color: '#f4f4f5' } }
    },
    series: [
      {
        name: 'P90 (樂觀)',
        type: 'line',
        data: results.value.percentile_paths.p90,
        symbol: 'none',
        lineStyle: { width: 1, color: '#94a3b8', type: 'dashed' },
        itemStyle: { color: '#94a3b8' }
      },
      {
        name: 'P75',
        type: 'line',
        data: results.value.percentile_paths.p75,
        symbol: 'none',
        lineStyle: { width: 1.5, color: '#cbd5e1' },
        itemStyle: { color: '#cbd5e1' }
      },
      {
        name: 'P50 (中位數)',
        type: 'line',
        data: results.value.percentile_paths.p50,
        symbol: 'none',
        lineStyle: { width: 3, color: '#22c55e' },
        itemStyle: { color: '#22c55e' }
      },
      {
        name: 'P25',
        type: 'line',
        data: results.value.percentile_paths.p25,
        symbol: 'none',
        lineStyle: { width: 1.5, color: '#fb923c' },
        itemStyle: { color: '#fb923c' }
      },
      {
        name: 'P10 (悲觀)',
        type: 'line',
        data: results.value.percentile_paths.p10,
        symbol: 'none',
        lineStyle: { width: 1, color: '#f43f5e', type: 'dashed' },
        itemStyle: { color: '#f43f5e' }
      }
    ]
  }
})

function formatNumber(num) {
  if (num === undefined || num === null) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

async function loadSavedPortfolios() {
  try {
    // ✅ 改為讀取 /api/backtest，顯示所有類型的組合（backtest, optimize, monte_carlo）
    // 這樣 MonteCarloView 可以加載任何功能保存的組合
    const res = await axios.get(`${API_BASE}/api/backtest`, { headers: auth.headers })
    savedPortfolios.value = res.data
    currentPage.value = 1  // ✅ 重置分頁到第一頁
  } catch (e) { console.error('Load saved failed', e) }
  finally {
    loadingSaved.value = false
  }
}

async function deleteSaved(id) {
  if (!confirm('確定刪除此蒙地卡羅結果？')) return
  try {
    saveError.value = ''
    // ✅ 改為使用 /api/backtest 刪除組合
    await axios.delete(`${API_BASE}/api/backtest/${id}`, { headers: auth.headers })
    await loadSavedPortfolios()
  } catch (e) { console.error('Delete failed', e) }
}

function loadSaved(p) {
  selectedItems.value = p.items.map(i => ({ ...i }))
  config.initial_amount = p.initial_amount || 100000
  
  // ✅ 從 results_json.config 中提取配置參數（新方案）
  const configFromResults = p.results_json?.config
  if (configFromResults) {
    config.years = configFromResults.years || 30
    config.simulations = configFromResults.simulations || 10000
    config.annual_contribution = configFromResults.annual_contribution || 0
    config.annual_withdrawal = configFromResults.annual_withdrawal || 4
    config.inflation_mean = (configFromResults.inflation_mean || 0.03) * 100
    config.inflation_std = (configFromResults.inflation_std || 0.01) * 100
    config.adjust_for_inflation = configFromResults.adjust_for_inflation !== false
  } else {
    // ✅ 後備方案：直接從 portfolio 對象讀取（舊數據）
    config.years = p.years || 30
    config.simulations = p.simulations || 10000
    config.annual_contribution = p.annual_contribution || 0
    config.annual_withdrawal = p.annual_withdrawal || 4
    config.inflation_mean = (p.inflation_mean || 0.03) * 100
    config.inflation_std = (p.inflation_std || 0.01) * 100
    config.adjust_for_inflation = p.adjust_for_inflation !== false
  }
  
  // Only restore results if valid monte carlo results_json exists
  results.value = (p.results_json && p.results_json.summary) ? p.results_json : null
  // ✅ 記錄載入的組合 ID 用於自動儲存
  loadedPortfolioId.value = p.id
  loadedPortfolioName.value = p.name
  // Switch to config panel immediately
  showSaved.value = false
}

// ✅ 自動儲存：當從已載入組合執行蒙地卡羅模擬時自動保存結果
async function autoSaveMonteCarloSimulation() {
  try {
    console.log('[MonteCarloView] Auto-saving simulation results...')
    const response = await axios.post(`${API_BASE}/api/monte-carlo/save`, {
      name: `${loadedPortfolioName.value} - 模擬結果`,
      items: selectedItems.value,
      initial_amount: config.initial_amount,
      years: config.years,
      simulations: config.simulations,
      annual_contribution: config.annual_contribution,
      annual_withdrawal: config.annual_withdrawal,
      inflation_mean: config.adjust_for_inflation ? config.inflation_mean : 0,
      inflation_std: config.adjust_for_inflation ? config.inflation_std : 0,
      adjust_for_inflation: config.adjust_for_inflation,
      results_json: results.value,
      portfolio_id: loadedPortfolioId.value,
    }, { headers: auth.headers })
    console.log('[MonteCarloView] Auto-save successful:', response.data)
    // ✅ 自動儲存成功：自動刷新側邊欄列表(無需用戶手動操作)
    await loadSavedPortfolios()
  } catch (e) {
    console.error('[MonteCarloView] Auto-save failed:', e.message, e.response?.data)
    // 不中斷用戶，允許手動儲存
  }
}

async function saveMonteCarloSimulation() {
  if (!saveName.value.trim()) return
  saveError.value = ''
  savingSimulation.value = true
  try {
    await axios.post(`${API_BASE}/api/monte-carlo/save`, {
      name: saveName.value,
      items: selectedItems.value,
      initial_amount: config.initial_amount,
      years: config.years,
      simulations: config.simulations,
      annual_contribution: config.annual_contribution,
      annual_withdrawal: config.annual_withdrawal,
      inflation_mean: config.adjust_for_inflation ? config.inflation_mean : 0,
      inflation_std: config.adjust_for_inflation ? config.inflation_std : 0,
      adjust_for_inflation: config.adjust_for_inflation,
      results_json: results.value,
      // portfolio_id 只在手動儲存時設為 null（新組合）
      portfolio_id: null,
    }, { headers: auth.headers })
    showSaveModal.value = false
    saveName.value = ''
    // 重置載入的組合
    loadedPortfolioId.value = null
    loadedPortfolioName.value = ''
    // ✅ 重新加載側邊欄列表
    await loadSavedPortfolios()
    alert('模擬結果已儲存！')
  } catch (e) { 
    saveError.value = e.response?.data?.detail || e.message 
  } finally {
    savingSimulation.value = false
  }
}

onMounted(() => {
  loadSymbols()
})
</script>

<style scoped>
.glass-card {
  background-color: #ffffff;
  border: 1px solid #e4e4e7;
  border-radius: 1rem;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  backdrop-filter: blur(12px);
}

:root.dark .glass-card {
  background-color: #18181b;
  border-color: #27272a;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e4e4e7;
  border-radius: 9999px;
}

:root.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
}

/* Range Slider Styling */
.weight-slider {
  -webkit-appearance: none;
  appearance: none;
}

.weight-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #22c55e;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(34, 197, 94, 0.3);
}

.weight-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #22c55e;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(34, 197, 94, 0.3);
}

.weight-slider::-moz-range-track {
  background: transparent;
  border: none;
}
</style>
