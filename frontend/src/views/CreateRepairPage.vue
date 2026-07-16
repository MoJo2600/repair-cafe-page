<template>
  <v-container class="d-flex justify-center align-center" style="min-height: 80vh">
    <v-card max-width="800px" width="100%">
      <v-card-title class="text-h5">Neue Reparatur erfassen</v-card-title>
      <v-card-text>
        <v-stepper v-model="step" alt-labels>
          <v-stepper-header>
            <v-stepper-item title="Kundendaten" :value="1" :complete="step > 1"></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item title="Reparaturdaten" :value="2" :complete="step > 2"></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item
              title="Haftungsbegrenzung"
              :value="3"
              :complete="step > 3"
            ></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item
              title="Zusammenfassung"
              :value="4"
              :complete="step > 4"
            ></v-stepper-item>
            <v-divider></v-divider>
            <v-stepper-item title="Bestätigung" :value="5" :complete="step > 5"></v-stepper-item>
          </v-stepper-header>
          <v-stepper-window>
            <!-- Step 1: Customer Information -->
            <v-stepper-window-item :value="1">
              <v-form ref="step1Form" v-model="step1Valid">
                <!-- Customer search -->
                <v-card variant="tonal" color="primary" class="mb-4">
                  <v-card-text>
                    <div class="text-subtitle-2 mb-2">Bestehenden Kunden suchen</div>
                    <v-autocomplete
                      v-model:search="customerSearchQuery"
                      :items="customerSearchResults"
                      :loading="customerSearchLoading"
                      :item-title="
                        (c: CustomerResponse) =>
                          `${c.vorname} ${c.nachname}${c.telefon ? ' · ' + c.telefon : ''}${c.email ? ' · ' + c.email : ''}`
                      "
                      item-value="id"
                      label="Name, Telefon oder E-Mail eingeben…"
                      prepend-inner-icon="mdi-account-search"
                      clearable
                      no-filter
                      return-object
                      hide-no-data
                      :no-data-text="
                        customerSearchQuery.length >= 2
                          ? 'Kein Kunde gefunden'
                          : 'Mindestens 2 Zeichen eingeben'
                      "
                      @update:search="onCustomerSearchInput"
                      @update:model-value="selectCustomer"
                    ></v-autocomplete>
                    <div v-if="selectedCustomerId" class="text-caption text-success">
                      <v-icon size="x-small">mdi-check-circle</v-icon>
                      Kunde verknüpft · Felder wurden ausgefüllt
                    </div>
                    <div v-else class="text-caption text-medium-emphasis">
                      Kein Kunde ausgewählt — beim Speichern wird ein neuer Eintrag erstellt
                    </div>
                  </v-card-text>
                </v-card>

                <v-text-field
                  v-model="formData.datum"
                  label="Datum"
                  type="date"
                  required
                  :rules="[(v) => !!v || 'Datum ist erforderlich']"
                ></v-text-field>
                <v-text-field
                  v-model="formData.customer.nachname"
                  label="Nachname"
                  required
                  :rules="[(v) => !!v || 'Nachname ist erforderlich']"
                ></v-text-field>
                <v-text-field
                  v-model="formData.customer.vorname"
                  label="Vorname"
                  required
                  :rules="[(v) => !!v || 'Vorname ist erforderlich']"
                ></v-text-field>
                <v-text-field v-model="formData.customer.telefon" label="Telefon"></v-text-field>
                <v-text-field
                  v-model="formData.customer.email"
                  label="Email (optional)"
                  type="email"
                  :rules="emailRules"
                ></v-text-field>
              </v-form>
            </v-stepper-window-item>

            <!-- Step 2: Repair Information -->
            <v-stepper-window-item :value="2">
              <v-form ref="step2Form" v-model="step2Valid">
                <v-select
                  v-model="formData.repair_type_id"
                  label="Kategorie"
                  :items="repairTypes"
                  item-value="id"
                  item-title="name"
                  required
                  :rules="[(v) => !!v || 'Kategorie ist erforderlich']"
                  @update:model-value="onRepairTypeChange"
                ></v-select>
                <v-text-field
                  v-model="formData.geraet_art"
                  label="Geräte Art / Bezeichnung"
                  required
                  :rules="[(v) => !!v || 'Geräte Art / Bezeichnung ist erforderlich']"
                ></v-text-field>
                <v-textarea
                  v-model="formData.defekt_besch"
                  label="Beschreibung des Defekts"
                  rows="3"
                  required
                  :rules="[(v) => !!v || 'Beschreibung ist erforderlich']"
                ></v-textarea>

                <!-- Photo Capture Section -->
                <v-card variant="outlined" class="mt-4">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2">mdi-camera</v-icon>
                    Fotos des Geräts
                  </v-card-title>
                  <v-card-text>
                    <p class="text-caption mb-3">
                      Nehmen Sie Fotos des Geräts auf, um den Zustand zu dokumentieren.
                    </p>

                    <!-- Camera preview -->
                    <div v-if="cameraActive" class="mb-3">
                      <video
                        ref="videoElement"
                        autoplay
                        playsinline
                        style="width: 100%; max-height: 400px; background: #000; border-radius: 4px"
                      ></video>
                      <canvas ref="photoCanvas" style="display: none"></canvas>
                    </div>

                    <!-- Camera controls -->
                    <div class="d-flex gap-2 mb-3">
                      <v-btn
                        v-if="!cameraActive"
                        color="primary"
                        prepend-icon="mdi-camera"
                        :disabled="cameraPermissionDenied"
                        @click="startCamera"
                      >
                        Kamera starten
                      </v-btn>
                      <v-btn
                        v-if="cameraActive"
                        color="success"
                        prepend-icon="mdi-camera"
                        @click="capturePhoto"
                      >
                        Foto aufnehmen
                      </v-btn>
                      <v-btn
                        v-if="cameraActive"
                        color="grey"
                        variant="outlined"
                        prepend-icon="mdi-close"
                        @click="stopCamera"
                      >
                        Kamera stoppen
                      </v-btn>
                    </div>

                    <v-alert v-if="cameraPermissionDenied" type="error" class="mb-3">
                      Kamerazugriff wurde verweigert. Bitte erlauben Sie den Kamerazugriff in Ihren
                      Browser-Einstellungen.
                    </v-alert>

                    <!-- Captured photos gallery -->
                    <div v-if="devicePhotos.length > 0">
                      <v-divider class="mb-3"></v-divider>
                      <div class="text-subtitle-2 mb-2">
                        Aufgenommene Fotos ({{ devicePhotos.length }})
                      </div>
                      <v-row>
                        <v-col
                          v-for="(photo, index) in devicePhotos"
                          :key="index"
                          cols="6"
                          sm="4"
                          md="3"
                        >
                          <v-card>
                            <v-img
                              :src="photo"
                              aspect-ratio="1"
                              cover
                              class="cursor-pointer"
                              @click="viewPhoto(photo)"
                            >
                              <template #placeholder>
                                <v-row class="fill-height ma-0" align="center" justify="center">
                                  <v-progress-circular
                                    indeterminate
                                    color="grey-lighten-5"
                                  ></v-progress-circular>
                                </v-row>
                              </template>
                            </v-img>
                            <v-card-actions>
                              <v-spacer></v-spacer>
                              <v-btn
                                icon="mdi-delete"
                                size="small"
                                color="error"
                                variant="text"
                                @click="deletePhoto(index)"
                              ></v-btn>
                            </v-card-actions>
                          </v-card>
                        </v-col>
                      </v-row>
                    </div>
                  </v-card-text>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Step 3: Haftungsbegrenzung -->
            <v-stepper-window-item :value="3">
              <v-form ref="step3Form" v-model="step3Valid">
                <v-card variant="outlined" class="mb-4">
                  <v-card-title class="text-h6">Bedingungen</v-card-title>
                  <v-card-text>
                    <iframe
                      src="/api/config/disclaimer"
                      width="100%"
                      height="500px"
                      style="border: none"
                      title="Disclaimer"
                    ></iframe>
                  </v-card-text>
                </v-card>

                <!-- Mode toggle -->
                <v-btn-toggle
                  v-model="disclaimerMode"
                  mandatory
                  color="primary"
                  class="mb-4"
                  density="comfortable"
                >
                  <v-btn value="sign" prepend-icon="mdi-draw"> Unterschreiben </v-btn>
                  <v-btn value="upload" prepend-icon="mdi-upload" @click="openPdfDialog">
                    PDF hochladen
                  </v-btn>
                </v-btn-toggle>

                <!-- Signature card -->
                <v-card v-if="disclaimerMode === 'sign'" variant="outlined" class="mb-4">
                  <v-card-title class="text-h6">Unterschrift</v-card-title>
                  <v-card-text>
                    <p class="mb-3">
                      Mit meiner Unterschrift bestätige ich die Bedingungen und bestätige die
                      Datenschutzerklärung gelesen und verstanden zu haben:
                    </p>
                    <div class="signature-container" :class="{ 'error-border': signatureError }">
                      <canvas
                        ref="signatureCanvas"
                        width="700"
                        height="200"
                        style="
                          border: 1px solid #ccc;
                          cursor: crosshair;
                          width: 100%;
                          max-width: 700px;
                          touch-action: none;
                        "
                        @mousedown="startDrawing"
                        @mousemove="draw"
                        @mouseup="stopDrawing"
                        @mouseleave="stopDrawing"
                        @touchstart="startDrawingTouch"
                        @touchmove="drawTouch"
                        @touchend="stopDrawing"
                      ></canvas>
                    </div>
                    <v-btn variant="outlined" size="small" class="mt-2" @click="clearSignature">
                      Unterschrift löschen
                    </v-btn>
                    <div v-if="signatureError" class="text-error text-caption mt-1">
                      {{ signatureError }}
                    </div>
                  </v-card-text>
                </v-card>

                <!-- Upload card -->
                <v-card v-else variant="outlined" class="mb-4">
                  <v-card-title class="text-h6">PDF hochladen</v-card-title>
                  <v-card-text>
                    <p class="mb-3">
                      Laden Sie eine bereits unterschriebene Haftungsausschluss-PDF hoch:
                    </p>
                    <v-file-input
                      ref="pdfFileInput"
                      v-model="uploadedPdfFile"
                      label="PDF-Datei auswählen"
                      accept=".pdf,application/pdf"
                      prepend-icon="mdi-file-pdf-box"
                      :error-messages="uploadedPdfError"
                      show-size
                      @update:model-value="uploadedPdfError = ''"
                    ></v-file-input>
                  </v-card-text>
                </v-card>
              </v-form>
            </v-stepper-window-item>

            <!-- Step 4: Review -->
            <v-stepper-window-item :value="4">
              <RepairSummaryCard :repair-data="formData" />
            </v-stepper-window-item>

            <!-- Step 4: Confirmation -->
            <v-stepper-window-item :value="5">
              <v-card variant="outlined" class="mb-4">
                <v-card-text class="text-center pa-8">
                  <v-icon size="80" color="success" class="mb-4">mdi-check-circle</v-icon>
                  <h2 class="text-h4 mb-4">Reparatur erfolgreich erstellt!</h2>
                  <v-divider class="my-4"></v-divider>
                  <div class="text-h5 mb-2">Reparatur ID:</div>
                  <div class="text-h3 font-weight-bold primary--text mb-4">
                    <router-link :to="`/edit/${createdRepairQrToken}`">{{ createdRepairId }}</router-link>
                  </div>
                  <p class="text-body-1 mb-4">
                    Die Reparatur wurde erfolgreich im System erfasst. Sie können diese ID
                    verwenden, um den Status der Reparatur zu verfolgen.
                  </p>
                  <v-card variant="outlined" class="mt-4 pa-4">
                    <div class="text-subtitle-1 font-weight-bold mb-2">Nächste Schritte:</div>
                    <v-list density="compact">
                      <v-list-item prepend-icon="mdi-printer">
                        <v-list-item-title
                          >Kleben Sie den gedrucken QR Code auf das Gerät</v-list-item-title
                        >
                      </v-list-item>
                      <v-list-item prepend-icon="mdi-clipboard-check">
                        <v-list-item-title>Übergeben Sie das Gerät zur Reparatur</v-list-item-title>
                      </v-list-item>
                      <v-list-item prepend-icon="mdi-qrcode">
                        <v-list-item-title
                          >Scannen Sie den QR-Code für schnellen Zugriff</v-list-item-title
                        >
                      </v-list-item>
                    </v-list>
                  </v-card>

                  <v-btn
                    v-if="disclaimerUrl"
                    :href="disclaimerUrl"
                    target="_blank"
                    color="primary"
                    variant="outlined"
                    prepend-icon="mdi-file-pdf-box"
                    class="mt-6"
                    download
                  >
                    Haftungsausschluss herunterladen &amp; drucken
                  </v-btn>

                  <div v-if="labelPrinterEnabled" class="mt-4">
                    <v-btn
                      color="secondary"
                      variant="tonal"
                      prepend-icon="mdi-printer"
                      :loading="printingLabel"
                      :disabled="createdRepairId === null"
                      @click="printLabel"
                    >
                      Etikett drucken
                    </v-btn>
                    <div v-if="printLabelError" class="text-error text-caption mt-1">
                      {{ printLabelError }}
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-stepper-window-item>
          </v-stepper-window>
        </v-stepper>
      </v-card-text>
      <v-card-actions>
        <v-btn v-if="step < 4" @click="goBack">Abbrechen</v-btn>
        <v-spacer></v-spacer>
        <v-btn v-if="step > 1 && step < 4" @click="step--">Zurück</v-btn>
        <v-btn v-if="step < 4" color="primary" @click="nextStep">Weiter</v-btn>
        <v-btn v-if="step === 4" color="primary" :loading="submitting" @click="submitForm"
          >Speichern</v-btn
        >
        <v-btn v-if="step === 5" color="primary" @click="goToRepairsList">Zur Reparaturliste</v-btn>
        <v-btn v-if="step === 5" color="secondary" variant="outlined" @click="createAnother"
          >Weitere Reparatur erfassen</v-btn
        >
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, inject, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ConfigService } from '@/api/services/ConfigService'
import { RepairsService } from '@/api/services/RepairsService'
import { CustomersService, type CustomerResponse } from '@/api/services/CustomersService'
import RepairSummaryCard from '@/components/RepairSummaryCard.vue'

