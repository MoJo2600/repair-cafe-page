import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { de } from 'vuetify/locale'
import '@mdi/font/css/materialdesignicons.css'
import { appDefaults, appThemes } from './theme'

export default createVuetify({
  // Built-in texts (table paging, "no data", pickers, ...) in German
  locale: { locale: 'de', fallback: 'en', messages: { de } },
  // VIconBtn and VFileUpload are core components since Vuetify 4
  components,
  defaults: appDefaults,
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
    themes: appThemes,
  },
})
