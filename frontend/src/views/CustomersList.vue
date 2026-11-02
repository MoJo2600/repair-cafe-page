<template>
    <v-container fluid class="pa-4">
        <!-- Header -->
        <v-row class="mb-4 align-center">
            <v-col>
                <h1 class="text-headline-small font-weight-bold">Kunden</h1>
            </v-col>
            <v-col cols="auto">
                <v-btn color="success" prepend-icon="mdi-account-plus" class="mr-2" @click="openCreateDialog">
                    Neuer Kunde
                </v-btn>
                <v-btn color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="loadCustomers">
                    Aktualisieren
                </v-btn>
            </v-col>
        </v-row>

        <!-- Filter row -->
        <v-row class="mb-2 align-center">
            <v-col cols="12" sm="4">
                <v-text-field
v-model="search" prepend-inner-icon="mdi-magnify" label="Suchen…" density="compact"
                    clearable hide-details />
            </v-col>
            <v-spacer />
            <v-col cols="auto" class="text-body-medium text-medium-emphasis">
                Gesamt: {{ customers.length }}
            </v-col>
        </v-row>

        <!-- Customers table -->
        <v-card>
            <v-data-table
:headers="headers" :items="customers" :loading="loading" :search="search" :items-per-page="15"
                hover @click:row="(_e: MouseEvent, { item }: { item: any }) => openEditDialog(item)">
                <template #item.repair_count="{ item }">
                    <v-chip
:color="item.repair_count ? 'primary' : 'grey'" size="small" variant="tonal"
                        style="cursor: pointer" @click.stop="goToRepairs(item)">
                        {{ item.repair_count ?? 0 }}
                    </v-chip>
                </template>

                <template #item.created_at="{ item }">
                    {{ formatDate(item.created_at) }}
                </template>

                <template #item.actions="{ item }">
                    <v-btn
icon="mdi-pencil" size="small" variant="text" density="compact"
                        @click.stop="openEditDialog(item)" />
                    <v-btn
v-if="authStore.isAdmin" icon="mdi-delete" size="small" variant="text" density="compact" color="error"
                        @click.stop="openDeleteDialog(item.id)" />
                </template>

                <template #loading>
                    <v-skeleton-loader type="table-row@10" />
                </template>

                <template #no-data>
                    <v-alert type="info" class="ma-4">
                        Noch keine Kunden vorhanden.
                    </v-alert>
                </template>
            </v-data-table>
        </v-card>

        <!-- Create / Edit Dialog -->
        <v-dialog v-model="editDialog" max-width="500" persistent>
            <v-card>
                <v-card-title class="text-headline-small">
                    <v-icon :icon="editedCustomer.id ? 'mdi-account-edit' : 'mdi-account-plus'" class="mr-2" />
                    {{ editedCustomer.id ? 'Kunde bearbeiten' : 'Neuer Kunde' }}
                </v-card-title>
                <v-card-text>
                    <v-form ref="editForm" v-model="editFormValid">
                        <v-row density="compact">
                            <v-col cols="12">
                                <v-text-field
v-model="editedCustomer.vorname" label="Vorname *"
                                    required :rules="[v => !!v || 'Vorname ist erforderlich']" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field
v-model="editedCustomer.nachname" label="Nachname *"
                                    required :rules="[v => !!v || 'Nachname ist erforderlich']" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field v-model="editedCustomer.telefon" label="Telefon" />
                            </v-col>
                            <v-col cols="12">
                                <v-text-field
v-model="editedCustomer.email" label="E-Mail (optional)" type="email"
                                    :rules="[v => !v || /.+@.+\..+/.test(v) || 'E-Mail muss gültig sein']" />
                            </v-col>
                        </v-row>
                    </v-form>
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" :disabled="saving" @click="closeEditDialog">Abbrechen</v-btn>
                    <v-btn
color="primary" variant="elevated" :loading="saving" :disabled="!editFormValid"
                        @click="saveCustomer">
                        Speichern
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="deleteDialog" max-width="420">
            <v-card>
                <v-card-title class="text-title-large">
                    <v-icon color="error" class="mr-2">mdi-account-remove</v-icon>
                    Kunden löschen?
                </v-card-title>
                <v-card-text>
                    Möchten Sie diesen Kunden wirklich löschen? Bestehende Reparaturen bleiben erhalten,
                    werden aber nicht mehr mit diesem Kunden verknüpft.
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" :disabled="deleting" @click="deleteDialog = false">Abbrechen</v-btn>
                    <v-btn color="error" variant="elevated" :loading="deleting" @click="confirmDelete">Löschen</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

    </v-container>
