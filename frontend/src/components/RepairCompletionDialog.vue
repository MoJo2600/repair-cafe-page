<template>
    <v-dialog v-model="open" max-width="720px">
        <v-card>
            <v-card-title class="d-flex align-center">
                <v-icon class="mr-2">mdi-check-circle</v-icon>
                {{ title }}
            </v-card-title>

            <v-card-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                    {{ message }}
                </v-alert>

                <v-form ref="formRef" v-model="formValid">
                    <v-textarea
v-model="description" label="Was wurde repariert?" rows="3" required
                        :rules="[v => !!String(v || '').trim() || 'Beschreibung ist erforderlich']"></v-textarea>

                    <v-text-field
v-model.number="duration" label="Gesamtdauer in Minuten" type="number" required
                        persistent-hint :rules="[
                            v => v !== null && v !== undefined && v !== '' || 'Dauer ist erforderlich',
                            v => Number(v) >= 0 || 'Dauer muss 0 oder groesser sein'
                        ]"></v-text-field>

                    <v-alert v-if="!hasAnyVdeTest" type="warning" variant="tonal" class="mb-4">
                        Es liegt noch kein VDE-Test vor. Ein Test wird empfohlen, ist aber optional.
                    </v-alert>

                    <v-alert v-else-if="lastVdeTestPassed" type="success" variant="tonal" class="mb-4">
                        Es liegt bereits ein bestandener VDE-Test vor. Du kannst trotzdem einen weiteren Test erfassen,
                        wenn du möchtest.
                    </v-alert>

                    <v-alert v-else-if="!lastVdeTestPassed" type="error" variant="tonal" class="mb-4">
                        Der letzte VDE-Test ist nicht bestanden. Ein neuer Test ist erforderlich.
                    </v-alert>

                    <v-switch
v-model="needsVdeTest" class="mt-4" color="primary" :label="vdeSwitchLabel"
                        :readonly="isVdeTestMandatory" :disabled="isVdeTestMandatory" hide-details></v-switch>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-btn variant="text" :disabled="loading" @click="closeDialog">{{ cancelText }}</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="primary" :loading="loading" @click="confirmDialog">{{ confirmText }}</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { VForm } from 'vuetify/components'

const open = defineModel<boolean>({ required: true })
const description = defineModel<string>('description', { required: true })
const duration = defineModel<number | null>('duration', { required: true })
const needsVdeTest = defineModel<boolean>('needsVdeTest', { default: false })

const props = withDefaults(defineProps<{
    suggestedDuration?: number
    hasAnyVdeTest?: boolean
    lastVdeTestPassed?: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
}>(), {
    suggestedDuration: 0,
    hasAnyVdeTest: false,
    lastVdeTestPassed: false,
    title: 'Reparatur abschliessen',
    message: 'Bitte erfasse die Abschlussdaten fuer die erfolgreiche Reparatur.',
    confirmText: 'Weiter',
    cancelText: 'Abbrechen',
    loading: false
})

const emit = defineEmits<{
    (e: 'confirm', value: { description: string; duration: number; needsVdeTest: boolean }): void
}>()

const formRef = ref<InstanceType<typeof VForm> | null>(null)
const formValid = ref(false)
const isVdeTestMandatory = computed(() => props.hasAnyVdeTest && !props.lastVdeTestPassed)
const vdeSwitchLabel = computed(() => {
    if (isVdeTestMandatory.value) {
        return 'VDE-Test ist erforderlich'
    }
    return props.hasAnyVdeTest ? 'VDE-Test jetzt erfassen' : 'VDE-Test jetzt erfassen (empfohlen)'
})

// A failed last VDE test forces a new one while the dialog is open.
watch([open, isVdeTestMandatory], ([isOpen, mandatory]) => {
    if (isOpen && mandatory) needsVdeTest.value = true
}, { immediate: true })

watch(open, (isOpen) => {
    if (!isOpen) return
    if (duration.value === null) duration.value = props.suggestedDuration
    formRef.value?.resetValidation()
})

function closeDialog() {
    open.value = false
}

async function confirmDialog() {
    if (!formRef.value) return

    const { valid } = await formRef.value.validate()
    if (!valid || duration.value === null) return

    emit('confirm', {
        description: description.value.trim(),
        duration: Number(duration.value),
        needsVdeTest: needsVdeTest.value,
    })
}
</script>
