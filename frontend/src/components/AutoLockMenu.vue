<script setup lang="ts">
import { shallowRef } from 'vue'
import { useToast } from '@/composables/useToast'

/** App-bar overflow menu for the shared screen's automatic lock preference. */
const { autoLockEnabled, setAutoLock } = defineProps<{
  autoLockEnabled: boolean
  setAutoLock: (enabled: boolean) => Promise<boolean>
}>()

const toast = useToast()
const saving = shallowRef(false)

async function toggle(enabled: boolean | null) {
  saving.value = true
  const ok = await setAutoLock(!!enabled)
  saving.value = false
  if (!ok) toast.error('Einstellung konnte nicht gespeichert werden')
  else toast.success('Automatische Sperre aktualisiert')
}
</script>

<template>
  <v-menu location="bottom end" :close-on-content-click="false">
    <template #activator="{ props: menuProps }">
      <v-btn
        v-bind="menuProps"
        icon="mdi-dots-vertical"
        variant="text"
        aria-label="Weitere Bildschirmsperren-Einstellungen"
      />
    </template>

    <v-card min-width="320">
      <v-card-item prepend-icon="mdi-lock-clock" title="Automatische Sperre" />
      <v-card-text>
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
          Die Einstellung gilt nur für dieses Gerät. Manuelles Sperren bleibt immer möglich.
        </p>
      </v-card-text>
    </v-card>
  </v-menu>
</template>
