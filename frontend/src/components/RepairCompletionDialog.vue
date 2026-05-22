<template>
    <v-dialog :model-value="modelValue" max-width="720px" @update:model-value="onDialogToggle">
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
                    <v-textarea v-model="localDescription" label="Was wurde repariert?" rows="3" required
                        :rules="[v => !!String(v || '').trim() || 'Beschreibung ist erforderlich']"></v-textarea>

                    <v-text-field v-model.number="localDuration" label="Gesamtdauer in Minuten" type="number" required
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

                    <v-switch v-model="localNeedsVdeTest" class="mt-4" color="primary" :label="vdeSwitchLabel"
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

const props = withDefaults(defineProps<{
    modelValue: boolean
    description: string
    duration: number | null
    suggestedDuration?: number
    hasAnyVdeTest?: boolean
    lastVdeTestPassed?: boolean
    needsVdeTest?: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
}>(), {
    suggestedDuration: 0,
    hasAnyVdeTest: false,
    lastVdeTestPassed: false,
    needsVdeTest: false,
    title: 'Reparatur abschliessen',
    message: 'Bitte erfasse die Abschlussdaten fuer die erfolgreiche Reparatur.',
    confirmText: 'Weiter',
    cancelText: 'Abbrechen',
    loading: false
})

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'update:description', value: string): void
    (e: 'update:duration', value: number | null): void
    (e: 'update:needsVdeTest', value: boolean): void
    (e: 'confirm', value: { description: string; duration: number; needsVdeTest: boolean }): void
}>()

const formRef = ref<any>(null)
const formValid = ref(false)
const localDescription = ref(props.description || '')
const localDuration = ref<number | null>(props.duration ?? props.suggestedDuration ?? 0)
const localNeedsVdeTest = ref(Boolean(props.needsVdeTest))
const isVdeTestMandatory = computed(() => props.hasAnyVdeTest && !props.lastVdeTestPassed)
const vdeSwitchLabel = computed(() => {
    if (isVdeTestMandatory.value) {
        return 'VDE-Test ist erforderlich'
    }
    return props.hasAnyVdeTest ? 'VDE-Test jetzt erfassen' : 'VDE-Test jetzt erfassen (empfohlen)'
})

watch(() => props.description, (value) => {
    localDescription.value = value || ''
})

watch(() => props.duration, (value) => {
    localDuration.value = value ?? props.suggestedDuration ?? 0
})

watch(() => props.suggestedDuration, (value) => {
    if (props.modelValue) {
        localDuration.value = props.duration ?? value ?? 0
    }
})

watch(() => props.needsVdeTest, (value) => {
    localNeedsVdeTest.value = Boolean(value)
})

watch(() => isVdeTestMandatory, (mandatory) => {
    if (mandatory) {
        localNeedsVdeTest.value = true
    }
}, { immediate: true })

watch(localDescription, (value) => {
    emit('update:description', value)
})

watch(localDuration, (value) => {
    emit('update:duration', value)
})

watch(localNeedsVdeTest, (value) => {
    emit('update:needsVdeTest', value)
})

watch(() => props.modelValue, (isOpen) => {
    if (isOpen) {
        localDescription.value = props.description || ''
        localDuration.value = props.duration ?? props.suggestedDuration ?? 0
        formRef.value?.resetValidation()
    }
})

function onDialogToggle(value: boolean) {
    emit('update:modelValue', value)
}

function closeDialog() {
    emit('update:modelValue', false)
}

async function confirmDialog() {
    if (!formRef.value) return

    const { valid } = await formRef.value.validate()
    if (!valid || localDuration.value === null) return

    emit('confirm', {
        description: localDescription.value.trim(),
        duration: Number(localDuration.value),
        needsVdeTest: localNeedsVdeTest.value,
    })
}
</script>
