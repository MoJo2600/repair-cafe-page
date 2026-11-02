<script setup lang="ts">
import { api } from '@/api/client'
import { computed, ref, shallowRef, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'
import { useToast } from '@/composables/useToast'
import { errorMessage } from '@/utils/errors'

/** Who is responsible for a repair; the backend logs each change as an assignee change. */
const { repairId, assigneeId } = defineProps<{
  repairId: number
  assigneeId: number | null
}>()

const emit = defineEmits<{
  /** Saved on the server; the owner should update its repair and reload logs. */
  assigned: [userId: number | null]
}>()

const authStore = useAuthStore()
const userStore = useUserStore()
const toast = useToast()

const selected = ref<number | null>(assigneeId)
const saving = shallowRef(false)

watch(
  () => assigneeId,
  (value) => {
    selected.value = value
  }
)

const userItems = computed(() =>
  userStore.users.map((u) => ({ value: u.id, title: `${u.vorname} ${u.nachname}` }))
)
const canAssignToMe = computed(
  () => !!authStore.currentUser && selected.value !== authStore.currentUser.id
)

async function assign(userId: number | null) {
  selected.value = userId
  saving.value = true
  try {
    await api.updateRepair({ id: repairId }, { user_id: userId })
    toast.success(userId ? 'Zuständigkeit aktualisiert' : 'Zuweisung entfernt')
    emit('assigned', userId)
  } catch (err) {
    toast.error('Fehler beim Zuweisen: ' + errorMessage(err, 'Unbekannter Fehler'))
    selected.value = assigneeId
  } finally {
    saving.value = false
  }
}

function assignToMe() {
  if (authStore.currentUser) void assign(authStore.currentUser.id)
}
</script>

<template>
  <div>
    <div class="d-flex align-center mb-2">
      <span class="text-body-large text-grey-darken-1">Zuständig</span>
      <v-spacer></v-spacer>
      <v-btn
        v-if="canAssignToMe"
        variant="text"
        size="x-small"
        prepend-icon="mdi-account-arrow-left"
        class="px-0"
        @click="assignToMe"
      >
        Mir zuweisen
      </v-btn>
    </div>
    <v-autocomplete
      :model-value="selected"
      :items="userItems"
      item-value="value"
      item-title="title"
      :loading="saving"
      density="compact"
      clearable
      hide-details
      placeholder="Niemand zugewiesen"
      @update:model-value="assign"
    ></v-autocomplete>
  </div>
</template>
