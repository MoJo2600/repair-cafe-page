<template>
    <v-dialog :model-value="modelValue" max-width="600px" @update:model-value="onDialogToggle">
        <v-card>
            <v-card-title class="d-flex align-center">
                <v-icon class="mr-2">mdi-account</v-icon>
                {{ title }}
            </v-card-title>

            <v-card-text>
                <slot name="context"></slot>

                <v-alert type="info" variant="tonal" class="mb-4">
                    {{ message }}
                </v-alert>

                <v-form ref="formRef" v-model="formValid">
                    <v-select v-model="localUserId" :items="userStore.users" item-title="displayName" item-value="id"
                        label="Reparateur" prepend-icon="mdi-account" required :loading="userStore.loading"
                        :rules="[v => !!v || 'Name des Reparateurs ist erforderlich']">
                        <template #item="{ props, item }">
                            <v-list-item v-bind="props"
                                :title="`${item.raw.vorname} ${item.raw.nachname}`"
                                :subtitle="item.raw.email"></v-list-item>
                        </template>
                        <template #selection="{ item }">
                            {{ item.raw.vorname }} {{ item.raw.nachname }}
                        </template>
                    </v-select>
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
import { ref, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'

const userStore = useUserStore()

const props = withDefaults(defineProps<{
    modelValue: boolean
    userId: number | null
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
}>(), {
    title: 'Reparatur starten',
    message: 'Für diesen Statuswechsel muss ein Reparateur angegeben werden.',
    confirmText: 'Weiter',
    cancelText: 'Abbrechen',
    loading: false
})

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'update:userId', value: number | null): void
    (e: 'confirm', value: number): void
}>()

const formRef = ref<any>(null)
const formValid = ref(false)
const localUserId = ref<number | null>(props.userId)

onMounted(() => {
    if (!userStore.loaded) userStore.fetchUsers()
})

watch(() => props.userId, (value) => {
    localUserId.value = value
})

watch(localUserId, (value) => {
    emit('update:userId', value)
})

watch(() => props.modelValue, (isOpen) => {
    if (isOpen) {
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
    if (!valid || !localUserId.value) return

    emit('confirm', localUserId.value)
}
</script>
