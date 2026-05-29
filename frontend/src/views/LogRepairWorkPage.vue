<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 80vh">
    <v-card max-width="1200px" width="100%">
      <v-card-text v-if="loading">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <span class="ml-3">Lade Reparaturdaten...</span>
      </v-card-text>

      <v-card-text v-else-if="error">
        <v-alert type="error">{{ error }}</v-alert>
      </v-card-text>

      <v-card-text v-else-if="repairRecord">
        <v-row align="start">
          <!-- Left column: summary + logs + attachments -->
          <v-col cols="12" md="8">
            <RepairSummaryCard
              :repair-data="repairRecord"
              :vde-tests="summaryVdeTests"
              @updated="onRepairFieldsUpdated"
            />

            <!-- Repair Logs Section -->
            <div>
              <h3 class="text-h6 mb-4">Reparatur Logeinträge</h3>

              <!-- Unified Activity Thread -->
              <v-timeline v-if="threadEntries.length > 0" density="compact" side="end" class="mb-4">
                <v-timeline-item
                  v-for="entry in threadEntries"
                  :key="entry.uniqueKey"
                  :dot-color="
                    entry.type === 'repair'
                      ? 'primary'
                      : entry.type === 'status_change'
                        ? 'warning'
                        : entry.type === 'created'
                          ? 'grey'
                          : entry.vdePassed
                            ? 'success'
                            : 'error'
                  "
                  :icon="
                    entry.type === 'repair'
                      ? 'mdi-wrench'
                      : entry.type === 'status_change'
                        ? 'mdi-swap-horizontal'
                        : entry.type === 'created'
                          ? 'mdi-clipboard-plus-outline'
                          : entry.vdePassed
                            ? 'mdi-flash'
                            : 'mdi-flash-off'
                  "
                  @click="entry.type === 'repair' ? openEditLogDialog(entry.id) : undefined"
                >
                  <div :class="entry.type === 'repair' ? 'repair-entry' : ''">
                    <div>
                      <!-- Header: person + timestamp -->
                      <div class="d-flex align-center justify-space-between flex-wrap ga-2 mb-1">
                        <div class="d-flex align-center ga-2 flex-wrap">
                          <v-chip
                            v-if="
                              entry.type === 'repair' && (logAttachments[entry.id]?.length ?? 0) > 0
                            "
                            size="x-small"
                            color="grey-darken-1"
                            variant="tonal"
                          >
                            <v-icon size="12" start>mdi-paperclip</v-icon>
                            {{ logAttachments[entry.id].length }}
                          </v-chip>
                        </div>
                      </div>

                      <!-- Status change entry: show from → to chips -->
                      <template v-if="entry.type === 'status_change'">
                        <div class="d-flex align-center ga-1 flex-wrap">
                          <v-chip
                            size="x-small"
                            variant="tonal"
                            :color="getRepairStatusColor(entry.status_from ?? '')"
                          >
                            {{ entry.status_from || '?' }}
                          </v-chip>
                          <v-icon size="14" color="grey">mdi-arrow-right</v-icon>
                          <v-chip
                            size="x-small"
                            variant="tonal"
                            :color="getRepairStatusColor(entry.status_to ?? '')"
                          >
                            {{ entry.status_to || '?' }}
                          </v-chip>
                        </div>
                      </template>

                      <!-- Work log entry -->
                      <template v-else-if="entry.type === 'repair'">
                        <div
                          v-if="entry.description"
                          class="text-body-2 text-high-emphasis mb-1"
                          style="white-space: normal"
                        >
                          {{ entry.description }}
                        </div>
                        <div class="d-flex align-center ga-2 flex-wrap">
                          <!-- <span class="text-caption text-grey-darken-1"
                        >Dauer: {{ entry.duration }} Min.</span
                      > -->
                          <template v-if="entry.status_from || entry.status_to">
                            <v-chip
                              size="x-small"
                              variant="tonal"
                              :color="getRepairStatusColor(entry.status_from ?? '')"
                            >
                              {{ entry.status_from || '?' }}
                            </v-chip>
                            <v-icon size="14" color="grey">mdi-arrow-right</v-icon>
                            <v-chip
                              size="x-small"
                              variant="flat"
                              :color="getRepairStatusColor(entry.status_to ?? '')"
                            >
                              {{ entry.status_to || '?' }}
                            </v-chip>
                          </template>
                        </div>
                      </template>

                      <!-- VDE test entry -->
                      <template v-else-if="entry.type === 'vde'">
                        <div class="d-flex align-center ga-2 flex-wrap">
                          <span
                            class="text-body-2 text-high-emphasis"
                            style="white-space: normal"
                            >{{ entry.description }}</span
                          >
                          <v-btn
                            size="small"
                            variant="text"
                            prepend-icon="mdi-file-pdf-box"
                            color="error"
                            @click="downloadVdePdf(entry.id)"
                          >
                            PDF herunterladen
                          </v-btn>
                        </div>
                      </template>

                      <!-- Repair created entry -->
                      <template v-else-if="entry.type === 'created'">
                        <v-chip
                          size="x-small"
                          variant="tonal"
                          :color="getRepairStatusColor('Offen')"
                        >
                          Offen
                        </v-chip>
                      </template>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      {{
                        entry.dateOnly
                          ? formatDate(entry.created_at)
                          : formatDateTime(entry.created_at)
                      }}<template v-if="entry.person">
                        - <strong>{{ entry.person }}</strong></template
                      >
                    </div>
                  </div>
                </v-timeline-item>
              </v-timeline>

              <v-alert v-else type="info" variant="tonal" class="mb-4">
                Noch keine Logeinträge vorhanden.
              </v-alert>
            </div>

            <!-- Attachments Section -->
            <div class="mt-6">
              <h3 class="text-h6 mb-3">Anhänge</h3>

              <!-- Disclaimer PDF – static read-only item -->
              <v-card variant="outlined" class="mb-3">
                <v-list lines="one" class="py-0">
                  <v-list-item
                    prepend-icon="mdi-file-pdf-box"
                    :href="disclaimerUrl"
                    target="_blank"
                    :disabled="!disclaimerExists"
                    :subtitle="disclaimerExists ? 'PDF herunterladen' : 'Nicht vorhanden'"
                  >
                    <v-list-item-title>Haftungsausschluss</v-list-item-title>
                    <template #append>
                      <v-btn
                        v-if="disclaimerExists"
                        icon="mdi-download"
                        variant="text"
                        size="small"
                        :href="disclaimerUrl"
                        :download="`haftungsausschluss_${repairRecord?.id}.pdf`"
                        @click.stop
                      ></v-btn>
                      <v-icon v-else color="grey" size="small">mdi-minus</v-icon>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card>

              <!-- Log entry attachments (photos / files uploaded with log entries) -->
              <v-file-upload-list v-if="allLogAttachmentItems.length > 0" show-size class="mb-3">
                <template #default>
                  <v-file-upload-item
                    v-for="att in allLogAttachmentItems"
                    :key="att.url"
                    :title="att.name"
                    :subtitle="formatFileSize(att.size)"
                    :file-icon="getAttachmentIcon(att.content_type)"
                  >
                    <template #append>
                      <v-btn
                        :icon="
                          att.content_type.startsWith('image/') ? 'mdi-open-in-new' : 'mdi-download'
                        "
                        variant="text"
                        size="small"
                        :href="att.url"
                        :download="att.content_type.startsWith('image/') ? undefined : att.name"
                        :target="att.content_type.startsWith('image/') ? '_blank' : undefined"
                        @click.stop
                      ></v-btn>
                    </template>
                  </v-file-upload-item>
                </template>
              </v-file-upload-list>

              <!-- Unified store attachments -->
              <v-file-upload-list v-if="repairAttachments.length > 0" show-size class="mb-3">
                <template #default>
                  <v-file-upload-item
                    v-for="att in repairAttachments"
                    :key="att.id"
                    :title="att.original_filename"
                    :subtitle="formatFileSize(att.size)"
                    :file-icon="getAttachmentIcon(att.content_type)"
                  >
                    <template #append>
                      <v-btn
                        :icon="
                          att.content_type.startsWith('image/') ? 'mdi-open-in-new' : 'mdi-download'
                        "
                        variant="text"
                        size="small"
                        :href="`/api/repairs/${repairRecord?.id}/attachments/${att.id}`"
                        :download="
                          att.content_type.startsWith('image/') ? undefined : att.original_filename
                        "
                        :target="att.content_type.startsWith('image/') ? '_blank' : undefined"
                        @click.stop
                      ></v-btn>
                      <v-btn
                        icon="mdi-delete"
                        variant="text"
                        size="small"
                        color="error"
                        @click.stop="deleteRepairAttachment(att.id)"
                      ></v-btn>
                    </template>
                  </v-file-upload-item>
                </template>
              </v-file-upload-list>

              <!-- Upload new files -->
              <v-file-upload
                v-model="pendingAttachmentFiles"
                multiple
                inset-file-list
                show-size
                clearable
                title="Neue Anhänge hochladen"
                subtitle="Bilder, PDFs oder andere Dateien ablegen"
                browse-text="Durchsuchen"
              ></v-file-upload>
              <div v-if="pendingAttachmentFiles.length > 0" class="d-flex justify-end mt-2">
                <v-btn
                  color="primary"
                  :loading="attachmentsUploading"
                  prepend-icon="mdi-upload"
                  @click="uploadRepairAttachments"
                >
                  Hochladen
                </v-btn>
              </div>
            </div>
          </v-col>

          <!-- Right column: status + assignee -->
          <v-col cols="12" md="4">
            <div>
              <!-- Status -->
              <div class="d-flex align-center ga-3 flex-wrap mb-6">
                <v-btn-group v-if="availableNextStatuses.length > 0" variant="outlined" divided>
                  <v-btn
                    :color="getRepairStatusColor(bestNextStatus ?? '')"
                    :prepend-icon="getRepairStatusIcon(bestNextStatus ?? '')"
                    @click="bestNextStatus && handleCloseRepair(bestNextStatus)"
                  >
                    {{ bestNextStatus }}
                  </v-btn>
                  <v-menu v-if="otherNextStatuses.length > 0">
                    <template #activator="{ props: menuProps }">
                      <v-btn
                        v-bind="menuProps"
                        :color="getRepairStatusColor(bestNextStatus ?? '')"
                        icon="mdi-chevron-down"
                      ></v-btn>
                    </template>
                    <v-list density="compact">
                      <v-list-item
                        v-for="status in otherNextStatuses"
                        :key="status"
                        :prepend-icon="getRepairStatusIcon(status)"
                        :title="status"
                        @click="handleCloseRepair(status)"
                      ></v-list-item>
                    </v-list>
                  </v-menu>
                </v-btn-group>
              </div>

              <!-- Assignee -->
              <div>
                <div class="d-flex align-center mb-2">
                  <span class="text-subtitle-1 text-grey-darken-1">Zuständig</span>
                  <v-spacer></v-spacer>
                  <v-btn
                    v-if="authStore.currentUser && selectedAssigneeId !== authStore.currentUser.id"
                    variant="text"
                    size="x-small"
                    prepend-icon="mdi-account-arrow-left"
                    class="px-0"
                    @click="assignToMe"
                  >
                    Mir zuweisen
                  </v-btn>
                </div>
                <v-select
                  v-model="selectedAssigneeId"
                  :items="assigneeItems"
                  item-value="value"
                  item-title="title"
                  :loading="assigneeLoading"
                  variant="outlined"
                  density="compact"
                  clearable
                  hide-details
                  placeholder="Niemand zugewiesen"
                  @update:model-value="assignUser"
                ></v-select>
              </div>

              <!-- Actions -->
              <div class="d-flex flex-column ga-2 mt-6">
                <span class="text-subtitle-1 text-grey-darken-1">Quick Actions</span>
                <v-btn
                  variant="tonal"
                  color="primary"
                  prepend-icon="mdi-plus"
                  block
                  @click="openLogDialog"
                >
                  Neuer Logeintrag
                </v-btn>
                <v-btn
                  variant="tonal"
                  color="primary"
                  prepend-icon="mdi-flash"
                  block
                  @click="openVdeDialog"
                >
                  VDE Test protokollieren
                </v-btn>
                <v-btn
                  v-if="labelPrinterEnabled"
                  variant="tonal"
                  color="primary"
                  prepend-icon="mdi-printer"
                  :loading="printingLabel"
                  block
                  @click="printLabel"
                >
                  Label drucken
                </v-btn>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions v-if="!loading && !error" class="flex-wrap ga-2">
        <v-btn @click="goBack">
          <v-icon start>mdi-arrow-left</v-icon>
          Zurück
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Success Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>

    <!-- Log Entry Dialog -->
    <v-dialog v-model="logDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">Neue Notiz</v-card-title>

        <v-card-text>
          <v-form ref="logForm" v-model="logFormValid">
            <v-select
              v-model="newLog.user_id"
              :items="userStore.users"
              item-value="id"
              label="Reparateur"
              required
              :loading="userStore.loading"
              :rules="[(v) => !!v || 'Reparateur ist erforderlich']"
            >
              <template #item="{ props, item }">
                <v-list-item
                  v-bind="props"
                  :title="`${item.raw.vorname} ${item.raw.nachname}`"
                  :subtitle="item.raw.email"
                ></v-list-item>
              </template>
              <template #selection="{ item }">
                {{ item.raw.vorname }} {{ item.raw.nachname }}
              </template>
            </v-select>

            <v-textarea
              v-model="newLog.reparatur_besch"
              label="Was wurde gemacht?"
              rows="3"
              required
              :rules="[(v) => !!v || 'Beschreibung ist erforderlich']"
            >
            </v-textarea>

            <v-text-field
              v-model.number="newLog.reparatur_dauer"
              label="Dauer in Minuten (Optional)"
              type="number"
            >
            </v-text-field>

            <v-divider class="my-4"></v-divider>
            <div class="text-subtitle-2 mb-3">Fotos &amp; Dateien (optional)</div>

            <!-- Camera preview -->
            <div v-if="logCameraActive" class="mb-3">
              <video
                ref="logVideoElement"
                autoplay
                playsinline
                style="width: 100%; max-height: 200px; background: #000; border-radius: 4px"
              ></video>
              <canvas ref="logPhotoCanvas" style="display: none"></canvas>
            </div>

            <div class="d-flex ga-2 flex-wrap mb-3">
              <v-btn
                v-if="!logCameraActive"
                variant="outlined"
                size="small"
                prepend-icon="mdi-camera"
                :disabled="logCameraPermissionDenied"
                @click="startLogCamera"
              >
                Foto aufnehmen
              </v-btn>
              <v-btn
                v-if="logCameraActive"
                color="success"
                size="small"
                prepend-icon="mdi-camera"
                @click="captureLogPhoto"
              >
                Aufnehmen
              </v-btn>
              <v-btn
                v-if="logCameraActive"
                variant="outlined"
                size="small"
                prepend-icon="mdi-close"
                @click="stopLogCamera"
              >
                Stop
              </v-btn>
            </div>

            <v-alert v-if="logCameraPermissionDenied" type="error" density="compact" class="mb-3">
              Kamerazugriff verweigert.
            </v-alert>

            <!-- File upload with inset list -->
            <v-file-upload
              v-model="pendingLogFiles"
              multiple
              inset-file-list
              show-size
              clearable
              title="Fotos &amp; Dateien"
              subtitle="Auswählen oder ablegen"
              browse-text="Durchsuchen"
            ></v-file-upload>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-btn @click="closeLogDialog">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primary" :disabled="!logFormValid" :loading="saving" @click="addLogEntry">
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <ReparateurRequiredDialog
      v-model="transitionDialog"
      v-model:user-id="transitionUserId"
      title="Reparatur starten"
      message="Für den Wechsel von 'Offen' zu 'In Bearbeitung' muss ein Reparateur angegeben werden."
      confirm-text="Weiter"
      @confirm="confirmTransitionWithReparateur"
    />

    <RepairCompletionDialog
      v-model="completionDialog"
      v-model:description="completionData.description"
      v-model:duration="completionData.duration"
      v-model:needs-vde-test="completionData.needsVdeTest"
      :suggested-duration="suggestedRepairDuration"
      :has-any-vde-test="hasVdeTest"
      :last-vde-test-passed="lastVdeTestPassed"
      :loading="saving"
      @confirm="confirmRepairCompletion"
    />

    <RepairNotRepairableDialog
      v-model="notRepairableDialog"
      :loading="savingStatus"
      @confirm="confirmNotRepairable"
    />

    <AbbruchSignatureDialog
      v-model="abbruchSignatureDialog"
      :loading="savingStatus"
      @confirm="confirmAbbruchSignature"
    />

    <VdeTestDialog
      v-model="vdeDialog"
      :saving="saving"
      :repair-id="repairRecord?.id"
      :selected-repair-status="selectedRepairStatus"
      :required-for-status="vdeDialogMode === 'close'"
      :confirm-text="
        vdeDialogMode === 'close' ? 'VDE speichern & Reparatur abschliessen' : 'VDE speichern'
      "
      :initial-prufer-user-id="vdeInitialPruferUserId"
      :users="userStore.users"
      :pruefgeraete="pruefgeraete"
      @submit="handleVdeSubmit"
    />

    <!-- Delete Log Confirmation Dialog -->
    <v-dialog v-model="deleteLogDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Logeintrag löschen</v-card-title>
        <v-card-text
          >Soll dieser Logeintrag wirklich gelöscht werden? Diese Aktion kann nicht rückgängig
          gemacht werden.</v-card-text
        >
        <v-card-actions>
          <v-btn @click="deleteLogDialog = false">Abbrechen</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="error" :loading="deleteLogLoading" @click="confirmDeleteLog">
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Log Entry Dialog -->
    <v-dialog v-model="editLogDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">Logeintrag bearbeiten</v-card-title>
        <v-card-text>
          <v-form ref="editLogForm" v-model="editLogFormValid">
            <v-select
              v-model="editLog.user_id"
              :items="userStore.users"
              item-value="id"
              label="Reparateur"
              required
              :loading="userStore.loading"
              :rules="[(v) => !!v || 'Reparateur ist erforderlich']"
            >
              <template #item="{ props, item }">
                <v-list-item
                  v-bind="props"
                  :title="`${item.raw.vorname} ${item.raw.nachname}`"
                  :subtitle="item.raw.email"
                ></v-list-item>
              </template>
              <template #selection="{ item }">
                {{ item.raw.vorname }} {{ item.raw.nachname }}
              </template>
            </v-select>
            <v-textarea
              v-model="editLog.reparatur_besch"
              label="Was wurde gemacht?"
              rows="3"
              required
              :rules="[(v) => !!v || 'Beschreibung ist erforderlich']"
            >
            </v-textarea>
            <v-text-field
              v-model.number="editLog.reparatur_dauer"
              label="Dauer in Minuten (Optional)"
              type="number"
            >
            </v-text-field>
          </v-form>

          <template v-if="editingLogId && (logAttachments[editingLogId]?.length ?? 0) > 0">
            <v-divider class="my-4"></v-divider>
            <div class="text-subtitle-2 mb-1">Anhänge</div>
            <v-list density="compact" class="pa-0">
              <v-list-item
                v-for="att in logAttachments[editingLogId]"
                :key="att.url"
                :prepend-icon="getAttachmentIcon(att.content_type)"
                :href="att.url"
                target="_blank"
              >
                <v-list-item-title>{{ att.name }}</v-list-item-title>
                <template #append>
                  <v-btn
                    :icon="
                      att.content_type.startsWith('image/') ? 'mdi-open-in-new' : 'mdi-download'
                    "
                    variant="text"
                    size="small"
                    :href="att.url"
                    :download="att.content_type.startsWith('image/') ? undefined : att.name"
                    :target="att.content_type.startsWith('image/') ? '_blank' : undefined"
                    @click.stop
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-btn
            color="error"
            variant="text"
            prepend-icon="mdi-delete"
            :loading="deleteLogLoading"
            @click="confirmDeleteFromEditDialog"
          >
            Löschen
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="editLogDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            :disabled="!editLogFormValid"
            :loading="editLogSaving"
            @click="saveEditLog"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RepairsService } from '@/api/services/RepairsService'
