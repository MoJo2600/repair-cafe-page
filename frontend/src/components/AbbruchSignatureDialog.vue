<script setup lang="ts">
import { ref, shallowRef, watch } from 'vue'
import { api } from '@/api/client'
import { sessionFetch } from '@/api/session'
import ResponsiveDialog from '@/components/ResponsiveDialog.vue'
import SignaturePad from '@/components/SignaturePad.vue'
import DocumentPreview from '@/components/DocumentPreview.vue'
import { errorMessage } from '@/utils/errors'

const open = defineModel<boolean>({ required: true })

const props = withDefaults(
  defineProps<{
    loading?: boolean
    repairId?: number | null
  }>(),
  {
    loading: false,
    repairId: null,
  }
)

const emit = defineEmits<{
  (e: 'confirm', value: { signature: string; templateVersionId: number }): void
}>()

const signature = ref<string | null>(null)
const signatureError = ref('')
const previewHtml = shallowRef('')
const previewLoading = shallowRef(false)
const previewError = shallowRef('')
const templateVersionId = shallowRef<number | null>(null)

async function loadDocument() {
  if (!props.repairId) {
    previewError.value = 'Reparatur nicht gefunden'
    return
  }
  previewLoading.value = true
  previewError.value = ''
  previewHtml.value = ''
  try {
    const template = (await api.getActiveDocumentTemplate({ role: 'cancellation' })).data
    const versionId = template.active_version_id
    if (!versionId) throw new Error('Keine veröffentlichte Dokumentversion')
    templateVersionId.value = versionId
    const response = await sessionFetch(`/api/document-templates/${template.id}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version_id: versionId, repair_id: props.repairId }),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    previewHtml.value = await response.text()
  } catch (error) {
    previewError.value =
      'Dokument konnte nicht geladen werden: ' + errorMessage(error, 'Unbekannter Fehler')
  } finally {
    previewLoading.value = false
  }
}

watch(open, (isOpen) => {
  if (!isOpen) return
  signature.value = null
  signatureError.value = ''
  templateVersionId.value = null
  void loadDocument()
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
  if (!templateVersionId.value) {
    previewError.value = 'Keine gültige Dokumentversion geladen'
    return
  }
  emit('confirm', {
    signature: signature.value,
    templateVersionId: templateVersionId.value,
  })
  signature.value = null
}
</script>

<template>
  <ResponsiveDialog v-model="open" max-width="760px" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="error">mdi-alert-octagon</v-icon>
        Abbruchbestätigung
      </v-card-title>
      <v-card-text>
        <v-alert v-if="previewError" type="error" variant="tonal" class="mb-4">
          {{ previewError }}
        </v-alert>
        <DocumentPreview v-else :html="previewHtml" :loading="previewLoading" class="mb-4" />
        <p class="text-body-medium text-medium-emphasis mb-3">
          Bitte hier unterschreiben zur Bestätigung:
        </p>
        <SignaturePad v-model="signature" :error="signatureError" />
      </v-card-text>
      <v-card-actions>
        <v-btn variant="text" @click="closeDialog">Abbrechen</v-btn>
        <v-spacer />
        <v-btn color="error" :loading="props.loading" @click="confirmDialog">
          <v-icon start>mdi-check</v-icon>
          Bestätigen
        </v-btn>
      </v-card-actions>
    </v-card>
  </ResponsiveDialog>
</template>
