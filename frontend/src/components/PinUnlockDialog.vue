<script setup lang="ts">
import { onScopeDispose, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { redirectTarget } from '@/utils/redirect'

/**
 * Helper change on the shared PC: 6-digit PIN on a large keypad for touch,
 * digits / Backspace / Enter on a keyboard. Submits on the sixth digit.
 */
const open = defineModel<boolean>({ required: true })

const PIN_LENGTH = 6
const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'clear', '0', 'back'] as const

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const pin = shallowRef('')
const error = shallowRef('')
const submitting = shallowRef(false)

watch(open, (isOpen) => {
  pin.value = ''
  error.value = ''
  if (isOpen) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
})
onScopeDispose(() => window.removeEventListener('keydown', onKeydown))

function press(key: (typeof KEYS)[number]) {
  if (submitting.value) return
  error.value = ''
  if (key === 'back') pin.value = pin.value.slice(0, -1)
  else if (key === 'clear') pin.value = ''
  else if (pin.value.length < PIN_LENGTH) {
    pin.value += key
    if (pin.value.length === PIN_LENGTH) void submit()
  }
}

function onKeydown(event: KeyboardEvent) {
  if (/^[0-9]$/.test(event.key)) press(event.key as (typeof KEYS)[number])
  else if (event.key === 'Backspace') press('back')
  else if (event.key === 'Enter') void submit()
  else return
  event.preventDefault()
}

async function submit() {
  if (pin.value.length !== PIN_LENGTH || submitting.value) return
  submitting.value = true
  const result = await authStore.unlock(pin.value)
  pin.value = ''
  submitting.value = false
  if (result.success) {
    open.value = false
    await router.replace(redirectTarget(route.query))
    return
  }
  if (result.sessionEnded) {
    // Too many wrong PINs end the whole session on the server
    open.value = false
    await router.replace({ name: 'Login', query: { error: 'pin_locked', redirect: redirectTarget(route.query) } })
    return
  }
  error.value = result.error ?? 'PIN ungültig'
}
</script>

<template>
  <v-dialog v-model="open" max-width="400">
    <v-card>
      <v-card-item prepend-icon="mdi-dialpad" title="PIN eingeben" subtitle="Helferwechsel">
        <template #append>
          <v-btn icon="mdi-close" variant="text" aria-label="PIN-Eingabe schließen" @click="open = false" />
        </template>
      </v-card-item>

      <v-card-text>
        <div class="d-flex justify-center ga-3 my-4" role="status" :aria-label="`${pin.length} von 6 Ziffern`">
          <span
            v-for="n in PIN_LENGTH"
            :key="n"
            class="pin-dot"
            :class="{ 'pin-dot--filled': n <= pin.length, 'pin-dot--error': !!error }"
          />
        </div>

        <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-4">
          {{ error }}
        </v-alert>

        <div class="keypad">
          <v-btn
            v-for="key in KEYS"
            :key="key"
            :disabled="submitting"
            :aria-label="key === 'back' ? 'Letzte Ziffer löschen' : key === 'clear' ? 'Alles löschen' : key"
            variant="tonal"
            height="64"
            class="text-headline-small"
            @click="press(key)"
          >
            <v-icon v-if="key === 'back'" icon="mdi-backspace-outline" />
            <v-icon v-else-if="key === 'clear'" icon="mdi-close-circle-outline" />
            <template v-else>{{ key }}</template>
          </v-btn>
        </div>

        <v-progress-linear v-if="submitting" indeterminate color="primary" class="mt-4" />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.keypad {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.pin-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid rgb(var(--v-theme-primary));
}

.pin-dot--filled {
  background: rgb(var(--v-theme-primary));
}

.pin-dot--error {
  border-color: rgb(var(--v-theme-error));
}
</style>