import {
  normalizeRepairStatus,
  getRepairStatusColor,
  getRepairStatusIcon,
  getRepairStatusDetailOptions,
  calculateRepairDurationFromLogs,
} from '@/stores/repairStore'
import { RepairLogsService } from '@/api/services/RepairLogsService'
import { VdeTestsService, type VdeTestCreate } from '@/api/services/VdeTestsService'
import { ConfigService } from '@/api/services/ConfigService'
import type { Repair, RepairLog, VdeTestResponse, PruefgeraetResponse } from '@/api/types'
import type { VdeFormData } from '@/components/VdeTestDialog.vue'
import RepairSummaryCard from '@/components/RepairSummaryCard.vue'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'
import RepairCompletionDialog from '@/components/RepairCompletionDialog.vue'
import RepairNotRepairableDialog from '@/components/RepairNotRepairableDialog.vue'
import AbbruchSignatureDialog from '@/components/AbbruchSignatureDialog.vue'
import VdeTestDialog from '@/components/VdeTestDialog.vue'
import { useRepairThread } from '@/composables/useRepairThread'
import { useRepairStatusTransition } from '@/composables/useRepairStatusTransition'
import { useUserStore } from '@/stores/userStore'
import { useAuthStore } from '@/stores/authStore'

interface NewLogFormData {
  user_id: number | null
  reparatur_dauer: number | null
  reparatur_besch: string
}

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref('')
const saving = ref(false)
const logFormValid = ref(false)
const logForm = ref<{
  validate: () => Promise<{ valid: boolean }>
  resetValidation?: () => void
} | null>(null)

