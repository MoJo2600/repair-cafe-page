<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { RepairListItem } from '@/api/types'
import { getRepairStatusColor } from '@/domain/repairStatus'
import { formatDateTime } from '@/utils/date'

/** A repair in the overview: tap the card to open it; the button runs its next step. */
const { repair } = defineProps<{ repair: RepairListItem }>()

const emit = defineEmits<{
  /** Open repair: assign a repairer and start it. */
  start: [repair: RepairListItem]
}>()

const router = useRouter()

function openRepair() {
  void router.push(`/edit/${repair.qr_token}`)
}

const isOpen = computed(() => repair.status === 'Offen')
const color = computed(() => getRepairStatusColor(repair.status))
const customerName = computed(() =>
  [repair.customer?.vorname, repair.customer?.nachname].filter(Boolean).join(' ')
)
const repairerName = computed(() =>
  repair.user ? `${repair.user.vorname} ${repair.user.nachname}` : ''
)
const latestLog = computed(() => {
  const log = repair.latest_log
  if (!log) return null
  const author = log.user ? `${log.user.vorname} ${log.user.nachname}` : ''
  return {
    meta: [formatDateTime(log.created_at), author].filter(Boolean).join(' · '),
    text: log.reparatur_besch,
  }
})
</script>

<template>
  <v-card class="d-flex flex-column h-100" border @click="openRepair">
    <v-card-item>
      <template #prepend>
        <v-avatar :color="color" size="48">
          <span class="text-title-medium font-weight-bold">{{ repair.id }}</span>
        </v-avatar>
      </template>
      <v-card-title class="text-title-large">{{ repair.geraet_art }}</v-card-title>
      <v-card-subtitle v-if="customerName">
        <v-icon icon="mdi-account" size="small" start />{{ customerName }}
      </v-card-subtitle>
    </v-card-item>

    <v-card-text class="flex-grow-1 pt-0">
      <div class="d-flex flex-wrap ga-2 mb-2">
        <v-chip v-if="repair.repair_type" size="small" prepend-icon="mdi-tools">
          {{ repair.repair_type.name }}
        </v-chip>
        <v-chip v-if="repairerName" size="small" prepend-icon="mdi-account-wrench" :color="color">
          {{ repairerName }}
        </v-chip>
      </div>

      <p v-if="isOpen && repair.defekt_besch" class="line-clamp-2 text-body-medium">
        {{ repair.defekt_besch }}
      </p>

      <div v-if="!isOpen && latestLog" class="text-body-small">
        <div class="text-medium-emphasis">
          <v-icon icon="mdi-history" size="small" start />{{ latestLog.meta }}
        </div>
        <p v-if="latestLog.text" class="line-clamp-2 mt-1">{{ latestLog.text }}</p>
      </div>
    </v-card-text>

    <v-card-actions class="pa-4 pt-0">
      <v-btn
        v-if="isOpen"
        color="success"
        variant="flat"
        size="large"
        prepend-icon="mdi-play-circle"
        block
        @click.stop="emit('start', repair)"
      >
        Reparatur starten
      </v-btn>
      <v-btn
        v-else
        color="primary"
        variant="tonal"
        size="large"
        prepend-icon="mdi-clipboard-edit"
        block
        @click.stop="openRepair"
      >
        Weiter bearbeiten
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
