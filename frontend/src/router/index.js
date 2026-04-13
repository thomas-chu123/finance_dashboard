import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/',
    component: () => import('../views/LayoutView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'briefing',
        name: 'Briefing',
        component: () => import('../views/BriefingView.vue'),
      },
      {
        path: 'dividend-calendar',
        name: 'DividendCalendar',
        component: () => import('../views/DividendCalendarView.vue'),
      },
      {
        path: 'tracking',
        name: 'Tracking',
        component: () => import('../views/TrackingView.vue'),
      },
      {
        path: 'backtest',
        name: 'Backtest',
        component: () => import('../views/BacktestView.vue'),
      },
      {
        path: 'optimize',
        name: 'Optimize',
        component: () => import('../views/OptimizeView.vue'),
      },
      {
        path: 'monte-carlo',
        name: 'MonteCarlo',
        component: () => import('../views/MonteCarloView.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/UsersView.vue'),
      },
      {
        path: 'notifications',
        name: 'NotificationLogs',
        component: () => import('../views/NotificationLogsView.vue'),
      },
      {
        path: 'line',
        name: 'Line',
        component: () => import('../views/LineView.vue'),
      },
      {
        path: 'guide',
        name: 'Guide',
        component: () => import('../views/GuideView.vue'),
      },
      {
        path: 'admin',
        name: 'AdminPanel',
        component: () => import('../views/AdminPanelView.vue'),
        meta: { requiresAdmin: true },
        children: [
          {
            path: 'users',
            name: 'AdminUsers',
            component: () => import('../views/AdminUsersView.vue'),
            meta: { requiresAdmin: true },
          },
          {
            path: 'scheduler',
            name: 'AdminScheduler',
            component: () => import('../views/AdminSchedulerView.vue'),
            meta: { requiresAdmin: true },
          },
          {
            path: 'logs',
            name: 'AdminLogs',
            component: () => import('../views/AdminLogsView.vue'),
            meta: { requiresAdmin: true },
          },
          {
            path: 'stats',
            name: 'AdminStats',
            component: () => import('../views/AdminStatsView.vue'),
            meta: { requiresAdmin: true },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    next('/login')
  } else if (to.meta.requiresGuest && auth.token) {
    next('/')
  } else if (to.meta.requiresAdmin && !auth.isAdmin) {
    // 重定向到主頁面（無管理員權限）
    next('/')
  } else {
    next()
  }
})

export default router
