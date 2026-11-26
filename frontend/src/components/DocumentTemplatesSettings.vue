<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from 'vue'
import { api } from '@/api/client'
import { sessionFetch } from '@/api/session'
import type { DocumentTemplateResponse, DocumentTemplateVersionResponse } from '@/api/types'
import { useToast } from '@/composables/useToast'
import { errorMessage } from '@/utils/errors'
import DocumentPreview from '@/components/DocumentPreview.vue'
import DocumentTemplateEditor from '@/components/DocumentTemplateEditor.vue'
import StatusChip from '@/components/ui/StatusChip.vue'

const toast = useToast()
const templates = ref<DocumentTemplateResponse[]>([])
const loading = shallowRef(false)
const editorOpen = shallowRef(false)
const saving = shallowRef(false)
const editorTemplate = ref<DocumentTemplateResponse | null>(null)
const editorTitle = shallowRef('')
const editorHtml = shallowRef('<p>Dokumenttext</p>')
const previewHtml = shallowRef('')
const previewLoading = shallowRef(false)
const previewTemplate = ref<DocumentTemplateResponse | null>(null)
const previewVersion = ref<DocumentTemplateVersionResponse | null>(null)
const activeDocumentCount = computed(
  () => templates.value.filter((template) => template.active_version_id != null).length
)

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = (await api.listDocumentTemplates()).data ?? []
  } catch (error) {
    toast.error(
      'Dokumentvorlagen konnten nicht geladen werden: ' + errorMessage(error, 'Unbekannter Fehler')
    )
  } finally {
    loading.value = false
  }
}

function latestVersion(template: DocumentTemplateResponse) {
  return [...(template.versions ?? [])].sort((a, b) => b.version_number - a.version_number)[0]
}

function openEditor(template: DocumentTemplateResponse) {
  const source = template.active_version ?? latestVersion(template)
  editorTemplate.value = template
  editorTitle.value = template.title
  editorHtml.value = source?.html ?? '<p>Dokumenttext</p>'
  editorOpen.value = true
}

async function publishVersion() {
  const template = editorTemplate.value
  if (!template) return
  saving.value = true
  try {
    if (editorTitle.value !== template.title) {
      await api.updateDocumentTemplate({ templateId: template.id }, { title: editorTitle.value })
    }
    const created = await api.createDocumentTemplateVersion(
      { templateId: template.id },
      { html: editorHtml.value }
    )
    await api.publishDocumentTemplateVersion({
      templateId: template.id,
      versionId: created.data.id,
    })
    editorOpen.value = false
    toast.success('Dokumentversion veröffentlicht')
    await loadTemplates()
  } catch (error) {
    toast.error(
      'Dokument konnte nicht veröffentlicht werden: ' + errorMessage(error, 'Unbekannter Fehler')
    )
  } finally {
    saving.value = false
  }
}

