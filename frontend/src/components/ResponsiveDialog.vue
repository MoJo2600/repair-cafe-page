<script setup lang="ts">
import { useDisplay } from 'vuetify'

/**
 * v-dialog that fills the screen on phones and portrait tablets, where a centered
 * dialog leaves little room for forms and on-screen keyboards. Other v-dialog
 * props (max-width, persistent, ...) fall through to the v-dialog.
 */
const open = defineModel<boolean>({ required: true })
const { smAndDown } = useDisplay()
</script>

<template>
  <v-dialog
    v-model="open"
    :fullscreen="smAndDown"
    :transition="smAndDown ? 'dialog-bottom-transition' : undefined"
    scrollable
  >
    <slot />
  </v-dialog>
</template>
