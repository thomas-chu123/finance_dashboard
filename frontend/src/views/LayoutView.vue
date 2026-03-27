<template>
  <div class="flex h-screen overflow-hidden transition-colors duration-300">
    <!-- Backdrop for Mobile -->
    <div 
      v-if="isSidebarOpen && !isLargeScreen"
      @click="closeSidebar"
      class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity duration-300"
      :class="isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    />

    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 bg-[var(--bg-sidebar)] border-r border-[var(--border-color)] transition-all duration-300 lg:relative lg:translate-x-0"
      :class="[
        !isSidebarOpen ? '-translate-x-full lg:translate-x-0' : '',
        isSidebarCollapsed ? 'w-20 lg:w-20' : 'w-60 lg:w-60'
      ]"
    >
      <div class="flex flex-col h-full p-4">
        <!-- Logo Section -->
        <div class="flex items-center justify-between mb-8 px-2">
          <div class="flex items-center gap-2 min-w-0" :class="!isSidebarCollapsed ? '' : 'lg:justify-center lg:w-full'">
            <div class="w-8 h-8 bg-brand-500 rounded-lg flex-shrink-0 flex items-center justify-center">
              <Globe class="text-white" :size="20" />
            </div>
            <span v-if="!isSidebarCollapsed" class="text-xl font-bold tracking-tighter text-[var(--text-primary)] whitespace-nowrap">
              NEXUS<span class="text-brand-500">.</span>
            </span>
          </div>
          
          <!-- Close Button (Mobile Only) -->
          <button 
            @click="closeSidebar"
            class="lg:hidden p-1 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors ml-auto flex-shrink-0"
            title="關閉菜單"
          >
            <X :size="20" />
          </button>
          
          <!-- Collapse Toggle (Desktop Only) -->
          <button 
            @click="toggleSidebarCollapse"
            class="hidden lg:p-1 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors ml-auto flex-shrink-0"
            :title="isSidebarCollapsed ? 'Expand Menu' : 'Collapse Menu'"
          >
            <component :is="isSidebarCollapsed ? ChevronRight : ChevronLeft" :size="18" />
          </button>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 space-y-1">
          <div v-if="!isSidebarCollapsed" class="text-xs font-bold text-zinc-500 uppercase tracking-widest px-3 mb-2">主選單</div>
          
          <router-link to="/" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="總覽" @click="handleMenuItemClick('/')">
            <LayoutDashboard :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">總覽</span>
          </router-link>

          <router-link to="/tracking" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/tracking' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="指數追蹤" @click="handleMenuItemClick('/tracking')">
            <TrendingUp :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/tracking' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">指數追蹤</span>
          </router-link>

          <router-link to="/backtest" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/backtest' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="回測管理" @click="handleMenuItemClick('/backtest')">
            <RefreshCcw :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/backtest' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">回測管理</span>
          </router-link>

          <router-link to="/optimize" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/optimize' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="投資組合最佳化" @click="handleMenuItemClick('/optimize')">
            <Target :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/optimize' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">投資組合最佳化</span>
          </router-link>

          <div v-if="!isSidebarCollapsed" class="text-xs font-bold text-zinc-500 uppercase tracking-widest px-3 mb-2 mt-6">系統</div>
          
          <router-link to="/users" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/users' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="使用者管理" @click="handleMenuItemClick('/users')">
            <Users :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/users' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">使用者管理</span>
          </router-link>

          <router-link to="/line" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/line' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="LINE 通知" @click="handleMenuItemClick('/line')">
            <MessageCircle :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/line' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">LINE 通知</span>
          </router-link>

          <router-link to="/guide" :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group cursor-pointer', isSidebarCollapsed ? 'justify-center' : 'w-full', $route.path === '/guide' ? 'bg-brand-500/10 text-brand-500 dark:text-brand-400' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50']" title="使用說明" @click="handleMenuItemClick('/guide')">
            <FileQuestion :size="20" :class="['flex-shrink-0 transition-colors', $route.path === '/guide' ? 'text-brand-500 dark:text-brand-400' : 'group-hover:text-zinc-900 dark:group-hover:text-zinc-200']" />
            <span v-if="!isSidebarCollapsed" class="font-medium text-sm">使用說明</span>
          </router-link>
        </nav>

        <div class="mt-auto pt-6 border-t border-[var(--border-color)]">
          <div v-if="!isSidebarCollapsed" class="flex items-center gap-3 px-2">
            <div class="w-10 h-10 rounded-full bg-brand-500 flex items-center justify-center border border-brand-600/20 shadow-sm flex-shrink-0">
              <span class="text-white font-bold text-lg">{{ userInitials }}</span>
            </div>
            <div class="flex flex-col flex-1 truncate">
              <span class="text-sm font-semibold text-[var(--text-primary)] truncate">{{ userName }}</span>
              <button @click="handleLogout" class="text-[10px] text-rose-500 text-left hover:underline">登出 (Logout)</button>
            </div>
          </div>
          <div v-else class="flex justify-center">
            <div class="w-10 h-10 rounded-full bg-brand-500 flex items-center justify-center border border-brand-600/20 shadow-sm cursor-pointer hover:opacity-80 transition-opacity" :title="userName" @click="handleLogout">
              <span class="text-white font-bold text-lg">{{ userInitials }}</span>
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
          <!-- Mobile Search Toggle -->
          <button 
            @click="toggleSearchModal"
            class="sm:hidden p-2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
          >
            <Search :size="20" />
          </button>
          <div class="relative max-w-md w-full hidden sm:block">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" :size="16" />
            <input 
              type="text" 
              placeholder="搜尋名稱、代碼或資產..." 
              class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500/50 transition-colors text-[var(--text-primary)]"
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
          <button 
            @click="auth.toggleGlobalNotify()"
            class="relative p-2 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
            :title="auth.profile?.global_notify !== false ? '關閉全部追蹤通知' : '開啟全部追蹤通知'"
          >
            <component :is="auth.profile?.global_notify !== false ? Bell : BellOff" :size="20" />
            <span v-if="auth.profile?.global_notify !== false" class="absolute top-2 right-2 w-2 h-2 bg-brand-500 rounded-full border-2 border-[var(--bg-header)]"></span>
          </button>
          <div class="h-8 w-[1px] bg-[var(--border-color)] mx-1 sm:mx-2"></div>
          <div class="flex flex-col items-end">
            <span class="text-[10px] text-zinc-500 font-medium uppercase tracking-widest">Market Status</span>
            <div class="flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 bg-brand-500 rounded-full animate-pulse"></span>
              <span class="text-xs font-bold text-brand-500">OPEN</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Dashboard Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar relative p-4 sm:p-6 pb-20 lg:pb-6">
        <router-view />
      </div>

      <!-- Mobile Bottom Navigation -->
      <nav class="fixed bottom-0 left-0 right-0 z-50 lg:hidden
                  bg-[var(--bg-sidebar)] border-t border-[var(--border-color)]
                  flex items-center justify-around h-16 safe-area-bottom">
        <router-link v-for="item in mobileNavItems" :key="item.path" :to="item.path"
          class="flex flex-col items-center gap-1 px-3 py-2 min-w-[64px]
                 text-zinc-500 transition-colors"
          active-class="text-brand-500">
          <component :is="item.icon" class="w-5 h-5" />
          <span class="text-[10px] font-bold">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Mobile Search Modal -->
      <Teleport to="body">
        <div v-if="isSearchModalOpen" 
             class="fixed inset-0 z-[60] bg-[var(--bg-main)] safe-area-top slide-up">
          <div class="p-4 border-b border-[var(--border-color)] flex items-center gap-3">
            <button @click="isSearchModalOpen = false" class="p-2 text-zinc-500">
              <ChevronLeft :size="24" />
            </button>
            <div class="relative flex-1">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" :size="18" />
              <input 
                type="text" 
                placeholder="搜尋名稱、代碼..." 
                class="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-xl py-3 pl-11 pr-4 text-base focus:outline-none focus:border-brand-500/50 text-[var(--text-primary)]"
                autofocus
              />
            </div>
          </div>
          <div class="p-6 text-center text-zinc-500">
            <p class="text-sm">輸入關鍵字開始搜尋...</p>
          </div>
        </div>
      </Teleport>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTheme } from '../composables/useTheme'
