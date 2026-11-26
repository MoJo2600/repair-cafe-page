<script setup lang="ts">
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { onBeforeUnmount, watch } from 'vue'

const model = defineModel<string>({ required: true })

const props = withDefaults(
  defineProps<{
    placeholder?: string
    disabled?: boolean
  }>(),
  {
    placeholder: 'Dokumenttext eingeben',
    disabled: false,
  }
)

const placeholders = [
  ['Kunde (voller Name)', 'customer_name'],
  ['Kundenvorname', 'customer_first_name'],
  ['Kundennachname', 'customer_last_name'],
  ['Kundentelefon', 'customer_phone'],
  ['Kunden-E-Mail', 'customer_email'],
  ['Datum', 'date'],
  ['Reparaturnummer', 'repair_number'],
  ['Reparaturkategorie', 'repair_type'],
  ['Gerät', 'device'],
  ['Fehlerbeschreibung', 'defect_description'],
  ['Unterschrift', 'signature'],
  ['Dokumentversion', 'template_version'],
] as const

const editor = useEditor({
  extensions: [StarterKit],
  content: model.value,
  editable: !props.disabled,
  editorProps: {
    attributes: {
      class: 'document-template-editor__content',
      role: 'textbox',
      'aria-label': props.placeholder,
      'aria-multiline': 'true',
    },
  },
  onUpdate: ({ editor: currentEditor }) => {
    model.value = currentEditor.getHTML()
  },
})

watch(model, (value) => {
  if (editor.value && value !== editor.value.getHTML()) {
    editor.value.commands.setContent(value, { emitUpdate: false })
  }
})

watch(
  () => props.disabled,
  (disabled) => editor.value?.setEditable(!disabled)
)

function command(name: 'bold' | 'italic' | 'bulletList' | 'orderedList' | 'undo' | 'redo') {
  const chain = editor.value?.chain().focus()
  if (!chain) return
  if (name === 'bold') chain.toggleBold().run()
  else if (name === 'italic') chain.toggleItalic().run()
  else if (name === 'bulletList') chain.toggleBulletList().run()
  else if (name === 'orderedList') chain.toggleOrderedList().run()
  else if (name === 'undo') chain.undo().run()
  else chain.redo().run()
}

function insertPlaceholder(name: string) {
  editor.value?.chain().focus().insertContent(`{{${name}}}`).run()
}

onBeforeUnmount(() => editor.value?.destroy())
</script>

<template>
  <div class="document-template-editor border rounded">
    <v-toolbar density="compact" flat class="document-template-editor__toolbar">
      <v-btn
        icon="mdi-format-bold"
        :active="editor?.isActive('bold')"
        :disabled="disabled || !editor"
        aria-label="Fett"
        @click="command('bold')"
      />
      <v-btn
        icon="mdi-format-italic"
        :active="editor?.isActive('italic')"
        :disabled="disabled || !editor"
        aria-label="Kursiv"
        @click="command('italic')"
      />
      <v-divider vertical class="mx-1" />
      <v-btn
        icon="mdi-format-list-bulleted"
        :active="editor?.isActive('bulletList')"
        :disabled="disabled || !editor"
        aria-label="Aufzählung"
        @click="command('bulletList')"
      />
      <v-btn
        icon="mdi-format-list-numbered"
        :active="editor?.isActive('orderedList')"
        :disabled="disabled || !editor"
        aria-label="Nummerierte Liste"
        @click="command('orderedList')"
      />
      <v-divider vertical class="mx-1" />
      <v-menu :disabled="disabled || !editor">
        <template #activator="{ props: menuProps }">
          <v-btn v-bind="menuProps" prepend-icon="mdi-code-braces">Platzhalter</v-btn>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="[label, name] in placeholders"
            :key="name"
            :title="label"
            :subtitle="`{{${name}}}`"
            @click="insertPlaceholder(name)"
          />
        </v-list>
      </v-menu>
      <v-spacer />
      <v-btn
        icon="mdi-undo"
        :disabled="disabled || !editor?.can().undo()"
        aria-label="Rückgängig"
        @click="command('undo')"
      />
      <v-btn
        icon="mdi-redo"
        :disabled="disabled || !editor?.can().redo()"
        aria-label="Wiederholen"
        @click="command('redo')"
      />
    </v-toolbar>
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.document-template-editor {
  overflow: hidden;
}

.document-template-editor__toolbar {
  border-bottom: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.document-template-editor :deep(.document-template-editor__content) {
  min-height: 300px;
  padding: 18px;
  outline: none;
  line-height: 1.55;
}

.document-template-editor :deep(.document-template-editor__content p) {
  margin-block: 0.7em;
}

.document-template-editor :deep(.document-template-editor__content ul),
.document-template-editor :deep(.document-template-editor__content ol) {
  padding-inline-start: 1.5rem;
}
</style>