const step = ref(1)
const step1Valid = ref(false)
const step2Valid = ref(false)
const step3Valid = ref(false)
const step1Form = ref<any>(null)
const step2Form = ref<any>(null)
const step3Form = ref<any>(null)
const submitting = ref(false)
const createdRepairId = ref<number | null>(null)
const createdRepairQrToken = ref<number | null>(null)
const printingLabel = ref(false)
const printLabelError = ref('')
const labelPrinterEnabled = ref(false)

const disclaimerUrl = computed(() =>
  createdRepairId.value !== null ? `/api/repairs/${createdRepairId.value}/disclaimer` : null
)

const showToast = inject('showToast') as
  | undefined
  | ((message: string, options?: { color?: string; timeout?: number }) => void)

// Repair types loaded from settings API
const repairTypes = ref<Array<{ id: number; name: string }>>([])

onMounted(async () => {
  try {
    const features = await ConfigService.getFeatures()
    labelPrinterEnabled.value = features.label_printer
  } catch {
    labelPrinterEnabled.value = false
  }
  try {
    const cfg = await ConfigService.getDropdownConfig()
    repairTypes.value = cfg.repair_type ?? []
  } catch {
    repairTypes.value = []
  }
})

// Initialize with current date
const now = new Date()
const year = now.getFullYear()
const month = String(now.getMonth() + 1).padStart(2, '0')
const day = String(now.getDate()).padStart(2, '0')

