import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/lock',
    name: 'PinLock',
    component: () => import('../components/PinLockScreen.vue'),
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/RepairsOverview.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/repairs',
    name: 'RepairsList',
    component: () => import('../views/RepairsList.vue'),
  },
  {
    path: '/create-repair',
    name: 'CreateRepair',
    component: () => import('../views/CreateRepairPage.vue'),
  },
  {
    path: '/edit/:qrToken',
    name: 'EditRepair',
    component: () => import('../views/LogRepairWorkPage.vue'),
  },
  {
    path: '/customers',
    name: 'CustomersList',
    component: () => import('../views/CustomersList.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfilePage.vue'),
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: () => import('../views/UserManagementPage.vue'),
    meta: { adminOnly: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsPage.vue'),
    meta: { adminOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard — requires auth for all non-public routes
router.beforeEach(async (to) => {
  // Lazy-import store to avoid circular dependency during module init
  const { useAuthStore } = await import('../stores/authStore')
  const authStore = useAuthStore()

  if (!authStore.sessionChecked) {
    await authStore.fetchMe()
  }

  if (authStore.pinSessionEligible) {
    if (authStore.isLocked) {
      return to.name === 'PinLock' ? true : { name: 'PinLock' }
    }
    if (to.name === 'PinLock' || to.name === 'Login') return { name: 'Home' }
    if (to.meta.adminOnly && !authStore.isAdmin) return { name: 'Home' }
    return true
  }

  if (to.meta.public && to.name === 'Login') return true
  return { name: 'Login', query: { redirect: to.fullPath } }
})

export default router
