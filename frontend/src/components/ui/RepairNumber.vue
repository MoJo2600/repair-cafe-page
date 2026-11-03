<script setup lang="ts">
import { getRepairStatusColor } from '@/domain/repairStatus'

/** The repair number as avatar in its status color (docs/STYLEGUIDE.md → Repair identity). */
const { id, status = null, size = 48 } = defineProps<{
  id: number | string | undefined
  status?: string | null
  size?: number
}>()
</script>

<template>
  <v-avatar :color="getRepairStatusColor(status ?? undefined)" :size="size">
    <span
      v-if="id !== undefined && id !== null"
      class="font-weight-bold"
      :class="size >= 48 ? 'text-title-medium' : 'text-label-large'"
    >
      {{ id }}
    </span>
    <!-- Not saved yet: no number -->
    <v-icon v-else icon="mdi-clipboard-plus-outline" />
  </v-avatar>
</template>
