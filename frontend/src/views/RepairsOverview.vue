<template>
  <v-container>
    <!-- <CreateRepairDialog v-model="createDialog" @submit="handleSubmit" /> -->

    <!-- Next Repair Card -->
    <v-row>
      <v-col cols="12">
        <v-card color="primary" variant="elevated" class="pa-2">
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon size="40" class="mr-3">mdi-tools</v-icon>
              <div>
                <div class="text-headline-small">Nächste Reparatur</div>
              </div>
            </div>
            <v-btn
              v-if="repairStore.nextRepair"
              color="white"
              prepend-icon="mdi-account-plus"
              @click="openStartRepairDialog(repairStore.nextRepair)"
            >
              Zuweisen
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center">
              <v-progress-circular indeterminate color="white"></v-progress-circular>
            </div>
            <div v-else-if="repairStore.nextRepair">
              <div class="text-display-medium font-weight-bold mb-2">ID: {{ repairStore.nextRepair.id }}</div>
              <v-divider class="my-3 opacity-50"></v-divider>
              <div class="text-body-large">
                <div><strong>Gerät:</strong> {{ repairStore.nextRepair.geraet_art }}</div>
                <div>
                  <strong>Kunde:</strong> {{ repairStore.nextRepair.customer?.vorname }}
                  {{ repairStore.nextRepair.customer?.nachname }}
                </div>
                <div><strong>Kategorie:</strong> {{ repairStore.nextRepair.repair_type?.name }}</div>
              </div>
            </div>
            <div v-else class="text-title-large">Keine offenen Reparaturen vorhanden</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" class="d-flex justify-end">
        <v-btn color="primary" prepend-icon="mdi-plus" @click="goToCreateRepair">
          Neue Reparatur
        </v-btn>
      </v-col>
    </v-row>

    <!-- In Progress Repairs List -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-wrench-clock</v-icon>
            Reparaturen in Bearbeitung
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center py-8">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>
            <div v-else-if="repairStore.inProgressRepairs.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey">mdi-wrench-clock-outline</v-icon>
              <p class="text-title-large mt-4">Keine Reparaturen in Bearbeitung</p>
            </div>
            <v-list v-else>
              <v-list-item
                v-for="repair in repairStore.inProgressRepairs"
                :key="repair.id"
                class="mb-2"
                border
              >
                <template #prepend>
                  <v-avatar color="warning" class="mr-3">
                    <span class="text-title-large">{{ repair.id }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-title-large mb-2">
                  {{ repair.geraet_art }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <div class="d-flex flex-column gap-1">
                    <div>
                      <v-icon size="small" class="mr-1">mdi-account</v-icon>
                      <strong>Name:</strong> {{ repair.customer?.vorname }}
                      {{ repair.customer?.nachname }}
                    </div>
                    <div>
                      <v-icon size="small" class="mr-1">mdi-tools</v-icon>
                      <strong>Kategorie:</strong> {{ repair.repair_type?.name }}
                    </div>
                    <div v-if="repair.user">
                      <v-icon size="small" class="mr-1">mdi-account</v-icon>
                      <strong>Reparateur:</strong> {{ repair.user.vorname }}
                      {{ repair.user.nachname }}
                    </div>
                    <div v-if="repair.latest_log" class="mt-2">
                      <v-divider class="mb-2"></v-divider>
                      <div class="text-body-small font-weight-bold mb-1">
                        <v-icon size="small" class="mr-1">mdi-history</v-icon>
                        Letzter Eintrag:
                      </div>
                      <div class="ml-6">
                        <div>
                          <strong>Von:</strong>
                          {{ logAuthor(repair.latest_log) }}
                        </div>
                        <div>
                          <strong>Datum:</strong>
                          {{ formatDateTime(repair.latest_log.created_at) }}
                        </div>
                        <div v-if="repair.latest_log.reparatur_besch">
                          {{ truncate(repair.latest_log.reparatur_besch, 100) }}
                        </div>
                      </div>
                    </div>
                  </div>
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-clipboard-edit"
                    @click="goToRepairWork(repair.qr_token)"
                  >
                    Weiter bearbeiten
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Open Repairs List -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <div>
              <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
              Offene Reparaturen
            </div>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="goToCreateRepair">
              Neue Reparatur
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div v-if="repairStore.loading" class="text-center py-8">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>
            <div v-else-if="repairStore.openRepairs.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey">mdi-clipboard-text-off</v-icon>
              <p class="text-title-large mt-4">Keine offenen Reparaturen</p>
            </div>
            <v-list v-else>
              <v-list-item
                v-for="repair in repairStore.openRepairs"
                :key="repair.id"
                class="mb-2"
                border
              >
                <template #prepend>
                  <v-avatar color="primary" class="mr-3">
                    <span class="text-title-large">{{ repair.id }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-title-large mb-2">
                  {{ repair.geraet_art }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <div class="d-flex flex-column gap-1">
                    <div>
                      <v-icon size="small" class="mr-1">mdi-account</v-icon>
                      <strong>Name:</strong> {{ repair.customer?.vorname }}
                      {{ repair.customer?.nachname }}
                    </div>
                    <div>
                      <v-icon size="small" class="mr-1">mdi-tools</v-icon>
                      <strong>Kategorie:</strong> {{ repair.repair_type?.name }}
                    </div>
                    <div v-if="repair.defekt_besch">
                      <v-icon size="small" class="mr-1">mdi-text</v-icon>
                      <strong>Defekt:</strong> {{ repair.defekt_besch.substring(0, 100)
                      }}{{ repair.defekt_besch.length > 100 ? '...' : '' }}
                    </div>
                  </div>
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    color="success"
                    prepend-icon="mdi-play-circle"
                    @click="openStartRepairDialog(repair)"
                  >
                    Reparatur starten
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Start Repair Dialog -->
    <ReparateurRequiredDialog
      v-model="startRepairDialog"
      v-model:user-id="startRepairUserId"
      title="Reparatur starten"
      message="Für den Wechsel von 'Offen' zu 'In Bearbeitung' muss ein Reparateur angegeben werden."
      confirm-text="Reparatur starten"
      :loading="startingRepair"
      @confirm="confirmStartRepair"
    >
      <template #context>
        <div v-if="selectedRepair" class="mb-4">
          <v-alert type="info" variant="tonal" class="mb-4">
            <div><strong>Reparatur ID:</strong> {{ selectedRepair.id }}</div>
            <div><strong>Gerät:</strong> {{ selectedRepair.geraet_art }}</div>
            <div>
              <strong>Kunde:</strong> {{ selectedRepair.customer?.vorname }}
              {{ selectedRepair.customer?.nachname }}
            </div>
          </v-alert>
        </div>
      </template>
    </ReparateurRequiredDialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { formatDateTime } from '@/utils/date'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useRepairStore } from '@/stores/repairStore'
import { normalizeRepairStatus } from '@/domain/repairStatus'
import type { Repair, RepairLog } from '@/api/types'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'

const router = useRouter()
const repairStore = useRepairStore()

const toast = useToast()

// Start repair dialog state
const startRepairDialog = ref(false)
const selectedRepair = ref<Repair | null>(null)
const startingRepair = ref(false)
const startRepairUserId = ref<number | null>(null)

function logAuthor(log: RepairLog): string {
  return log.user ? `${log.user.vorname} ${log.user.nachname}` : ''
}

function truncate(text: string, length: number): string {
  return text.length > length ? `${text.substring(0, length)}...` : text
}

onMounted(async () => {
  await repairStore.fetchRepairs()
  repairStore.startAutoRefresh()
})

// Clean up auto-refresh on unmount
onUnmounted(() => {
  repairStore.stopAutoRefresh()
})

function goToCreateRepair() {
  router.push('/create-repair')
}

function goToRepairWork(qrToken: string) {
  router.push(`/edit/${qrToken}`)
}

function openStartRepairDialog(repair: Repair) {
  selectedRepair.value = repair
  startRepairUserId.value = null
  startRepairDialog.value = true
}

function closeStartRepairDialog() {
  startRepairDialog.value = false
  selectedRepair.value = null
  startRepairUserId.value = null
}

async function confirmStartRepair(userId: number) {
  if (!selectedRepair.value) return

  const qrToken = selectedRepair.value.qr_token
  const repairId = selectedRepair.value.id
  const fromStatus = normalizeRepairStatus(selectedRepair.value.status)

  startingRepair.value = true
  try {
    await repairStore.transitionRepairStatus({
      repairId,
      fromStatus,
      toStatus: 'In Bearbeitung',
      user_id: userId,
    })


    toast.show('Reparatur wurde gestartet', { color: 'success' })

    // Close dialog
    closeStartRepairDialog()

    // Redirect to LogRepairWorkPage using the stored token
    router.push(`/edit/${qrToken}`)
  } catch (error) {
    console.error('Error starting repair:', error)
    toast.show('Fehler beim Starten der Reparatur', { color: 'error' })
  } finally {
    startingRepair.value = false
  }
}
</script>
