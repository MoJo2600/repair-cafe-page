<template>
    <v-dialog :model-value="modelValue" max-width="800px" persistent scrollable @update:model-value="onDialogToggle">
        <v-card>
            <v-card-title class="text-h5">
                <v-icon start>mdi-flash</v-icon>
                Elektrische Sicherheitspruefung nach VDE-Normen
            </v-card-title>

            <v-card-text style="max-height: 70vh;">
                <v-alert :type="requiredForStatus ? 'info' : 'success'" variant="tonal" class="mb-4" density="compact">
                    <template v-if="requiredForStatus">
                        Fuer den Status "{{ selectedRepairStatus }}" ist ein VDE Test erforderlich.
                    </template>
                    <template v-else>
                        VDE Test wird als zusaetzlicher Logeintrag protokolliert.
                    </template>
                </v-alert>

                <v-form ref="inlineVdeForm" v-model="inlineVdeFormValid">
                    <h4 class="text-subtitle-2 mb-2">Allgemeine Angaben</h4>
                    <v-row dense>
                        <v-col cols="12" sm="6">
                            <v-text-field v-model="form.created_at" label="Prüfung nach DIN VDE 0701 am"
                                type="datetime-local" density="compact" required
                                :rules="[(v: string) => !!v || 'Datum ist erforderlich']" />
                        </v-col>
                        <v-col cols="12" sm="6">
                            <v-text-field :model-value="repairId" label="Gehört zu Laufzettel-Nummer" density="compact"
                                readonly />
                        </v-col>
                    </v-row>

                    <v-row dense>
                        <v-col cols="12" sm="6">
                            <v-select v-model="selectedPruefgeraet" :items="pruefgeraete" item-title="name"
                                item-value="name" label="Mit Prüfgerät" density="compact" clearable />
                        </v-col>
                        <v-col cols="12" sm="6">
                            <v-text-field :model-value="selectedPruefgeraetSerial" read-only
                                label="Seriennummer Prüfgerät" density="compact" readonly />
                        </v-col>
                    </v-row>

                    <v-row dense>
                        <v-col cols="12" sm="6">
                            <v-select v-model="form.prufer_user_id" :items="userItems" item-title="label"
                                item-value="id" label="Durchgeführt von" density="compact" clearable required
                                :rules="[(v: number | null) => !!v || 'Prüfer ist erforderlich']" />
                        </v-col>
                        <v-col cols="12" sm="6">
                            <v-text-field v-model="form.electrician" label="Falls EuP, im Beisein von Elektrofachkraft"
                                density="compact" />
                        </v-col>
                    </v-row>

                    <v-row dense>
                        <v-col cols="12">
                            <v-textarea v-model="form.bemerkungen" label="Bemerkungen / Mängel" rows="2"
                                density="compact" auto-grow />
                        </v-col>
                    </v-row>

                    <v-divider class="my-3" />

                    <h4 class="text-subtitle-2 mb-2">Sichtprüfung</h4>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Gehäuse i.O.? <span class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.sichtpruefung_gehaeuse" inline density="compact"
                                :rules="[(v: boolean | null) => v !== null || 'Erforderlich']" hide-details="auto">
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Kabel i.O.? <span class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.sichtpruefung_kabel" inline density="compact"
                                :rules="[(v: boolean | null) => v !== null || 'Erforderlich']" hide-details="auto">
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Stecker i.O.? <span class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.sichtpruefung_stecker" inline density="compact"
                                :rules="[(v: boolean | null) => v !== null || 'Erforderlich']" hide-details="auto">
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Zugentlastungsvorrichtung i.O.? <span
                                    class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.sichtpruefung_zugentlastung" inline density="compact"
                                :rules="[(v: boolean | null) => v !== null || 'Erforderlich']" hide-details="auto">
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Sicherheitseinrichtungen i.O.? <span
                                    class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.sichtpruefung_sicherheit" inline density="compact"
                                :rules="[(v: boolean | null) => v !== null || 'Erforderlich']" hide-details="auto">
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>

                    <v-divider class="my-3" />

                    <h4 class="text-subtitle-2 mb-2">Messung</h4>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Schutzklasse</span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-select v-model="form.schutzklasse"
                                :items="['Schutzklasse I', 'Schutzklasse II', 'Schutzklasse III']" density="compact"
                                hide-details />
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Schutzleiterpruefung i.O.?</span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.schutzleiter_pruefung" inline density="compact" hide-details>
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Isolationspruefung i.O.?</span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.isolationspruefung" inline density="compact" hide-details>
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2">Ableitstrompruefung i.O.?</span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.ableitstrom_pruefung" inline density="compact" hide-details>
                                <v-radio label="Ja" :value="true" />
                                <v-radio label="Nein" :value="false" />
                            </v-radio-group>
                        </v-col>
                    </v-row>

                    <v-divider class="my-3" />

                    <h4 class="text-subtitle-2 mb-2">Ergebnis</h4>
                    <v-row dense align="center">
                        <v-col cols="6" sm="4">
                            <span class="text-body-2 font-weight-bold">Geraetetest bestanden? <span
                                    class="text-error">*</span></span>
                        </v-col>
                        <v-col cols="6" sm="8">
                            <v-radio-group v-model="form.gesamtergebnis" inline density="compact" hide-details="auto"
                                required :rules="[(v: boolean | null) => v !== null || 'Ergebnis erforderlich']"
                                :disabled="vdeTestHasFailedQuestion && vdeTestAllQuestionsAnswered"
                                :readonly="vdeTestHasFailedQuestion && vdeTestAllQuestionsAnswered">
                                <v-radio label="Ja" :value="true" color="success" />
                                <v-radio label="Nein" :value="false" color="error" />
                            </v-radio-group>
                        </v-col>
                    </v-row>

                    <v-alert type="warning" variant="tonal" density="compact" class="mt-2 mb-3">
                        <b>Achtung:</b> Bei nicht bestandener Geraetepruefung ist die weitere Benutzung des Geraetes
                        lebensgefaehrlich und daher nicht zulaessig.
                    </v-alert>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-btn @click="onCancel">Abbrechen</v-btn>
                <v-spacer />
                <v-btn color="primary" @click="onSubmit" :disabled="!inlineVdeFormValid" :loading="saving">
                    <v-icon start>mdi-check-all</v-icon>
                    {{ confirmText }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { UserResponse, PruefgeraetResponse } from '@/api/types'

export interface VdeFormData {
    created_at: string
    prufer_user_id: number | null
    electrician: string
    pruefgeraet_name: string
    pruefgeraet_serial: string
    sichtpruefung_gehaeuse: boolean | null
    sichtpruefung_kabel: boolean | null
    sichtpruefung_stecker: boolean | null
    sichtpruefung_zugentlastung: boolean | null
    sichtpruefung_sicherheit: boolean | null
    schutzklasse: string
    schutzleiter_pruefung: boolean | null
    isolationspruefung: boolean | null
    ableitstrom_pruefung: boolean | null
    gesamtergebnis: boolean | null
    bemerkungen: string
}

interface Props {
    modelValue: boolean
    saving: boolean
    repairId?: number
    selectedRepairStatus?: string
    requiredForStatus?: boolean
    confirmText?: string
    initialPruferUserId?: number | null
    users: UserResponse[]
    pruefgeraete: PruefgeraetResponse[]
}

const props = withDefaults(defineProps<Props>(), {
    repairId: undefined,
    selectedRepairStatus: '',
    requiredForStatus: false,
    confirmText: 'VDE speichern',
    initialPruferUserId: null
})

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'submit', payload: VdeFormData): void
}>()

