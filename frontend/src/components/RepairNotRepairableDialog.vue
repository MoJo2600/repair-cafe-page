<template>
    <v-dialog v-model="open" max-width="640px">
        <v-card>
            <v-card-title class="d-flex align-center">
                <v-icon class="mr-2" color="error">mdi-close-circle</v-icon>
                {{ title }}
            </v-card-title>

            <v-card-text>
                <v-alert type="warning" variant="tonal" class="mb-4">
                    {{ message }}
                </v-alert>

                <v-form ref="formRef" v-model="formValid">
                    <v-textarea
v-model="localDescription" label="Warum konnte die Reparatur nicht durchgeführt werden?"
                        rows="3" required
                        :rules="[v => !!String(v || '').trim() || 'Begründung ist erforderlich']"></v-textarea>

                    <v-select
v-model="localStatusDetail" :items="statusDetailOptions" label="Abschlussgrund"
                        clearable></v-select>

                    <v-text-field
v-model.number="localDuration" label="Gesamtdauer in Minuten" type="number" required
                        persistent-hint :rules="[
                            v => v !== null && v !== undefined && v !== '' || 'Dauer ist erforderlich',
                            v => Number(v) >= 0 || 'Dauer muss 0 oder groesser sein'
                        ]"></v-text-field>                        
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-btn variant="text" :disabled="loading" @click="closeDialog">{{ cancelText }}</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="error" :loading="loading" :disabled="!formValid" @click="confirmDialog">{{ confirmText
                    }}</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { VForm } from 'vuetify/components'
import { REPAIR_STATUS_DETAIL_OPTIONS } from '@/stores/repairStore'

const open = defineModel<boolean>({ required: true })

const props = withDefaults(defineProps<{
    suggestedDuration?: number
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
}>(), {
    suggestedDuration: 0,
    title: 'Reparatur nicht möglich',
    message: 'Bitte gib an, warum die Reparatur nicht durchgeführt werden konnte.',
    confirmText: 'Abschließen',
    cancelText: 'Abbrechen',
    loading: false
})

const emit = defineEmits<{
    (e: 'confirm', value: { description: string; statusDetail: string; duration: number }): void
}>()

const formRef = ref<InstanceType<typeof VForm> | null>(null)
const formValid = ref(false)
// Draft values, reset each time the dialog opens and sent with "confirm"
const localDescription = ref('')
const localStatusDetail = ref('')
const localDuration = ref<number>(props.suggestedDuration)
const statusDetailOptions = REPAIR_STATUS_DETAIL_OPTIONS['Nicht Repariert']

watch(open, (isOpen) => {
    if (isOpen) {
        localDescription.value = ''
        localStatusDetail.value = ''
        localDuration.value = props.suggestedDuration
        formRef.value?.resetValidation()
    }
})

function closeDialog() {
    open.value = false
}

async function confirmDialog() {
    if (!formRef.value) return
    const { valid } = await formRef.value.validate()
    if (!valid) return

    emit('confirm', {
        description: localDescription.value.trim(),
        statusDetail: localStatusDetail.value || '',
        duration: Number(localDuration.value)
    })
}
</script>