const formData = ref({
  datum: `${year}-${month}-${day}`,
  customer: {
    vorname: '',
    nachname: '',
    telefon: '',
    email: '',
  },
  repair_type_id: null as number | null,
  repair_type: null as { id: number; name: string } | null,
  geraet_art: '',
  defekt_besch: '',
  status: 'Offen',
})

const termsAccepted = ref(false)

// Disclaimer mode: 'sign' or 'upload'
const disclaimerMode = ref<'sign' | 'upload'>('sign')
const uploadedPdfFile = ref<File | null>(null)
const uploadedPdfError = ref('')
const pdfFileInput = ref<{ $el: HTMLElement } | null>(null)

// Switch to upload mode and immediately open the native file picker
function openPdfDialog() {
  disclaimerMode.value = 'upload'
  nextTick(() => {
    pdfFileInput.value?.$el?.querySelector('input')?.click()
  })
}

// Signature pad variables
const signatureCanvas = ref<HTMLCanvasElement | null>(null)
const isDrawing = ref(false)
const signatureData = ref<string | null>(null)
const signatureError = ref('')

// Camera and photo variables
const videoElement = ref<HTMLVideoElement | null>(null)
const photoCanvas = ref<HTMLCanvasElement | null>(null)
const cameraActive = ref(false)
const cameraPermissionDenied = ref(false)
const devicePhotos = ref<string[]>([])
let cameraStream: MediaStream | null = null

