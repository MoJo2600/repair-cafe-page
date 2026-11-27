<template>
  <v-container fluid class="page-container">
    <PageHeader
      title="Einstellungen"
      subtitle="Organisation, Dokumente und Werkstattangaben verwalten"
    />

    <v-tabs v-model="activeSection" class="mb-4" color="primary" grow show-arrows>
      <v-tab value="general" prepend-icon="mdi-cog">Allgemein</v-tab>
      <v-tab value="documents" prepend-icon="mdi-file-document-edit">Kundendokumente</v-tab>
      <v-tab value="workshop" prepend-icon="mdi-tools">Werkstatt</v-tab>
    </v-tabs>

    <section v-if="activeSection === 'general'">
        <!-- Organisation -->
        <v-card class="mb-6">
          <v-card-title>Organisation</v-card-title>
          <v-card-text>
            <p class="mb-4">
              Name und Website der Organisation werden auf gedruckten Etiketten angezeigt.
            </p>
            <v-row class="ga-4">
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="orgForm.org_name"
                  label="Name der Organisation"
                  hide-details="auto"
                  placeholder="Repair Café"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="orgForm.org_website"
                  label="Website der Organisation"
                  hide-details="auto"
                  placeholder="https://example.org"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="orgForm.app_url"
                  label="App-URL (für QR-Codes)"
                  hide-details="auto"
                  placeholder="https://repaircafe.example.org"
                />
              </v-col>
            </v-row>
            <v-divider class="my-6" />
            <div class="text-title-small mb-1">Logo / Icon</div>
            <p class="mb-4 text-body-medium text-medium-emphasis">
              Laden Sie ein neues Logo hoch (PNG oder JPEG). Es wird sofort als App-Icon und Favicon
              aktiv.
            </p>
            <v-row class="ga-4 align-center">
              <v-col cols="auto">
                <v-img
                  :src="logoPreview ?? '/api/config/logo'"
                  width="64"
                  height="64"
                  cover
                  rounded="lg"
                  class="border"
                />
              </v-col>
              <v-col cols="12" sm>
                <v-file-input
                  v-model="logoFile"
                  label="Neues Logo hochladen"
                  accept="image/png,image/jpeg,.png,.jpg,.jpeg"
                  prepend-icon="mdi-image"
                  hide-details="auto"
                  @update:model-value="onLogoFileChange"
                />
              </v-col>
              <v-col cols="12" sm="auto">
                <v-btn
                  color="primary"
                  variant="flat"
                  :loading="logoUploading"
                  :disabled="!logoFile"
                  @click="uploadLogo"
                >
                  Hochladen
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn color="primary" variant="flat" :loading="orgSaving" @click="saveOrg">
              Speichern
            </v-btn>
          </v-card-actions>
        </v-card>

        <!-- Optionale Funktionen -->
        <v-card class="mb-6">
          <v-card-title>Optionale Funktionen</v-card-title>
          <v-card-text>
            <v-switch
              v-model="orgForm.repair_handover_enabled"
              label="Kundengeräte bis zur Abholung verwalten"
              color="primary"
              hint="Zeigt nach dem Reparaturabschluss den Status „Zur Abholung bereit“ und protokolliert die Ausgabe."
              persistent-hint
            />
            <v-divider class="my-6" />
            <div class="text-title-small mb-1">Jubelton</div>
            <p class="mb-4">
              Wird auf dem Dashboard abgespielt, wenn ein Gerät repariert wurde. Laden Sie eine
              MP3-Datei hoch (max. 2 MB). Geöffnete Dashboards übernehmen den neuen Ton nach dem
              Neuladen.
            </p>
            <v-row class="ga-4 align-center">
              <v-col cols="12" sm>
                <v-file-input
                  v-model="soundFile"
                  label="Neuen Jubelton hochladen"
                  accept="audio/mpeg,.mp3"
                  prepend-icon="mdi-music-note"
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" sm="auto" class="d-flex flex-wrap ga-2">
                <v-btn
                  color="primary"
                  variant="flat"
                  :loading="soundUploading"
                  :disabled="!soundFile"
                  @click="uploadSound"
                >
                  Hochladen
                </v-btn>
                <v-btn variant="tonal" prepend-icon="mdi-play" @click="previewSound">Anhören</v-btn>
                <v-btn variant="text" :loading="soundResetting" @click="resetSound">Standard</v-btn>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn
              color="primary"
              variant="flat"
              :loading="featuresSaving"
              @click="saveFeatures"
            >
              Speichern
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card>
          <v-card-title>Sonstiges</v-card-title>
          <v-list bg-color="transparent">
            <v-list-item
              to="/styleguide"
              prepend-icon="mdi-palette-outline"
              title="Styleguide"
              subtitle="Gestaltungsrichtlinien und UI-Komponenten anzeigen"
              append-icon="mdi-chevron-right"
            />
          </v-list>
        </v-card>
    </section>

    <section v-else-if="activeSection === 'documents'">
      <DocumentTemplatesSettings />
    </section>

    <section v-else>
        <!-- Reparaturarten -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2">
            <span>Reparaturarten</span>
            <v-btn
              size="small"
              color="primary"
              prepend-icon="mdi-plus"
              @click="openCreate('repair_type')"
              >Hinzufügen</v-btn
            >
          </v-card-title>
          <v-data-table
            v-if="!smAndDown"
            :headers="headersBasic"
            :items="byCategory('repair_type')"
            :loading="loading"
            item-value="id"
            hover
            density="comfortable"
          >
            <template #item.is_active="{ item }">
              <StatusChip v-if="item.is_active" label="Aktiv" color="success" icon="mdi-check" />
              <StatusChip v-else label="Inaktiv" icon="mdi-cancel" />
            </template>
            <template #item.actions="{ item }">
              <TableRowActions primary-label="Bearbeiten" @primary="openEdit(item)">
                <template #secondary>
                  <v-list-item
                    prepend-icon="mdi-delete"
                    title="Löschen"
                    base-color="error"
                    @click="confirmDelete(item)"
                  />
                </template>
              </TableRowActions>
            </template>
          </v-data-table>
          <v-list v-else lines="two">
            <v-list-item
              v-for="item in byCategory('repair_type')"
              :key="item.id"
              :title="item.name"
              :subtitle="`Reihenfolge ${item.sort_order}`"
            >
              <template #prepend>
                <v-icon
                  :icon="item.is_active ? 'mdi-check-circle' : 'mdi-cancel'"
                  :color="item.is_active ? 'success' : undefined"
                />
              </template>
              <template #append>
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
                <v-btn
                  icon="mdi-delete"
                  size="small"
                  variant="text"
                  color="error"
                  @click="confirmDelete(item)"
                />
              </template>
            </v-list-item>
            <v-list-item v-if="byCategory('repair_type').length === 0" title="Keine Einträge" />
          </v-list>
        </v-card>

        <!-- Prüfgeräte -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2">
            <span>Prüfgeräte</span>
            <v-btn
              size="small"
              color="primary"
              prepend-icon="mdi-plus"
              @click="openCreate('test_device')"
              >Hinzufügen</v-btn
            >
          </v-card-title>
          <v-data-table
            v-if="!smAndDown"
            :headers="headersDevice"
            :items="byCategory('test_device')"
            :loading="loading"
            item-value="id"
            hover
            density="comfortable"
          >
            <template #item.is_active="{ item }">
              <StatusChip v-if="item.is_active" label="Aktiv" color="success" icon="mdi-check" />
              <StatusChip v-else label="Inaktiv" icon="mdi-cancel" />
            </template>
            <template #item.actions="{ item }">
              <TableRowActions primary-label="Bearbeiten" @primary="openEdit(item)">
                <template #secondary>
                  <v-list-item
                    prepend-icon="mdi-delete"
                    title="Löschen"
                    base-color="error"
                    @click="confirmDelete(item)"
                  />
                </template>
              </TableRowActions>
            </template>
          </v-data-table>
          <v-list v-else lines="two">
            <v-list-item
              v-for="item in byCategory('test_device')"
              :key="item.id"
              :title="item.name"
              :subtitle="item.serial_number || `Reihenfolge ${item.sort_order}`"
            >
              <template #prepend>
                <v-icon
                  :icon="item.is_active ? 'mdi-check-circle' : 'mdi-cancel'"
                  :color="item.is_active ? 'success' : undefined"
                />
              </template>
              <template #append>
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
                <v-btn
                  icon="mdi-delete"
                  size="small"
                  variant="text"
                  color="error"
                  @click="confirmDelete(item)"
                />
              </template>
            </v-list-item>
            <v-list-item v-if="byCategory('test_device').length === 0" title="Keine Einträge" />
          </v-list>
        </v-card>
    </section>

    <!-- Add / Edit dialog -->
    <v-dialog v-model="formDialog" max-width="480" persistent>
      <v-card>
        <v-card-title>{{ editingItem ? 'Eintrag bearbeiten' : 'Neuer Eintrag' }}</v-card-title>
        <v-card-text>
          <v-alert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4">
            {{ formError }}
          </v-alert>
          <v-form ref="formRef" @submit.prevent="saveItem">
            <v-text-field
              v-model="form.name"
              label="Name *"
              :rules="[required]"
              autofocus
              class="mb-2"
            />
            <v-text-field
              v-if="formCategory === 'test_device'"
              v-model="form.serial_number"
              label="Seriennummer"
            />
            <v-checkbox
              v-if="editingItem"
              v-model="form.is_active"
              label="Aktiv"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDialog">Abbrechen</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" @click="saveItem"
            >Speichern</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete confirm dialog -->
    <v-dialog v-model="deleteDialog" max-width="380" @after-leave="deletingItem = null">
      <v-card>
        <v-card-title>Eintrag löschen?</v-card-title>
        <v-card-text>
          <span v-if="deletingItem?.category === 'repair_type'">
            Soll <strong>{{ deletingItem?.name }}</strong> wirklich gelöscht werden?<br />
            <span class="text-body-small text-medium-emphasis">
              Reparaturarten die bereits Reparaturen zugewiesen sind, können nicht gelöscht werden.
              Deaktivieren Sie diese stattdessen.
            </span>
          </span>
          <span v-else>
            Soll <strong>{{ deletingItem?.name }}</strong> wirklich gelöscht werden?
          </span>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" :loading="saving" @click="doDelete">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import PageHeader from '@/components/ui/PageHeader.vue'
