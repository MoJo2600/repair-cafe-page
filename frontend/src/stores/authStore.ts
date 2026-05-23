import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { AuthService } from "@/api/services/AuthService";
import type { UserResponse } from "@/api/types";

export const useAuthStore = defineStore("auth", () => {
  const currentUser = ref<UserResponse | null>(null);
  const loading = ref(false);

  const isAuthenticated = computed(() => currentUser.value !== null);
  const isAdmin = computed(() => currentUser.value?.is_admin ?? false);

  /** Called on app startup to restore session from cookie. */
  async function fetchMe(): Promise<boolean> {
    try {
      const data = await AuthService.me();
      currentUser.value = data.data ?? null;
      return currentUser.value !== null;
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
      const data = await AuthService.login({ username, password });
      currentUser.value = data.data ?? null;
      return { success: true };
    } catch (err: any) {
      const message: string =
        err?.body?.error ?? err?.message ?? "Login failed";
      return { success: false, error: message };
    } finally {
      loading.value = false;
    }
  }

  async function logout() {
    try {
      await AuthService.logout();
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
