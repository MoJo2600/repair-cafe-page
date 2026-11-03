<script setup lang="ts">
/** A count next to a tab or section title (docs/STYLEGUIDE.md → Chips). */
const { count } = defineProps<{ count: number }>()
</script>

<template>
  <v-chip size="x-small" variant="tonal" class="ml-2">{{ count }}</v-chip>
</template>