const repairRecord = ref<Repair | null>(null)
const repairLogs = ref<RepairLog[]>([])
const vdeTests = ref<VdeTestResponse[]>([])
const pruefgeraete = ref<PruefgeraetResponse[]>([])
const disclaimerExists = ref(false)
const disclaimerUrl = computed(() =>
  repairRecord.value?.id ? `/api/repairs/${repairRecord.value.id}/disclaimer` : ''
)

// Log attachments
interface AttachmentInfo {
  name: string
  url: string
  content_type: string
  size: number
}
const logAttachments = ref<Record<number, AttachmentInfo[]>>({})

// Flatten all log attachments for display in the Anhänge section
const allLogAttachmentItems = computed(() => {
  const items: AttachmentInfo[] = []
  for (const atts of Object.values(logAttachments.value)) {
    items.push(...atts)
  }
  return items
})

// Unified repair attachments (new attachment store)
interface RepairAttachment {
  id: number
  repair_id: number
  log_id: number | null
  attachment_type: string
  original_filename: string
  stored_filename: string
  content_type: string
  size: number
  uploaded_at: string
  uploaded_by_id: number | null
}
const repairAttachments = ref<RepairAttachment[]>([])
const pendingAttachmentFiles = ref<File[]>([])
const attachmentsUploading = ref(false)

