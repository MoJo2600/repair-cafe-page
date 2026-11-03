<script setup lang="ts">
import { computed } from 'vue'
import { personName, type NamedPerson } from '@/utils/person'

/**
 * A person, always as role icon + full name in plain text (docs/STYLEGUIDE.md → People).
 * role "author" has no icon; it follows a date in meta lines.
 */
const {
  person,
  role,
  emptyText = '–',
} = defineProps<{
  person: NamedPerson | null | undefined
  role: 'customer' | 'repairer' | 'author'
  /** Shown when there is no person, e.g. "Niemand zugewiesen". */
  emptyText?: string
}>()

const ROLE_ICON = { customer: 'mdi-account', repairer: 'mdi-account-wrench', author: '' } as const

const name = computed(() => (person ? personName(person) : emptyText))
</script>

<template>
  <span class="person-label" :class="{ 'text-medium-emphasis': !person }">
    <v-icon v-if="ROLE_ICON[role]" :icon="ROLE_ICON[role]" size="small" class="mr-1" />{{ name }}
  </span>
</template>

<style scoped>
.person-label {
  display: inline-flex;
  align-items: center;
}
</style>