// Email validation rules: optional but must be valid if provided
const emailRules = [(v: string) => !v || /.+@.+\..+/.test(v) || 'Email muss gültig sein']

// Customer search state
const customerSearchQuery = ref('')
const customerSearchResults = ref<CustomerResponse[]>([])
const customerSearchLoading = ref(false)
const selectedCustomerId = ref<number | null>(null)
let customerSearchTimer: ReturnType<typeof setTimeout> | null = null

async function onCustomerSearchInput(query: string) {
  customerSearchQuery.value = query
  if (customerSearchTimer) clearTimeout(customerSearchTimer)
  if (!query || query.length < 2) {
    customerSearchResults.value = []
    return
  }
  customerSearchTimer = setTimeout(async () => {
    customerSearchLoading.value = true
    try {
      const res = await CustomersService.searchCustomers(query)
      customerSearchResults.value = res.data ?? []
    } catch {
      customerSearchResults.value = []
    } finally {
      customerSearchLoading.value = false
    }
  }, 300)
}

function selectCustomer(customer: CustomerResponse | null) {
  if (!customer) {
    selectedCustomerId.value = null
    return
  }
  selectedCustomerId.value = customer.id
  formData.value.customer.nachname = customer.nachname
  formData.value.customer.vorname = customer.vorname
  formData.value.customer.telefon = customer.telefon ?? ''
  formData.value.customer.email = customer.email ?? ''
}