import DocumentTemplatesSettings from '@/components/DocumentTemplatesSettings.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import TableRowActions from '@/components/ui/TableRowActions.vue'
import { api } from '@/api/client'
import { errorMessage } from '@/utils/errors'
import { onMounted, onUnmounted, ref } from 'vue'
import { useDisplay } from 'vuetify'
import { CELEBRATION_SOUND_URL } from '@/composables/useCelebration'
import type { VForm } from 'vuetify/components'
import type { SettingResponse } from '../api/generated/data-contracts'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const { smAndDown } = useDisplay()
const activeSection = ref<'general' | 'documents' | 'workshop'>('general')

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
const formRef = ref<InstanceType<typeof VForm> | null>(null)

const form = ref({ name: '', serial_number: '', is_active: true })

const deleteDialog = ref(false)
const deletingItem = ref<SettingResponse | null>(null)

// ── Helpers ───────────────────────────────────────────────────────────────────

function required(v: string) {
  return (v && v.trim().length > 0) || 'Pflichtfeld'
}

function byCategory(category: string): SettingResponse[] {
  return settings.value.filter((s) => s.category === category)
}

// ── Organisation config ───────────────────────────────────────────────────

const orgForm = ref({
  org_name: '',
  org_website: '',
  app_url: '',
  repair_handover_enabled: false,
})
const orgSaving = ref(false)
const featuresSaving = ref(false)

