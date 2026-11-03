<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { useToast } from '@/composables/useToast'

/**
 * App bar control for the screen lock (workshop network only): countdown to the
 * idle auto-lock, lock now, and switching the auto-lock off for this device.
 */
const {
  secondsUntilLock,
  autoLockEnabled,
  setAutoLock,
} = defineProps<{
  /** null while no auto-lock is running */
  secondsUntilLock: number | null
  autoLockEnabled: boolean
  setAutoLock: (enabled: boolean) => Promise<boolean>
}>()

const emit = defineEmits<{ lock: [] }>()

const toast = useToast()
const saving = shallowRef(false)

const countdown = computed(() => {
  if (secondsUntilLock === null) return ''
  const minutes = Math.floor(secondsUntilLock / 60)
  const seconds = String(secondsUntilLock % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})
const soon = computed(() => secondsUntilLock !== null && secondsUntilLock <= 10)

async function toggle(enabled: boolean | null) {
  saving.value = true
  const ok = await setAutoLock(!!enabled)
  saving.value = false
  if (!ok) toast.error('Einstellung konnte nicht gespeichert werden')
}
</script>

<template>
  <v-menu location="bottom end" :close-on-content-click="false">
    <template #activator="{ props: menuProps }">
      <v-btn
        v-bind="menuProps"
        variant="text"
        :color="soon ? 'warning' : undefined"
        :prepend-icon="autoLockEnabled ? 'mdi-timer-lock-outline' : 'mdi-lock-off-outline'"
        :aria-label="
          autoLockEnabled ? `Automatische Sperre in ${countdown}` : 'Automatische Sperre ist aus'
        "
      >
        <span v-if="autoLockEnabled" class="countdown">{{ countdown }}</span>
        <span v-else class="text-body-medium">Aus</span>
      </v-btn>
    </template>

    <v-card min-width="300">
      <v-card-item prepend-icon="mdi-lock-outline" title="Bildschirmsperre" />
      <v-card-text class="pt-0">
        <v-switch
          :model-value="autoLockEnabled"
          :loading="saving"
          :disabled="saving"
          color="primary"
          label="Automatische Sperre auf diesem Gerät"
          hide-details
          @update:model-value="toggle"
        />
        <p class="text-body-small text-medium-emphasis mt-2">
          Auf dem Werkstatt-PC eingeschaltet lassen. Auf dem eigenen Gerät kannst du sie
          ausschalten; die Einstellung bleibt auf diesem Gerät gespeichert.
        </p>
      </v-card-text>
      <v-card-actions>
        <v-btn
          color="primary"
          variant="flat"
          block
          size="large"
          prepend-icon="mdi-lock"
          @click="emit('lock')"
        >
          Jetzt sperren
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<style scoped>
.countdown {
  font-variant-numeric: tabular-nums;
  min-width: 2.5rem;
}
</style>