function onRepairTypeChange(id: number | null) {
  const found = repairTypes.value.find((t) => t.id === id) ?? null
  formData.value.repair_type = found
}

const router = useRouter()

// Signature pad functions
function getContext(): CanvasRenderingContext2D | null {
  if (!signatureCanvas.value) return null
  return signatureCanvas.value.getContext('2d')
}

function startDrawing(event: MouseEvent) {
  isDrawing.value = true
  const ctx = getContext()
  if (!ctx) return

  const rect = signatureCanvas.value!.getBoundingClientRect()
  const scaleX = signatureCanvas.value!.width / rect.width
  const scaleY = signatureCanvas.value!.height / rect.height

  ctx.beginPath()
  ctx.moveTo((event.clientX - rect.left) * scaleX, (event.clientY - rect.top) * scaleY)
  signatureError.value = ''
}

function draw(event: MouseEvent) {
  if (!isDrawing.value) return
  const ctx = getContext()
  if (!ctx) return

  const rect = signatureCanvas.value!.getBoundingClientRect()
  const scaleX = signatureCanvas.value!.width / rect.width
  const scaleY = signatureCanvas.value!.height / rect.height

  ctx.lineTo((event.clientX - rect.left) * scaleX, (event.clientY - rect.top) * scaleY)
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.stroke()
}

function stopDrawing() {
  if (isDrawing.value) {
    isDrawing.value = false
    saveSignature()
  }
}

