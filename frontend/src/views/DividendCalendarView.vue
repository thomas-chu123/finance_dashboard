<template>
  <div class="p-4 lg:p-6 space-y-6">
    <!-- 頁首 -->
    <div>
      <h1 class="text-2xl font-bold text-[var(--text-primary)]">除權息日曆</h1>
      <p class="text-sm text-zinc-500 mt-1">
        台股除權息行事曆，追蹤中的標的將於除息前 7 天與前 1 天自動發送提醒。
      </p>
    </div>

    <div class="flex flex-col xl:flex-row gap-6">
      <!-- 左欄：月曆 -->
      <div class="flex-1 min-w-0">
        <DividendCalendar />
      </div>

      <!-- 右欄：即將除息清單 -->
      <div class="xl:w-80 flex-shrink-0 space-y-4">
        <!-- 即將除息卡片 -->
        <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] overflow-hidden">
          <div class="px-4 py-3 border-b border-[var(--border-color)] flex items-center justify-between">
            <h3 class="font-semibold text-sm text-[var(--text-primary)] flex items-center gap-2">
              <CalendarClock :size="15" class="text-brand-500" />
              30 天內除權息
            </h3>
            <span class="text-xs text-zinc-500 dark:text-zinc-400 border border-[var(--border-color)] px-2 py-0.5 rounded-full">
              {{ upcomingTracked.length }} 支追蹤中
            </span>
          </div>

          <!-- 載入中 -->
          <div v-if="upcomingLoading" class="p-6 flex justify-center">
            <div class="animate-spin w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full"></div>
          </div>

          <!-- 空狀態 -->
          <div v-else-if="!store.upcomingItems.length" class="p-6 text-center text-zinc-400 text-sm">
            未來 30 天內無除權息事件
          </div>

          <!-- 資料列表 -->
          <div v-else class="divide-y divide-[var(--border-color)] max-h-[420px] overflow-y-auto">
            <!-- 追蹤中的優先顯示 -->
            <template v-if="upcomingTracked.length">
              <div class="px-3 py-1.5 border-b border-[var(--border-color)]">
                <span class="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
                  追蹤中（將收到通知）
                </span>
              </div>
              <div
                v-for="item in upcomingTracked"
                :key="`t-${item.code}-${item.ex_date}`"
                class="px-4 py-2.5 flex items-center justify-between gap-2 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
              >
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs font-bold text-[var(--text-primary)]">{{ item.code }}</span>
                    <span
                      class="text-[10px] px-1 py-0.5 rounded font-medium"
                      :class="getTypePillClass(item.ex_type)"
                    >{{ item.ex_type }}</span>
                    <Bell :size="11" class="text-emerald-500 flex-shrink-0" />
                  </div>
                  <div class="text-xs text-zinc-500 truncate mt-0.5">{{ item.name }}</div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-xs font-medium text-[var(--text-primary)]">{{ formatDate(item.ex_date) }}</div>
                  <div v-if="item.cash_dividend" class="text-xs text-emerald-600 dark:text-emerald-400">
                    ${{ Number(item.cash_dividend).toFixed(2) }}
                  </div>
                  <div class="text-[10px] text-zinc-400">{{ daysUntil(item.ex_date) }} 天後</div>
                </div>
              </div>
            </template>

            <!-- 未追蹤的其他除息 -->
            <template v-if="upcomingUntracked.length">
              <div class="px-3 py-1.5 border-b border-[var(--border-color)]">
                <span class="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide">其他</span>
              </div>
              <div
                v-for="item in upcomingUntracked.slice(0, 20)"
                :key="`u-${item.code}-${item.ex_date}`"
                class="px-4 py-2 flex items-center justify-between gap-2 hover:bg-brand-500/5 dark:hover:bg-brand-500/10 transition-colors"
              >
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs font-semibold text-[var(--text-primary)]">{{ item.code }}</span>
                    <span
                      class="text-[10px] px-1 py-0.5 rounded font-medium"
                      :class="getTypePillClass(item.ex_type)"
                    >{{ item.ex_type }}</span>
                  </div>
                  <div class="text-xs text-zinc-500 truncate mt-0.5">{{ item.name }}</div>
                </div>
                <div class="text-right flex-shrink-0">
                  <div class="text-xs text-zinc-500">{{ formatDate(item.ex_date) }}</div>
                  <div v-if="item.cash_dividend" class="text-xs text-zinc-400">
                    ${{ Number(item.cash_dividend).toFixed(2) }}
                  </div>
                </div>
              </div>
              <div v-if="upcomingUntracked.length > 20" class="px-4 py-2 text-center text-xs text-zinc-400">
                還有 {{ upcomingUntracked.length - 20 }} 支...
              </div>
            </template>
          </div>
        </div>

        <!-- 通知說明卡片 -->
        <div class="border border-[var(--border-color)] rounded-xl px-4 py-3.5">
          <div class="flex items-start gap-2.5">
            <Bell :size="16" class="text-brand-500 flex-shrink-0 mt-0.5" />
            <div class="text-xs text-zinc-500 dark:text-zinc-400 space-y-1">
              <p class="font-semibold">通知設定說明</p>
              <p>系統會針對你在「<strong>指數追蹤</strong>」中設定的標的，</p>
              <p>在除息日前 <strong>7 天</strong>與前 <strong>1 天</strong>自動發送提醒。</p>
              <p>通知管道（Email / LINE）依各標的設定為準。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bell, CalendarClock } from 'lucide-vue-next'
import { useDividendStore } from '../stores/dividend'
import DividendCalendar from '../components/DividendCalendar.vue'

const store = useDividendStore()
const upcomingLoading = ref(false)

const upcomingTracked = computed(() => store.upcomingItems.filter(i => i.is_tracked))
const upcomingUntracked = computed(() => store.upcomingItems.filter(i => !i.is_tracked))

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${m}/${d}`
}

function daysUntil(dateStr) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(dateStr)
  return Math.ceil((target - today) / 86400000)
}

function getTypePillClass(type) {
  if (type === '息') return 'bg-blue-500 text-white'
  if (type === '權') return 'bg-orange-500 text-white'
  return 'bg-violet-500 text-white'
}

onMounted(async () => {
  upcomingLoading.value = true
  try {
    await store.loadUpcoming(30)
  } finally {
    upcomingLoading.value = false
  }
  // 日曆由 DividendCalendar 元件內部的 onMounted 負責載入
})
</script>
