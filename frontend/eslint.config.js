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
    },
  }
)