function startDrawingTouch(event: TouchEvent) {
  event.preventDefault()
  isDrawing.value = true
  const ctx = getContext()
  if (!ctx) return

  const rect = signatureCanvas.value!.getBoundingClientRect()
  const scaleX = signatureCanvas.value!.width / rect.width
  const scaleY = signatureCanvas.value!.height / rect.height
  const touch = event.touches[0]

  ctx.beginPath()
  ctx.moveTo((touch.clientX - rect.left) * scaleX, (touch.clientY - rect.top) * scaleY)
  signatureError.value = ''
}

function drawTouch(event: TouchEvent) {
  event.preventDefault()
  if (!isDrawing.value) return
  const ctx = getContext()
  if (!ctx) return

  const rect = signatureCanvas.value!.getBoundingClientRect()
  const scaleX = signatureCanvas.value!.width / rect.width
  const scaleY = signatureCanvas.value!.height / rect.height
  const touch = event.touches[0]

  ctx.lineTo((touch.clientX - rect.left) * scaleX, (touch.clientY - rect.top) * scaleY)
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.stroke()
}

function saveSignature() {
  if (!signatureCanvas.value) return
  signatureData.value = signatureCanvas.value.toDataURL()
}

function clearSignature() {
  const ctx = getContext()
  if (!ctx || !signatureCanvas.value) return

  ctx.clearRect(0, 0, signatureCanvas.value.width, signatureCanvas.value.height)
  signatureData.value = null
  signatureError.value = ''
}

function isCanvasEmpty(): boolean {
  if (!signatureCanvas.value) return true
  const ctx = getContext()
  if (!ctx) return true

  const pixelData = ctx.getImageData(
    0,
    0,
    signatureCanvas.value.width,
    signatureCanvas.value.height
  )
  return !pixelData.data.some((channel) => channel !== 0)
}

async function nextStep() {
  if (step.value === 1) {
    const { valid } = await step1Form.value.validate()
    if (valid) {
      step.value++
    }
  } else if (step.value === 2) {
    const { valid } = await step2Form.value.validate()
    if (valid) {
      // Stop camera when leaving step 2
      if (cameraActive.value) {
        stopCamera()
      }
      termsAccepted.value = false
      clearSignature() // Clear signature when moving to review
      step.value++
    }
  } else if (step.value === 3) {
    const { valid } = await step3Form.value.validate()
    if (valid) {
      // Stop camera when leaving step 3
      step.value++
    }
  }
}

async function submitForm() {
  // Validate disclaimer
  if (disclaimerMode.value === 'sign') {
    if (isCanvasEmpty()) {
      signatureError.value = 'Bitte unterschreiben Sie, um fortzufahren'
      return
    }
  } else {
    if (!uploadedPdfFile.value) {
      uploadedPdfError.value = 'Bitte laden Sie eine PDF-Datei hoch'
      step.value = 3
      return
    }
  }

  const { valid } = await step3Form.value.validate()
  if (valid) {
    submitting.value = true
    try {
      // Prepare data for API
      const repairData: Record<string, unknown> = {
        datum: formData.value.datum,
        nachname: formData.value.customer.nachname,
        vorname: formData.value.customer.vorname,
        telefon: formData.value.customer.telefon,
        email: formData.value.customer.email,
        repair_type_id: formData.value.repair_type_id,
        geraet_art: formData.value.geraet_art,
        defekt_besch: formData.value.defekt_besch,
      }
      if (selectedCustomerId.value !== null) {
        repairData.customer_id = selectedCustomerId.value
      }
      if (disclaimerMode.value === 'sign') {
        repairData.unterschrift = signatureData.value
      }

      // Call API to create repair
      const response = await RepairsService.createRepair(repairData as any)

      if (response.reply === 'done') {
        createdRepairId.value = response.id || null
        createdRepairQrToken.value = response.data.qr_token || null

        // Upload pre-signed PDF if applicable
        if (
          disclaimerMode.value === 'upload' &&
          uploadedPdfFile.value &&
          createdRepairId.value !== null
        ) {
          const fd = new FormData()
          fd.append('file', uploadedPdfFile.value)
          await fetch(`/api/repairs/${createdRepairId.value}/disclaimer`, {
            method: 'POST',
            body: fd,
          })
        }

        showToast?.('Reparatur erfolgreich erstellt', { color: 'success' })
        // Move to confirmation step
        step.value = 5
      } else {
        console.error('Error creating repair:', response)
        showToast?.('Fehler beim Speichern der Reparatur', { color: 'error' })
      }
    } catch (error) {
      console.error('Error submitting repair:', error)
      const errorMessage =
        (error as any)?.body?.error || (error as Error).message || 'Unbekannter Fehler'
      showToast?.(`Fehler beim Speichern der Reparatur: ${errorMessage}`, { color: 'error' })
    } finally {
      submitting.value = false
    }
  }
}

