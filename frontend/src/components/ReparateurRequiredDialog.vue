<template>
    <ResponsiveDialog v-model="open" max-width="600px">
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
                    <v-autocomplete
                        v-model="userId"
                        :items="userStore.users"
                        :item-title="getUserTitle"
                        item-value="id"
                        label="Reparateur"
                        prepend-icon="mdi-account"
                        required
                        :loading="userStore.loading"
                        :rules="[v => !!v || 'Name des Reparateurs ist erforderlich']"
                    >
                        <template #item="{ props: itemProps, item }">
                            <v-list-item
                                v-bind="itemProps"
                                :title="`${item.vorname} ${item.nachname}`"
                                :subtitle="item.email"></v-list-item>
                        </template>
                        <template #selection="{ item }">
                            {{ item.vorname }} {{ item.nachname }}
                        </template>
                    </v-autocomplete>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-btn variant="text" :disabled="loading" @click="closeDialog">{{ cancelText }}</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="primary" :loading="loading" @click="confirmDialog">{{ confirmText }}</v-btn>
            </v-card-actions>
        </v-card>
    </ResponsiveDialog>
</template>

<script setup lang="ts">
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'
import { ref, watch, onMounted } from 'vue'
import type { VForm } from 'vuetify/components'
import { useUserStore } from '@/stores/userStore'
import type { UserResponse } from '@/api/types'

const userStore = useUserStore()

const open = defineModel<boolean>({ required: true })
const userId = defineModel<number | null>('userId', { required: true })

withDefaults(defineProps<{
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
    (e: 'confirm', value: number): void
}>()

const formRef = ref<InstanceType<typeof VForm> | null>(null)
const formValid = ref(false)

function getUserTitle(user: UserResponse): string {
    return [user.vorname, user.nachname].filter(Boolean).join(' ') || `User #${user.id}`
}

onMounted(() => {
    if (!userStore.loaded) userStore.fetchUsers()
})

watch(open, (isOpen) => {
    if (isOpen) formRef.value?.resetValidation()
})

function closeDialog() {
    open.value = false
}

async function confirmDialog() {
    if (!formRef.value) return

    const { valid } = await formRef.value.validate()
    if (!valid || !userId.value) return

    emit('confirm', userId.value)
}
</script>
