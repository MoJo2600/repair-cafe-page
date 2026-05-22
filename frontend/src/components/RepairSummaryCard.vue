<template>
  <v-card class="mb-4">
    <v-card-title class="text-h5">
      <div class="d-flex justify-space-between align-center">
        <span>{{ repairData.geraet_art }}</span>
        <v-chip :color="getStatusColor(repairData.status ?? '')" size="large">
          {{ repairData.status }}
        </v-chip>
      </div>
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Datum</div>
          <div>{{ formatDateTime(repairData.datum) }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Name</div>
          <div>{{ repairData.customer?.vorname }} {{ repairData.customer?.nachname }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Telefon</div>
          <div>{{ repairData.customer?.telefon || '-' }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Email</div>
          <div>{{ repairData.customer?.email || '-' }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Kategorie</div>
          <div>{{ repairData.reparatur_art }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Geräte Art / Bezeichnung</div>
          <div>{{ repairData.geraet_art }}</div>
        </v-col>
        <v-col cols="6">
          <div class="text-subtitle-2 text-grey-darken-1">Beschreibung des Defekts</div>
          <div>{{ repairData.defekt_besch }}</div>
        </v-col>
        <template v-if="repairData.status === 'Repariert' || repairData.status === 'Nicht Repariert'">
          <v-col cols="12">
            <v-divider class="my-3"></v-divider>
          </v-col>
          <v-col cols="12" v-if="repairData.reparatur_besch">
            <div class="text-subtitle-2 text-grey-darken-1">
              {{ repairData.status === 'Repariert' ? 'Reparaturergebnis' : 'Begründung' }}
            </div>
            <div>{{ repairData.reparatur_besch }}</div>
          </v-col>
          <v-col cols="6" v-if="repairData.status_detail">
            <div class="text-subtitle-2 text-grey-darken-1">Abschlussgrund</div>
            <div>{{ repairData.status_detail }}</div>
          </v-col>
          <v-col cols="6" v-if="repairData.reparatur_dauer">
            <div class="text-subtitle-2 text-grey-darken-1">Reparaturdauer</div>
            <div>{{ repairData.reparatur_dauer }} Min.</div>
          </v-col>
        </template>
        <v-col cols="12" v-if="vdeTests && vdeTests.length > 0">
          <v-divider class="my-3"></v-divider>
          <div class="text-subtitle-2 text-grey-darken-1 mb-2">Letztes Test Ergebnis nach VDE</div>
          <v-alert v-for="test in vdeTests" :key="test.id"
            :type="test.gesamtergebnis === true ? 'success' : 'error'" variant="tonal" density="compact"
            class="mb-2">
            <div class="d-flex align-center">
              <div class="flex-grow-1">
                <strong>{{ test.gesamtergebnis === true ? '✓ Bestanden' : '⚠ Nicht bestanden' }}</strong>
                <span class="ml-2 text-caption">{{ formatDateTime(test.created_at) }}</span>
                <div class="text-caption mt-1">
                  Prüfer: {{ test.prufer }} | Gerät: {{ test.pruefgeraet_name || '-' }}
                </div>
                <div v-if="test.bemerkungen" class="text-caption mt-1">
                  {{ test.bemerkungen }}
                </div>
              </div>
            </div>
          </v-alert>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { Repair, VdeTestResponse } from '@/api/types'

interface Props {
  repairData: Partial<Repair>
  vdeTests?: VdeTestResponse[]
}

defineProps<Props>()

function formatDateTime(dateTimeString: string | undefined) {
  if (!dateTimeString) return ''
  const date = new Date(dateTimeString)
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'Offen':
      return 'warning'
    case 'In Bearbeitung':
      return 'info'
    case 'Repariert':
      return 'success'
    case 'Nicht Repariert':
      return 'error'
    default:
      return 'grey'
  }
}
</script>