async function loadOrgConfig() {
  try {
    const cfg = await api.getAppConfig()
    orgForm.value = {
      org_name: cfg.org_name ?? '',
      org_website: cfg.org_website ?? '',
      app_url: cfg.app_url ?? '',
      repair_handover_enabled: cfg.repair_handover_enabled ?? false,
    }
  } catch (err) {
    toast.error(errorMessage(err, 'Konfiguration konnte nicht geladen werden'))
  }
}

async function saveOrg() {
  orgSaving.value = true
  try {
    const cfg = await api.updateAppConfig({
      org_name: orgForm.value.org_name,
      org_website: orgForm.value.org_website,
      app_url: orgForm.value.app_url,
    })
    orgForm.value = {
      org_name: cfg.org_name ?? '',
      org_website: cfg.org_website ?? '',
      app_url: cfg.app_url ?? '',
      repair_handover_enabled: cfg.repair_handover_enabled ?? false,
    }
    toast.success('Organisation gespeichert')
  } catch (err) {
    toast.error(errorMessage(err, 'Fehler beim Speichern der Organisation'))
  } finally {
    orgSaving.value = false
  }
}

async function saveFeatures() {
  featuresSaving.value = true
  try {
    const cfg = await api.updateAppConfig({
      repair_handover_enabled: orgForm.value.repair_handover_enabled,
    })
    orgForm.value.repair_handover_enabled = cfg.repair_handover_enabled ?? false
    toast.success('Optionale Funktionen gespeichert')
  } catch (err) {
    toast.error(errorMessage(err, 'Fehler beim Speichern der optionalen Funktionen'))
  } finally {
    featuresSaving.value = false
  }
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadSettings() {
  loading.value = true
  try {
    const res = await api.listAllSettings()
    settings.value = res.data ?? []
  } catch {
    toast.error('Fehler beim Laden der Einstellungen')
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
      const res = await api.updateSetting(
        { settingId: editingItem.value.id },
        {
          name: form.value.name,
          serial_number: form.value.serial_number || null,
          is_active: form.value.is_active,
        }
      )
      const idx = settings.value.findIndex((s) => s.id === editingItem.value!.id)
      if (idx !== -1) settings.value[idx] = res.data
      toast.success('Eintrag gespeichert')
    } else {
      const res = await api.createSetting({
        category: formCategory.value,
        name: form.value.name,
        serial_number: form.value.serial_number || null,
      })
      settings.value.push(res.data)
      toast.success('Eintrag hinzugefügt')
    }
    closeDialog()
  } catch (err: unknown) {
    const msg = (err as { body?: { error?: string } })?.body?.error ?? 'Fehler beim Speichern'
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
    await api.deleteSetting({ settingId: deletingItem.value.id })
    settings.value = settings.value.filter((s) => s.id !== deletingItem.value!.id)
    toast.success('Eintrag gelöscht')
    deleteDialog.value = false
  } catch (err: unknown) {
    const msg = (err as { body?: { error?: string } })?.body?.error ?? 'Fehler beim Löschen'
    toast.error(msg)
  } finally {
    saving.value = false
  }
}

