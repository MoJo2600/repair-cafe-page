<template>
  <v-container fluid class="pa-4">
    <!-- Header -->
    <v-row align="center" class="mb-4">
      <v-col>
        <h1 class="text-h5 font-weight-bold">Reparaturliste</h1>
      </v-col>
      <v-col cols="auto">
        <v-btn color="success" prepend-icon="mdi-plus" class="mr-2" @click="createNewRepair">
          Neue Reparatur
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-refresh" :loading="loading" @click="loadRepairs">
          Aktualisieren
        </v-btn>
      </v-col>
    </v-row>

    <!-- Filter row -->
    <v-row class="mb-2">
      <v-col cols="12" sm="4">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Suchen…"
          variant="outlined"
          density="compact"
          clearable
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="filterStatus"
          :items="statusFilterOptions"
          label="Status"
          variant="outlined"
          density="compact"
          hide-details
        />
      </v-col>
      <v-spacer />
      <v-col cols="auto" class="text-body-2 text-medium-emphasis align-self-center">
        {{ filteredRepairs.length }} von {{ totalCount }}
      </v-col>
    </v-row>

    <!-- Customer filter indicator -->
    <v-row v-if="customerFilter" class="mb-2">
      <v-col cols="auto">
        <v-chip
          closable
          color="primary"
          prepend-icon="mdi-account"
          @click:close="clearCustomerFilter"
        >
          {{ customerFilter.name }}
        </v-chip>
      </v-col>
    </v-row>

    <!-- Repairs table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="filteredRepairs"
        :search="search"
        :custom-filter="customerNameFilter"
        :loading="loading"
        :items-per-page="10"
        @click:row="(_e: MouseEvent, { item }: { item: Repair }) => editRepair(item)"
        hover
      >
        <template #item.status="{ item }">
          <v-chip :color="getRepairStatusColor(item.status)" size="small">
            {{ item.status }}
          </v-chip>
        </template>

        <template #item.repair_type="{ item }">
          {{ item.repair_type?.name || '-' }}
        </template>

        <template #item.geraet_art="{ item }">
          {{ item.geraet_art }}
        </template>

        <template #item.status_detail="{ item }">
          {{ item.status_detail || '-' }}
        </template>

        <template #item.reparatur_dauer="{ item }"> {{ item.reparatur_dauer }} min </template>

        <template #item.datum="{ item }">
          {{ formatDate(item.datum) }}
        </template>

        <template #item.closed_at="{ item }">
          {{ item.closed_at ? formatDateTime(item.closed_at) : '-' }}
        </template>

        <template #item.actions="{ item }">
          <v-btn
            icon="mdi-pencil"
            size="small"
            variant="text"
            density="compact"
            @click.stop="editRepair(item)"
          />
          <v-btn
            v-if="labelPrinterEnabled"
            icon="mdi-printer"
            size="small"
            variant="text"
            density="compact"
            :loading="printingLabelId === item.id"
            @click.stop="printLabel(item.id)"
          />
          <v-btn
            icon="mdi-delete"
            size="small"
            variant="text"
            density="compact"
            color="error"
            @click.stop="deleteRepair(item.id)"
          />
        </template>

        <template #loading>
          <v-skeleton-loader type="table-row@10" />
        </template>

        <template #no-data>
          <v-alert type="info" class="ma-4"> Keine Reparaturen gefunden. </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="420">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="error" class="mr-2">mdi-delete-alert</v-icon>
          Reparatur löschen?
        </v-card-title>
        <v-card-text>
          Möchten Sie die Reparatur <strong>#{{ deleteTargetId }}</strong> wirklich löschen? Diese
          Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" :disabled="deleting" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" variant="elevated" :loading="deleting" @click="confirmDelete"
            >Löschen</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="800" persistent>
      <v-card>
        <v-card-title class="text-h5">
          <v-icon icon="mdi-pencil" class="mr-2" />
          Reparatur bearbeiten #{{ editedItem.id }}
        </v-card-title>
        <v-card-text>
          <v-form ref="editForm">
            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="editedItem.datum"
                  label="Datum"
                  type="date"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.status"
                  :items="statusOptions"
                  label="Status"
                  variant="outlined"
                  density="comfortable"
                  required
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.status_detail"
                  :items="currentStatusDetailOptions"
                  label="Status Detail"
                  variant="outlined"
                  density="comfortable"
                  clearable
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.repair_type_id"
                  :items="repairTypes"
                  item-value="id"
                  item-title="name"
                  label="Reparaturart"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  :model-value="editedItem.customer?.vorname"
                  label="Vorname"
                  variant="outlined"
                  density="comfortable"
                  readonly
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  :model-value="editedItem.customer?.nachname"
                  label="Nachname"
                  variant="outlined"
                  density="comfortable"
                  readonly
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  :model-value="editedItem.customer?.telefon"
                  label="Telefon"
                  variant="outlined"
                  density="comfortable"
                  readonly
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  :model-value="editedItem.customer?.email"
                  label="E-Mail"
                  type="email"
                  variant="outlined"
                  density="comfortable"
                  readonly
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="editedItem.reparatur_sonstiges"
                  label="Sonstiges"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="editedItem.geraet_art"
                  label="Geräteart"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editedItem.defekt_besch"
                  label="Defektbeschreibung"
                  rows="3"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editedItem.reparatur_besch"
                  label="Reparaturbeschreibung"
                  rows="3"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="editedItem.user_id"
                  :items="userStore.users"
                  item-value="id"
                  :item-title="(u: any) => `${u.vorname} ${u.nachname}`"
                  label="Reparateur"
                  variant="outlined"
                  density="comfortable"
                  clearable
                  :loading="userStore.loading"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model.number="editedItem.reparatur_dauer"
                  label="Dauer (Minuten)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="12">
                <v-switch
                  v-model="editedItem.din_pruef"
                  label="DIN-Prüfung"
                  color="primary"
                  :true-value="true"
                  :false-value="false"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" :disabled="saving" @click="closeEditDialog">Abbrechen</v-btn>
          <v-btn color="primary" variant="elevated" :loading="saving" @click="saveRepair"
            >Speichern</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RepairsService } from '@/api/services/RepairsService'