import { useBreakpoint } from '../composables/useBreakpoint'
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
  BellOff,
  Sun, 
  Moon, 
  Menu, 
  X,
  ChevronLeft,
  ChevronRight,
  FileQuestion
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleDark } = useTheme()
const { isMobile, isTablet, isDesktop, isLargeScreen } = useBreakpoint()

const isSidebarOpen = ref(true)
const isSidebarCollapsed = ref(false)
const isSearchModalOpen = ref(false)

const userName = computed(() => auth.profile?.display_name || auth.email || 'User')
const userInitials = computed(() => userName.value.charAt(0).toUpperCase())

const mobileNavItems = [
  { path: '/', label: '總覽', icon: LayoutDashboard },
  { path: '/tracking', label: '追蹤', icon: TrendingUp },
  { path: '/backtest', label: '回測', icon: RefreshCcw },
  { path: '/optimize', label: '最佳化', icon: Target },
]

// 關閉sidebar和backdrop
function closeSidebar() {
  if (!isLargeScreen.value) {
    isSidebarOpen.value = false
  }
}

// 移動設備上導航時自動關閉sidebar（直接檢查視窗寬度，不依賴ref）
function closeSidebarOnMobile() {
  if (window.innerWidth < 1024) {
    isSidebarOpen.value = false
  }
}

// 直接關閉菜單的函數（用在點擊菜單項時）
function handleMenuItemClick(routePath) {
  if (window.innerWidth < 1024) {
    isSidebarOpen.value = false
  }
  
  router.push(routePath)
}

// 切換sidebar折疊狀態（桌面版）
function toggleSidebarCollapse() {
  if (isLargeScreen.value) {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }
}

// 路由變化時自動關閉手機菜單
router.afterEach(() => {
  closeSidebarOnMobile()
})

function toggleSearchModal() {
  isSearchModalOpen.value = !isSearchModalOpen.value
}

onMounted(async () => {
  console.log('[LayoutView.onMounted] Starting profile initialization...', { hasToken: !!auth.token, apiBase: import.meta.env.VITE_API_BASE_URL })
  try {
    console.log('[LayoutView.onMounted] Calling auth.fetchProfile()...')
    await auth.fetchProfile()
    console.log('[LayoutView.onMounted] ✓ Profile loaded successfully:', {
      displayName: auth.profile?.display_name,
      email: auth.profile?.email,
      hasQuotes: !!auth.profile?.dashboard_quotes,
      quotesCount: auth.profile?.dashboard_quotes?.length
    })
  } catch (error) {
    console.error('[LayoutView.onMounted] ✗ Failed to load profile:', error)
  }
})

onUnmounted(() => {
})


function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
