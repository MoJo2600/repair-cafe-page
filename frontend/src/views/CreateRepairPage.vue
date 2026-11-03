<script setup lang="ts">
import { computed, nextTick, onMounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import type { VForm } from 'vuetify/components'
import { api, asFormData } from '@/api/client'
import { documentUrl } from '@/api/documents'
import type { CustomerResponse, RepairCreate } from '@/api/types'
import { useToast } from '@/composables/useToast'
import { errorMessage } from '@/utils/errors'
import { personName } from '@/utils/person'
import DevicePhotoCapture from '@/components/DevicePhotoCapture.vue'
import RepairSummaryCard from '@/components/RepairSummaryCard.vue'
import SignaturePad from '@/components/SignaturePad.vue'
import DateField from '@/components/ui/DateField.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import RepairNumber from '@/components/ui/RepairNumber.vue'

/**
 * New repair in five steps: customer, device, disclaimer (read and signed by the
 * customer, hence "Sie"), review, done. Helpers are addressed with "du".
 */
const router = useRouter()
const toast = useToast()
const { smAndDown } = useDisplay()

const STEPS = [
  { value: 1, title: 'Kunde' },
  { value: 2, title: 'Gerät' },
  { value: 3, title: 'Haftung' },
  { value: 4, title: 'Prüfen' },
  { value: 5, title: 'Fertig' },
]
const step = shallowRef(1)

// ── Form state ───────────────────────────────────────────────────────────────
function today(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

function initialForm() {
  return {
    datum: today(),
    customer: { vorname: '', nachname: '', telefon: '', email: '' },
    repair_type_id: null as number | null,
    repair_type: null as { id: number; name: string } | null,
    geraet_art: '',
    defekt_besch: '',
    status: 'Offen',
  }
}

const formData = ref(initialForm())
const devicePhotos = ref<File[]>([])
const repairTypes = ref<Array<{ id: number; name: string }>>([])
const labelPrinterEnabled = shallowRef(false)

const customerForm = ref<InstanceType<typeof VForm> | null>(null)
const deviceForm = ref<InstanceType<typeof VForm> | null>(null)

const requiredRule = (message: string) => (v: unknown) => !!v || message
const emailRules = [(v: string) => !v || /.+@.+\..+/.test(v) || 'E-Mail-Adresse ist ungültig']

onMounted(async () => {
  const [features, dropdowns] = await Promise.allSettled([
    api.getFeatures(),
    api.getDropdownConfig(),
  ])
  labelPrinterEnabled.value =
    features.status === 'fulfilled' ? (features.value.label_printer ?? false) : false
  repairTypes.value = dropdowns.status === 'fulfilled' ? dropdowns.value.repair_type : []
})

function onRepairTypeChange(id: number | null) {
  formData.value.repair_type = repairTypes.value.find((t) => t.id === id) ?? null
}

// ── Customer search (step 1) ─────────────────────────────────────────────────
const customerSearchQuery = shallowRef('')
const customerSearchResults = ref<CustomerResponse[]>([])
const customerSearchLoading = shallowRef(false)
const selectedCustomerId = ref<number | null>(null)
let customerSearchTimer: ReturnType<typeof setTimeout> | null = null

function onCustomerSearchInput(query: string) {
  customerSearchQuery.value = query
  if (customerSearchTimer) clearTimeout(customerSearchTimer)
  if (!query || query.length < 2) {
    customerSearchResults.value = []
    return
  }
  customerSearchTimer = setTimeout(async () => {
    customerSearchLoading.value = true
    try {
      customerSearchResults.value = (await api.searchCustomers({ q: query })).data
    } catch {
      customerSearchResults.value = []
    } finally {
      customerSearchLoading.value = false
    }
  }, 300)
}

const customerItemProps = (c: CustomerResponse) => ({
  title: personName(c),
  subtitle: [c.telefon, c.email].filter(Boolean).join(' · '),
  prependIcon: 'mdi-account',
})

function selectCustomer(customer: CustomerResponse | null) {
  selectedCustomerId.value = customer?.id ?? null
  if (!customer) return
  formData.value.customer = {
    vorname: customer.vorname,
    nachname: customer.nachname,
    telefon: customer.telefon ?? '',
    email: customer.email ?? '',
  }
}

// ── Disclaimer (step 3) ──────────────────────────────────────────────────────
const disclaimerMode = ref<'sign' | 'upload'>('sign')
const signatureData = ref<string | null>(null)
const signatureError = shallowRef('')
const uploadedPdfFile = ref<File | null>(null)
const uploadedPdfError = shallowRef('')
const pdfFileInput = ref<{ $el: HTMLElement } | null>(null)

watch(signatureData, (value) => {
  if (value) signatureError.value = ''
})

// Switch to upload mode and immediately open the native file picker
function openPdfDialog() {
  disclaimerMode.value = 'upload'
  void nextTick(() => pdfFileInput.value?.$el.querySelector('input')?.click())
}

/** The customer has either signed or a signed PDF is attached. */
function disclaimerComplete(): boolean {
  if (disclaimerMode.value === 'sign') {
    if (!signatureData.value) signatureError.value = 'Bitte unterschreiben Sie, um fortzufahren'
    return !!signatureData.value
  }
  if (!uploadedPdfFile.value) uploadedPdfError.value = 'Bitte eine unterschriebene PDF-Datei wählen'
  return !!uploadedPdfFile.value
}

// ── Navigation ───────────────────────────────────────────────────────────────
async function isFormValid(form: InstanceType<typeof VForm> | null): Promise<boolean> {
  return (await form?.validate())?.valid ?? false
}

async function next() {
  if (step.value === 1 && !(await isFormValid(customerForm.value))) return
  if (step.value === 2) {
    if (!(await isFormValid(deviceForm.value))) return
    // The customer signs fresh for this repair
    signatureData.value = null
  }
  if (step.value === 3 && !disclaimerComplete()) return
  step.value++
}

function cancel() {
  router.back()
}

// ── Save (step 4) ────────────────────────────────────────────────────────────
const submitting = shallowRef(false)
const createdRepairId = ref<number | null>(null)
const createdRepairQrToken = ref<string | null>(null)

async function uploadExtras(repairId: number) {
  const problems: string[] = []
  if (disclaimerMode.value === 'upload' && uploadedPdfFile.value) {
    try {
      await api.uploadRepairDisclaimer({ id: repairId }, { file: uploadedPdfFile.value })
    } catch (err) {
      console.error('Error uploading disclaimer PDF:', err)
      problems.push('Haftungsausschluss')
    }
  }
  if (devicePhotos.value.length > 0) {
    try {
      await api.uploadRepairAttachments(
        { repairId },
        asFormData({ files: devicePhotos.value, attachment_type: 'device_photo' })
      )
    } catch (err) {
      console.error('Error uploading device photos:', err)
      problems.push('Fotos')
    }
  }
  if (problems.length > 0) {
    // The repair exists; don't report the whole save as failed (risk of duplicates)
    toast.warning(
      `Reparatur erstellt, aber ${problems.join(' und ')} konnten nicht hochgeladen werden. ` +
        'Bitte in der Reparatur erneut hochladen.',
      8000
    )
  }
}

async function submit() {
  if (!disclaimerComplete()) {
    step.value = 3
    return
  }
  submitting.value = true
  try {
    const payload: RepairCreate = {
      datum: formData.value.datum,
      vorname: formData.value.customer.vorname,
      nachname: formData.value.customer.nachname,
      telefon: formData.value.customer.telefon || null,
      email: formData.value.customer.email || null,
      repair_type_id: formData.value.repair_type_id!,
      geraet_art: formData.value.geraet_art,
      defekt_besch: formData.value.defekt_besch,
      customer_id: selectedCustomerId.value,
      unterschrift: disclaimerMode.value === 'sign' ? signatureData.value : null,
    }
    const response = await api.createRepair(payload)
    if (response.reply !== 'done' || !response.id) {
      toast.error('Fehler beim Speichern der Reparatur')
      return
    }
    createdRepairId.value = response.id
    createdRepairQrToken.value = response.data?.qr_token ?? null
    await uploadExtras(response.id)
    toast.success('Reparatur erstellt')
    step.value = 5
  } catch (err) {
    console.error('Error submitting repair:', err)
    toast.error('Fehler beim Speichern der Reparatur: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    submitting.value = false
  }
}

// ── Done (step 5) ────────────────────────────────────────────────────────────
const printingLabel = shallowRef(false)
const createdDisclaimerUrl = computed(() =>
  createdRepairId.value !== null ? documentUrl(createdRepairId.value, 'disclaimer') : null
)

async function printLabel() {
  if (createdRepairId.value === null) return
  printingLabel.value = true
  try {
    const result = await api.printRepairLabel({ id: createdRepairId.value }, {})
    toast.success(result.message || 'Etikett gedruckt')
  } catch (err) {
    toast.error('Fehler beim Drucken: ' + errorMessage(err, 'Unbekannter Fehler'))
  } finally {
    printingLabel.value = false
  }
}

function openCreatedRepair() {
  if (createdRepairQrToken.value) void router.push(`/edit/${createdRepairQrToken.value}`)
}

function createAnother() {
  formData.value = initialForm()
  devicePhotos.value = []
  signatureData.value = null
  signatureError.value = ''
  disclaimerMode.value = 'sign'
  uploadedPdfFile.value = null
  uploadedPdfError.value = ''
  selectedCustomerId.value = null
  customerSearchQuery.value = ''
  customerSearchResults.value = []
  createdRepairId.value = null
  createdRepairQrToken.value = null
  step.value = 1
}
</script>

<template>
  <v-container fluid class="create-repair pb-16">
    <PageHeader title="Neue Reparatur" />

    <!-- The mobile stepper shows numbers only; name the current step -->
    <div v-if="smAndDown" class="text-title-medium mb-2">
      Schritt {{ step }} von {{ STEPS.length }} · {{ STEPS[step - 1]?.title }}
    </div>
    <v-stepper v-model="step" :items="STEPS" :mobile="smAndDown" hide-actions flat>
      <!-- Step 1: customer -->
      <template #[`item.1`]>
        <v-form ref="customerForm">
          <v-autocomplete
            v-model:search="customerSearchQuery"
            :items="customerSearchResults"
            :item-props="customerItemProps"
            :loading="customerSearchLoading"
            label="Bestehenden Kunden suchen"
            placeholder="Name, Telefon oder E-Mail"
            prepend-inner-icon="mdi-account-search"
            clearable
            no-filter
            return-object
            :hide-no-data="customerSearchQuery.length < 2"
            no-data-text="Kein Kunde gefunden"
            @update:search="onCustomerSearchInput"
            @update:model-value="selectCustomer"
          />
          <p class="text-body-small text-medium-emphasis mb-4">
            <template v-if="selectedCustomerId">
              <v-icon icon="mdi-link-variant" size="small" /> Kunde verknüpft, Felder übernommen
            </template>
            <template v-else>Kein Kunde gewählt: beim Speichern wird ein neuer angelegt</template>
          </p>

          <v-row density="compact">
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.customer.vorname"
                label="Vorname"
                :rules="[requiredRule('Vorname ist erforderlich')]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.customer.nachname"
                label="Nachname"
                :rules="[requiredRule('Nachname ist erforderlich')]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formData.customer.telefon" label="Telefon" type="tel" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.customer.email"
                label="E-Mail (optional)"
                type="email"
                :rules="emailRules"
              />
            </v-col>
          </v-row>
        </v-form>
      </template>

      <!-- Step 2: device -->
      <template #[`item.2`]>
        <v-form ref="deviceForm">
          <v-row density="compact">
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.geraet_art"
                label="Gerät"
                placeholder="z. B. Toaster, Stehlampe"
                :rules="[requiredRule('Gerät ist erforderlich')]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="formData.repair_type_id"
                label="Kategorie"
                :items="repairTypes"
                item-value="id"
                item-title="name"
                :rules="[requiredRule('Kategorie ist erforderlich')]"
                @update:model-value="onRepairTypeChange"
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="formData.defekt_besch"
                label="Beschreibung des Defekts"
                rows="3"
                :rules="[requiredRule('Beschreibung ist erforderlich')]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <DateField
                v-model="formData.datum"
                label="Angenommen am"
                :rules="[requiredRule('Datum ist erforderlich')]"
              />
            </v-col>
          </v-row>
        </v-form>

        <div class="text-title-small text-medium-emphasis mb-1">Fotos des Geräts (optional)</div>
        <p class="text-body-small text-medium-emphasis mb-3">
          Fotos dokumentieren den Zustand bei der Annahme.
        </p>
        <DevicePhotoCapture v-model="devicePhotos" :active="step === 2" />
      </template>

      <!-- Step 3: disclaimer, read and signed by the customer -->
      <template #[`item.3`]>
        <p class="text-body-medium mb-3">
          Bitte lesen Sie die Bedingungen und bestätigen Sie diese mit Ihrer Unterschrift.
        </p>
        <iframe src="/api/config/disclaimer" class="disclaimer-frame mb-4" title="Haftungsbedingungen" />

        <v-btn-toggle v-model="disclaimerMode" mandatory color="primary" variant="outlined" class="mb-4">
          <v-btn value="sign" prepend-icon="mdi-draw">Unterschreiben</v-btn>
          <v-btn value="upload" prepend-icon="mdi-upload" @click="openPdfDialog">PDF hochladen</v-btn>
        </v-btn-toggle>

        <template v-if="disclaimerMode === 'sign'">
          <p class="text-body-medium mb-2">
            Mit meiner Unterschrift bestätige ich die Bedingungen und habe die
            Datenschutzerklärung gelesen und verstanden.
          </p>
          <SignaturePad v-model="signatureData" :width="900" :height="260" :error="signatureError" />
        </template>
        <v-file-input
          v-else
          ref="pdfFileInput"
          v-model="uploadedPdfFile"
          label="Unterschriebene PDF-Datei"
          accept=".pdf,application/pdf"
          prepend-icon="mdi-file-pdf-box"
          :error-messages="uploadedPdfError"
          show-size
          @update:model-value="uploadedPdfError = ''"
        />
      </template>

      <!-- Step 4: review -->
      <template #[`item.4`]>
        <RepairSummaryCard :repair-data="formData" />
        <div class="d-flex flex-wrap ga-4 text-body-medium text-medium-emphasis">
          <span>
            <v-icon icon="mdi-camera" size="small" />
            {{ devicePhotos.length }} {{ devicePhotos.length === 1 ? 'Foto' : 'Fotos' }}
          </span>
          <span>
            <v-icon :icon="disclaimerMode === 'sign' ? 'mdi-draw' : 'mdi-file-pdf-box'" size="small" />
            {{ disclaimerMode === 'sign' ? 'Unterschrieben' : 'Unterschriebene PDF' }}
          </span>
        </div>
      </template>

      <!-- Step 5: done -->
      <template #[`item.5`]>
        <v-empty-state icon="mdi-check-circle" color="success" title="Reparatur erstellt">
          <template #media>
            <RepairNumber :id="createdRepairId ?? undefined" status="Offen" :size="72" class="mb-4" />
          </template>
          <template #text>
            Klebe das Etikett auf das Gerät und gib es zur Reparatur weiter.
          </template>
          <template #actions>
            <div class="d-flex flex-wrap justify-center ga-2">
              <v-btn
                v-if="labelPrinterEnabled"
                color="primary"
                variant="flat"
                size="large"
                prepend-icon="mdi-printer"
                :loading="printingLabel"
                @click="printLabel"
              >
                Etikett drucken
              </v-btn>
              <v-btn
                v-if="createdDisclaimerUrl"
                :href="createdDisclaimerUrl"
                target="_blank"
                variant="tonal"
                size="large"
                prepend-icon="mdi-file-pdf-box"
              >
                Haftungsausschluss
              </v-btn>
              <v-btn variant="tonal" size="large" prepend-icon="mdi-clipboard-edit" @click="openCreatedRepair">
                Reparatur öffnen
              </v-btn>
            </div>
          </template>
        </v-empty-state>
      </template>
    </v-stepper>

    <!-- Actions within thumb reach -->
    <div class="action-bar d-flex align-center ga-2 pa-3">
      <template v-if="step < 5">
        <v-btn variant="text" size="large" @click="cancel">Abbrechen</v-btn>
        <v-spacer />
        <v-btn v-if="step > 1" variant="tonal" size="large" @click="step--">Zurück</v-btn>
        <v-btn v-if="step < 4" color="primary" variant="flat" size="large" @click="next">Weiter</v-btn>
        <v-btn
          v-else
          color="primary"
          variant="flat"
          size="large"
          prepend-icon="mdi-content-save"
          :loading="submitting"
          @click="submit"
        >
          Speichern
        </v-btn>
      </template>
      <template v-else>
        <v-btn variant="text" size="large" to="/">Zur Übersicht</v-btn>
        <v-spacer />
        <v-btn color="primary" variant="flat" size="large" prepend-icon="mdi-plus" @click="createAnother">
          Weitere Reparatur
        </v-btn>
      </template>
    </div>
  </v-container>
</template>

<style scoped>
.create-repair {
  max-width: 1000px;
}

.disclaimer-frame {
  width: 100%;
  height: min(60vh, 600px);
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
}

.action-bar {
  position: sticky;
  bottom: var(--v-layout-bottom, 0px);
  z-index: 2;
  background: rgb(var(--v-theme-surface));
  border-top: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
