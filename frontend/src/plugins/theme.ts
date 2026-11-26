import type { ThemeDefinition, VuetifyOptions } from 'vuetify'

/**
 * Application theme tokens and component defaults.
 *
 * Deployments can customize the visual identity here without changing components
 * or exposing appearance settings in the UI.
 */
export const appThemes: Record<'light' | 'dark', ThemeDefinition> = {
  light: {
    colors: {
      primary: '#1976D2',
      secondary: '#424242',
      accent: '#82B1FF',
      'media-background': '#000000',
      'signature-ink': '#111111',
      error: '#FF5252',
      info: '#2196F3',
      success: '#4CAF50',
      warning: '#FB8C00',
      'status-open': '#EF8A00',
      'status-in-progress': '#1E88E5',
      'status-repaired': '#2E9D4F',
      'status-not-repaired': '#D93A35',
    },
  },
  dark: {
    dark: true,
    colors: {
      primary: '#2196F3',
      secondary: '#424242',
      accent: '#FF4081',
      'media-background': '#000000',
      'signature-ink': '#111111',
      error: '#FF5252',
      info: '#2196F3',
      success: '#4CAF50',
      warning: '#FB8C00',
      'status-open': '#FFA726',
      'status-in-progress': '#64B5F6',
      'status-repaired': '#66BB6A',
      'status-not-repaired': '#EF5350',
    },
  },
}

export const appDefaults: VuetifyOptions['defaults'] = {
  VAutocomplete: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VCombobox: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VDateInput: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VFileInput: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VFileUpload: {
    rounded: 'lg',
    density: 'compact',
  },
  VSelect: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VTextarea: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
  VTextField: {
    variant: 'outlined',
    density: 'comfortable',
    rounded: 'lg',
  },
}
