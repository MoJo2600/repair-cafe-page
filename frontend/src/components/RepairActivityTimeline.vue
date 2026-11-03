<script setup lang="ts">
import { computed } from 'vue'
import type { RepairThreadEntry } from '@/composables/useRepairThread'
import { getRepairStatusColor } from '@/domain/repairStatus'
import { formatDate, formatDateTime } from '@/utils/date'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import StatusChip from '@/components/ui/StatusChip.vue'

/** Chronological activity of a repair: work logs, status/assignee changes, VDE tests. */
const {
  entries,
  attachmentCounts,
  showTitle = true,
} = defineProps<{
  entries: RepairThreadEntry[]
  /** Number of attachments per work-log id. */
  attachmentCounts: Record<number, number>
  /** Off when a surrounding tab already names the section. */
  showTitle?: boolean
}>()

const emit = defineEmits<{
  editLog: [logId: number]
  downloadVde: [testId: number]
}>()

/** Dot per entry type (docs/STYLEGUIDE.md: status colors only for statuses). */
function entryStyle(entry: RepairThreadEntry): { color: string; icon: string } {
  switch (entry.type) {
    case 'repair':
      return { color: 'primary', icon: 'mdi-wrench' }
    case 'status_change':
      return { color: getRepairStatusColor(entry.status_to), icon: 'mdi-swap-horizontal' }
    case 'created':
      return { color: getRepairStatusColor('Offen'), icon: 'mdi-clipboard-plus-outline' }
    case 'assignee_change':
      return { color: 'surface-variant', icon: 'mdi-account-arrow-right' }
    case 'vde':
      // The test result is feedback, so it uses the feedback colors
      return entry.vdePassed
        ? { color: 'success', icon: 'mdi-flash' }
        : { color: 'error', icon: 'mdi-flash-off' }
  }
}

const items = computed(() =>
  entries.map((entry) => {
    const style = entryStyle(entry)
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
    <SectionTitle v-if="showTitle" title="Verlauf" icon="mdi-history" />

    <v-timeline v-if="items.length > 0" density="compact" side="end" class="mb-4">
      <v-timeline-item
        v-for="item in items"
        :key="item.entry.uniqueKey"
        :dot-color="item.color"
        :icon="item.icon"
        @click="onEntryClick(item.entry)"
      >
        <div :class="{ 'repair-entry': item.entry.type === 'repair' }">

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
            <StatusChip :status="item.entry.status_from" size="x-small" />
            <v-icon size="14" class="text-medium-emphasis">mdi-arrow-right</v-icon>
            <StatusChip :status="item.entry.status_to" size="x-small" />
          </div>

          <div v-else-if="item.entry.type === 'vde'" class="d-flex align-center ga-2 flex-wrap">
            <span class="text-body-medium text-high-emphasis entry-text">
              {{ item.entry.description }}
            </span>
            <v-btn
              size="small"
              variant="text"
              prepend-icon="mdi-file-pdf-box"
              color="primary"
              @click.stop="emit('downloadVde', item.entry.id)"
            >
              PDF herunterladen
            </v-btn>
          </div>

          <div v-else-if="item.entry.type === 'created'" class="text-body-medium">
            Reparatur angenommen
          </div>

          <div
            v-else-if="item.entry.type === 'assignee_change'"
            class="d-flex align-center ga-1 flex-wrap"
          >
            <span class="text-body-medium">{{ item.entry.description }}</span>
          </div>

          <div class="text-body-small text-medium-emphasis">
            {{ item.timestamp }}<template v-if="item.entry.person"> · {{ item.entry.person }}</template>
            <span v-if="item.attachments > 0" class="ml-2">
              <v-icon icon="mdi-paperclip" size="x-small" />{{ item.attachments }}
            </span>
          </div>
        </div>
      </v-timeline-item>
    </v-timeline>

    <v-empty-state
      v-else
      icon="mdi-history"
      title="Noch keine Einträge"
      text="Arbeitsschritte, Statuswechsel und VDE-Tests erscheinen hier."
      size="64"
    />
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
