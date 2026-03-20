<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-text">📈 Finance Dashboard</div>
        <div class="logo-sub">INVESTMENT PLATFORM</div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-label">主選單</div>
        <router-link to="/" class="nav-item" :class="{ active: route.path === '/' }">
          <span class="icon">📊</span> 總覽
        </router-link>
        <router-link to="/tracking" class="nav-item" :class="{ active: route.path === '/tracking' }">
          <span class="icon">📡</span> 指數追蹤
        </router-link>
        <router-link to="/backtest" class="nav-item" :class="{ active: route.path === '/backtest' }">
          <span class="icon">🔬</span> 回測管理
        </router-link>
        <router-link to="/optimize" class="nav-item" :class="{ active: route.path === '/optimize' }">
          <span class="icon">🎯</span> 投資組合最佳化
        </router-link>

        <div class="nav-label" style="margin-top:8px;">系統</div>
        <router-link to="/users" class="nav-item" :class="{ active: route.path === '/users' }">
          <span class="icon">👥</span> 使用者管理
        </router-link>
        <router-link to="/line" class="nav-item" :class="{ active: route.path === '/line' }">
          <span class="icon">💬</span> LINE 通知設定
        </router-link>
      </nav>
    </aside>

    <!-- Main -->
    <main class="main-content">
      <div class="page-header">
        <span class="page-breadcrumb" style="display:none;">{{ routeTitle }}</span> <!-- Hid the breadcrumb to match the cleaner header in reference -->
        <div style="flex:1;"></div>
        
        <div style="display:flex;align-items:center;gap:16px;">
          <div class="user-profile">
            <div class="user-avatar">{{ userInitials }}</div>
            <span class="user-name">{{ userName }}</span>
          </div>
          <button class="btn btn-ghost btn-sm" @click="handleLogout">
            登出
          </button>
        </div>
      </div>
      <div class="page-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const routeTitle = computed(() => {
  const map = { '/': '總覽 Dashboard', '/tracking': '指數追蹤管理', '/backtest': '回測管理', '/optimize': '投資組合最佳化', '/users': '使用者管理' }
  return map[route.path] || route.path
})

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

<style scoped>
.sidebar-logo {
  padding: 24px 24px;
  border-bottom: 1px solid var(--border);
}

.sidebar-logo .logo-text {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-logo .logo-sub {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: 4px;
  letter-spacing: 0.05em;
  margin-left: 28px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  background: var(--purple);
  color: #fff;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.user-name {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.page-header {
  padding: 0 24px;
}

.page-body {
  padding: 24px;
}
</style>
