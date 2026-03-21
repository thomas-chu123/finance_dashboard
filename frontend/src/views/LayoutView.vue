<template>
  <div class="flex h-screen overflow-hidden transition-colors duration-300">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 w-64 bg-[var(--bg-sidebar)] border-r border-[var(--border-color)] transition-transform duration-300 lg:relative lg:translate-x-0"
      :class="!isSidebarOpen ? '-translate-x-full' : ''"
    >
      <div class="flex flex-col h-full p-6">
        <div class="flex items-center gap-2 mb-10 px-2">
          <div class="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
            <Globe class="text-white dark:text-black" :size="20" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-[var(--text-primary)]">
            NEXUS<span class="text-emerald-500">.</span>
          </span>
        </div>

        <nav class="flex-1 space-y-2">
          <div class="text-xs font-bold text-zinc-500 uppercase tracking-widest px-4 mb-2">主選單</div>
          
          <router-link to="/" custom v-slot="{ href, navigate, isExactActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isExactActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <LayoutDashboard :size="20" :class="['transition-colors', isExactActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">總覽</span>
            </a>
          </router-link>

          <router-link to="/tracking" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <TrendingUp :size="20" :class="['transition-colors', isActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">指數追蹤</span>
            </a>
          </router-link>

          <router-link to="/backtest" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <RefreshCcw :size="20" :class="['transition-colors', isActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">回測管理</span>
            </a>
          </router-link>

          <router-link to="/optimize" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <Target :size="20" :class="['transition-colors', isActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">投資組合最佳化</span>
            </a>
          </router-link>

          <div class="text-xs font-bold text-zinc-500 uppercase tracking-widest px-4 mb-2 mt-6">系統</div>
          
          <router-link to="/users" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <Users :size="20" :class="['transition-colors', isActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">使用者管理</span>
            </a>
          </router-link>

          <router-link to="/line" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click="navigate" :class="['flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all duration-200 group', isActive ? 'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']">
              <MessageCircle :size="20" :class="['transition-colors', isActive ? 'text-emerald-500 dark:text-emerald-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
              <span class="font-medium text-sm">LINE 通知</span>
            </a>
          </router-link>
        </nav>

        <div class="mt-auto pt-6 border-t border-[var(--border-color)]">
          <div class="flex items-center gap-3 px-2">
            <div class="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center border border-zinc-300 dark:border-zinc-700">
              <span class="text-[var(--text-primary)] font-bold text-lg">{{ userInitials }}</span>
            </div>
            <div class="flex flex-col flex-1 truncate">
              <span class="text-sm font-semibold text-[var(--text-primary)] truncate">{{ userName }}</span>
              <button @click="handleLogout" class="text-[10px] text-rose-500 text-left hover:underline">登出 (Logout)</button>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden bg-[var(--bg-main)]">
      <!-- Header -->
      <header class="h-16 flex-shrink-0 border-b border-[var(--border-color)] flex items-center justify-between px-6 bg-[var(--bg-header)] backdrop-blur-md sticky top-0 z-40">
        <div class="flex items-center gap-4 flex-1">
          <button 
            @click="isSidebarOpen = !isSidebarOpen"
            class="lg:hidden p-2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
          >
            <component :is="isSidebarOpen ? X : Menu" :size="20" />
          </button>
          <div class="relative max-w-md w-full hidden sm:block">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" :size="16" />
            <input 
              type="text" 
              placeholder="搜尋名稱、代碼或資產..." 
              class="w-full bg-zinc-100 dark:bg-zinc-900/50 border border-[var(--border-color)] rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-emerald-500/50 transition-colors text-[var(--text-primary)]"
            />
          </div>
        </div>
        
        <div class="flex items-center gap-2 sm:gap-4">
          <button 
            @click="toggleDark()"
            class="p-2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
            :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
          >
            <component :is="isDark ? Sun : Moon" :size="20" />
          </button>
          <button class="relative p-2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
            <Bell :size="20" />
            <span class="absolute top-2 right-2 w-2 h-2 bg-emerald-500 rounded-full border-2 border-[var(--bg-header)]"></span>
          </button>
          <div class="h-8 w-[1px] bg-[var(--border-color)] mx-1 sm:mx-2"></div>
          <div class="flex flex-col items-end">
            <span class="text-[10px] text-zinc-500 font-medium uppercase tracking-widest">Market Status</span>
            <div class="flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
              <span class="text-xs font-bold text-emerald-500">OPEN</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Dashboard Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar relative p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTheme } from '../composables/useTheme'
import { 
  Globe, 
  LayoutDashboard, 
  TrendingUp, 
  RefreshCcw, 
  Target, 
  Users, 
  MessageCircle, 
  Search, 
  Bell, 
  Sun, 
  Moon, 
  Menu, 
  X 
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleDark } = useTheme()

const isSidebarOpen = ref(true)

const userName = computed(() => auth.profile?.display_name || auth.email || 'User')
const userInitials = computed(() => userName.value.charAt(0).toUpperCase())

onMounted(() => {
  auth.fetchProfile()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
