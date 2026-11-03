<script setup lang="ts">
/** Title row of a page, with optional subtitle and actions (docs/STYLEGUIDE.md → Layout). */
const { title, subtitle = '' } = defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="d-flex flex-wrap align-center ga-3 mb-4">
    <div class="flex-grow-1">
      <h1 class="text-headline-small">{{ title }}</h1>
      <div v-if="subtitle" class="text-body-medium text-medium-emphasis">{{ subtitle }}</div>
    </div>
    <div v-if="$slots.actions" class="d-flex flex-wrap ga-2">
      <slot name="actions" />
    </div>
  </div>
</template>
