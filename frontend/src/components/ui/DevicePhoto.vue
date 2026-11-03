<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { categoryIcon } from '@/domain/repairCategory'

/**
 * Picture of a device (docs/STYLEGUIDE.md → Repair identity): the device photo,
 * or a placeholder with the category's icon when there is none (or it fails to load).
 */
const {
  src = null,
  category = null,
  height = 160,
} = defineProps<{
  src?: string | null
  category?: string | null
  height?: number | string
}>()

const failed = shallowRef(false)
watch(
  () => src,
  () => {
    failed.value = false
  }
)

const showPhoto = computed(() => !!src && !failed.value)
// Scale the icon with a pixel height; relative heights ("100%") get a medium icon
const iconSize = computed(() => {
  const px = Number(height)
  return Number.isFinite(px) ? Math.max(32, Math.min(96, px / 2.5)) : 64
})
</script>

<template>
  <v-img
    v-if="showPhoto"
    :src="src ?? undefined"
    :height="height"
    cover
    class="device-photo"
    :alt="category ? `Foto des Geräts (${category})` : 'Foto des Geräts'"
    @error="failed = true"
  />
  <v-sheet
    v-else
    :height="height"
    color="surface-light"
    class="device-photo d-flex flex-column align-center justify-center ga-1"
    role="img"
    :aria-label="category ? `Kein Foto, Kategorie ${category}` : 'Kein Foto'"
  >
    <v-icon :icon="categoryIcon(category)" :size="iconSize" class="text-medium-emphasis" />
    <span v-if="category" class="text-body-small text-medium-emphasis">{{ category }}</span>
  </v-sheet>
</template>

<style scoped>
.device-photo {
  border-radius: 4px;
}
</style>