// Camera state for log dialog
const logVideoElement = ref<HTMLVideoElement | null>(null)
const logPhotoCanvas = ref<HTMLCanvasElement | null>(null)
let logCameraStream: MediaStream | null = null
const logCameraActive = ref(false)
const logCameraPermissionDenied = ref(false)

// Pending files for the new log entry (shown in VFileUpload inset list)
const pendingLogFiles = ref<File[]>([])

// Repair status selection
const selectedRepairStatus = ref<string>('')
const selectedStatusDetail = ref<string>('')
const currentRepairStatus = computed(() => normalizeRepairStatus(repairRecord.value?.status))

watch(selectedRepairStatus, (newStatus) => {
  const allowedDetails = getRepairStatusDetailOptions(newStatus)
  if (selectedStatusDetail.value && !allowedDetails.includes(selectedStatusDetail.value)) {
    selectedStatusDetail.value = ''
  }
})

const { latestVdeTests, lastVdeTestPassed, threadEntries } = useRepairThread(
  repairLogs,
  vdeTests,
  repairRecord
)

const summaryVdeTests = computed(() => latestVdeTests.value)

// Check if at least one VDE test exists
const hasVdeTest = computed(() => vdeTests.value.length > 0)
const suggestedRepairDuration = computed(() => calculateRepairDurationFromLogs(repairLogs.value))

