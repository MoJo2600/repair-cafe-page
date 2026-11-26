<script setup lang="ts">
import TextAlign from '@tiptap/extension-text-align'
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
  extensions: [
    StarterKit,
    TextAlign.configure({
      types: ['heading', 'paragraph'],
      alignments: ['left', 'center', 'right', 'justify'],
    }),
  ],
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

type EditorCommand =
  | 'bold'
  | 'italic'
  | 'underline'
  | 'strike'
  | 'bulletList'
  | 'orderedList'
  | 'blockquote'
  | 'horizontalRule'
  | 'undo'
  | 'redo'

function command(name: EditorCommand) {
  const chain = editor.value?.chain().focus()
  if (!chain) return
  if (name === 'bold') chain.toggleBold().run()
  else if (name === 'italic') chain.toggleItalic().run()
  else if (name === 'underline') chain.toggleUnderline().run()
  else if (name === 'strike') chain.toggleStrike().run()
  else if (name === 'bulletList') chain.toggleBulletList().run()
  else if (name === 'orderedList') chain.toggleOrderedList().run()
  else if (name === 'blockquote') chain.toggleBlockquote().run()
  else if (name === 'horizontalRule') chain.setHorizontalRule().run()
  else if (name === 'undo') chain.undo().run()
  else chain.redo().run()
}

function setBlock(level: 1 | 2 | 3 | 4 | 5 | 6 | null) {
  const chain = editor.value?.chain().focus()
  if (!chain) return
  if (level === null) chain.setParagraph().run()
  else chain.toggleHeading({ level }).run()
}

function setTextAlign(alignment: 'left' | 'center' | 'right' | 'justify') {
  editor.value?.chain().focus().setTextAlign(alignment).run()
}

function clearFormatting() {
  editor.value?.chain().focus().unsetAllMarks().clearNodes().run()
}

function insertPlaceholder(name: string) {
  editor.value?.chain().focus().insertContent(`{{${name}}}`).run()
}

onBeforeUnmount(() => editor.value?.destroy())
</script>

<template>
  <div class="document-template-editor border rounded">
    <div class="document-template-editor__toolbar d-flex flex-wrap align-center ga-1 pa-2">
      <v-menu :disabled="disabled || !editor">
        <template #activator="{ props: menuProps }">
          <v-btn
            v-bind="menuProps"
            prepend-icon="mdi-format-header-pound"
            append-icon="mdi-menu-down"
          >
            Absatzstil
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item title="Normaler Text" @click="setBlock(null)" />
          <v-divider class="my-1" />
          <v-list-item title="Überschrift 1" @click="setBlock(1)" />
          <v-list-item title="Überschrift 2" @click="setBlock(2)" />
          <v-list-item title="Überschrift 3" @click="setBlock(3)" />
          <v-list-item title="Überschrift 4" @click="setBlock(4)" />
          <v-list-item title="Überschrift 5" @click="setBlock(5)" />
          <v-list-item title="Überschrift 6" @click="setBlock(6)" />
        </v-list>
      </v-menu>
      <v-divider vertical class="mx-1" />
      <v-btn
        icon="mdi-format-bold"
        :active="editor?.isActive('bold')"
        :disabled="disabled || !editor"
        aria-label="Fett"
        title="Fett"
        @click="command('bold')"
      />
      <v-btn
        icon="mdi-format-italic"
        :active="editor?.isActive('italic')"
        :disabled="disabled || !editor"
        aria-label="Kursiv"
        title="Kursiv"
        @click="command('italic')"
      />
      <v-btn
        icon="mdi-format-underline"
        :active="editor?.isActive('underline')"
        :disabled="disabled || !editor"
        aria-label="Unterstreichen"
        title="Unterstreichen"
        @click="command('underline')"
      />
      <v-btn
        icon="mdi-format-strikethrough"
        :active="editor?.isActive('strike')"
        :disabled="disabled || !editor"
        aria-label="Durchstreichen"
        title="Durchstreichen"
        @click="command('strike')"
      />
      <v-divider vertical class="mx-1" />
      <v-btn
        v-for="alignment in [
          { value: 'left', icon: 'mdi-format-align-left', label: 'Linksbündig' },
          { value: 'center', icon: 'mdi-format-align-center', label: 'Zentriert' },
          { value: 'right', icon: 'mdi-format-align-right', label: 'Rechtsbündig' },
          { value: 'justify', icon: 'mdi-format-align-justify', label: 'Blocksatz' },
        ] as const"
        :key="alignment.value"
        :icon="alignment.icon"
        :active="editor?.isActive({ textAlign: alignment.value })"
        :disabled="disabled || !editor"
        :aria-label="alignment.label"
        :title="alignment.label"
        @click="setTextAlign(alignment.value)"
      />
      <v-divider vertical class="mx-1" />
      <v-btn
        icon="mdi-format-list-bulleted"
        :active="editor?.isActive('bulletList')"
        :disabled="disabled || !editor"
        aria-label="Aufzählung"
        title="Aufzählung"
        @click="command('bulletList')"
      />
      <v-btn
        icon="mdi-format-list-numbered"
        :active="editor?.isActive('orderedList')"
        :disabled="disabled || !editor"
        aria-label="Nummerierte Liste"
        title="Nummerierte Liste"
        @click="command('orderedList')"
      />
      <v-btn
        icon="mdi-format-quote-close"
        :active="editor?.isActive('blockquote')"
        :disabled="disabled || !editor"
        aria-label="Zitatblock"
        title="Zitatblock"
        @click="command('blockquote')"
      />
      <v-btn
        icon="mdi-minus"
        :disabled="disabled || !editor"
        aria-label="Trennlinie"
        title="Trennlinie"
        @click="command('horizontalRule')"
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
      <v-btn
        icon="mdi-format-clear"
        :disabled="disabled || !editor"
        aria-label="Formatierung entfernen"
        title="Formatierung entfernen"
        @click="clearFormatting"
      />
      <v-spacer />
      <v-btn
        icon="mdi-undo"
        :disabled="disabled || !editor?.can().undo()"
        aria-label="Rückgängig"
        title="Rückgängig"
        @click="command('undo')"
      />
      <v-btn
        icon="mdi-redo"
        :disabled="disabled || !editor?.can().redo()"
        aria-label="Wiederholen"
        title="Wiederholen"
        @click="command('redo')"
      />
    </div>
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

.document-template-editor :deep(.document-template-editor__content blockquote) {
  margin-inline: 0;
  padding-inline-start: 1rem;
  border-inline-start: 3px solid rgba(var(--v-theme-primary), 0.5);
}

.document-template-editor :deep(.document-template-editor__content hr) {
  margin-block: 1.5rem;
}
</style>
