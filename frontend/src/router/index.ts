import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/LoginPage.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    name: "Home",
    component: () => import("../views/Dashboard.vue"),
  },
  {
    path: "/repairs",
    name: "RepairsList",
    component: () => import("../views/RepairsList.vue"),
  },
  {
    path: "/create-repair",
    name: "CreateRepair",
    component: () => import("../views/CreateRepairPage.vue"),
  },
  {
    path: "/edit/:qrToken",
    name: "EditRepair",
    component: () => import("../views/LogRepairWorkPage.vue"),
  },
  {
    path: "/customers",
    name: "CustomersList",
    component: () => import("../views/CustomersList.vue"),
  },
  {
    path: "/users",
    name: "UserManagement",
    component: () => import("../views/UserManagementPage.vue"),
    meta: { adminOnly: true },
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("../views/SettingsPage.vue"),
    meta: { adminOnly: true },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Navigation guard — requires auth for all non-public routes
router.beforeEach(async (to) => {
  if (to.meta.public) return true;

  // Lazy-import store to avoid circular dependency during module init
  const { useAuthStore } = await import("../stores/authStore");
  const authStore = useAuthStore();

  if (authStore.isAuthenticated) {
    if (to.meta.adminOnly && !authStore.isAdmin) return { name: "Home" };
    return true;
  }

  // Try to restore session from cookie before deciding
  const ok = await authStore.fetchMe();
  if (ok) {
    // Block non-admins from admin-only routes
    if (to.meta.adminOnly && !authStore.isAdmin) return { name: "Home" };
    return true;
  }

  return { name: "Login", query: { redirect: to.fullPath } };
});

export default router;
