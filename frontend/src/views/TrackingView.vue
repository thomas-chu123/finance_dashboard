<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h2 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">指數追蹤管理</h2>
      <div v-if="!isMobile" class="flex gap-2">
        <button class="flex items-center justify-center px-4 py-2 text-zinc-600 dark:text-zinc-400 hover:text-[var(--text-primary)] hover:bg-[var(--input-bg)] rounded-xl transition-all text-sm font-bold" @click="async () => { console.log('Manual refresh triggered'); diagnosePageState(); await trackingStore.fetchAll(); console.log('Manual refresh completed'); }">
          <Loader2 class="w-4 h-4 mr-2" />
          重新加載
        </button>
        <button class="flex items-center justify-center px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-brand-500/20" @click="showAddModal = true">
          <Plus class="w-4 h-4 mr-2" />
          新增追蹤
        </button>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex flex-wrap gap-2 pb-1">
        <button v-for="cat in categories" :key="cat.value"
          :class="['px-4 py-1.5 rounded-full text-sm font-bold transition-colors border relative whitespace-nowrap', activeCategory === cat.value ? 'bg-brand-500 border-brand-500 text-white shadow-sm' : 'bg-transparent border-[var(--border-color)] text-zinc-500 hover:border-brand-500 hover:text-brand-500']"
          @click="activeCategory = cat.value">
          {{ cat.label }}
          <span v-if="cat.value === 'all'" class="ml-1 text-xs opacity-70">({{ trackingStore.items.length }})</span>
          <span v-else class="ml-1 text-xs opacity-70">({{ trackingStore.items.filter(i => i.category === cat.value).length }})</span>
        </button>
      </div>
      <div>
        <button class="flex items-center px-3 py-1.5 text-sm font-bold text-zinc-500 hover:text-[var(--text-primary)] transition-colors" @click="fetchFundamentals" :disabled="loadingFundamentals">
          <Loader2 v-if="loadingFundamentals" class="w-4 h-4 mr-2 animate-spin text-brand-500" />
          <BarChart2 v-else class="w-4 h-4 mr-2" />
          {{ loadingFundamentals ? '載入中...' : '載入台股基本面數據' }}
        </button>
      </div>
    </div>

    <!-- Fundamentals Dashboard (Optional) -->
    <div v-if="Object.keys(fundamentalsData).length > 0" class="glass-card border-l-4 border-brand-500">
      <div class="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
        <h3 class="text-lg font-bold text-[var(--text-primary)] flex items-center">
          <TrendingUp class="w-5 h-5 mr-2 text-brand-500" />
          台股基本面 (TWSE/TPEx)
        </h3>
        <button class="p-1 text-zinc-500 hover:text-zinc-900 dark:hover:text-white rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors" @click="fundamentalsData = {}">
          <X class="w-5 h-5" />
        </button>
      </div>
      <div class="p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="(data, sym) in fundamentalsData" :key="sym" class="bg-[var(--bg-main)]/50 rounded-xl p-4 border border-[var(--border-color)]/50 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <span class="font-bold text-[var(--text-primary)] text-sm tracking-tight">{{ sym }}</span>
            <span class="text-xs text-zinc-500 truncate max-w-[100px]">{{ data.name }}</span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-sm">
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">本益比</div>
              <div class="font-bold font-mono text-[var(--text-primary)]">{{ data.pe_ratio }}</div>
            </div>
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">殖利率</div>
              <div class="font-bold font-mono text-brand-600 dark:text-brand-400">
                {{ data.dividend_yield }}{{ data.dividend_yield !== 'N/A' ? '%' : '' }}
              </div>
            </div>
            <div>
              <div class="text-zinc-500 font-bold text-[10px] uppercase tracking-wider mb-1">淨值比</div>
              <div class="font-bold font-mono text-[var(--text-primary)]">{{ data.pb_ratio }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card rounded-2xl overflow-hidden">
      <!-- Debug info (can be removed later) -->
      <div v-if="trackingStore.items.length > 0 && trackingStore.items.some(i => !i.category)" class="px-4 py-3 bg-amber-50 dark:bg-amber-500/10 border-l-4 border-amber-500 text-sm flex items-center justify-between">
        <div>
          <span class="text-amber-700 dark:text-amber-300 font-bold">⚠️ 警告:</span>
          <span class="text-amber-600 dark:text-amber-200 ml-2">某些追蹤項目遺漏 category 欄位，請聯繫管理員更新資料庫</span>
        </div>
        <button class="ml-4 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded whitespace-nowrap" @click="trackingStore.fetchAll()">重新同步</button>
      </div>

      <div v-if="trackingStore.loading" class="flex justify-center items-center py-20">
        <Loader2 class="w-8 h-8 text-brand-500 animate-spin" />
      </div>
      <div v-else-if="!filteredItems.length" class="px-4 py-20 text-left text-zinc-500">
        <div class="text-4xl mb-4 opacity-50">📭</div>
        <div class="text-lg">此類別尚無追蹤項目</div>
      </div>
      <div v-else-if="!isMobile" class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="text-[10px] text-zinc-500 uppercase font-bold tracking-widest bg-[var(--bg-sidebar)]/50 border-b border-[var(--border-color)]">
            <tr class="text-xs text-zinc-500 dark:text-zinc-400 border-b border-[var(--border-color)]">
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">代碼</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">名稱</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">類別</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">目前價格</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">觸發模式</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">價格觸發條件</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">RSI 指標</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">通知方式</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">狀態</th>
              <th class="px-4 py-4 text-left font-medium whitespace-nowrap">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border-color)]">
            <tr v-for="item in filteredItems" :key="item.id" class="hover:bg-[var(--bg-main)]/50 transition-colors">
              <td class="px-4 py-4">
                <span class="font-bold text-sm tracking-tight text-brand-600 dark:text-brand-400">{{ item.symbol }}</span>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <button
                  @click="openQuoteUrl(item.symbol, item.category)"
                  class="text-sm text-[var(--text-primary)] font-medium underline decoration-dotted underline-offset-2 hover:text-brand-600 dark:hover:text-brand-400 transition-colors text-left"
                >{{ item.name }}</button>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <span :class="['px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider whitespace-nowrap', categoryBadgeInfo(item.category).class]">
                  {{ categoryBadgeInfo(item.category).label }}
                </span>
              </td>
              <td class="px-4 py-4 text-left">
                <span v-if="item.current_price" class="font-mono text-sm font-bold text-[var(--text-primary)]">{{ formatPrice(item.current_price) }}</span>
                <span v-else class="text-zinc-500">—</span>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <span :class="['px-2 py-0.5 text-[10px] font-bold rounded-full whitespace-nowrap border', triggerModeLabel(item.trigger_mode).class]">
                  {{ triggerModeLabel(item.trigger_mode).icon }} {{ triggerModeLabel(item.trigger_mode).label }}
                </span>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <div v-if="item.trigger_price" class="flex items-center space-x-2">
                  <span v-if="item.trigger_direction" :class="['flex items-center text-[11px] font-bold tracking-wider uppercase whitespace-nowrap', item.trigger_direction === 'above' ? 'text-rose-600 dark:text-rose-400' : 'text-brand-600 dark:text-brand-400']">
                    <TrendingUp v-if="item.trigger_direction === 'above'" class="w-3 h-3 mr-1" />
                    <TrendingDown v-else class="w-3 h-3 mr-1" />
                    {{ item.trigger_direction === 'above' ? '突破' : '跌破' }}
                  </span>
                  <span class="font-mono text-sm font-bold text-[var(--text-primary)] whitespace-nowrap">{{ formatPrice(item.trigger_price) }}</span>
                </div>
                <span v-else class="text-zinc-500 text-sm">—</span>
              </td>
              <td class="px-4 py-4">
                <div v-if="item.trigger_mode && item.trigger_mode !== 'price'" class="flex items-center space-x-2">
                  <button 
                    @click="showRSIModal = true; selectedRSIItem = item"
                    class="flex items-center gap-1.5 text-sm font-bold transition-all hover:opacity-70"
                    :class="item.current_rsi !== null && item.current_rsi !== undefined
                      ? item.current_rsi < (item.rsi_below || 30) 
                        ? 'text-red-600 dark:text-red-400'
                        : item.current_rsi > (item.rsi_above || 70)
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-blue-600 dark:text-blue-400'
                      : 'text-zinc-400'"
                    title="檢視 RSI 詳情"
                  >
                    <span class="text-base">📈</span>
                    <span v-if="item.current_rsi !== null && item.current_rsi !== undefined" class="font-mono">{{ item.current_rsi.toFixed(1) }}</span>
                    <span v-else class="text-zinc-400">--</span>
                  </button>
                </div>
                <span v-else class="text-zinc-500 text-sm">—</span>
              </td>
              <td class="px-4 py-4 whitespace-nowrap">
                <span class="inline-flex items-center gap-1 bg-white dark:bg-white text-zinc-950 dark:text-zinc-950 border border-zinc-200 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider whitespace-nowrap shadow-sm">
                  <Mail v-if="item.notify_channel === 'email' || item.notify_channel === 'both'" class="w-3 h-3" />
                  <MessageCircle v-if="item.notify_channel === 'line' || item.notify_channel === 'both'" class="w-3 h-3" />
                  {{ channelLabel(item.notify_channel) }}
                </span>
              </td>
              <td class="px-4 py-4 text-left">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" :checked="item.is_active" @change="toggleActive(item)" class="sr-only peer">
                  <div class="w-9 h-5 bg-zinc-300 peer-focus:outline-none rounded-full peer dark:bg-zinc-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-zinc-600 peer-checked:bg-brand-500"></div>
                </label>
              </td>
              <td class="px-4 py-4 text-left">
                <div class="flex items-center justify-start space-x-2">
                  <button class="p-1.5 text-zinc-400 hover:text-brand-600 dark:hover:text-brand-400 transition-colors rounded-md hover:bg-brand-500/10" @click="openEdit(item)" title="編輯">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button class="p-1.5 text-zinc-400 hover:text-amber-600 dark:hover:text-amber-400 transition-colors rounded-md hover:bg-amber-500/10" :disabled="testingId === item.id" @click="testAlert(item)" title="测試通知">
                    <Loader2 v-if="testingId === item.id" class="w-4 h-4 animate-spin" />
                    <Bell v-else class="w-4 h-4" />
                  </button>
                  <button class="p-1.5 text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors rounded-md hover:bg-rose-50/50 dark:hover:bg-rose-500/10" @click="confirmDelete(item)" title="刪除">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Card List -->
      <div v-else class="divide-y divide-[var(--border-color)]">
        <div v-for="item in filteredItems" :key="item.id" class="p-4 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <span class="font-extrabold text-brand-600 dark:text-brand-400 text-lg leading-tight">{{ item.symbol }}</span>
              <button @click="openQuoteUrl(item.symbol, item.category)" class="text-xs text-zinc-500 underline decoration-dotted underline-offset-2 text-left">
                {{ item.name }}
              </button>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span v-if="item.current_price" class="font-mono font-black text-[var(--text-primary)] text-lg">
                {{ formatPrice(item.current_price) }}
              </span>
              <span :class="['px-2 py-0.5 text-[9px] font-black rounded uppercase tracking-tighter', categoryBadgeInfo(item.category).class]">
                {{ categoryBadgeInfo(item.category).label }}
              </span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 text-[11px]">
            <div class="bg-[var(--bg-main)]/40 p-2 rounded-lg border border-[var(--border-color)]/30">
              <div class="text-zinc-500 font-bold mb-1 uppercase tracking-widest text-[9px]">觸發模式</div>
              <div class="flex items-center gap-1 font-bold text-[var(--text-primary)]">
                {{ triggerModeLabel(item.trigger_mode).icon }} {{ triggerModeLabel(item.trigger_mode).label }}
              </div>
            </div>
            <div class="bg-[var(--bg-main)]/40 p-2 rounded-lg border border-[var(--border-color)]/30">
              <div class="text-zinc-500 font-bold mb-1 uppercase tracking-widest text-[9px]">觸發條件</div>
              <div v-if="item.trigger_price" class="flex items-center gap-1 font-bold text-[var(--text-primary)]">
                 <TrendingUp v-if="item.trigger_direction === 'above'" class="w-3 h-3 text-rose-500" />
                 <TrendingDown v-else class="w-3 h-3 text-brand-500" />
                 {{ formatPrice(item.trigger_price) }}
              </div>
              <div v-else class="text-zinc-400">尚未設定</div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-1">
            <div class="flex items-center gap-3">
              <button 
                v-if="item.trigger_mode !== 'price'"
                @click="showRSIModal = true; selectedRSIItem = item"
                class="flex items-center gap-1 px-2 py-1 bg-brand-500/10 rounded-lg"
              >
                <span class="text-sm">📈</span>
                <span class="font-mono font-bold text-brand-600 dark:text-brand-400">
                  {{ item.current_rsi ? item.current_rsi.toFixed(1) : '--' }}
                </span>
              </button>
              <span class="flex items-center gap-1 text-[10px] font-bold text-zinc-500">
                <Mail v-if="item.notify_channel === 'email' || item.notify_channel === 'both'" class="w-3 h-3" />
                <MessageCircle v-if="item.notify_channel === 'line' || item.notify_channel === 'both'" class="w-3 h-3" />
                {{ channelLabel(item.notify_channel) }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <label class="relative inline-flex items-center cursor-pointer scale-90">
                <input type="checkbox" :checked="item.is_active" @change="toggleActive(item)" class="sr-only peer">
                <div class="w-9 h-5 bg-zinc-300 peer-focus:outline-none rounded-full peer dark:bg-zinc-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-zinc-600 peer-checked:bg-brand-500"></div>
              </label>
              <button @click="openEdit(item)" class="p-2 text-zinc-400 hover:text-brand-500">
                <Edit2 class="w-4 h-4" />
              </button>
              <button @click="confirmDelete(item)" class="p-2 text-zinc-400 hover:text-rose-500">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Footer -->
      <div v-if="trackingStore.items.length > 0" class="px-4 py-3 bg-[var(--bg-sidebar)]/50 border-t border-[var(--border-color)] text-sm text-zinc-500">
        <span>共計 <span class="font-bold text-[var(--text-primary)]">{{ trackingStore.items.length }}</span> 個追蹤項目</span>
        <span class="mx-2">•</span>
        <span>篩選結果: <span class="font-bold text-[var(--text-primary)]">{{ filteredItems.length }}</span> 個</span>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
        <div class="fixed inset-0 bg-zinc-900/60 backdrop-blur-sm transition-opacity" @click="closeModal"></div>
        
        <div class="relative bg-[var(--bg-main)] rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-md overflow-hidden ring-2 ring-brand-500/20 h-[90vh] sm:h-auto">
          <div class="px-6 py-4 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-sidebar)]/50">
            <h3 class="text-lg font-bold tracking-tight text-[var(--text-primary)] flex items-center">
              <PlusCircle v-if="!editItem" class="w-5 h-5 mr-2 text-brand-500" />
              <Edit2 v-else class="w-5 h-5 mr-2 text-brand-500" />
              {{ editItem ? '修改追蹤' : '新增追蹤指數' }}
            </h3>
            <button class="text-zinc-400 hover:text-zinc-500 dark:hover:text-zinc-300 transition-colors" @click="closeModal">
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="p-6 space-y-4 h-[calc(90vh-8rem)] sm:max-h-[70vh] overflow-y-auto pb-safe">
            <div v-if="modalError" class="p-3 text-sm text-rose-600 bg-rose-50 dark:bg-rose-500/10 dark:text-rose-400 rounded-lg flex items-start">
              <AlertCircle class="w-4 h-4 mr-2 mt-0.5 shrink-0" />
              {{ modalError }}
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">類別</label>
              <select v-model="form.category" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3" @change="symbolSearch = ''; form.symbol = ''; form.name = ''; currentPrice = null">
                <option value="vix">VIX (波動指數)</option>
                <option value="oil">石油期貨</option>
                <option value="us_etf">美國 ETF</option>
                <option value="tw_etf">台灣 ETF</option>
                <option value="funds">共同基金</option>
                <option value="index">大盤指數</option>
                <option value="crypto">加密貨幣</option>
                <option value="exchange">匯率</option>
              </select>
            </div>
            
            <div v-if="currentPrice !== null || fetchingPrice" class="flex items-center p-3 bg-[var(--bg-sidebar)] border border-[var(--border-color)] rounded-lg">
              <span class="text-sm font-medium text-zinc-500 dark:text-zinc-400 mr-2">目前價格: </span>
              <Loader2 v-if="fetchingPrice" class="w-4 h-4 text-brand-500 animate-spin" />
              <span v-else class="text-lg font-bold tracking-tight text-[var(--text-primary)]">{{ formatPrice(currentPrice) }}</span>
            </div>

            <div class="relative">
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">代碼 / Symbol</label>
              <div class="relative input-with-dropdown">
                <input v-model="symbolSearch" type="text" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3" 
                  placeholder="輸入或選擇代碼..." :disabled="!!editItem"
                  @input="onSymbolInput" 
                  @focus="showSymbolDropdown = true"
                  @compositionstart="isComposingSymbol = true"
                  @compositionend="handleCompositionEnd"
                  @keydown.enter.prevent="handleSymbolInputEnter" />
                
                <div v-if="showSymbolDropdown && filteredSymbols.length" class="absolute z-10 w-full mt-1 bg-[var(--bg-main)] border border-[var(--border-color)] rounded-lg shadow-lg max-h-60 overflow-auto">
                  <div v-for="s in filteredSymbols" :key="s.symbol" class="px-4 py-2 hover:bg-[var(--bg-sidebar)] cursor-pointer border-b border-[var(--border-color)] last:border-0" @click="selectSymbol(s)">
                    <div class="font-bold text-[var(--text-primary)]">{{ s.symbol }}</div>
                    <div class="text-xs font-medium text-zinc-500 dark:text-zinc-400 truncate">{{ s.name }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">名稱</label>
              <input v-model="form.name" type="text" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3" placeholder="例: 元大台灣50" />
            </div>

            <!-- Trigger Mode Selector -->
            <TriggerModeSelector v-model="form.trigger_mode" />

            <!-- RSI Parameters Form -->
            <RSIParametersForm 
              :show="form.trigger_mode !== 'price'"
              :period="form.rsi_period"
              :rsi-below="form.rsi_below"
              :rsi-above="form.rsi_above"
              @update:period="form.rsi_period = $event"
              @update:rsiBelow="form.rsi_below = $event"
              @update:rsiAbove="form.rsi_above = $event"
            />

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">觸發方向</label>
                <select v-model="form.trigger_direction" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3">
                  <option value="above" class="text-rose-600 font-bold">↑ 突破 (漲到)</option>
                  <option value="below" class="text-brand-600 font-bold">↓ 跌破 (跌到)</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">觸發價格</label>
                <input v-model.number="form.trigger_price" type="number" step="0.01" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3" placeholder="選填" />
              </div>
            </div>

            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">通知方式</label>
              <select v-model="form.notify_channel" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3">
                <option value="email">📧 Email</option>
                <option value="line">💬 LINE</option>
                <option value="both">📧💬 Email + LINE</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-bold text-[var(--text-primary)] mb-1">備註 (選填)</label>
              <input v-model="form.notes" type="text" class="w-full h-10 bg-[var(--input-bg)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block px-3" placeholder="備注..." />
            </div>
          </div>
          
          <div class="px-6 py-4 border-t border-[var(--border-color)] bg-[var(--bg-sidebar)] flex justify-end space-x-3">
            <button class="px-4 py-2 text-sm font-bold text-zinc-600 dark:text-zinc-400 hover:text-[var(--text-primary)] hover:bg-[var(--input-bg)] rounded-lg transition-colors border border-transparent" @click="closeModal">取消</button>
            <button class="flex items-center justify-center px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-bold rounded-lg transition-all shadow-lg shadow-brand-500/20" @click="handleSave" :disabled="saving">
              <Loader2 v-if="saving" class="w-4 h-4 mr-2 animate-spin" />
              {{ saving ? '儲存中...' : (editItem ? '更新' : '新增') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- RSI Monitoring Modal -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0">
      <div v-if="showRSIModal" class="fixed inset-0 z-50 bg-black/50 dark:bg-black/70 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4">
        <div class="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-t-2xl sm:rounded-2xl shadow-2xl max-w-2xl w-full h-[95vh] sm:h-auto max-h-[95vh] sm:max-h-[90vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-sidebar)] flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span class="text-2xl">📈</span>
              <div>
                <h3 class="text-lg font-bold text-[var(--text-primary)]">RSI 監控詳情</h3>
                <p class="text-xs text-zinc-500 mt-1">{{ selectedRSIItem?.symbol }} - {{ selectedRSIItem?.name }}</p>
              </div>
            </div>
            <button @click="closeRSIModal" class="p-1 text-zinc-500 hover:text-[var(--text-primary)] rounded-lg hover:bg-[var(--input-bg)] transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Content -->
          <div class="flex-1 px-6 py-6 overflow-y-auto">
            <RSIMonitoringDashboard :item="selectedRSIItem" />
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-[var(--border-color)] bg-[var(--bg-sidebar)] flex justify-between items-center gap-3">
            <button class="px-4 py-2 text-sm font-bold text-zinc-600 dark:text-zinc-400 hover:text-[var(--text-primary)] hover:bg-[var(--input-bg)] rounded-lg transition-colors border border-transparent" @click="closeRSIModal">關閉</button>
            <div class="flex gap-2">
              <button class="flex items-center justify-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-bold rounded-lg transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed" @click="calculateRSINow(selectedRSIItem)" v-if="selectedRSIItem" :disabled="calculatingRSI">
                <BarChart2 v-if="!calculatingRSI" class="w-4 h-4 mr-2" />
                <Loader2 v-else class="w-4 h-4 mr-2 animate-spin" />
                {{ calculatingRSI ? '計算中...' : '計算RSI' }}
              </button>
              <button class="flex items-center justify-center px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-bold rounded-lg transition-all shadow-lg shadow-amber-500/20" @click="testAlert(selectedRSIItem)" v-if="selectedRSIItem">
                <Bell class="w-4 h-4 mr-2" />
                測試通知
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Floating Action Button (FAB) for Mobile -->
    <div v-if="isMobile" class="fixed bottom-20 right-4 flex flex-col gap-3 z-40 safe-area-bottom">
      <button 
        class="w-12 h-12 bg-[var(--bg-main)] text-zinc-600 dark:text-zinc-400 rounded-full shadow-xl border border-[var(--border-color)] flex items-center justify-center transition-all active:scale-90"
        @click="trackingStore.fetchAll()"
      >
        <Loader2 class="w-6 h-6" />
      </button>
      <button 
        class="w-14 h-14 bg-brand-500 text-white rounded-full shadow-2xl flex items-center justify-center transition-all active:scale-95 shadow-brand-500/40"
        @click="showAddModal = true"
      >
        <Plus class="w-8 h-8" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import axios from 'axios'
import {
  Plus, Loader2, BarChart2, TrendingUp, TrendingDown, X, ArrowUpRight, ArrowDownRight,
  Mail, MessageCircle, Edit2, Bell, Trash2, PlusCircle, AlertCircle
} from 'lucide-vue-next'
import { useAuthStore, API_BASE_URL as API_BASE } from '../stores/auth'
import { useTrackingStore } from '../stores/tracking'
import { useBreakpoint } from '../composables/useBreakpoint'
import TriggerModeSelector from '../components/TriggerModeSelector.vue'
import RSIParametersForm from '../components/RSIParametersForm.vue'
import RSIMonitoringDashboard from '../components/RSIMonitoringDashboard.vue'

const auth = useAuthStore()
const trackingStore = useTrackingStore()
const { isMobile, isTablet, isDesktop } = useBreakpoint()
const showAddModal = ref(false)
const editItem = ref(null)
const saving = ref(false)
const modalError = ref('')
const activeCategory = ref('all')
const showRSIModal = ref(false)
const selectedRSIItem = ref(null)
const calculatingRSI = ref(false)

const fundamentalsData = ref({})
const loadingFundamentals = ref(false)
const symbolCatalog = ref({})

const categories = [
  { value: 'all', label: '全部' },
  { value: 'vix', label: 'VIX' },
  { value: 'oil', label: '石油' },
  { value: 'us_etf', label: '美國ETF' },
  { value: 'tw_etf', label: '台灣ETF' },
  { value: 'funds', label: '共同基金' },
  { value: 'index', label: '指數' },
  { value: 'exchange', label: '匯率' },
]

const form = reactive({
  symbol: '', name: '', category: 'us_etf',
  trigger_direction: 'below', trigger_price: null,
  trigger_mode: 'price', rsi_period: 14, rsi_below: 30, rsi_above: 70,
  notify_channel: 'email', notes: ''
})

const availableSymbols = ref({ tw_etf: [], us_etf: [], index: [], funds: [] })
const symbolSearch = ref('')
const showSymbolDropdown = ref(false)
const currentPrice = ref(null)
const fetchingPrice = ref(false)
const isComposingSymbol = ref(false)  // 中文輸入法狀態
let fetchPriceTimeout = null  // 防抖計時器
let justCompletedCompositionSymbol = false  // 標記剛完成 composition

// Close dropdown when clicking outside
if (typeof window !== 'undefined') {
  window.addEventListener('click', (e) => {
    if (!e.target.closest('.input-with-dropdown')) {
      showSymbolDropdown.value = false
    }
  })
}

const allSymbols = computed(() => {
  const list = []
  const cat = form.category
  if (cat === 'tw_etf') {
    availableSymbols.value.tw_etf.forEach(s => list.push({ ...s, type: 'tw_etf' }))
  } else if (cat === 'us_etf') {
    availableSymbols.value.us_etf.forEach(s => list.push({ ...s, type: 'us_etf' }))
  } else if (cat === 'funds') {
    availableSymbols.value.funds.forEach(s => list.push({ ...s, type: 'funds' }))
  } else if (['index', 'vix', 'oil', 'crypto', 'exchange'].includes(cat)) {
    // Filter index list by category
    const indices = availableSymbols.value.index || []
    indices.filter(s => s.category === cat).forEach(s => list.push({ ...s, type: 'index' }))
  } else {
    // Fallback or other
    availableSymbols.value.us_etf.forEach(s => list.push({ ...s, type: 'us_etf' }))
  }
  return list
})

const filteredSymbols = computed(() => {
  const q = symbolSearch.value.toLowerCase()
  if (!q) return allSymbols.value.slice(0, 10)
  return allSymbols.value.filter(s => 
    s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  ).slice(0, 15)
})

async function fetchAvailableSymbols() {
  try {
    console.log('[TrackingView] Fetching available symbols...')
    const res = await axios.get(`${API_BASE}/api/market/symbols`, { headers: auth.headers })
    console.log('[TrackingView] Available symbols received:', {
      tw_etf: res.data.tw_etf?.length || 0,
      us_etf: res.data.us_etf?.length || 0,
      funds: res.data.funds?.length || 0,
      index: res.data.index?.length || 0
    })
    // Ensure funds array always exists, even if API doesn't return it
    availableSymbols.value = {
      ...res.data,
      funds: res.data.funds || []
    }
  } catch (e) {
    console.error('[TrackingView] Failed to fetch symbols:', e.message, e.response?.status)
    // Set empty fallback
    availableSymbols.value = { tw_etf: [], us_etf: [], index: [], funds: [] }
  }
}

async function fetchPrice(symbol, category) {
  if (!symbol) return
  fetchingPrice.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/market/quotes?symbols=${symbol}`, { headers: auth.headers })
    if (res.data && res.data[0]) {
      currentPrice.value = res.data[0].price
      console.log('[TrackingView] 成功獲取價格:', { symbol, price: currentPrice.value })
    }
  } catch (e) {
    console.error('[TrackingView] 獲取價格失敗:', {
      symbol,
      error: e.message,
      status: e.response?.status,
      timestamp: new Date().toISOString()
    })
    currentPrice.value = null
  } finally {
    fetchingPrice.value = false
  }
}

function selectSymbol(s) {
  form.symbol = s.symbol
  form.name = s.name
  symbolSearch.value = s.symbol
  showSymbolDropdown.value = false
  // 清除之前的防抖計時器
  if (fetchPriceTimeout) clearTimeout(fetchPriceTimeout)
  fetchPrice(s.symbol, form.category).catch(err => {
    console.error('[TrackingView] 選擇符號後獲取價格失敗:', err)
    // 不要中斷用戶流程
  })
}

function handleCompositionEnd(e) {
  console.log('[TrackingView] compositionend 事件', { timestamp: new Date().getTime() })
  isComposingSymbol.value = false
  
  // 設置標記：剛剛完成 composition，接下來的 @input 應該跳過 fetchPrice（短時間內）
  justCompletedCompositionSymbol = true
  
  // 300ms 後重置標記
  setTimeout(() => {
    justCompletedCompositionSymbol = false
    console.log('[TrackingView] 重置 justCompletedCompositionSymbol 標記')
  }, 300)
}

function handleSymbolInputEnter(e) {
  console.log('[TrackingView] Enter 鍵按下', {
    isComposing: isComposingSymbol.value,
    query: symbolSearch.value,
    timestamp: new Date().toISOString()
  })
  
  // 如果正在進行中文輸入組合，忽略 Enter 鍵
  if (isComposingSymbol.value) {
    console.log('[TrackingView] 正在進行中文輸入組合，忽略 Enter 鍵')
    return
  }
  
  // 如果有相符的符號，直接選擇
  const match = allSymbols.value.find(s => s.symbol.toLowerCase() === symbolSearch.value.toLowerCase())
  if (match) {
    console.log('[TrackingView] 直接選擇符號:', match.symbol)
    selectSymbol(match)
  } else {
    console.log('[TrackingView] 未找到相符的符號')
  }
}

function onSymbolInput() {
  // 如果正在進行中文輸入組合，忽略此事件
  if (isComposingSymbol.value) {
    console.log('[TrackingView] 正在進行中文輸入組合，忽略 input 事件')
    return
  }
  
  // 如果剛剛完成 composition，也忽略此 input（避免立即執行 fetchPrice）
  if (justCompletedCompositionSymbol) {
    console.log('[TrackingView] 剛剛完成 composition，跳過 fetchPrice 執行')
    form.symbol = symbolSearch.value
    showSymbolDropdown.value = true
    return
  }

  form.symbol = symbolSearch.value
  showSymbolDropdown.value = true
  
  // 清除之前的防抖計時器
  if (fetchPriceTimeout) clearTimeout(fetchPriceTimeout)
  
  // 防抖：延遲 300ms 後才執行 fetchPrice
  fetchPriceTimeout = setTimeout(() => {
    // Try to find if it matches exactly
    const match = allSymbols.value.find(s => s.symbol.toLowerCase() === symbolSearch.value.toLowerCase())
    if (match) {
      form.name = match.name
      fetchPrice(match.symbol, form.category).catch(err => {
        console.error('[TrackingView] 獲取價格失敗:', err)
        // 不要中斷用戶流程，只是記錄錯誤
      })
    }
  }, 300)
}


const filteredItems = computed(() => {
  const items = trackingStore.items.map(item => {
    // Ensure category field exists; fallback to 'us_etf' if missing
    if (!item.category) {
      return {
        ...item,
        category: inferCategory(item.symbol)
      }
    }
    return item
  })
  
  return activeCategory.value === 'all'
    ? items
    : items.filter(i => i.category === activeCategory.value)
})

function inferCategory(symbol) {
  // Infer category from symbol if category field is missing
  if (!symbol) return 'us_etf'
  const upper = symbol.toUpperCase()
  if (upper === '^VIX') return 'vix'
  if (upper === 'CL=F' || upper === 'BZ=F') return 'oil'
  if (upper === 'TWSE' || upper === 'TPEX') return 'index'
  if (upper.endsWith('.TW')) return 'tw_etf'
  if (upper.includes('BTC') || upper.includes('ETH')) return 'crypto'
  if (upper === 'EURUSD=X' || upper === 'JPYUSD=X') return 'exchange'
  return 'us_etf' // Default
}

function categoryBadgeInfo(cat) {
  const map = {
    vix: { label: 'VIX', class: 'bg-rose-500 text-white border border-rose-600' },
    oil: { label: '石油', class: 'bg-amber-500 text-white border border-amber-600' },
    us_etf: { label: '美股', class: 'bg-blue-500 text-white border border-blue-600' },
    tw_etf: { label: '台股', class: 'bg-purple-500 text-white border border-purple-600' },
    funds: { label: '基金', class: 'bg-green-500 text-white border border-green-600' },
    index: { label: '大盤', class: 'bg-violet-500 text-white border border-violet-600' },
    crypto: { label: '加密', class: 'bg-brand-500 text-white border border-brand-600' },
    exchange: { label: '匯率', class: 'bg-cyan-500 text-white border border-cyan-600' }
  }
  return map[cat] || { label: cat.toUpperCase(), class: 'bg-zinc-500 text-white border border-zinc-600' }
}

function channelLabel(ch) {
  const map = { email: 'Email', line: 'LINE', both: 'Email + LINE' }
  return map[ch] || ch
}

function triggerModeLabel(mode) {
  const map = {
    price:  { label: '價格',     icon: '💰', class: 'bg-yellow-50 text-yellow-700 border-yellow-300 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/30' },
    rsi:    { label: 'RSI',      icon: '📈', class: 'bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/30' },
    both:   { label: '價格及RSI', icon: '⚡', class: 'bg-purple-50 text-purple-700 border-purple-300 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/30' },
    either: { label: '價格或RSI', icon: '🔀', class: 'bg-teal-50 text-teal-700 border-teal-300 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/30' }
  }
  return map[mode] || map['price']
}

async function loadSymbolCatalog() {
  try {
    const res = await axios.get(`${API_BASE}/api/market/symbol-catalog`)
    symbolCatalog.value = res.data
  } catch (e) {
    console.error('[TrackingView] Failed to load symbol catalog:', e)
  }
}

function openQuoteUrl(symbol, category = null) {
  if (!symbol) return
  const upper = symbol.toUpperCase()

  // 優先從後端 SSOT 取得正確 URL（處理 WTX&、BZ=F、^VIX 等特殊符號）
  const config = symbolCatalog.value[upper]
  if (config && config.url_path) {
    window.open(`https://${config.domain}/${config.url_path}`, '_blank', 'noopener,noreferrer')
    return
  }

  // Fallback
  const isNumericTwCode = /^\d{4,6}$/.test(upper)
  if (category === 'tw_etf' || isNumericTwCode) {
    let finalSymbol = upper
    if (!upper.includes('.')) finalSymbol = upper + '.TW'
    window.open(`https://tw.stock.yahoo.com/quote/${finalSymbol}`, '_blank', 'noopener,noreferrer')
  } else {
    window.open(`https://finance.yahoo.com/quote/${upper}`, '_blank', 'noopener,noreferrer')
  }
}

function formatPrice(price) {
  if (price === null || price === undefined) return '—'
  return Number(price).toLocaleString('zh-TW', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function diagnosePageState() {
  const diagnosis = {
    timestamp: new Date().toISOString(),
    authToken: auth.token ? '✓ Present' : '✗ Missing',
    userId: auth.userId ? '✓ ' + auth.userId : '✗ Missing',
    isLoggedIn: auth.isLoggedIn,
    trackingStoreItems: trackingStore.items.length,
    trackingStoreLoading: trackingStore.loading,
    filteredItems: filteredItems.value.length,
    activeCategory: activeCategory.value,
    categoryCounts: categories.map(cat => ({
      category: cat.label,
      count: cat.value === 'all' ? trackingStore.items.length : trackingStore.items.filter(i => i.category === cat.value).length
    }))
  }
  console.log('[Diagnosis]', JSON.stringify(diagnosis, null, 2))
  return diagnosis
}

function openEdit(item) {
  editItem.value = item
  symbolSearch.value = item.symbol
  currentPrice.value = item.current_price
  Object.assign(form, {
    symbol: item.symbol, name: item.name, category: item.category,
    trigger_direction: item.trigger_direction || 'below',
    trigger_price: item.trigger_price, 
    trigger_mode: item.trigger_mode || 'price',
    rsi_period: item.rsi_period || 14,
    rsi_below: item.rsi_below || 30,
    rsi_above: item.rsi_above || 70,
    notify_channel: item.notify_channel,
    notes: item.notes || ''
  })
  showAddModal.value = true
}

function closeModal() {
  showAddModal.value = false
  editItem.value = null
  modalError.value = ''
  symbolSearch.value = ''
  currentPrice.value = null
  Object.assign(form, { 
    symbol: '', name: '', category: 'us_etf', 
    trigger_direction: 'below', trigger_price: null, 
    trigger_mode: 'price', rsi_period: 14, rsi_below: 30, rsi_above: 70,
    notify_channel: 'email', notes: '' 
  })
}

async function handleSave() {
  if (!form.symbol || !form.name) { modalError.value = '請填寫代碼和名稱'; return }
  saving.value = true
  modalError.value = ''
  try {
    const data = { ...form }
    
    console.log('[TrackingView.handleSave] 準備提交的數據:', {
      symbol: data.symbol,
      name: data.name,
      category: data.category,
      trigger_mode: data.trigger_mode,
      notify_channel: data.notify_channel,
      notes: data.notes
    })
    
    // 根據觸發模式決定要保留/刪除哪些參數
    if (form.trigger_mode === 'price') {
      // Price 模式：只需要 trigger_price，刪除 RSI 參數
      console.log('[TrackingView.handleSave] Price 模式: 保留 trigger_price，刪除 RSI 參數')
      delete data.rsi_period
      delete data.rsi_below
      delete data.rsi_above
    } else if (form.trigger_mode === 'rsi') {
      // RSI 模式：只需要 RSI 參數，刪除 price 相關參數
      console.log('[TrackingView.handleSave] RSI 模式: 保留 RSI 參數，刪除 trigger_price')
      delete data.trigger_price
      delete data.trigger_direction
    } else if (form.trigger_mode === 'both') {
      // 'both' 模式：保留所有參數（同時滿足 price 和 RSI 條件）
      console.log('[TrackingView.handleSave] 價格及RSI 模式: 保留所有參數(AND邏輯)')
    } else if (form.trigger_mode === 'either') {
      // 'either' 模式：保留所有參數（滿足 price 或 RSI 任一條件）
      console.log('[TrackingView.handleSave] 價格或RSI 模式: 保留所有參數(OR邏輯)')
    }
    
    console.log('[TrackingView.handleSave] 最終提交數據:', data)
    
    if (editItem.value) {
      console.log('[TrackingView.handleSave] 更新模式, ID:', editItem.value.id)
      await trackingStore.update(editItem.value.id, data)
    } else {
      console.log('[TrackingView.handleSave] 新增模式')
      await trackingStore.create(data)
    }
    
    console.log('[TrackingView.handleSave] 成功!')
    closeModal()
  } catch (e) {
    console.error('[TrackingView.handleSave] 錯誤:', {
      message: e.message,
      status: e.response?.status,
      detail: e.response?.data?.detail,
      data: e.response?.data
    })
    modalError.value = e.response?.data?.detail || e.message || '保存失敗'
  } finally {
    saving.value = false
  }
}

async function toggleActive(item) {
  await trackingStore.update(item.id, { is_active: !item.is_active })
}

async function confirmDelete(item) {
  if (confirm(`確定刪除追蹤「${item.name}」?`)) {
    await trackingStore.remove(item.id)
  }
}

const testingId = ref(null)

async function testAlert(item) {
  testingId.value = item.id
  try {
    const res = await axios.post(
      `${API_BASE}/api/tracking/${item.id}/test-alert`,
      {},
      { headers: auth.headers }
    )
    const r = res.data.results
    const parts = []
    if (r.email) parts.push(`Email: ${r.email}`)
    if (r.line) parts.push(`LINE: ${r.line}`)
    alert(`测試通知已發送！\n${parts.join('\n')}`)
  } catch (e) {
    alert('發送失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    testingId.value = null
  }
}

async function closeRSIModal() {
  showRSIModal.value = false
  // 關閉 modal 後自動重新整理追蹤清單，確保主畫面 RSI 欄位即時更新
  await trackingStore.fetchAll()
  // 同步更新 selectedRSIItem，下次開啟時顯示最新數據
  if (selectedRSIItem.value) {
    const updated = trackingStore.items.find(i => i.id === selectedRSIItem.value.id)
    if (updated) selectedRSIItem.value = updated
  }
}

async function calculateRSINow(item) {
  calculatingRSI.value = true
  try {
    const res = await axios.post(
      `${API_BASE}/api/tracking/${item.id}/calculate-rsi`,
      {},
      { headers: auth.headers }
    )
    alert(`✅ RSI 計算完成！\n目前 RSI: ${res.data.current_rsi?.toFixed(2) || 'N/A'}`)
    // 刷新 selectedRSIItem 以顯示最新的 RSI 值
    if (selectedRSIItem.value && selectedRSIItem.value.id === item.id) {
      selectedRSIItem.value = res.data
    }
  } catch (e) {
    alert('計算失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    calculatingRSI.value = false
  }
}

async function fetchFundamentals() {
  const twSymbols = trackingStore.items
    .filter(i => i.category === 'tw_etf' || i.symbol.endsWith('.TW') || i.symbol.endsWith('.TWO'))
    .map(i => i.symbol)
    
  if (twSymbols.length === 0) {
    alert("您的追蹤清單中目前沒有台灣ETF或台股代碼 (需要設定類別為台股ETF或是附帶.TW)。")
    return
  }

  loadingFundamentals.value = true
  try {
    const params = new URLSearchParams()
    twSymbols.forEach(s => params.append('symbols', s))
    const res = await axios.get(`${API_BASE}/api/fundamentals/tw?${params.toString()}`, { headers: auth.headers })
    fundamentalsData.value = res.data
  } catch (e) {
    alert('載入基本面失敗: ' + (e.response?.data?.detail || e.message))
  } finally {
    loadingFundamentals.value = false
  }
}

onMounted(async () => {
  try {
    console.log('[TrackingView] Mounted, loading tracking items...')
    console.log('[TrackingView] Current auth state:', {
      isLoggedIn: auth.isLoggedIn,
      userId: auth.userId,
      hasToken: !!auth.token
    })
    await trackingStore.fetchAll()
    console.log('[TrackingView] ✓ Loaded tracking items:', trackingStore.items.length, 'items')
    
    await trackingStore.fetchAlertLogs()
    console.log('[TrackingView] ✓ Loaded alert logs:', trackingStore.alertLogs.length, 'logs')
    
    diagnosePageState()
  } catch (e) {
    console.error('[TrackingView] Failed to fetch tracking items on first attempt:', e)
    // Retry after 1 second
    setTimeout(async () => {
      try {
        console.log('[TrackingView] Retrying fetchAll...')
        await trackingStore.fetchAll()
        console.log('[TrackingView] ✓ Retry successful:', trackingStore.items.length, 'items')
        
        try {
          await trackingStore.fetchAlertLogs()
          console.log('[TrackingView] ✓ Alert logs loaded on retry:', trackingStore.alertLogs.length, 'logs')
        } catch (alertError) {
          console.error('[TrackingView] Alert logs fetch failed on retry:', alertError)
        }
        
        diagnosePageState()
      } catch (retryError) {
        console.error('[TrackingView] Retry failed:', retryError)
        diagnosePageState()
      }
    }, 1000)
  }
  
  try {
    await fetchAvailableSymbols()
    console.log('[TrackingView] ✓ Available symbols loaded')
  } catch (e) {
    console.error('[TrackingView] Failed to fetch available symbols:', e)
  }

  try {
    await loadSymbolCatalog()
    console.log('[TrackingView] ✓ Symbol catalog loaded')
  } catch (e) {
    console.error('[TrackingView] Failed to load symbol catalog:', e)
  }
})
</script>

<style scoped>
/* Removed old scoped styling; using global Tailwind CSS classes now */
</style>