import { ConfigService } from '@/api/services/ConfigService'
import { useUserStore } from '@/stores/userStore'
import type { Repair } from '@/api/types'
import {
  REPAIR_STATUSES,
  REPAIR_STATUS_DETAIL_OPTIONS,
  getRepairStatusColor,
  isOpenRepairStatus,
  isClosedRepairStatus,
  type RepairStatus,
} from '@/stores/repairStore'

type RepairEditForm = Partial<Omit<Repair, 'status'>> & { status?: RepairStatus }

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const repairs = ref<Repair[]>([])
const loading = ref(false)
const totalCount = ref(0)

const labelPrinterEnabled = ref(false)
const printingLabelId = ref<number | null>(null)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

function showMsg(text: string, color = 'success') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}
const filterStatus = ref<'open' | 'closed' | 'all'>('open')
const search = ref('')
const customerFilter = ref<{ id: number; name: string } | null>(null)

const statusFilterOptions = [
  { title: 'Offen', value: 'open' },
  { title: 'Geschlossen', value: 'closed' },
  { title: 'Alle', value: 'all' },
]

// Computed property to filter repairs based on status
const filteredRepairs = computed(() => {
  if (filterStatus.value === 'all') {
    return repairs.value
  } else if (filterStatus.value === 'open') {
    return repairs.value.filter((repair) => isOpenRepairStatus(repair.status))
  } else {
    return repairs.value.filter((repair) => isClosedRepairStatus(repair.status))
  }
})

// Edit dialog state
const editDialog = ref(false)
const saving = ref(false)
const editedItem = ref<RepairEditForm>({})
const defaultItem: RepairEditForm = {
  datum: '',
  reparatur_sonstiges: '',
  geraet_art: '',
  defekt_besch: '',
  status_detail: '',
  reparatur_besch: '',
  user_id: undefined,
  reparatur_dauer: 0,
  status: 'Offen',
  din_pruef: false,
}

const statusOptions = [...REPAIR_STATUSES]

const currentStatusDetailOptions = computed(() => {
  if (!editedItem.value.status) return []
  return (
    REPAIR_STATUS_DETAIL_OPTIONS[
      editedItem.value.status as keyof typeof REPAIR_STATUS_DETAIL_OPTIONS
    ] || []
  )
})

// Dropdown options from backend
const repairTypes = ref<Array<{ id: number; name: string }>>([])  

// Load dropdown options from backend
async function loadDropdownOptions() {
  try {
    const config = await ConfigService.getDropdownConfig()
    if (config.repair_type) {
      repairTypes.value = config.repair_type
    }
  } catch (err) {
    console.error('Error loading dropdown options:', err)
  }
}

function customerNameFilter(value: unknown, query: string, item?: { raw: Repair }): boolean {
  if (!query) return true
  const q = query.toLowerCase()
  if (item?.raw?.customer) {
    const fullName = `${item.raw.customer.vorname} ${item.raw.customer.nachname}`.toLowerCase()
    if (fullName.includes(q)) return true
  }
  if (value == null) return false
  return String(value).toLowerCase().includes(q)
}

