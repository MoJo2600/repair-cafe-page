import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { UserResponse } from "@/api/types";

export const useAuthStore = defineStore("auth", () => {
  const currentUser = ref<UserResponse | null>(null);
  const loading = ref(false);

  const isAuthenticated = computed(() => currentUser.value !== null);
  const isAdmin = computed(() => currentUser.value?.is_admin ?? false);

  /** Called on app startup to restore session from cookie. */
  async function fetchMe(): Promise<boolean> {
    try {
      const res = await fetch("/api/auth/me", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        currentUser.value = data.data;
        return true;
      }
      currentUser.value = null;
      return false;
    } catch {
      currentUser.value = null;
      return false;
    }
  }

  async function login(
    username: string,
    password: string,
  ): Promise<{ success: boolean; error?: string }> {
    loading.value = true;
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) {
        currentUser.value = data.data;
        return { success: true };
      }
      return { success: false, error: data.error ?? "Login failed" };
    } catch {
      return { success: false, error: "Network error" };
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      currentUser.value = null;
    }
  }

  return {
    currentUser,
    loading,
    isAuthenticated,
    isAdmin,
    fetchMe,
    login,
    logout,
  };
});
