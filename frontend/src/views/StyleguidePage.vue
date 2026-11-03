<script setup lang="ts">
import { REPAIR_STATUSES, getRepairStatusColor, getRepairStatusIcon } from '@/domain/repairStatus'
import { formatDate, formatDateTime } from '@/utils/date'
import CountBadge from '@/components/ui/CountBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PersonLabel from '@/components/ui/PersonLabel.vue'
import RepairNumber from '@/components/ui/RepairNumber.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import TagChip from '@/components/ui/TagChip.vue'

/** Living version of docs/STYLEGUIDE.md: every shared building block with sample data. */
const customer = { vorname: 'Erika', nachname: 'Muster' }
const repairer = { vorname: 'Hans', nachname: 'Müller' }
const sampleDate = '2026-11-03T15:09:00Z'

const feedbackColors = ['success', 'info', 'warning', 'error'] as const
const typography = [
  { label: 'Seitentitel', cls: 'text-headline-small' },
  { label: 'Abschnitt / Kartentitel', cls: 'text-title-large' },
  { label: 'Feldbezeichnung', cls: 'text-title-small text-medium-emphasis' },
  { label: 'Haupttext einer Karte', cls: 'text-body-large' },
  { label: 'Text', cls: 'text-body-medium' },
  { label: 'Meta (Datum, Autor)', cls: 'text-body-small text-medium-emphasis' },
]
</script>

<template>
  <v-container fluid class="page-container">
    <PageHeader title="Styleguide" subtitle="Lebende Version von docs/STYLEGUIDE.md" />

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-item title="Farben: Reparaturstatus" subtitle="Nur für Status-Chips, Nummern und Statusbuttons" />
          <v-card-text class="d-flex flex-wrap ga-3">
            <div v-for="status in REPAIR_STATUSES" :key="status" class="swatch">
              <v-sheet :color="getRepairStatusColor(status)" height="48" rounded class="mb-1" />
              <div class="text-body-small">{{ status }}</div>
              <code class="text-body-small">{{ getRepairStatusColor(status) }}</code>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="mb-4">
          <v-card-item title="Farben: Rückmeldungen" subtitle="Toasts, Hinweise, Validierung, VDE-Ergebnis" />
          <v-card-text class="d-flex flex-column ga-2">
            <v-alert
              v-for="color in feedbackColors"
              :key="color"
              :type="color"
              variant="tonal"
              density="compact"
              :text="`${color}: Meldung zum Ergebnis einer Aktion`"
            />
          </v-card-text>
        </v-card>

        <v-card class="mb-4">
          <v-card-item title="Chips" subtitle="Nur kurze Werte aus einer festen Menge" />
          <v-card-text class="d-flex flex-column ga-3">
            <div class="d-flex flex-wrap ga-2 align-center">
              <span class="label">Status</span>
              <StatusChip v-for="status in REPAIR_STATUSES" :key="status" :status="status" />
            </div>
            <div class="d-flex flex-wrap ga-2 align-center">
              <span class="label">Zustand</span>
              <StatusChip label="Aktiv" color="success" icon="mdi-check" />
              <StatusChip label="Inaktiv" icon="mdi-cancel" />
            </div>
            <div class="d-flex flex-wrap ga-2 align-center">
              <span class="label">Kategorie</span>
              <TagChip label="Elektro" />
              <TagChip label="Fahrrad" />
            </div>
            <div class="d-flex flex-wrap ga-2 align-center">
              <span class="label">Anzahl</span>
              <span>Offen<CountBadge :count="5" /></span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-item title="Personen" subtitle="Rollen-Icon + voller Name, nie als Chip" />
          <v-card-text class="d-flex flex-column ga-2">
            <PersonLabel :person="customer" role="customer" />
            <PersonLabel :person="repairer" role="repairer" />
            <PersonLabel :person="null" role="repairer" empty-text="Niemand zugewiesen" />
            <div class="text-body-small text-medium-emphasis">
              {{ formatDateTime(sampleDate) }} · <PersonLabel :person="repairer" role="author" />
            </div>
          </v-card-text>
        </v-card>

        <v-card class="mb-4">
          <v-card-item title="Reparatur" subtitle="Nummer in Statusfarbe, Gerät als Titel" />
          <v-card-item>
            <template #prepend><RepairNumber :id="23" status="In Bearbeitung" /></template>
            <v-card-title>Toaster</v-card-title>
            <v-card-subtitle>
              <PersonLabel :person="customer" role="customer" />
            </v-card-subtitle>
          </v-card-item>
          <v-card-text class="d-flex flex-wrap ga-2">
            <StatusChip status="In Bearbeitung" />
            <TagChip label="Elektro" />
          </v-card-text>
        </v-card>

        <v-card class="mb-4">
          <v-card-item title="Typografie, Datum, Dauer" />
          <v-card-text class="d-flex flex-column ga-2">
            <div v-for="t in typography" :key="t.cls" :class="t.cls">{{ t.label }}</div>
            <v-divider class="my-2" />
            <div>{{ formatDate(sampleDate) }} · {{ formatDateTime(sampleDate) }} · 45 Min. · #23</div>
          </v-card-text>
        </v-card>

        <v-card class="mb-4">
          <v-card-item title="Buttons" />
          <v-card-text class="d-flex flex-column ga-3">
            <SectionTitle title="Abschnittstitel" icon="mdi-wrench-clock" :count="3" />
            <div class="d-flex flex-wrap ga-2">
              <v-btn color="primary" variant="flat" size="large">Hauptaktion</v-btn>
              <v-btn
                :color="getRepairStatusColor('Repariert')"
                :prepend-icon="getRepairStatusIcon('Repariert')"
                variant="flat"
                size="large"
              >
                Repariert
              </v-btn>
            </div>
            <div class="d-flex flex-wrap ga-2">
              <v-btn color="primary" variant="tonal">Nebenaktion</v-btn>
              <v-btn variant="text">Abbrechen</v-btn>
              <v-btn color="error" variant="text" prepend-icon="mdi-delete">Löschen</v-btn>
              <v-btn icon="mdi-pencil" variant="text" aria-label="Bearbeiten" />
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>

.swatch {
  width: 120px;
}

.label {
  min-width: 80px;
}
</style>
