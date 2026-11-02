<script setup lang="ts">
import { ref, watch } from 'vue'

/**
 * Signature field for mouse, pen and touch.
 * v-model is the signature as PNG data URL, or null while empty.
 * Setting the model to null from outside clears the pad.
 */
const signature = defineModel<string | null>({ required: true })

const {
  width = 600,
  height = 180,
  error = '',
} = defineProps<{
  /** Canvas resolution; the element itself scales to the container width. */
  width?: number
  height?: number
  error?: string
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
let drawing = false

watch(signature, (value) => {
  if (value === null) clearCanvas()
})

function context(): CanvasRenderingContext2D | null {
  return canvas.value?.getContext('2d') ?? null
}

function toCanvasPoint(event: PointerEvent): { x: number; y: number } {
  const el = canvas.value!
  const rect = el.getBoundingClientRect()
  return {
    x: (event.clientX - rect.left) * (el.width / rect.width),
    y: (event.clientY - rect.top) * (el.height / rect.height),
  }
}

function onPointerDown(event: PointerEvent) {
  const ctx = context()
  if (!ctx || !canvas.value) return
  canvas.value.setPointerCapture(event.pointerId)
  drawing = true
  const { x, y } = toCanvasPoint(event)
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.beginPath()
  ctx.moveTo(x, y)
}

function onPointerMove(event: PointerEvent) {
  if (!drawing) return
  const ctx = context()
  if (!ctx) return
  const { x, y } = toCanvasPoint(event)
  ctx.lineTo(x, y)
  ctx.stroke()
}

function onPointerUp() {
  if (!drawing) return
  drawing = false
  signature.value = canvas.value?.toDataURL() ?? null
}

function clearCanvas() {
  const ctx = context()
  if (ctx && canvas.value) ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
}

function clear() {
  clearCanvas()
  signature.value = null
}
</script>

<template>
  <div class="signature-pad">
    <canvas
      ref="canvas"
      class="signature-pad__canvas"
      :class="{ 'signature-pad__canvas--error': error }"
      :width="width"
      :height="height"
      :style="{ maxWidth: `${width}px` }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    ></canvas>
    <div v-if="error" class="text-error text-body-small mt-1">{{ error }}</div>
    <v-btn size="small" variant="text" prepend-icon="mdi-eraser" class="mt-2" @click="clear">
      Unterschrift löschen
    </v-btn>
  </div>
</template>

<style scoped>
.signature-pad__canvas {
  display: block;
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: crosshair;
  /* Keep touch strokes from scrolling the page */
  touch-action: none;
}

.signature-pad__canvas--error {
  border: 2px solid rgb(var(--v-theme-error));
}
</style>