function getAttachmentIcon(contentType: string): string {
  if (contentType.startsWith('image/')) return 'mdi-image'
  if (contentType === 'application/pdf') return 'mdi-file-pdf-box'
  return 'mdi-file-outline'
}

const newLog = ref<NewLogFormData>({
  user_id: null,
  reparatur_dauer: null,
  reparatur_besch: '',
})

const logDialog = ref(false)
const vdeDialog = ref(false)
const vdeDialogMode = ref<'manual' | 'close'>('manual')
const vdeInitialPruferUserId = ref<number | null>(null)

// Delete log dialog state
const deleteLogDialog = ref(false)
const deleteLogLoading = ref(false)
const deletingLogId = ref<number | null>(null)

function openDeleteLogDialog(logId: number) {
  deletingLogId.value = logId
  deleteLogDialog.value = true
}

async function confirmDeleteLog() {
  if (!repairRecord.value || !deletingLogId.value) return
  deleteLogLoading.value = true
  try {
    const response = await RepairLogsService.deleteRepairLog(
      repairRecord.value.id,
      deletingLogId.value
    )
    if (response.reply === 'done') {
      showSnackbar('Logeintrag gelöscht')
      deleteLogDialog.value = false
      await loadRepairLogs()
    } else {
      showSnackbar(response.error || 'Fehler beim Löschen', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Löschen: ' + (err as Error).message, 'error')
  } finally {
    deleteLogLoading.value = false
    deletingLogId.value = null
  }
}

// Edit log dialog state
const editLogDialog = ref(false)
const editLogFormValid = ref(false)
const editLogSaving = ref(false)
const editingLogId = ref<number | null>(null)
const editLogForm = ref<{
  validate: () => Promise<{ valid: boolean }>
  resetValidation?: () => void
} | null>(null)
const editLog = ref({
  user_id: null as number | null,
  reparatur_besch: '',
  reparatur_dauer: 0 as number | null,
})
const labelPrinterEnabled = ref(false)
const printingLabel = ref(false)

// Assignee
const selectedAssigneeId = ref<number | null>(null)
const assigneeLoading = ref(false)
const assigneeItems = computed(() =>
  userStore.users.map((u) => ({
    value: u.id,
    title: `${u.vorname} ${u.nachname}`,
  }))
)

const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

function showSnackbar(message: string, color: string = 'success') {
  snackbar.value = {
    show: true,
    message,
    color,
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}.${month}.${year}`
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}.${month}.${year} ${hours}:${minutes}`
}

function onRepairFieldsUpdated(fields: {
  reparatur_art: string
  geraet_art: string
  defekt_besch: string
}) {
  if (repairRecord.value) {
    repairRecord.value = { ...repairRecord.value, ...fields }
  }
}

async function loadRepairLogs() {
  if (!repairRecord.value?.id) return

  try {
    const response = await RepairLogsService.listRepairLogs(repairRecord.value.id)
    if (response.data) {
      repairLogs.value = response.data
    }
  } catch (err) {
    console.error('Error loading repair logs:', err)
  }
}

async function loadVdeTests() {
  if (!repairRecord.value?.id) return

  try {
    const response = await VdeTestsService.listVdeTests(repairRecord.value.id)
    if (response.reply === 'done' && response.data) {
      vdeTests.value = response.data
    }
  } catch (err) {
    console.error('Error loading VDE tests:', err)
  }
}

async function loadPruefgeraete() {
  try {
    const devices = await ConfigService.getPruefgeraete()
    pruefgeraete.value = devices
  } catch (err) {
    console.error('Error loading testing devices:', err)
    pruefgeraete.value = []
  }
}

async function printLabel() {
  if (!repairRecord.value?.id) return
  printingLabel.value = true
  try {
    const result = await RepairsService.printLabel(repairRecord.value.id)
    showSnackbar(result.message || 'Label gedruckt')
  } catch (err: any) {
    const msg = err?.body?.error || err?.message || 'Fehler beim Drucken'
    showSnackbar(msg, 'error')
  } finally {
    printingLabel.value = false
  }
}

async function assignUser(userId: number | null) {
  if (!repairRecord.value?.id) return
  assigneeLoading.value = true
  try {
    await RepairsService.updateRepair(repairRecord.value.id, { user_id: userId })
    repairRecord.value.user_id = userId
    repairRecord.value.user = userId ? (userStore.users.find((u) => u.id === userId) ?? null) : null
    showSnackbar(userId ? 'Zuständigkeit aktualisiert' : 'Zuweisung entfernt')
  } catch (err) {
    showSnackbar('Fehler beim Zuweisen: ' + (err as Error).message, 'error')
    selectedAssigneeId.value = repairRecord.value.user_id ?? null
  } finally {
    assigneeLoading.value = false
  }
}

function assignToMe() {
  const me = authStore.currentUser
  if (!me) return
  selectedAssigneeId.value = me.id
  assignUser(me.id)
}

// ── Status-transition composable ──────────────────────────────────────────────
const {
  savingStatus,
  transitionDialog,
  transitionUserId,
  completionDialog,
  completionData,
  notRepairableDialog,
  abbruchSignatureDialog,
  availableNextStatuses,
  bestNextStatus,
  otherNextStatuses,
  handleCloseRepair,
  closeRepair,
  confirmTransitionWithReparateur,
  confirmRepairCompletion,
  confirmNotRepairable,
  confirmAbbruchSignature,
} = useRepairStatusTransition({
  repairRecord,
  selectedRepairStatus,
  selectedStatusDetail,
  currentRepairStatus,
  hasVdeTest,
  lastVdeTestPassed,
  suggestedRepairDuration,
  selectedAssigneeId,
  showSnackbar,
  loadRepairLogs,
  onNeedsVdeTest: (preFilledUserId) => openVdeDialogForCloseFlow(preFilledUserId),
})

onMounted(async () => {
  const qrToken = route.params.qrToken as string

  if (!qrToken) {
    error.value = 'Kein QR-Token angegeben'
    loading.value = false
    return
  }

  try {
    // Load testing devices and users first
    await Promise.all([
      loadPruefgeraete(),
      userStore.loaded ? Promise.resolve() : userStore.fetchUsers(),
      ConfigService.getFeatures()
        .then((f) => {
          labelPrinterEnabled.value = f.label_printer
        })
        .catch(() => {}),
    ])

    // Fetch repair data by QR token
    const response = await RepairsService.getRepairByQrToken(qrToken)

    if (!response || !response.data) {
      error.value = 'Reparatur nicht gefunden'
      loading.value = false
      return
    }

    const repair = response.data as Repair
    repairRecord.value = repair

    selectedRepairStatus.value = repair.status || 'Offen'
    selectedStatusDetail.value = repair.status_detail || ''
    selectedAssigneeId.value = repair.user_id ?? null

    vdeInitialPruferUserId.value = repair.user_id ?? null

    // Load repair logs, VDE tests, attachments, and check for disclaimer
    await Promise.all([
      loadRepairLogs(),
      loadVdeTests(),
      loadLogAttachments(),
      loadRepairAttachments(),
    ])

    // Check if disclaimer PDF exists
    if (repairRecord.value?.id) {
      try {
        const res = await fetch(`/api/repairs/${repairRecord.value.id}/disclaimer`, {
          method: 'HEAD',
        })
        disclaimerExists.value = res.ok
      } catch {
        disclaimerExists.value = false
      }
    }

    loading.value = false
  } catch (err) {
    console.error('Error loading repair:', err)
    error.value = 'Fehler beim Laden der Reparaturdaten: ' + (err as Error).message
    loading.value = false
  }
})

async function loadLogAttachments() {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/log_attachments`)
    if (res.ok) {
      const data = await res.json()
      if (data.reply === 'done') {
        const mapped: Record<number, AttachmentInfo[]> = {}
        for (const [k, v] of Object.entries(data.data as Record<string, AttachmentInfo[]>)) {
          mapped[Number(k)] = v
        }
        logAttachments.value = mapped
      }
    }
  } catch {
    // silently ignore
  }
}

async function startLogCamera() {
  try {
    logCameraPermissionDenied.value = false
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' } },
      audio: false,
    })
    logCameraStream = stream
    logCameraActive.value = true
    await nextTick()
    if (logVideoElement.value) {
      logVideoElement.value.srcObject = stream
    }
  } catch {
    logCameraPermissionDenied.value = true
  }
}

function stopLogCamera() {
  if (logCameraStream) {
    logCameraStream.getTracks().forEach((t) => t.stop())
    logCameraStream = null
  }
  if (logVideoElement.value) logVideoElement.value.srcObject = null
  logCameraActive.value = false
}

function captureLogPhoto() {
  if (!logVideoElement.value || !logPhotoCanvas.value) return
  const video = logVideoElement.value
  const canvas = logPhotoCanvas.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(video, 0, 0)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
    pendingLogFiles.value = [
      ...pendingLogFiles.value,
      dataUrlToFile(dataUrl, `foto_${Date.now()}.jpg`),
    ]
  }
}

function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header, data] = dataUrl.split(',')
  const mime = header.match(/:(.*?);/)?.[1] || 'image/jpeg'
  const bytes = atob(data)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  return new File([arr], filename, { type: mime })
}

async function uploadPendingAttachments(logId: number): Promise<void> {
  if (pendingLogFiles.value.length === 0) return
  const fd = new FormData()
  pendingLogFiles.value.forEach((f) => fd.append('files', f))
  await fetch(`/api/repair_logs/${logId}/attachments`, { method: 'POST', body: fd })
}

async function loadRepairAttachments() {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/attachments`)
    if (res.ok) {
      const data = await res.json()
      if (data.reply === 'done') {
        repairAttachments.value = data.data
      }
    }
  } catch {
    // silently ignore
  }
}

