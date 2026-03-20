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
        path: 'users',
        name: 'Users',
        component: () => import('../views/UsersView.vue'),
      },
      {
        path: 'line',
        name: 'Line',
        component: () => import('../views/LineView.vue'),
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
  } else {
    next()
  }
})

export default router