</template>

<script setup lang="ts">
import { api } from '@/api/client'
import type { CustomerWithRepairCountResponse as CustomerResponse } from '@/api/types'
import { ref, onMounted } from 'vue'
import type { VForm } from 'vuetify/components'
import { formatDate } from '@/utils/date'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const router = useRouter()
const authStore = useAuthStore()

const customers = ref<CustomerResponse[]>([])
const loading = ref(false)
const search = ref('')


const headers = [
    { title: 'ID', key: 'id', sortable: true },
    { title: 'Vorname', key: 'vorname', sortable: true },
    { title: 'Nachname', key: 'nachname', sortable: true },
    { title: 'Telefon', key: 'telefon', sortable: false },
    { title: 'E-Mail', key: 'email', sortable: false },
    { title: 'Reparaturen', key: 'repair_count', sortable: true },
    { title: 'Erstellt am', key: 'created_at', sortable: true },
    { title: 'Aktionen', key: 'actions', sortable: false },
]

// Edit / create dialog
const editDialog = ref(false)
const editFormValid = ref(false)
const saving = ref(false)
const editForm = ref<InstanceType<typeof VForm> | null>(null)

type EditableCustomer = { id?: number; vorname: string; nachname: string; telefon: string; email: string }
const blankCustomer = (): EditableCustomer => ({ vorname: '', nachname: '', telefon: '', email: '' })
const editedCustomer = ref<EditableCustomer>(blankCustomer())

// Delete dialog
const deleteDialog = ref(false)
const deleteTargetId = ref<number | null>(null)
const deleting = ref(false)

async function loadCustomers() {
    loading.value = true
    try {
        const res = await api.listCustomers()
        customers.value = res.data ?? []
    } catch (err: any) {
        toast.error(err.message || 'Fehler beim Laden der Kunden')
    } finally {
        loading.value = false
    }
}

function goToRepairs(customer: CustomerResponse) {
    router.push({ path: '/repairs', query: { customer_id: customer.id, customer_name: `${customer.vorname} ${customer.nachname}`, status: 'all' } })
}

function openCreateDialog() {
    editedCustomer.value = blankCustomer()
    editDialog.value = true
}

function openEditDialog(customer: CustomerResponse) {
    editedCustomer.value = {
        id: customer.id,
        vorname: customer.vorname,
        nachname: customer.nachname,
        telefon: customer.telefon ?? '',
        email: customer.email ?? '',
    }
    editDialog.value = true
}

function closeEditDialog() {
    editDialog.value = false
    setTimeout(() => { editedCustomer.value = blankCustomer() }, 200)
}

async function saveCustomer() {
    if (!editForm.value) return
    const { valid } = await editForm.value.validate()
    if (!valid) return

    saving.value = true
    try {
        const payload = {
            vorname: editedCustomer.value.vorname,
            nachname: editedCustomer.value.nachname,
            telefon: editedCustomer.value.telefon || null,
            email: editedCustomer.value.email || null,
        }
        if (editedCustomer.value.id) {
            await api.updateCustomer({ customerId: editedCustomer.value.id }, payload)
            toast.success('Kunde aktualisiert')
        } else {
            await api.createCustomer(payload)
            toast.success('Kunde erstellt')
        }
        closeEditDialog()
        await loadCustomers()
    } catch (err: any) {
        toast.error(err.message || 'Fehler beim Speichern')
    } finally {
        saving.value = false
    }
}

function openDeleteDialog(id?: number) {
    if (!id) return
    deleteTargetId.value = id
    deleteDialog.value = true
}

async function confirmDelete() {
    if (!deleteTargetId.value) return
    deleting.value = true
    try {
        await api.deleteCustomer({ customerId: deleteTargetId.value })
        deleteDialog.value = false
        toast.success('Kunde gelöscht')
        await loadCustomers()
    } catch (err) {
        toast.error('Fehler beim Löschen: ' + (err as Error).message)
    } finally {
        deleting.value = false
        deleteTargetId.value = null
    }
}

onMounted(loadCustomers)
</script>