async function uploadRepairAttachments() {
  if (!repairRecord.value?.id || pendingAttachmentFiles.value.length === 0) return
  attachmentsUploading.value = true
  try {
    const fd = new FormData()
    pendingAttachmentFiles.value.forEach((f) => fd.append('files', f))
    fd.append('attachment_type', 'misc')
    if (authStore.currentUser?.id) {
      fd.append('uploaded_by_id', String(authStore.currentUser.id))
    }
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/attachments`, {
      method: 'POST',
      body: fd,
    })
    if (res.ok) {
      pendingAttachmentFiles.value = []
      await loadRepairAttachments()
      showSnackbar('Dateien hochgeladen')
    } else {
      showSnackbar('Fehler beim Hochladen', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Hochladen: ' + (err as Error).message, 'error')
  } finally {
    attachmentsUploading.value = false
  }
}

async function deleteRepairAttachment(attachmentId: number) {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/attachments/${attachmentId}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      await loadRepairAttachments()
      showSnackbar('Anhang gelöscht')
    } else {
      showSnackbar('Fehler beim Löschen', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Löschen: ' + (err as Error).message, 'error')
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} kB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function addLogEntry() {
  if (!repairRecord.value || !logForm.value) return

  const { valid } = await logForm.value.validate()

  if (!valid) return

  saving.value = true

  try {
    const response = await RepairLogsService.createRepairLog(repairRecord.value.id, {
      user_id: newLog.value.user_id ?? undefined,
      reparatur_dauer: newLog.value.reparatur_dauer ?? 0,
      reparatur_besch: newLog.value.reparatur_besch,
    })

    if (response.reply === 'done') {
      // Upload any pending attachments
      if (response.id) {
        await uploadPendingAttachments(response.id)
        await loadLogAttachments()
      }

      showSnackbar('Logeintrag erfolgreich hinzugefügt')

      // Close dialog
      closeLogDialog()

      // Reload logs
      await loadRepairLogs()
    } else {
      showSnackbar(
        'Fehler beim Hinzufügen des Logeintrags: ' + (response.error || 'Unbekannter Fehler'),
        'error'
      )
    }
  } catch (err) {
    console.error('Error adding log entry:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    saving.value = false
  }
}

function openLogDialog() {
  newLog.value.user_id = authStore.currentUser?.id ?? null
  logDialog.value = true
}

function openEditLogDialog(logId: number) {
  const log = repairLogs.value.find((l) => l.id === logId)
  if (!log) return
  editingLogId.value = logId
  editLog.value = {
    user_id: log.user_id ?? null,
    reparatur_besch: log.reparatur_besch,
    reparatur_dauer: log.reparatur_dauer ?? null,
  }
  editLogDialog.value = true
}

async function downloadVdePdf(testId: number) {
  if (!repairRecord.value?.id) return
  try {
    const res = await fetch(`/api/repairs/${repairRecord.value.id}/vde-tests/${testId}/pdf`, {
      credentials: 'include',
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `vde_pruefprotokoll_${repairRecord.value.id}_${testId}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    showSnackbar('Fehler beim Erzeugen des PDF')
  }
}

