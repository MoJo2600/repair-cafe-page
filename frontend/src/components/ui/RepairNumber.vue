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
    <span class="font-weight-bold" :class="size >= 48 ? 'text-title-medium' : 'text-label-large'">
      {{ id }}
    </span>
  </v-avatar>
</template>