const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Device Type', key: 'geraet_art', sortable: true },
  { title: 'First Name', key: 'customer.vorname', sortable: false },
  { title: 'Last Name', key: 'customer.nachname', sortable: false },
  { title: 'Repair Type', key: 'repair_type', sortable: false },
  { title: 'Status Detail', key: 'status_detail', sortable: true },
  { title: 'Duration', key: 'reparatur_dauer', sortable: true },
  { title: 'Date', key: 'datum', sortable: true },
  { title: 'Closed', key: 'closed_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
]

const loadRepairs = async (customerId?: number) => {
  loading.value = true

  try {
    const response = await RepairsService.listRepairs(customerId)
    repairs.value = response.data || []
    totalCount.value = response.count || 0
  } catch (err: any) {
    console.error('Error loading repairs:', err)
    showMsg(err.message || 'Fehler beim Laden der Reparaturen', 'error')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const formatDateTime = (dateString?: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
}

const editRepair = (item: Repair) => {
  if (item.qr_token) {
    router.push(`/edit/${item.qr_token}`)
  }
}

const closeEditDialog = () => {
  editDialog.value = false
  setTimeout(() => {
    editedItem.value = { ...defaultItem }
  }, 300)
}

const saveRepair = async () => {
  if (!editedItem.value.id) return

  saving.value = true
  try {
    const data = await RepairsService.updateRepair(editedItem.value.id, editedItem.value)

    if (data.reply === 'done') {
      showMsg('Reparatur gespeichert')
      closeEditDialog()
      await loadRepairs(customerFilter.value?.id)
    } else {
      throw new Error((data as any).error || 'Failed to update repair')
    }
  } catch (err: any) {
    console.error('Error updating repair:', err)
    showMsg(err.message || 'Fehler beim Speichern', 'error')
  } finally {
    saving.value = false
  }
}

const createNewRepair = () => {
  router.push('/create-repair')
}

const deleteDialog = ref(false)
const deleteTargetId = ref<number | null>(null)
const deleting = ref(false)

const deleteRepair = (id?: number) => {
  if (!id) return
  deleteTargetId.value = id
  deleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deleteTargetId.value) return
  deleting.value = true
  try {
    await RepairsService.deleteRepair(deleteTargetId.value)
    deleteDialog.value = false
    showMsg('Reparatur gelöscht')
    await loadRepairs(customerFilter.value?.id)
  } catch (err) {
    showMsg('Fehler beim Löschen: ' + (err as Error).message, 'error')
  } finally {
    deleting.value = false
    deleteTargetId.value = null
  }
}

watch(
  () => editedItem.value.status,
  (newStatus, oldStatus) => {
    if (!newStatus) {
      editedItem.value.status_detail = ''
      return
    }

    if (oldStatus === 'In Bearbeitung' && newStatus === 'Offen') {
      editedItem.value.user_id = null
    }

    const allowedDetails =
      REPAIR_STATUS_DETAIL_OPTIONS[newStatus as keyof typeof REPAIR_STATUS_DETAIL_OPTIONS] || []
    if (
      editedItem.value.status_detail &&
      !allowedDetails.includes(editedItem.value.status_detail)
    ) {
      editedItem.value.status_detail = ''
    }
  }
)

const printLabel = async (id: number) => {
  printingLabelId.value = id
  try {
    const result = await RepairsService.printLabel(id)
    showMsg(result.message || 'Label gedruckt')
  } catch (err: any) {
    const msg = err?.body?.error || err?.message || 'Fehler beim Drucken'
    showMsg(msg, 'error')
  } finally {
    printingLabelId.value = null
  }
}

function clearCustomerFilter() {
  customerFilter.value = null
  loadRepairs()
}

onMounted(() => {
  const customerId = route.query.customer_id ? Number(route.query.customer_id) : undefined
  const customerName = route.query.customer_name as string | undefined
  if (customerId && customerName) {
    customerFilter.value = { id: customerId, name: customerName }
    filterStatus.value = 'all'
  } else if (route.query.customer) {
    search.value = route.query.customer as string
  }
  if (
    route.query.status === 'all' ||
    route.query.status === 'open' ||
    route.query.status === 'closed'
  ) {
    filterStatus.value = route.query.status
  }
  loadDropdownOptions()
  userStore.fetchUsers()
  loadRepairs(customerId)
  ConfigService.getFeatures()
    .then((f) => {
      labelPrinterEnabled.value = f.label_printer
    })
    .catch(() => {})
})
</script>