async function confirmDeleteFromEditDialog() {
  if (!editingLogId.value) return
  editLogDialog.value = false
  deletingLogId.value = editingLogId.value
  await confirmDeleteLog()
}

async function saveEditLog() {
  if (!repairRecord.value || !editingLogId.value || !editLogForm.value) return
  const { valid } = await editLogForm.value.validate()
  if (!valid) return

  editLogSaving.value = true
  try {
    const response = await RepairLogsService.updateRepairLog(
      repairRecord.value.id,
      editingLogId.value,
      {
        user_id: editLog.value.user_id ?? undefined,
        reparatur_besch: editLog.value.reparatur_besch,
        reparatur_dauer: editLog.value.reparatur_dauer ?? 0,
      }
    )
    if (response.reply === 'done') {
      showSnackbar('Logeintrag aktualisiert')
      editLogDialog.value = false
      await loadRepairLogs()
    } else {
      showSnackbar(response.error || 'Fehler beim Speichern', 'error')
    }
  } catch (err) {
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    editLogSaving.value = false
  }
}

function openVdeDialog() {
  vdeDialogMode.value = 'manual'
  vdeInitialPruferUserId.value = repairRecord.value?.user_id ?? null
  vdeDialog.value = true
}

function openVdeDialogForCloseFlow(preFilledPruferUserId?: number | null) {
  vdeDialogMode.value = 'close'
  vdeInitialPruferUserId.value = preFilledPruferUserId ?? repairRecord.value?.user_id ?? null
  vdeDialog.value = true
}

