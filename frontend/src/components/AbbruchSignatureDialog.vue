<template>
    <v-dialog :model-value="modelValue" max-width="680px" persistent @update:model-value="onDialogToggle">
        <v-card>
            <v-card-title class="d-flex align-center">
                <v-icon class="mr-2" color="error">mdi-alert-octagon</v-icon>
                Gerät darf nicht mehr benutzt werden
            </v-card-title>

            <v-card-text>
                <v-alert type="error" variant="tonal" class="mb-4" icon="mdi-alert-octagon">
                    <strong>Das Gerät darf nicht mehr benutzt werden.</strong> Anschluss sowie Benutzung dieses Gerätes
                    (auch durch Dritte) ist in keinem Fall zulässig. Ich bestätige durch meine Unterschrift, darüber
                    informiert worden zu sein.
                </v-alert>

                <v-divider class="my-4" />

                <p class="text-body-2 text-medium-emphasis mb-3">
                    Bitte hier unterschreiben zur Bestätigung:
                </p>

                <div class="signature-container" :class="{ 'error-border': signatureError }">
                    <canvas ref="signatureCanvas" width="600" height="180"
                        style="border: 1px solid #ccc; cursor: crosshair; width: 100%; touch-action: none; border-radius: 4px;"
                        @mousedown="startDrawing" @mousemove="draw" @mouseup="stopDrawing" @mouseleave="stopDrawing"
                        @touchstart="startDrawingTouch" @touchmove="drawTouch" @touchend="stopDrawing"></canvas>
                </div>
                <div v-if="signatureError" class="text-error text-caption mt-1">
                    {{ signatureError }}
                </div>

                <div class="mt-2">
                    <v-btn size="small" variant="text" prepend-icon="mdi-eraser" @click="clearSignature">
                        Unterschrift löschen
                    </v-btn>
                </div>
            </v-card-text>

            <v-card-actions>
                <v-btn variant="text" @click="closeDialog">Abbrechen</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="error" :loading="loading" @click="confirmDialog">
                    <v-icon start>mdi-check</v-icon>
                    Bestätigen
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = withDefaults(defineProps<{
    modelValue: boolean
    loading?: boolean
}>(), {
    loading: false
})

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'confirm', value: { signature: string }): void
}>()

const signatureCanvas = ref<HTMLCanvasElement | null>(null)
const isDrawing = ref(false)
const signatureData = ref<string | null>(null)
const signatureError = ref('')

watch(() => props.modelValue, async (isOpen) => {
    if (isOpen) {
        signatureData.value = null
        signatureError.value = ''
        await nextTick()
        clearSignature()
    }
})

function getContext(): CanvasRenderingContext2D | null {
    if (!signatureCanvas.value) return null
    return signatureCanvas.value.getContext('2d')
}

function startDrawing(event: MouseEvent) {
    isDrawing.value = true
    const ctx = getContext()
    if (!ctx || !signatureCanvas.value) return
    const rect = signatureCanvas.value.getBoundingClientRect()
    const scaleX = signatureCanvas.value.width / rect.width
    const scaleY = signatureCanvas.value.height / rect.height
    ctx.beginPath()
    ctx.moveTo((event.clientX - rect.left) * scaleX, (event.clientY - rect.top) * scaleY)
    signatureError.value = ''
}

function draw(event: MouseEvent) {
    if (!isDrawing.value) return
    const ctx = getContext()
    if (!ctx || !signatureCanvas.value) return
    const rect = signatureCanvas.value.getBoundingClientRect()
    const scaleX = signatureCanvas.value.width / rect.width
    const scaleY = signatureCanvas.value.height / rect.height
    ctx.lineTo((event.clientX - rect.left) * scaleX, (event.clientY - rect.top) * scaleY)
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.stroke()
}

function stopDrawing() {
    if (isDrawing.value) {
        isDrawing.value = false
        if (signatureCanvas.value) {
            signatureData.value = signatureCanvas.value.toDataURL()
        }
    }
}

function startDrawingTouch(event: TouchEvent) {
    event.preventDefault()
    isDrawing.value = true
    const ctx = getContext()
    if (!ctx || !signatureCanvas.value) return
    const rect = signatureCanvas.value.getBoundingClientRect()
    const scaleX = signatureCanvas.value.width / rect.width
    const scaleY = signatureCanvas.value.height / rect.height
    const touch = event.touches[0]
    ctx.beginPath()
    ctx.moveTo((touch.clientX - rect.left) * scaleX, (touch.clientY - rect.top) * scaleY)
    signatureError.value = ''
}

function drawTouch(event: TouchEvent) {
    event.preventDefault()
    if (!isDrawing.value) return
    const ctx = getContext()
    if (!ctx || !signatureCanvas.value) return
    const rect = signatureCanvas.value.getBoundingClientRect()
    const scaleX = signatureCanvas.value.width / rect.width
    const scaleY = signatureCanvas.value.height / rect.height
    const touch = event.touches[0]
    ctx.lineTo((touch.clientX - rect.left) * scaleX, (touch.clientY - rect.top) * scaleY)
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.stroke()
}

function clearSignature() {
    const ctx = getContext()
    if (!ctx || !signatureCanvas.value) return
    ctx.clearRect(0, 0, signatureCanvas.value.width, signatureCanvas.value.height)
    signatureData.value = null
    signatureError.value = ''
}

function isCanvasEmpty(): boolean {
    if (!signatureCanvas.value) return true
    const ctx = getContext()
    if (!ctx) return true
    const pixelData = ctx.getImageData(0, 0, signatureCanvas.value.width, signatureCanvas.value.height)
    return !pixelData.data.some(channel => channel !== 0)
}

function onDialogToggle(value: boolean) {
    if (!value) closeDialog()
}

function closeDialog() {
    emit('update:modelValue', false)
}

function confirmDialog() {
    if (isCanvasEmpty()) {
        signatureError.value = 'Unterschrift ist erforderlich'
        return
    }
    emit('confirm', { signature: signatureData.value! })
}
</script>

<style scoped>
.signature-container {
    display: block;
}

.signature-container.error-border canvas {
    border-color: rgb(var(--v-theme-error)) !important;
    border-width: 2px;
}
</style>
