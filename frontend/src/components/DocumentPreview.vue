<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const { html, loading = false } = defineProps<{
  html: string
  loading?: boolean
}>()

const safeHtml = computed(() =>
  DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
  })
)
</script>

<template>
  <v-sheet class="document-preview" border rounded>
    <v-progress-linear v-if="loading" indeterminate />
    <!-- The backend HTML is sanitized again here before this trusted display boundary. -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <article v-else class="document-preview__content" v-html="safeHtml" />
  </v-sheet>
</template>

<style scoped>
.document-preview {
  max-width: 860px;
  min-height: 240px;
  margin-inline: auto;
  background: rgb(var(--v-theme-surface));
  overflow: auto;
}

.document-preview__content {
  min-height: 240px;
  padding: clamp(20px, 6vw, 64px);
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.55;
}

.document-preview__content :deep(h1),
.document-preview__content :deep(h2),
.document-preview__content :deep(h3),
.document-preview__content :deep(h4),
.document-preview__content :deep(h5),
.document-preview__content :deep(h6) {
  line-height: 1.25;
  margin-block: 1em 0.45em;
}

.document-preview__content :deep(h1:first-child),
.document-preview__content :deep(h2:first-child),
.document-preview__content :deep(h3:first-child),
.document-preview__content :deep(h4:first-child),
.document-preview__content :deep(h5:first-child),
.document-preview__content :deep(h6:first-child),
.document-preview__content :deep(p:first-child) {
  margin-top: 0;
}

.document-preview__content :deep(p) {
  margin-block: 0.7em;
}

.document-preview__content :deep(.document-signature) {
  max-width: min(70mm, 100%);
  max-height: 25mm;
}

.document-preview__content :deep(.document-signature--blank) {
  display: inline-block;
  width: min(65mm, 60vw);
  height: 12mm;
  vertical-align: bottom;
  border-bottom: 1px solid currentColor;
}

.document-preview__content :deep(.document-footer) {
  margin-top: 32px;
  padding-top: 10px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  color: rgba(var(--v-theme-on-surface), 0.65);
  font-size: 0.75rem;
  text-align: right;
}
</style>
