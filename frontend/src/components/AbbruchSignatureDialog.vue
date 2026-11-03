<template>
    <ResponsiveDialog v-model="open" max-width="680px" persistent>
        <v-card>
            <v-card-title class="d-flex align-center">
                <v-icon class="mr-2" color="error">mdi-alert-octagon</v-icon>
                Gerät darf nicht mehr benutzt werden
            </v-card-title>

            <v-card-text>
                <v-alert type="error" variant="tonal" class="mb-4" icon="mdi-alert-octagon">
                    <strong>Das Gerät darf nicht mehr benutzt werden.</strong> Anschluss sowie Benutzung dieses Gerätes
                    (auch durch Dritte) ist in keinem Fall zulässig. Ich bestätige durch meine Unterschrift, darüber
                    informiert worden zu sein.
                </v-alert>

                <v-divider class="my-4" />

                <p class="text-body-medium text-medium-emphasis mb-3">
                    Bitte hier unterschreiben zur Bestätigung:
                </p>

                <SignaturePad v-model="signature" :error="signatureError" />
            </v-card-text>

            <v-card-actions>
                <v-btn variant="text" @click="closeDialog">Abbrechen</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="error" :loading="loading" @click="confirmDialog">
                    <v-icon start>mdi-check</v-icon>
                    Bestätigen
                </v-btn>
            </v-card-actions>
        </v-card>
    </ResponsiveDialog>
</template>

<script setup lang="ts">
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'
import { ref, watch } from 'vue'
import SignaturePad from '@/components/SignaturePad.vue'

const open = defineModel<boolean>({ required: true })

withDefaults(defineProps<{
    loading?: boolean
}>(), {
    loading: false
})

const emit = defineEmits<{
    (e: 'confirm', value: { signature: string }): void
}>()

const signature = ref<string | null>(null)
const signatureError = ref('')

watch(open, (isOpen) => {
    if (isOpen) {
        signature.value = null
        signatureError.value = ''
    }
})

watch(signature, (value) => {
    if (value) signatureError.value = ''
})

function closeDialog() {
    open.value = false
}

function confirmDialog() {
    if (!signature.value) {
        signatureError.value = 'Unterschrift ist erforderlich'
        return
    }
    emit('confirm', { signature: signature.value })
}
</script>
