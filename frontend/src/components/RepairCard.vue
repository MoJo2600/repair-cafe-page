<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { RepairListItem } from '@/api/types'
import { formatDateTime } from '@/utils/date'
import { getRepairStatusColor, getRepairStatusIcon } from '@/domain/repairStatus'
import PersonLabel from '@/components/ui/PersonLabel.vue'
import RepairNumber from '@/components/ui/RepairNumber.vue'
import TagChip from '@/components/ui/TagChip.vue'

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
</script>

<template>
  <v-card class="d-flex flex-column h-100" border @click="openRepair">
    <v-card-item>
      <template #prepend>
        <RepairNumber :id="repair.id" :status="repair.status" />
      </template>
      <v-card-title class="text-title-large">{{ repair.geraet_art }}</v-card-title>
      <v-card-subtitle>
        <PersonLabel :person="repair.customer" role="customer" />
      </v-card-subtitle>
    </v-card-item>

    <v-card-text class="flex-grow-1 pt-0 d-flex flex-column ga-2">
      <div v-if="repair.repair_type || repair.user" class="d-flex flex-wrap align-center ga-3">
        <TagChip v-if="repair.repair_type" :label="repair.repair_type.name" />
        <PersonLabel v-if="repair.user" :person="repair.user" role="repairer" />
      </div>

      <p v-if="isOpen && repair.defekt_besch" class="line-clamp-2 text-body-medium">
        {{ repair.defekt_besch }}
      </p>

      <div v-if="!isOpen && repair.latest_log" class="text-body-medium">
        <p v-if="repair.latest_log.reparatur_besch" class="line-clamp-2">
          {{ repair.latest_log.reparatur_besch }}
        </p>
        <div class="text-body-small text-medium-emphasis">
          {{ formatDateTime(repair.latest_log.created_at) }}
          <template v-if="repair.latest_log.user">
            · <PersonLabel :person="repair.latest_log.user" role="author" />
          </template>
        </div>
      </div>
    </v-card-text>

    <v-card-actions class="pa-4 pt-0">
      <v-btn
        v-if="isOpen"
        :color="getRepairStatusColor('In Bearbeitung')"
        variant="flat"
        size="large"
        :prepend-icon="getRepairStatusIcon('In Bearbeitung')"
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
