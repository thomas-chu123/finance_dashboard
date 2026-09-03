<template>
  <div class="max-w-2xl mx-auto p-4 sm:p-0">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-[var(--text-primary)] mb-2">{{ $t('pages.guide') }}</h1>
      <p class="text-zinc-600 dark:text-zinc-400">{{ $t('guide.description') }}</p>
    </div>

    <div class="space-y-6">
      <section
        v-for="section in guideSections"
        :key="section.key"
        class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 transition-all duration-200 hover:border-brand-500/30"
      >
        <div class="flex items-start gap-4">
          <div :class="['p-3 rounded-lg', section.backgroundClass]">
            <component :is="section.icon" :class="section.iconClass" :size="24" />
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">{{ section.content.title }}</h2>
            <p class="text-zinc-600 dark:text-zinc-400 mb-2">{{ section.content.description }}</p>
            <ul class="list-disc list-inside space-y-1 text-zinc-600 dark:text-zinc-400 ml-2">
              <li v-for="item in section.content.items" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="bg-gradient-to-r from-brand-500/5 to-blue-500/5 border border-brand-500/20 rounded-xl p-6">
        <h2 class="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Lightbulb class="text-brand-500" :size="20" />
          {{ $t('guide.tips.title') }}
        </h2>
        <ul class="space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
          <li v-for="item in guideTips" :key="item">• {{ item }}</li>
        </ul>
      </section>

      <section class="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl p-6 text-center">
        <h2 class="text-lg font-bold text-[var(--text-primary)] mb-2">{{ $t('guide.support.title') }}</h2>
        <p class="text-zinc-600 dark:text-zinc-400 mb-4">{{ $t('guide.support.description') }}</p>
        <router-link to="/users" class="inline-block px-6 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg font-medium transition-colors">
          {{ $t('guide.support.backToUserCenter') }}
        </router-link>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  LayoutDashboard,
  TrendingUp,
  RefreshCcw,
  Target,
  Users,
  MessageCircle,
  Lightbulb,
  Sparkles,
  Calendar,
  Bell,
} from 'lucide-vue-next'
import { useLocale } from '../composables/useLocale'

const { t } = useLocale()

const sectionDefinitions = [
  ['dashboard', LayoutDashboard, 'bg-brand-500/10', 'text-brand-500'],
  ['briefing', Sparkles, 'bg-cyan-500/10', 'text-cyan-500'],
  ['dividend', Calendar, 'bg-emerald-500/10', 'text-emerald-500'],
  ['tracking', TrendingUp, 'bg-blue-500/10', 'text-blue-500'],
  ['backtest', RefreshCcw, 'bg-purple-500/10', 'text-purple-500'],
  ['optimize', Target, 'bg-amber-500/10', 'text-amber-500'],
  ['notifications', Bell, 'bg-red-500/10', 'text-red-500'],
  ['users', Users, 'bg-green-500/10', 'text-green-500'],
  ['line', MessageCircle, 'bg-rose-500/10', 'text-rose-500'],
]

const guideSections = computed(() => sectionDefinitions.map(([key, icon, backgroundClass, iconClass]) => ({
  key,
  icon,
  backgroundClass,
  iconClass,
  content: t(`guide.sections.${key}`),
})))

const guideTips = computed(() => t('guide.tips.items'))
</script>
