<script setup lang="ts">
import StatusChip from './StatusChip.vue'
import TagChip from './TagChip.vue'

/**
 * The meta row of a repair (docs/STYLEGUIDE.md → Repair identity): status, then
 * category, always in this order and always right below the title.
 * Leave out `status` where the context already shows it (e.g. a status section).
 */
const { status = null, category = null } = defineProps<{
  status?: string | null
  category?: string | null
}>()
</script>

<template>
  <div v-if="status || category" class="d-flex flex-wrap align-center ga-2">
    <StatusChip v-if="status" :status="status" />
    <TagChip v-if="category" :label="category" />
    <slot />
  </div>
</template>
