<script setup lang="ts">
import { computed } from 'vue'

/**
 * Date field in German format, independent of the browser language (docs/STYLEGUIDE.md).
 * The model stays an API date string, "YYYY-MM-DD".
 */
const date = defineModel<string>({ required: true })

const pad = (n: number) => String(n).padStart(2, '0')

const value = computed<Date | null>({
  get: () => (date.value ? new Date(`${date.value.slice(0, 10)}T00:00:00`) : null),
  set: (d) => {
    date.value = d ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` : ''
  },
})
</script>

<template>
  <v-date-input
    v-model="value"
    prepend-icon=""
    prepend-inner-icon="mdi-calendar"
    input-format="dd.mm.yyyy"
  />
</template>
