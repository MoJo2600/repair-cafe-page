<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { api, asFormData } from '@/api/client'
import { attachmentUrl, documentUrl } from '@/api/documents'
import type { RepairAttachmentResponse as RepairAttachment } from '@/api/types'
import { useAuthStore } from '@/stores/authStore'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useToast } from '@/composables/useToast'
import { fileIcon, formatFileSize, isImage } from '@/utils/files'
import { errorMessage } from '@/utils/errors'

/** Generated PDFs plus uploaded files of a repair; uploads and deletes files itself. */
const {
  repairId,
  attachments,
  disclaimerExists,
  cancellationExists,
  showCancellation,
  showTitle = true,
} = defineProps<{
  repairId: number
  attachments: RepairAttachment[]
  disclaimerExists: boolean
  cancellationExists: boolean
  /** Show the cancellation row even before its PDF exists (status detail "Abbruch"). */
  showCancellation: boolean
  /** Off when a surrounding tab already names the section. */
  showTitle?: boolean
}>()

const emit = defineEmits<{
  /** Files were uploaded or deleted; the owner should reload the list. */
  changed: []
}>()

const authStore = useAuthStore()
const toast = useToast()

const pendingFiles = ref<File[]>([])
const uploading = shallowRef(false)

const documents = computed(() => [
  {
    key: 'disclaimer',
    title: 'Haftungsausschluss',
    exists: disclaimerExists,
    url: documentUrl(repairId, 'disclaimer'),
    filename: `haftungsausschluss_${repairId}.pdf`,
  },
  ...(cancellationExists || showCancellation
    ? [
        {
          key: 'cancellation',
          title: 'Abbruchbestätigung',
          exists: cancellationExists,
          url: documentUrl(repairId, 'cancellation'),
          filename: `abbruch_${repairId}.pdf`,
        },
      ]
    : []),
])

const files = computed(() =>
  attachments.map((att) => {
    const image = isImage(att.content_type)
    return {
      ...att,
      url: attachmentUrl(repairId, att.id),
      icon: fileIcon(att.content_type),
      // Images open in a new tab, everything else downloads
      openIcon: image ? 'mdi-open-in-new' : 'mdi-download',
      download: image ? undefined : att.original_filename,
      target: image ? '_blank' : undefined,
      deletable: authStore.canDeleteOwnedBy(att.uploaded_by_id),
    }
  })
)

async function upload() {
  if (pendingFiles.value.length === 0) return
  uploading.value = true
  try {
    await api.uploadRepairAttachments(
      { repairId },
      asFormData({
        files: pendingFiles.value,
        attachment_type: 'misc',
        uploaded_by_id: authStore.currentUser?.id,
      })
    )
    pendingFiles.value = []
    toast.success('Dateien hochgeladen')
    emit('changed')
  } catch (err) {
    toast.error('Fehler beim Hochladen: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    uploading.value = false
  }
}

async function remove(attachmentId: number) {
  try {
    await api.deleteRepairAttachment({ repairId, attachmentId })
    toast.success('Anhang gelöscht')
    emit('changed')
  } catch (err) {
    toast.error('Fehler beim Löschen: ' + errorMessage(err, 'Unbekannter Fehler'))
  }
}
</script>

<template>
  <div>
    <SectionTitle v-if="showTitle" title="Anhänge" icon="mdi-paperclip" />

    <!-- Generated PDFs (read-only) -->
    <v-card class="mb-3">
      <v-list lines="one" class="py-0">
        <template v-for="(doc, index) in documents" :key="doc.key">
          <v-divider v-if="index > 0" />
          <v-list-item
            prepend-icon="mdi-file-pdf-box"
            :href="doc.url"
            target="_blank"
            :disabled="!doc.exists"
            :subtitle="doc.exists ? 'PDF herunterladen' : 'Nicht vorhanden'"
          >
            <v-list-item-title>{{ doc.title }}</v-list-item-title>
            <template #append>
              <v-btn
                v-if="doc.exists"
                icon="mdi-download"
                variant="text"
                size="small"
                :href="doc.url"
                :download="doc.filename"
                @click.stop
              ></v-btn>
              <v-icon v-else size="small" class="text-medium-emphasis">mdi-minus</v-icon>
            </template>
          </v-list-item>
        </template>
      </v-list>
    </v-card>

    <!-- Uploaded files -->
    <v-file-upload-list v-if="files.length > 0" show-size class="mb-3">
      <v-file-upload-item
        v-for="file in files"
        :key="file.id"
        :title="file.original_filename"
        :subtitle="formatFileSize(file.size)"
        :file-icon="file.icon"
      >
        <template #append>
          <v-btn
            :icon="file.openIcon"
            variant="text"
            size="small"
            :href="file.url"
            :download="file.download"
            :target="file.target"
            @click.stop
          ></v-btn>
          <v-btn
            v-if="file.deletable"
            icon="mdi-delete"
            variant="text"
            size="small"
            color="error"
            @click.stop="remove(file.id)"
          ></v-btn>
        </template>
      </v-file-upload-item>
    </v-file-upload-list>

    <v-file-upload
      v-model="pendingFiles"
      multiple
      inset-file-list
      show-size
      clearable
      title="Neue Anhänge hochladen"
      subtitle="Bilder, PDFs oder andere Dateien ablegen"
      browse-text="Durchsuchen"
    ></v-file-upload>
    <div v-if="pendingFiles.length > 0" class="d-flex justify-end mt-2">
      <v-btn color="primary" :loading="uploading" prepend-icon="mdi-upload" @click="upload">
        Hochladen
      </v-btn>
    </div>
  </div>
</template>
