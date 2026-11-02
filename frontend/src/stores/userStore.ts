import { defineStore } from "pinia";
import { ref } from "vue";
import type { UserResponse } from "@/api/types";
import { api } from "@/api/client";

export const useUserStore = defineStore("users", () => {
  const users = ref<UserResponse[]>([]);
  const loading = ref(false);
  const loaded = ref(false);
  let fetchRevision = 0;

  async function fetchUsers() {
    if (loading.value) return;
    const revision = fetchRevision;
    loading.value = true;
    try {
      const res = await api.listUsers();
      if (revision === fetchRevision) {
        users.value = res.data;
        loaded.value = true;
      }
    } catch (err) {
      // Keep `loaded` false (e.g. locked session) so a later call retries
      console.error("Error loading users:", err);
    } finally {
      if (revision === fetchRevision) {
        loading.value = false;
      }
    }
  }

  function clear() {
    fetchRevision += 1;
    users.value = [];
    loading.value = false;
    loaded.value = false;
  }

  function getUserById(id: number): UserResponse | undefined {
    return users.value.find((u) => u.id === id);
  }

  function getUserDisplayName(id: number | undefined | null): string {
    if (!id) return "";
    const u = getUserById(id);
    return u ? `${u.vorname} ${u.nachname}` : String(id);
  }

  return {
    users,
    loading,
    loaded,
    fetchUsers,
    clear,
    getUserById,
    getUserDisplayName,
  };
});
