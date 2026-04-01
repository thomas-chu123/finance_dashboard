<template>
  <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] overflow-hidden">
    <!-- 月份導覽列 -->
    <div class="flex items-center justify-between px-5 py-4 border-b border-[var(--border-color)]">
      <button
        @click="store.prevMonth()"
        class="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <ChevronLeft :size="18" />
      </button>

      <div class="text-center">
        <h2 class="font-bold text-[var(--text-primary)] text-base">
          {{ store.currentYear }} 年 {{ store.currentMonth }} 月
        </h2>
        <p class="text-xs text-zinc-500 mt-0.5">除權息日曆</p>
      </div>

      <button
        @click="store.nextMonth()"
        class="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <ChevronRight :size="18" />
      </button>
    </div>

    <!-- 圖例 -->
    <div class="flex items-center gap-4 px-5 py-2.5 border-b border-[var(--border-color)] text-xs text-zinc-500 flex-wrap">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2.5 h-2.5 rounded-sm bg-blue-500/20 border border-blue-400"></span>除息
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2.5 h-2.5 rounded-sm bg-orange-500/20 border border-orange-400"></span>除權
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2.5 h-2.5 rounded-sm bg-violet-500/20 border border-violet-400"></span>除權息
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-500/20 border border-emerald-400"></span>
        <Bell :size="10" class="text-emerald-500 -ml-0.5" />追蹤中
      </span>
    </div>

    <!-- Loading 狀態 -->
    <div v-if="store.loading" class="p-8 flex justify-center">
      <div class="animate-spin w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full"></div>
    </div>

    <!-- 錯誤狀態 -->
    <div v-else-if="store.error" class="p-6 text-center text-red-500 text-sm">
      {{ store.error }}
    </div>

    <template v-else>
      <!-- 星期標頭 -->
      <div class="grid grid-cols-7 border-b border-[var(--border-color)]">
        <div
          v-for="day in ['日', '一', '二', '三', '四', '五', '六']"
          :key="day"
          class="py-2 text-center text-xs font-semibold text-zinc-400"
          :class="day === '日' ? 'text-red-400' : day === '六' ? 'text-blue-400' : ''"
        >
          {{ day }}
        </div>
      </div>

      <!-- 日曆格子 -->
      <div class="grid grid-cols-7">
        <!-- 月份開始前的空格 -->
        <div
          v-for="n in leadingBlanks"
          :key="`blank-${n}`"
          class="min-h-[72px] border-r border-b border-[var(--border-color)]"
        ></div>

        <!-- 每天格子 -->
        <div
          v-for="day in daysInMonth"
          :key="day"
          class="min-h-[72px] border-r border-b border-[var(--border-color)] p-1 cursor-pointer transition-colors relative bg-[var(--bg-card)] hover:bg-brand-500/5 dark:hover:bg-brand-500/10"
          :class="[
            isToday(day) ? 'bg-brand-500/5 dark:bg-brand-500/10' : '',
            selectedDay === day ? 'ring-2 ring-inset ring-brand-400 bg-brand-500/5 dark:bg-brand-500/10' : '',
          ]"
          @click="toggleDay(day)"
        >
          <!-- 日期數字 -->
          <div
            class="text-xs font-semibold mb-0.5 w-5 h-5 flex items-center justify-center rounded-full"
            :class="[
              isToday(day) ? 'bg-brand-500 text-white' : 'text-[var(--text-primary)]',
              getDayOfWeek(day) === 0 ? '!text-red-400' : '',
              getDayOfWeek(day) === 6 ? '!text-blue-400' : '',
              isToday(day) ? '!text-white' : '',
            ]"
          >
            {{ day }}
          </div>

          <!-- 除權息徽章（最多顯示 3 個，其餘折疊） -->
          <div class="flex flex-col gap-0.5">
            <template v-for="(item, idx) in getEventsForDay(day)" :key="`${item.code}-${item.ex_type}`">
              <div
                v-if="idx < 3"
                class="flex items-center gap-0.5 rounded px-1 py-0.5 text-[10px] leading-tight truncate max-w-full"
                :class="getBadgeClass(item)"
                :title="`${item.code} ${item.name} - ${item.ex_type}${item.cash_dividend ? ' $' + Number(item.cash_dividend).toFixed(2) : ''}`"
              >
                <Bell v-if="item.is_tracked" :size="8" class="flex-shrink-0" />
                <span class="truncate font-medium">{{ item.code }}</span>
              </div>
            </template>
            <div
              v-if="getEventsForDay(day).length > 3"
              class="text-[10px] text-zinc-400 px-1"
            >
              +{{ getEventsForDay(day).length - 3 }} 支
            </div>
          </div>
        </div>

        <!-- 月份結束後的空格 -->
        <div
          v-for="n in trailingBlanks"
          :key="`trail-${n}`"
          class="min-h-[72px] border-r border-b border-[var(--border-color)]"
        ></div>
      </div>

      <!-- 選取日期的詳細面板 -->
      <Transition name="slide-down">
        <div
          v-if="selectedDay && getEventsForDay(selectedDay).length"
          class="border-t border-[var(--border-color)] px-5 py-4"
        >
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sm text-[var(--text-primary)]">
              {{ store.currentYear }}/{{ String(store.currentMonth).padStart(2,'0') }}/{{ String(selectedDay).padStart(2,'0') }} — {{ getEventsForDay(selectedDay).length }} 支除權息
            </h3>
            <button @click="selectedDay = null" class="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200">
              <X :size="16" />
            </button>
          </div>

          <div class="space-y-2">
            <div
              v-for="item in getEventsForDay(selectedDay)"
              :key="`detail-${item.code}-${item.ex_type}`"
              class="flex items-center justify-between rounded-lg px-3 py-2.5 text-sm"
              :class="item.is_tracked ? 'bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800' : 'bg-[var(--bg-card)] border border-[var(--border-color)]'"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span
                  class="flex-shrink-0 text-[11px] font-bold px-1.5 py-0.5 rounded"
                  :class="getTypePillClass(item.ex_type)"
                >{{ item.ex_type }}</span>
                <div class="min-w-0">
                  <span class="font-semibold text-[var(--text-primary)]">{{ item.code }}</span>
                  <span class="text-zinc-500 ml-1.5 truncate">{{ item.name }}</span>
                </div>
              </div>

              <div class="flex items-center gap-2 flex-shrink-0 ml-2">
                <span v-if="item.cash_dividend" class="text-emerald-600 dark:text-emerald-400 font-medium text-xs">
                  ${{ Number(item.cash_dividend).toFixed(4) }}
                </span>
                <div v-if="item.is_tracked" class="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 text-xs">
                  <Bell :size="12" />
                  <span class="hidden sm:inline">{{ channelLabel(item.notify_channel) }}</span>
                </div>
              </div>
            </div>
          </div>

          <p v-if="hasTrackedItems(selectedDay)" class="text-xs text-zinc-400 mt-3">
            🔔 通知設定（管道、開關）請至「指數追蹤」頁面管理
          </p>
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ChevronLeft, ChevronRight, Bell, X } from 'lucide-vue-next'
import { useDividendStore } from '../stores/dividend'

