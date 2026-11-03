import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { de } from 'vuetify/locale'
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
  // Built-in texts (table paging, "no data", pickers, ...) in German
  locale: { locale: 'de', fallback: 'en', messages: { de } },
  // VIconBtn and VFileUpload are core components since Vuetify 4
  components,
  defaults: {
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
      // The default dropzone is very tall; compact keeps forms and dialogs usable on tablets
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
  },
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FB8C00',
          // Repair statuses (docs/STYLEGUIDE.md): only for status chips, avatars and
          // status buttons; never for messages
          'status-open': '#EF8A00',
          'status-in-progress': '#1E88E5',
          'status-repaired': '#2E9D4F',
          'status-not-repaired': '#D93A35',
        },
      },
      dark: {
        colors: {
          primary: '#2196F3',
          secondary: '#424242',
          accent: '#FF4081',
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
    },
  },
})
