<template>
    <v-container fluid class="pa-4">
        <v-row align="center" class="mb-4">
            <v-col>
                <h1 class="text-h5 font-weight-bold">Einstellungen</h1>
            </v-col>
        </v-row>

        <!-- Haftungserklärung / Disclaimer Template -->
        <v-card class="mb-6">
            <v-card-title class="d-flex align-center justify-space-between">
                <span>Haftungserklärung (Vorlage)</span>
            </v-card-title>
            <v-card-text>
                <p class="text-body-2 text-medium-emphasis mb-4">
                    Laden Sie eine eigene PDF-Vorlage hoch. Die Datei muss die AcroForm-Felder
                    <strong>date</strong> und <strong>signature</strong> enthalten. Feld <strong>name</strong> ist
                    optional. Die neue Vorlage wird sofort ohne Neustart des Servers aktiv.
                </p>
                <v-row align="center" class="ga-4">
                    <v-col cols="12" sm="auto">
                        <v-btn color="primary" variant="outlined" prepend-icon="mdi-file-pdf-box"
                            href="/api/config/disclaimer" target="_blank">
                            Aktuelle Vorlage anzeigen
                        </v-btn>
                    </v-col>
                    <v-col cols="12" sm>
                        <v-file-input v-model="disclaimerFile" label="Neue PDF-Vorlage hochladen"
                            accept=".pdf,application/pdf" prepend-icon="mdi-upload" :error-messages="disclaimerError"
                            hide-details="auto" density="comfortable" @update:model-value="disclaimerError = ''" />
                    </v-col>
                    <v-col cols="12" sm="auto">
                        <v-btn color="primary" :loading="disclaimerUploading" :disabled="!disclaimerFile"
                            @click="uploadDisclaimer">
                            Hochladen
                        </v-btn>
                    </v-col>
                </v-row>
                <v-alert v-if="disclaimerSuccess" type="success" variant="tonal" density="compact" class="mt-4">
                    Vorlage erfolgreich aktualisiert.
                </v-alert>
            </v-card-text>
        </v-card>

        <!-- Reparaturarten -->
        <v-card class="mb-6">
            <v-card-title class="d-flex align-center justify-space-between">
                <span>Reparaturarten</span>
                <v-btn size="small" color="primary" prepend-icon="mdi-plus"
                    @click="openCreate('repair_type')">Hinzufügen</v-btn>
            </v-card-title>
            <v-data-table :headers="headersBasic" :items="byCategory('repair_type')" :loading="loading" item-value="id"
                hover density="comfortable">
                <template #item.is_active="{ item }">
                    <v-chip :color="item.is_active ? 'success' : 'error'" size="small" variant="tonal">
                        {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
                    </v-chip>
                </template>
                <template #item.actions="{ item }">
                    <v-btn icon="mdi-pencil" size="small" variant="text" density="compact" @click="openEdit(item)" />
                    <v-btn icon="mdi-delete" size="small" variant="text" density="compact" color="error"
                        @click="confirmDelete(item)" />
                </template>
            </v-data-table>
        </v-card>

        <!-- Prüfgeräte -->
        <v-card class="mb-6">
            <v-card-title class="d-flex align-center justify-space-between">
                <span>Prüfgeräte</span>
                <v-btn size="small" color="primary" prepend-icon="mdi-plus"
                    @click="openCreate('test_device')">Hinzufügen</v-btn>
            </v-card-title>
            <v-data-table :headers="headersDevice" :items="byCategory('test_device')" :loading="loading" item-value="id"
                hover density="comfortable">
                <template #item.is_active="{ item }">
                    <v-chip :color="item.is_active ? 'success' : 'error'" size="small" variant="tonal">
                        {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
                    </v-chip>
                </template>
                <template #item.actions="{ item }">
                    <v-btn icon="mdi-pencil" size="small" variant="text" density="compact" @click="openEdit(item)" />
                    <v-btn icon="mdi-delete" size="small" variant="text" density="compact" color="error"
                        @click="confirmDelete(item)" />
                </template>
            </v-data-table>
        </v-card>

        <!-- Add / Edit dialog -->
        <v-dialog v-model="formDialog" max-width="480" persistent>
            <v-card>
                <v-card-title>{{ editingItem ? 'Eintrag bearbeiten' : 'Neuer Eintrag' }}</v-card-title>
                <v-card-text>
                    <v-alert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4">
                        {{ formError }}
                    </v-alert>
                    <v-form ref="formRef" @submit.prevent="saveItem">
                        <v-text-field v-model="form.name" label="Name *" variant="outlined" density="comfortable"
                            :rules="[required]" autofocus class="mb-2" />
                        <v-text-field v-if="formCategory === 'test_device'" v-model="form.serial_number"
                            label="Seriennummer" variant="outlined" density="comfortable" />
                        <v-checkbox v-if="editingItem" v-model="form.is_active" label="Aktiv" density="comfortable" />
                    </v-form>
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="closeDialog">Abbrechen</v-btn>
                    <v-btn color="primary" :loading="saving" @click="saveItem">Speichern</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Delete confirm dialog -->
        <v-dialog v-model="deleteDialog" max-width="380">
            <v-card>
                <v-card-title>Eintrag löschen?</v-card-title>
                <v-card-text>
                    Soll <strong>{{ deletingItem?.name }}</strong> wirklich gelöscht werden?
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
                    <v-btn color="error" :loading="saving" @click="doDelete">Löschen</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <!-- Snackbar -->
        <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="bottom right">
            {{ snackbar.text }}
        </v-snackbar>
    </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { SettingResponse } from '../api/generated/data-contracts'
import { SettingsService } from '../api/services/SettingsService'

// ── Table column definitions ─────────────────────────────────────────────────

const headersBasic = [
    { title: 'Name', key: 'name', sortable: true },
    { title: 'Reihenfolge', key: 'sort_order', sortable: true, width: '120px' },
    { title: 'Status', key: 'is_active', sortable: false, width: '100px' },
    { title: 'Aktionen', key: 'actions', sortable: false, width: '100px', align: 'end' as const },
]

const headersDevice = [
    { title: 'Name', key: 'name', sortable: true },
    { title: 'Seriennummer', key: 'serial_number', sortable: false },
    { title: 'Reihenfolge', key: 'sort_order', sortable: true, width: '120px' },
    { title: 'Status', key: 'is_active', sortable: false, width: '100px' },
    { title: 'Aktionen', key: 'actions', sortable: false, width: '100px', align: 'end' as const },
]

// ── State ─────────────────────────────────────────────────────────────────────

const settings = ref<SettingResponse[]>([])
const loading = ref(false)
const saving = ref(false)

const formDialog = ref(false)
const formCategory = ref<string>('repair_type')
const editingItem = ref<SettingResponse | null>(null)
const formError = ref<string | null>(null)
const formRef = ref<{ validate: () => Promise<{ valid: boolean }> } | null>(null)

const form = ref({ name: '', serial_number: '', is_active: true })

const deleteDialog = ref(false)
const deletingItem = ref<SettingResponse | null>(null)

const snackbar = ref({ show: false, text: '', color: 'success' })

// ── Helpers ───────────────────────────────────────────────────────────────────

function required(v: string) {
    return (v && v.trim().length > 0) || 'Pflichtfeld'
}

function showMsg(text: string, color: 'success' | 'error' = 'success') {
    snackbar.value = { show: true, text, color }
}

function byCategory(category: string): SettingResponse[] {
    return settings.value.filter(s => s.category === category)
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadSettings() {
    loading.value = true
    try {
        const res = await SettingsService.getAll()
        settings.value = res.data
    } catch {
        showMsg('Fehler beim Laden der Einstellungen', 'error')
    } finally {
        loading.value = false
    }
}

// ── Create / Edit ─────────────────────────────────────────────────────────────

function openCreate(category: string) {
    editingItem.value = null
    formCategory.value = category
    form.value = { name: '', serial_number: '', is_active: true }
    formError.value = null
    formDialog.value = true
}

function openEdit(item: SettingResponse) {
    editingItem.value = item
    formCategory.value = item.category
    form.value = {
        name: item.name,
        serial_number: item.serial_number ?? '',
        is_active: item.is_active,
    }
    formError.value = null
    formDialog.value = true
}

function closeDialog() {
    formDialog.value = false
    editingItem.value = null
}

async function saveItem() {
    const validation = await formRef.value?.validate()
    if (!validation?.valid) return

    saving.value = true
    formError.value = null

    try {
        if (editingItem.value) {
            const res = await SettingsService.update(editingItem.value.id, {
                name: form.value.name,
                serial_number: form.value.serial_number || null,
                is_active: form.value.is_active,
            })
            const idx = settings.value.findIndex(s => s.id === editingItem.value!.id)
            if (idx !== -1) settings.value[idx] = res.data
            showMsg('Eintrag gespeichert')
        } else {
            const res = await SettingsService.create({
                category: formCategory.value,
                name: form.value.name,
                serial_number: form.value.serial_number || null,
            })
            settings.value.push(res.data)
            showMsg('Eintrag hinzugefügt')
        }
        closeDialog()
    } catch (err: unknown) {
        const msg =
            (err as { body?: { error?: string } })?.body?.error
            ?? 'Fehler beim Speichern'
        formError.value = msg
    } finally {
        saving.value = false
    }
}

// ── Delete ────────────────────────────────────────────────────────────────────

function confirmDelete(item: SettingResponse) {
    deletingItem.value = item
    deleteDialog.value = true
}

async function doDelete() {
    if (!deletingItem.value) return
    saving.value = true
    try {
        await SettingsService.delete(deletingItem.value.id)
        settings.value = settings.value.filter(s => s.id !== deletingItem.value!.id)
        showMsg('Eintrag gelöscht')
        deleteDialog.value = false
    } catch {
        showMsg('Fehler beim Löschen', 'error')
    } finally {
        saving.value = false
        deletingItem.value = null
    }
}

// ── Mount ─────────────────────────────────────────────────────────────────────

onMounted(loadSettings)

// ── Disclaimer upload ─────────────────────────────────────────────────────────

const disclaimerFile = ref<File | null>(null)
const disclaimerUploading = ref(false)
const disclaimerError = ref('')
const disclaimerSuccess = ref(false)

async function uploadDisclaimer() {
    if (!disclaimerFile.value) return
    disclaimerUploading.value = true
    disclaimerError.value = ''
    disclaimerSuccess.value = false
    try {
        const fd = new FormData()
        fd.append('file', disclaimerFile.value)
        const res = await fetch('/api/config/disclaimer', { method: 'POST', body: fd })
        const json = await res.json()
        if (!res.ok || json.reply !== 'done') {
            disclaimerError.value = json.error ?? 'Fehler beim Hochladen'
        } else {
            disclaimerSuccess.value = true
            disclaimerFile.value = null
        }
    } catch {
        disclaimerError.value = 'Netzwerkfehler beim Hochladen'
    } finally {
        disclaimerUploading.value = false
    }
}
</script>
