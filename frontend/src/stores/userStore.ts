import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { UserResponse } from "@/api/types";
import { api } from "@/api/client";
import { personName } from "@/utils/person";

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

  /** Items for user dropdowns (repairer, tester), sorted by name. */
  const userOptions = computed(() =>
    users.value
      .map((u) => ({ value: u.id, title: personName(u) }))
      .sort((a, b) => a.title.localeCompare(b.title, "de")),
  );

  return {
    users,
    loading,
    loaded,
    fetchUsers,
    clear,
    getUserById,
    userOptions,
  };
});
