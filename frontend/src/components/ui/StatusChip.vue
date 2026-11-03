<script setup lang="ts">
import { computed } from 'vue'
import { getRepairStatusColor, getRepairStatusIcon } from '@/domain/repairStatus'

/**
 * A status from a fixed set (docs/STYLEGUIDE.md → Chips).
 * Pass `status` for a repair status, or `label`/`color`/`icon` for other states
 * (e.g. active / inactive).
 */
const {
  status = null,
  label = '',
  color = undefined,
  icon = undefined,
  size = 'small',
} = defineProps<{
  status?: string | null
  label?: string
  color?: string
  icon?: string
  size?: 'x-small' | 'small' | 'default'
}>()

const chip = computed(() =>
  status
    ? { text: status, color: getRepairStatusColor(status), icon: getRepairStatusIcon(status) }
    : { text: label, color, icon }
)
</script>

<template>
  <v-chip :color="chip.color" :prepend-icon="chip.icon" :size="size" variant="tonal" label>
    {{ chip.text }}
  </v-chip>
</template>