const inlineVdeFormValid = ref(false)
const inlineVdeForm = ref<{ validate: () => Promise<{ valid: boolean }>; resetValidation?: () => void } | null>(null)
const selectedPruefgeraet = ref<string>('')

const userItems = computed(() =>
    props.users.map((u) => ({
        id: u.id,
        label: [u.vorname, u.nachname].filter(Boolean).join(' ') || `User #${u.id}`
    }))
)

function getCurrentDateTime(): string {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
}

function createEmptyForm(): VdeFormData {
    return {
        created_at: getCurrentDateTime(),
        prufer_user_id: props.initialPruferUserId ?? null,
        electrician: '',
        pruefgeraet_name: '',
        pruefgeraet_serial: '',
        sichtpruefung_gehaeuse: null,
        sichtpruefung_kabel: null,
        sichtpruefung_stecker: null,
        sichtpruefung_zugentlastung: null,
        sichtpruefung_sicherheit: null,
        schutzklasse: '',
        schutzleiter_pruefung: null,
        isolationspruefung: null,
        ableitstrom_pruefung: null,
        gesamtergebnis: null,
        bemerkungen: ''
    }
}

const form = ref<VdeFormData>(createEmptyForm())

watch(
    () => props.modelValue,
    (isOpen) => {
        if (isOpen) {
            form.value = createEmptyForm()
            selectedPruefgeraet.value = ''
            if (inlineVdeForm.value?.resetValidation) {
                inlineVdeForm.value.resetValidation()
            }
        }
    }
)