function goToRepairsList() {
  router.push('/repairs')
}

function createAnother() {
  // Reset form
  step.value = 1
  createdRepairId.value = null
  printLabelError.value = ''
  formData.value = {
    datum: `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}-${String(new Date().getDate()).padStart(2, '0')}`,
    customer: {
      nachname: '',
      vorname: '',
      telefon: '',
      email: '',
    },
    repair_type_id: null,
    repair_type: null,
    geraet_art: '',
    defekt_besch: '',
    status: 'Offen',
  }
  signatureData.value = null
  signatureError.value = ''
  clearSignature()
  disclaimerMode.value = 'sign'
  uploadedPdfFile.value = null
  uploadedPdfError.value = ''
  selectedCustomerId.value = null
  customerSearchQuery.value = ''
  customerSearchResults.value = []
}

async function printLabel() {
  if (createdRepairId.value === null) return
  printingLabel.value = true
  printLabelError.value = ''
  try {
    const result = await RepairsService.printLabel(createdRepairId.value)
    if (result.reply === 'done') {
      showToast?.('Etikett erfolgreich gedruckt', { color: 'success' })
    } else {
      printLabelError.value = result.error ?? 'Drucken fehlgeschlagen'
      showToast?.(printLabelError.value, { color: 'error' })
    }
  } catch (error) {
    printLabelError.value =
      (error as any)?.body?.error ?? (error as Error).message ?? 'Unbekannter Fehler'
    showToast?.(`Fehler beim Drucken: ${printLabelError.value}`, { color: 'error' })
  } finally {
    printingLabel.value = false
  }
}

// Camera functions
async function startCamera() {
  try {
    cameraPermissionDenied.value = false
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }, // Use back camera on mobile if available
      audio: false,
    })
    cameraStream = stream
    if (videoElement.value) {
      videoElement.value.srcObject = stream
      cameraActive.value = true
    }
  } catch (error) {
    console.error('Error accessing camera:', error)
    cameraPermissionDenied.value = true
    showToast?.('Fehler beim Zugriff auf die Kamera', { color: 'error' })
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop())
    cameraStream = null
  }
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
  cameraActive.value = false
}

function capturePhoto() {
  if (!videoElement.value || !photoCanvas.value) return

  const video = videoElement.value
  const canvas = photoCanvas.value

  // Set canvas dimensions to match video
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  // Draw the current video frame to the canvas
  const context = canvas.getContext('2d')
  if (context) {
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert canvas to base64 image
    const photoData = canvas.toDataURL('image/jpeg', 0.8)
    devicePhotos.value.push(photoData)

    showToast?.('Foto aufgenommen', { color: 'success', timeout: 2000 })
  }
}

function deletePhoto(index: number) {
  devicePhotos.value.splice(index, 1)
  showToast?.('Foto gelöscht', { color: 'info', timeout: 2000 })
}

function viewPhoto(photo: string) {
  // Open photo in new window/tab
  const win = window.open()
  if (win) {
    win.document.write(`<img src="${photo}" style="max-width: 100%; height: auto;" />`)
  }
}

function goBack() {
  // Stop camera if active
  if (cameraActive.value) {
    stopCamera()
  }
  router.back()
}
</script>

<style scoped>
.signature-container {
  display: inline-block;
}

.signature-container.error-border canvas {
  border-color: rgb(var(--v-theme-error)) !important;
  border-width: 2px;
}

.cursor-pointer {
  cursor: pointer;
}

.gap-2 {
  gap: 8px;
}
</style>