const store = useDividendStore()
const selectedDay = ref(null)

// ── 月曆計算 ─────────────────────────────────────────────────────────────────

const daysInMonth = computed(() => {
  return new Date(store.currentYear, store.currentMonth, 0).getDate()
})

/** 月份第一天是星期幾 (0=日, 6=六) */
const leadingBlanks = computed(() => {
  return new Date(store.currentYear, store.currentMonth - 1, 1).getDay()
})

/** 補齊最後一列的空格 */
const trailingBlanks = computed(() => {
  const total = leadingBlanks.value + daysInMonth.value
  const remainder = total % 7
  return remainder === 0 ? 0 : 7 - remainder
})

function getDayOfWeek(day) {
  return new Date(store.currentYear, store.currentMonth - 1, day).getDay()
}

function isToday(day) {
  const t = new Date()
  return (
    t.getFullYear() === store.currentYear &&
    t.getMonth() + 1 === store.currentMonth &&
    t.getDate() === day
  )
}

function getDateKey(day) {
  return `${store.currentYear}-${String(store.currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function getEventsForDay(day) {
  return store.calendarByDate[getDateKey(day)] || []
}

function hasTrackedItems(day) {
  return getEventsForDay(day).some(i => i.is_tracked)
}

function toggleDay(day) {
  selectedDay.value = selectedDay.value === day ? null : day
}

// ── 樣式輔助 ─────────────────────────────────────────────────────────────────

function getBadgeClass(item) {
  if (item.is_tracked) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
  if (item.ex_type === '息') return 'bg-blue-500/10 text-blue-700 dark:text-blue-400'
  if (item.ex_type === '權') return 'bg-orange-500/10 text-orange-700 dark:text-orange-400'
  return 'bg-violet-500/10 text-violet-700 dark:text-violet-400'
}

function getTypePillClass(type) {
  if (type === '息') return 'bg-blue-500 text-white'
  if (type === '權') return 'bg-orange-500 text-white'
  return 'bg-violet-500 text-white'
}

function channelLabel(channel) {
  if (channel === 'line') return 'LINE'
  if (channel === 'both') return 'Email+LINE'
  return 'Email'
}

// ── 月份切換時清除選取 ────────────────────────────────────────────────────────
watch([() => store.currentYear, () => store.currentMonth], () => {
  selectedDay.value = null
})

onMounted(() => {
  if (!store.calendarItems.length) {
    store.loadCalendar(store.currentYear, store.currentMonth)
  }
})
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