// ── Mount ─────────────────────────────────────────────────────────────────────

onMounted(loadSettings)
onMounted(loadOrgConfig)

// ── Logo upload ──────────────────────────────────────────────────────────────

const logoFile = ref<File | null>(null)
const logoUploading = ref(false)
const logoPreview = ref<string | null>(null)

function onLogoFileChange(file: File | File[] | null) {
  const f = Array.isArray(file) ? file[0] : file
  if (f) {
    logoPreview.value = URL.createObjectURL(f)
  } else {
    logoPreview.value = null
  }
}

async function uploadLogo() {
  if (!logoFile.value) return
  logoUploading.value = true
  try {
    await api.uploadLogo({ file: logoFile.value })
    toast.success('Logo erfolgreich aktualisiert')
    logoFile.value = null
    // Update all favicon links in the document head
    const bust = `?t=${Date.now()}`
    document
      .querySelectorAll<HTMLLinkElement>('link[rel="icon"], link[rel="apple-touch-icon"]')
      .forEach((el) => {
        el.href = `/api/config/logo${bust}`
      })
  } catch (err) {
    toast.error(errorMessage(err, 'Fehler beim Hochladen des Logos'))
  } finally {
    logoUploading.value = false
  }
}

// ── Celebration sound ────────────────────────────────────────────────────────

const soundFile = ref<File | null>(null)
const soundUploading = ref(false)
const soundResetting = ref(false)
let soundPreview: HTMLAudioElement | null = null

/** Plays the active sound (fresh from the server, so right after an upload too). */
function previewSound() {
  soundPreview?.pause()
  soundPreview = new Audio(`${CELEBRATION_SOUND_URL}?t=${Date.now()}`)
  soundPreview.play().catch((err) => {
    toast.error(errorMessage(err, 'Ton konnte nicht abgespielt werden'))
  })
}

async function uploadSound() {
  if (!soundFile.value) return
  soundUploading.value = true
  try {
    await api.uploadCelebrationSound({ file: soundFile.value })
    toast.success('Jubelton erfolgreich aktualisiert')
    soundFile.value = null
  } catch (err) {
    toast.error(errorMessage(err, 'Fehler beim Hochladen des Jubeltons'))
  } finally {
    soundUploading.value = false
  }
}

async function resetSound() {
  soundResetting.value = true
  try {
    await api.resetCelebrationSound()
    toast.success('Standard-Jubelton ist wieder aktiv')
  } catch (err) {
    toast.error(errorMessage(err, 'Zurücksetzen fehlgeschlagen'))
  } finally {
    soundResetting.value = false
  }
}

onUnmounted(() => soundPreview?.pause())
</script>
