<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useToast } from '@/composables/useToast'
import { useRepairStore } from '@/stores/repairStore'
import { normalizeRepairStatus } from '@/domain/repairStatus'
import type { RepairListItem } from '@/api/types'
import RepairCard from '@/components/RepairCard.vue'
import CountBadge from '@/components/ui/CountBadge.vue'
import PersonLabel from '@/components/ui/PersonLabel.vue'
import RepairNumber from '@/components/ui/RepairNumber.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import TagChip from '@/components/ui/TagChip.vue'
import ReparateurRequiredDialog from '@/components/ReparateurRequiredDialog.vue'

const router = useRouter()
const repairStore = useRepairStore()
const toast = useToast()
// Side by side from md up; tabs on phones and tablets in portrait
const { mdAndUp } = useDisplay()

type SectionKey = 'in_progress' | 'open'

const sections = computed(() => [
  {
    key: 'in_progress' as SectionKey,
    title: 'In Bearbeitung',
    icon: 'mdi-wrench-clock',
    emptyText: 'Keine Reparaturen in Bearbeitung',
    repairs: repairStore.inProgressRepairs,
  },
  {
    key: 'open' as SectionKey,
    title: 'Offen',
    icon: 'mdi-clipboard-text-clock',
    emptyText: 'Keine offenen Reparaturen',
    repairs: repairStore.openRepairs,
  },
])
const activeTab = shallowRef<SectionKey>('in_progress')
const visibleSections = computed(() =>
  mdAndUp.value ? sections.value : sections.value.filter((s) => s.key === activeTab.value)
)
// Skeletons only on the first load; background refreshes keep the cards
const initialLoading = computed(() => repairStore.loading && repairStore.repairs.length === 0)

const nextRepair = computed(() => repairStore.nextRepair)
onMounted(async () => {
  await repairStore.fetchRepairs()
  repairStore.startAutoRefresh()
})

onUnmounted(() => {
  repairStore.stopAutoRefresh()
})

// ── Start repair (assign repairer, Offen -> In Bearbeitung) ──────────────────
const startRepairDialog = shallowRef(false)
const selectedRepair = ref<RepairListItem | null>(null)
const startingRepair = shallowRef(false)
const startRepairUserId = ref<number | null>(null)

function openStartRepairDialog(repair: RepairListItem) {
  selectedRepair.value = repair
  startRepairUserId.value = null
  startRepairDialog.value = true
}

async function confirmStartRepair(userId: number) {
  const repair = selectedRepair.value
  if (!repair) return

  startingRepair.value = true
  try {
    await repairStore.transitionRepairStatus({
      repairId: repair.id,
      fromStatus: normalizeRepairStatus(repair.status),
      toStatus: 'In Bearbeitung',
      user_id: userId,
    })
    toast.success('Reparatur wurde gestartet')
    startRepairDialog.value = false
    void router.push(`/edit/${repair.qr_token}`)
  } catch (error) {
    console.error('Error starting repair:', error)
    toast.error('Fehler beim Starten der Reparatur')
  } finally {
    startingRepair.value = false
  }
}
</script>

<template>
  <v-container fluid class="page-container pb-16">
    <!-- Next repair to start -->
    <v-card color="primary" class="mb-6">
      <v-card-item prepend-icon="mdi-tools" title="Nächste Reparatur" />
      <v-card-text>
        <v-skeleton-loader
          v-if="initialLoading"
          type="list-item-avatar-two-line"
          color="transparent"
        />
        <v-list-item v-else-if="nextRepair" class="px-0" :title="nextRepair.geraet_art">
          <template #prepend>
            <RepairNumber :id="nextRepair.id" :status="nextRepair.status" class="mr-4" />
          </template>
          <v-list-item-subtitle class="d-flex flex-wrap align-center ga-3 mt-1">
            <PersonLabel :person="nextRepair.customer" role="customer" />
            <TagChip v-if="nextRepair.repair_type" :label="nextRepair.repair_type.name" />
          </v-list-item-subtitle>
        </v-list-item>
        <div v-else class="text-title-medium">Keine offenen Reparaturen vorhanden</div>
      </v-card-text>
      <v-card-actions v-if="nextRepair" class="pa-4 pt-0">
        <v-btn
          color="surface"
          variant="flat"
          size="large"
          prepend-icon="mdi-play-circle"
          :block="!mdAndUp"
          @click="openStartRepairDialog(nextRepair)"
        >
          Zuweisen und starten
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Small screens: one section at a time -->
    <v-tabs v-if="!mdAndUp" v-model="activeTab" grow class="mb-4">
      <v-tab v-for="section in sections" :key="section.key" :value="section.key">
        {{ section.title }}
        <CountBadge :count="section.repairs.length" />
      </v-tab>
    </v-tabs>

    <v-row>
      <v-col v-for="section in visibleSections" :key="section.key" cols="12" md="6">
        <SectionTitle
          v-if="mdAndUp"
          :title="section.title"
          :icon="section.icon"
          :count="section.repairs.length"
        />

        <v-row v-if="initialLoading" density="compact">
          <v-col v-for="n in 2" :key="n" cols="12">
            <v-skeleton-loader type="list-item-avatar-two-line, actions" />
          </v-col>
        </v-row>

        <v-empty-state
          v-else-if="section.repairs.length === 0"
          :icon="section.icon"
          :title="section.emptyText"
          size="64"
        />

        <v-row v-else>
          <v-col
            v-for="repair in section.repairs"
            :key="repair.id"
            cols="12"
            :sm="mdAndUp ? 12 : 6"
            xl="6"
          >
            <RepairCard :repair="repair" @start="openStartRepairDialog" />
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <!-- On large screens the app bar's "+" is enough -->
    <v-fab
      v-if="!mdAndUp"
      icon="mdi-plus"
      color="success"
      size="large"
      location="bottom end"
      app
      aria-label="Neue Reparatur"
      @click="router.push('/create-repair')"
    />

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
        <v-alert v-if="selectedRepair" type="info" variant="tonal" class="mb-4">
          <div><strong>Reparatur ID:</strong> {{ selectedRepair.id }}</div>
          <div><strong>Gerät:</strong> {{ selectedRepair.geraet_art }}</div>
          <div>
            <strong>Kunde:</strong> {{ selectedRepair.customer?.vorname }}
            {{ selectedRepair.customer?.nachname }}
          </div>
        </v-alert>
      </template>
    </ReparateurRequiredDialog>
  </v-container>
</template>

