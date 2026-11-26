<script setup lang="ts">
import { useSlots } from 'vue'

const { primaryLabel, primaryIcon = 'mdi-pencil', hasSecondary = true } = defineProps<{
  primaryLabel: string
  primaryIcon?: string
  hasSecondary?: boolean
}>()

const emit = defineEmits<{
  primary: []
}>()

const slots = useSlots()
</script>

<template>
  <div class="d-flex align-center justify-end ga-1">
    <v-btn variant="tonal" :prepend-icon="primaryIcon" @click.stop="emit('primary')">
      {{ primaryLabel }}
    </v-btn>
    <v-menu v-if="hasSecondary && slots.secondary" location="bottom end">
      <template #activator="{ props: menuProps }">
        <v-btn
          v-bind="menuProps"
          icon="mdi-dots-vertical"
          variant="text"
          aria-label="Weitere Aktionen"
          @click.stop
        />
      </template>
      <v-list density="compact">
        <slot name="secondary" />
      </v-list>
    </v-menu>
  </div>
</template>
