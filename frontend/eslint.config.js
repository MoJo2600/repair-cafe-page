import pluginVue from 'eslint-plugin-vue'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import prettierConfig from 'eslint-config-prettier'

export default defineConfigWithVueTs(
  { files: ['**/*.{ts,vue}'] },
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  prettierConfig,
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      // Vuetify data tables use dotted slot names like #item.status
      'vue/valid-v-slot': ['error', { allowModifiers: true }],
      // Route-level views keep their single-word names (Dashboard)
      'vue/multi-word-component-names': ['error', { ignores: ['Dashboard'] }],
    },
  },
  {
    files: ['src/vite-env.d.ts'],
    rules: { '@typescript-eslint/no-empty-object-type': 'off' },
  }
)
