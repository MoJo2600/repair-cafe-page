<script setup lang="ts">
import { computed } from 'vue'
import type { RepairThreadEntry } from '@/composables/useRepairThread'
import { getRepairStatusColor } from '@/stores/repairStore'
import { formatDate, formatDateTime } from '@/utils/date'

/** Chronological activity of a repair: work logs, status/assignee changes, VDE tests. */
const { entries, attachmentCounts } = defineProps<{
  entries: RepairThreadEntry[]
  /** Number of attachments per work-log id. */
  attachmentCounts: Record<number, number>
}>()

const emit = defineEmits<{
  editLog: [logId: number]
  downloadVde: [testId: number]
}>()

const ENTRY_STYLE: Record<RepairThreadEntry['type'], { color: string; icon: string }> = {
  repair: { color: 'primary', icon: 'mdi-wrench' },
  status_change: { color: 'warning', icon: 'mdi-swap-horizontal' },
  created: { color: 'grey', icon: 'mdi-clipboard-plus-outline' },
  assignee_change: { color: 'blue-lighten-1', icon: 'mdi-account-arrow-right' },
  vde: { color: 'success', icon: 'mdi-flash' },
}

const items = computed(() =>
  entries.map((entry) => {
    const style =
      entry.type === 'vde' && !entry.vdePassed
        ? { color: 'error', icon: 'mdi-flash-off' }
        : ENTRY_STYLE[entry.type]
    return {
      entry,
      ...style,
      attachments: entry.type === 'repair' ? (attachmentCounts[entry.id] ?? 0) : 0,
      timestamp: entry.dateOnly ? formatDate(entry.created_at) : formatDateTime(entry.created_at),
    }
  })
)

function onEntryClick(entry: RepairThreadEntry) {
  if (entry.type === 'repair') emit('editLog', entry.id)
}
</script>

<template>
  <div>
    <h3 class="text-title-large mb-4">Reparatur Logeinträge</h3>

    <v-timeline v-if="items.length > 0" density="compact" side="end" class="mb-4">
      <v-timeline-item
        v-for="item in items"
        :key="item.entry.uniqueKey"
        :dot-color="item.color"
        :icon="item.icon"
        @click="onEntryClick(item.entry)"
      >
        <div :class="{ 'repair-entry': item.entry.type === 'repair' }">
          <v-chip
            v-if="item.attachments > 0"
            size="x-small"
            color="grey-darken-1"
            variant="tonal"
            class="mb-1"
          >
            <v-icon size="12" start>mdi-paperclip</v-icon>
            {{ item.attachments }}
          </v-chip>

          <!-- Status change, or a work log that also changed the status -->
          <div
            v-if="item.entry.type === 'repair' && item.entry.description"
            class="text-body-medium text-high-emphasis mb-1 entry-text"
          >
            {{ item.entry.description }}
          </div>
          <div
            v-if="
              item.entry.type === 'status_change' ||
              (item.entry.type === 'repair' && (item.entry.status_from || item.entry.status_to))
            "
            class="d-flex align-center ga-1 flex-wrap"
          >
            <v-chip size="x-small" variant="tonal" :color="getRepairStatusColor(item.entry.status_from)">
              {{ item.entry.status_from || '?' }}
            </v-chip>
            <v-icon size="14" color="grey">mdi-arrow-right</v-icon>
            <v-chip size="x-small" variant="tonal" :color="getRepairStatusColor(item.entry.status_to)">
              {{ item.entry.status_to || '?' }}
            </v-chip>
          </div>

          <div v-else-if="item.entry.type === 'vde'" class="d-flex align-center ga-2 flex-wrap">
            <span class="text-body-medium text-high-emphasis entry-text">
              {{ item.entry.description }}
            </span>
            <v-btn
              size="small"
              variant="text"
              prepend-icon="mdi-file-pdf-box"
              color="error"
              @click.stop="emit('downloadVde', item.entry.id)"
            >
              PDF herunterladen
            </v-btn>
          </div>

          <v-chip
            v-else-if="item.entry.type === 'created'"
            size="x-small"
            variant="tonal"
            :color="getRepairStatusColor('Offen')"
          >
            Offen
          </v-chip>

          <div
            v-else-if="item.entry.type === 'assignee_change'"
            class="d-flex align-center ga-1 flex-wrap"
          >
            <v-icon size="14" color="blue-lighten-1">mdi-account-arrow-right</v-icon>
            <span class="text-body-medium">{{ item.entry.description }}</span>
          </div>

          <div class="text-body-small text-medium-emphasis">
            {{ item.timestamp }}
            <template v-if="item.entry.person">
              - <strong>{{ item.entry.person }}</strong>
            </template>
          </div>
        </div>
      </v-timeline-item>
    </v-timeline>

    <v-alert v-else type="info" variant="tonal" class="mb-4">
      Noch keine Logeinträge vorhanden.
    </v-alert>
  </div>
</template>

<style scoped>
.entry-text {
  white-space: normal;
}

.repair-entry {
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background-color 0.15s ease;
}

.repair-entry:hover {
  background-color: rgba(var(--v-theme-primary), 0.12);
}
</style>