const selectedPruefgeraetSerial = computed(() => {
    if (!selectedPruefgeraet.value) return ''
    const device = props.pruefgeraete.find((d) => d.name === selectedPruefgeraet.value)
    return device?.serial_number || ''
})

watch(selectedPruefgeraet, (name) => {
    form.value.pruefgeraet_name = name || ''
    form.value.pruefgeraet_serial = selectedPruefgeraetSerial.value || ''
})

watch(
    () => ({
        gehaeuse: form.value.sichtpruefung_gehaeuse,
        kabel: form.value.sichtpruefung_kabel,
        stecker: form.value.sichtpruefung_stecker,
        zugentlastung: form.value.sichtpruefung_zugentlastung,
        sicherheit: form.value.sichtpruefung_sicherheit,
        schutzleiter: form.value.schutzleiter_pruefung,
        isolation: form.value.isolationspruefung,
        ableitstrom: form.value.ableitstrom_pruefung
    }),
    () => {
        if (vdeTestAllQuestionsAnswered.value) {
            form.value.gesamtergebnis = vdeTestHasFailedQuestion.value ? false : true
        }
    },
    { deep: true }
)

const vdeTestHasFailedQuestion = computed((): boolean => {
    if (
        form.value.sichtpruefung_gehaeuse === false ||
        form.value.sichtpruefung_kabel === false ||
        form.value.sichtpruefung_stecker === false ||
        form.value.sichtpruefung_zugentlastung === false ||
        form.value.sichtpruefung_sicherheit === false
    ) {
        return true
    }

    if (
        form.value.schutzleiter_pruefung === false ||
        form.value.isolationspruefung === false ||
        form.value.ableitstrom_pruefung === false
    ) {
        return true
    }

    return false
})

const vdeTestAllQuestionsAnswered = computed((): boolean => {
    return (
        form.value.sichtpruefung_gehaeuse !== null &&
        form.value.sichtpruefung_kabel !== null &&
        form.value.sichtpruefung_stecker !== null &&
        form.value.sichtpruefung_zugentlastung !== null &&
        form.value.sichtpruefung_sicherheit !== null &&
        form.value.schutzleiter_pruefung !== null &&
        form.value.isolationspruefung !== null &&
        form.value.ableitstrom_pruefung !== null
    )
})

async function onSubmit() {
    if (!inlineVdeForm.value) return

    const { valid } = await inlineVdeForm.value.validate()
    if (!valid) return

    emit('submit', {
        ...form.value,
        pruefgeraet_name: selectedPruefgeraet.value || form.value.pruefgeraet_name,
        pruefgeraet_serial: selectedPruefgeraetSerial.value || form.value.pruefgeraet_serial
    })
}

function onCancel() {
    emit('update:modelValue', false)
}

function onDialogToggle(isOpen: boolean) {
    emit('update:modelValue', isOpen)
}
</script>
