<script setup lang="ts">
import CountBadge from './CountBadge.vue'

/** Title of a section inside a page, with icon and optional count (docs/STYLEGUIDE.md → Typography). */
const {
  title,
  icon = '',
  count = undefined,
} = defineProps<{ title: string; icon?: string; count?: number }>()
</script>

<template>
  <h2 class="text-title-large d-flex align-center ga-2 mb-3">
    <v-icon v-if="icon" :icon="icon" />
    {{ title }}
    <CountBadge v-if="count !== undefined" :count="count" class="ml-0" />
  </h2>
</template>