function closeLogDialog() {
  logDialog.value = false
  stopLogCamera()
  pendingLogFiles.value = []
  // Reset form after closing
  setTimeout(() => {
    newLog.value = {
      user_id: null,
      reparatur_dauer: null,
      reparatur_besch: '',
    }
    logForm.value?.resetValidation?.()
  }, 300)
}

async function handleVdeSubmit(payload: VdeFormData) {
  if (!repairRecord.value?.id) return

  saving.value = true

  try {
    const vdePayload: Omit<VdeTestCreate, 'repair_id'> = {
      // The datetime-local input gives a local-time string; convert to UTC ISO so
      // the backend stores UTC just like auto-generated created_at timestamps.
      created_at: payload.created_at ? new Date(payload.created_at).toISOString() : undefined,
      prufer_user_id: payload.prufer_user_id ?? undefined,
      electrician: payload.electrician || undefined,
      pruefgeraet_name: payload.pruefgeraet_name || undefined,
      pruefgeraet_serial: payload.pruefgeraet_serial || undefined,
      sichtpruefung_gehaeuse: payload.sichtpruefung_gehaeuse ?? undefined,
      sichtpruefung_kabel: payload.sichtpruefung_kabel ?? undefined,
      sichtpruefung_stecker: payload.sichtpruefung_stecker ?? undefined,
      sichtpruefung_zugentlastung: payload.sichtpruefung_zugentlastung ?? undefined,
      sichtpruefung_sicherheit: payload.sichtpruefung_sicherheit ?? undefined,
      schutzklasse: payload.schutzklasse || undefined,
      schutzleiter_pruefung: payload.schutzleiter_pruefung ?? undefined,
      isolationspruefung: payload.isolationspruefung ?? undefined,
      ableitstrom_pruefung: payload.ableitstrom_pruefung ?? undefined,
      gesamtergebnis: payload.gesamtergebnis!,
      bemerkungen: payload.bemerkungen || undefined,
    }

    const vdeResponse = await VdeTestsService.createVdeTest(repairRecord.value.id, vdePayload)

    if (vdeResponse.reply !== 'done') {
      showSnackbar('Fehler beim Speichern des VDE Tests', 'error')
      return
    }

    await loadVdeTests()
    vdeDialog.value = false

    if (vdeDialogMode.value === 'manual') {
      showSnackbar('VDE-Test erfolgreich protokolliert')
      return
    }

    if (!payload.gesamtergebnis) {
      selectedRepairStatus.value = repairRecord.value.status || 'In Bearbeitung'
      showSnackbar(
        'VDE-Test nicht bestanden. Die Reparatur kann nicht als repariert abgeschlossen werden. ' +
          'Bitte weiterarbeiten oder den Status auf "Nicht Repariert" setzen.',
        'warning'
      )
      return
    }

    await closeRepair('Repariert')
  } catch (err) {
    console.error('Error saving VDE test:', err)
    showSnackbar('Fehler beim Speichern: ' + (err as Error).message, 'error')
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.repair-entry {
  cursor: pointer;
}

.repair-entry:hover :deep(.v-timeline-item__body) {
  background-color: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 6px;
}
</style>
