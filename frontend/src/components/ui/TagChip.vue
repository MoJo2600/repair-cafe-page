<script setup lang="ts">
/** A category-like value, e.g. the repair type (docs/STYLEGUIDE.md → Chips). Neutral. */
const { label, icon = 'mdi-tag-outline' } = defineProps<{ label: string; icon?: string }>()
</script>

<template>
  <v-chip :prepend-icon="icon" size="small" variant="tonal">{{ label }}</v-chip>
</template>
