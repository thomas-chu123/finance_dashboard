<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="space-y-2">
      <h1 class="text-3xl font-bold text-[var(--text-primary)]">{{ $t('pages.admin') }}</h1>
      <p class="text-[var(--text-secondary)]">{{ $t('admin.description') }}</p>
    </div>

    <!-- Navigation Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 用戶管理卡片 -->
      <router-link to="/admin/users" 
        class="p-4 rounded-lg border border-[var(--border-color)] hover:border-brand-500 hover:bg-brand-500/5 transition-all cursor-pointer"
      >
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <Users class="text-blue-500" :size="24" />
          </div>
          <div>
            <h3 class="font-semibold text-[var(--text-primary)]">{{ $t('pages.adminUsers') }}</h3>
            <p class="text-xs text-[var(--text-secondary)]">{{ $t('admin.userDescription') }}</p>
          </div>
        </div>
      </router-link>

      <!-- 時程表管理卡片 -->
      <router-link to="/admin/scheduler"
        class="p-4 rounded-lg border border-[var(--border-color)] hover:border-brand-500 hover:bg-brand-500/5 transition-all cursor-pointer"
      >
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
            <Clock class="text-purple-500" :size="24" />
          </div>
          <div>
            <h3 class="font-semibold text-[var(--text-primary)]">{{ $t('pages.scheduler') }}</h3>
            <p class="text-xs text-[var(--text-secondary)]">{{ $t('admin.schedulerDescription') }}</p>
          </div>
        </div>
      </router-link>

      <!-- 日誌查看卡片 -->
      <router-link to="/admin/logs"
        class="p-4 rounded-lg border border-[var(--border-color)] hover:border-brand-500 hover:bg-brand-500/5 transition-all cursor-pointer"
      >
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
            <FileText class="text-green-500" :size="24" />
          </div>
          <div>
            <h3 class="font-semibold text-[var(--text-primary)]">{{ $t('pages.logs') }}</h3>
            <p class="text-xs text-[var(--text-secondary)]">{{ $t('admin.logsDescription') }}</p>
          </div>
        </div>
      </router-link>

      <!-- 系統監控卡片 -->
      <router-link to="/admin/stats"
        class="p-4 rounded-lg border border-[var(--border-color)] hover:border-brand-500 hover:bg-brand-500/5 transition-all cursor-pointer"
      >
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-orange-500/10 flex items-center justify-center">
            <BarChart3 class="text-orange-500" :size="24" />
          </div>
          <div>
            <h3 class="font-semibold text-[var(--text-primary)]">{{ $t('pages.stats') }}</h3>
            <p class="text-xs text-[var(--text-secondary)]">{{ $t('admin.statsDescription') }}</p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- Admin Info Alert -->
    <div class="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300">
      <div class="flex gap-3">
        <Shield :size="20" class="flex-shrink-0 mt-0.5" />
        <div class="text-sm">
          <p class="font-semibold">管理員權限</p>
          <p class="text-xs opacity-80">您擁有系統管理員權限。所有操作都會被記錄在審計日誌中。</p>
        </div>
      </div>
    </div>

    <!-- Router Output -->
    <router-view />
  </div>
</template>

<script setup>
import { Shield, Users, Clock, FileText, BarChart3 } from 'lucide-vue-next'
</script>
