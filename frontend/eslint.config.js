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
  // docs/STYLEGUIDE.md: chips and colors come from the shared ui components and theme
  {
    files: ['src/**/*.vue'],
    ignores: ['src/components/ui/**'],
    rules: {
      'vue/no-restricted-syntax': [
        'error',
        {
          selector: "VElement[rawName='v-chip']:not(:has(VAttribute[key.name='closable']))",
          message:
            'Style guide: use StatusChip, TagChip or CountBadge from components/ui (only closable filter chips here).',
        },
      ],
      'vue/no-restricted-static-attribute': [
        'error',
        ...['color', 'dot-color', 'bg-color'].map((key) => ({
          key,
          value:
            '/^(red|pink|purple|deep-purple|indigo|blue|light-blue|cyan|teal|green|light-green|lime|yellow|amber|orange|deep-orange|brown|blue-grey|grey|white|black|secondary|accent)(-.*)?$/',
          message:
            'Style guide: use theme roles (primary, success, info, warning, error, status-*) instead of palette colors.',
        })),
      ],
    },
  },
  {
    files: ['src/vite-env.d.ts'],
    rules: { '@typescript-eslint/no-empty-object-type': 'off' },
  }
)