async function showPreview(
  template: DocumentTemplateResponse,
  version = template.active_version ?? latestVersion(template)
) {
  if (!version) return
  previewTemplate.value = template
  previewVersion.value = version
  previewHtml.value = ''
  previewLoading.value = true
  try {
    const response = await sessionFetch(`/api/document-templates/${template.id}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version_id: version.id }),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    previewHtml.value = await response.text()
  } catch (error) {
    toast.error(
      'Vorschau konnte nicht geladen werden: ' + errorMessage(error, 'Unbekannter Fehler')
    )
  } finally {
    previewLoading.value = false
  }
}

async function activateVersion(
  template: DocumentTemplateResponse,
  version: DocumentTemplateVersionResponse
) {
  saving.value = true
  try {
    await api.publishDocumentTemplateVersion({
      templateId: template.id,
      versionId: version.id,
    })
    toast.success(`Version ${version.version_number} aktiviert`)
    await loadTemplates()
  } catch (error) {
    toast.error(
      'Version konnte nicht aktiviert werden: ' + errorMessage(error, 'Unbekannter Fehler')
    )
  } finally {
    saving.value = false
  }
}

async function printBlank(template: DocumentTemplateResponse) {
  const version = template.active_version
  if (!version) {
    toast.error('Das Dokument hat noch keine veröffentlichte Version')
    return
  }
  try {
    const response = await sessionFetch(
      `/api/settings/document-templates/${template.id}/blank-print`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version_id: version.id }),
      }
    )
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const pdf = await response.blob()
    const url = URL.createObjectURL(pdf)
    const link = document.createElement('a')
    link.href = url
    link.download = `${template.role}_leer.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    toast.error(
      'Leeres Dokument konnte nicht erstellt werden: ' + errorMessage(error, 'Unbekannter Fehler')
    )
  }
}

onMounted(loadTemplates)
</script>

<template>
  <v-card class="mb-6">
    <v-card-title class="d-flex align-center justify-space-between flex-wrap ga-2">
      <span>Kundendokumente</span>
    </v-card-title>
    <v-card-text>
      <p class="mb-4">
        Dokumente können direkt bearbeitet und versioniert werden. Neue Versionen werden erst nach
        der Veröffentlichung für Reparaturen verwendet. {{ activeDocumentCount }}
        Dokument(e) sind aktiv.
      </p>
      <v-progress-linear v-if="loading" indeterminate class="mb-4" />
      <v-expansion-panels v-else>
        <v-expansion-panel v-for="template in templates" :key="template.id">
          <v-expansion-panel-title>
            <div>
              <div class="text-title-medium">{{ template.title }}</div>
              <div class="text-body-small text-medium-emphasis">
                <template v-if="template.active_version">
                  Aktiv: Version {{ template.active_version.version_number }}
                </template>
                <template v-else>Noch nicht veröffentlicht</template>
              </div>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="d-flex flex-wrap ga-2 mb-4">
              <v-btn color="primary" prepend-icon="mdi-pencil" @click="openEditor(template)">
                Neue Version
              </v-btn>
              <v-btn
                variant="tonal"
                prepend-icon="mdi-eye"
                :disabled="!template.versions?.length"
                @click="showPreview(template)"
              >
                Vorschau
              </v-btn>
              <v-btn
                variant="tonal"
                prepend-icon="mdi-printer"
                :disabled="!template.active_version"
                @click="printBlank(template)"
              >
                Leer drucken
              </v-btn>
            </div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="version in [...(template.versions ?? [])].sort(
                    (a, b) => b.version_number - a.version_number
                  )"
                  :key="version.id"
                >
                  <td>{{ version.version_number }}</td>
                  <td>
                    <StatusChip
                      v-if="version.id === template.active_version_id"
                      color="success"
                      label="Aktiv"
                    />
                    <StatusChip v-else-if="version.published_at" label="Veröffentlicht" />
                    <StatusChip v-else color="warning" label="Entwurf" />
                  </td>
                  <td class="d-flex ga-1 py-1">
                    <v-btn
                      icon="mdi-eye"
                      size="small"
                      variant="text"
                      aria-label="Version ansehen"
                      @click="showPreview(template, version)"
                    />
                    <v-btn
                      v-if="version.id !== template.active_version_id && version.published_at"
                      icon="mdi-check"
                      size="small"
                      variant="text"
                      aria-label="Version aktivieren"
                      @click="activateVersion(template, version)"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>
  </v-card>

  <v-dialog v-model="editorOpen" fullscreen transition="dialog-bottom-transition">
    <v-card>
      <v-toolbar>
        <v-btn icon="mdi-close" @click="editorOpen = false" />
        <v-toolbar-title>Neue Dokumentversion</v-toolbar-title>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          :loading="saving"
          prepend-icon="mdi-publish"
          @click="publishVersion"
        >
          Veröffentlichen
        </v-btn>
      </v-toolbar>
      <v-container fluid>
        <v-row>
          <v-col cols="12" md="5">
            <v-text-field v-model="editorTitle" label="Dokumentname" />
            <v-alert type="info" variant="tonal" class="mb-4">
              Vorhandene Reparaturen behalten ihre veröffentlichte Version. Diese Version wird erst
              nach dem Veröffentlichen aktiv.
            </v-alert>
          </v-col>
          <v-col cols="12" md="7">
            <DocumentTemplateEditor v-model="editorHtml" />
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </v-dialog>

  <v-dialog
    :model-value="!!previewTemplate"
    max-width="980"
    @update:model-value="previewTemplate = null"
  >
    <v-card>
      <v-card-title>
        {{ previewTemplate?.title }} · Version {{ previewVersion?.version_number }}
      </v-card-title>
      <v-card-text>
        <DocumentPreview :html="previewHtml" :loading="previewLoading" />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="previewTemplate = null">Schließen</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
