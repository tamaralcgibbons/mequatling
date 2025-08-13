import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const mequatlingTheme = {
  dark: false,
  colors: {
    primary: '#B63400',      // orange
    secondary: '#FFFFFF',    // white
    background: '#FFFFFF',   // page background
    surface: '#FFFFFF',      // cards, app bar surface in light mode
    error: '#E53935',
    info: '#1E88E5',
    success: '#43A047',
    warning: '#FB8C00',
  },
}

export default createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'mequatling',
    themes: { mequatling: mequatlingTheme },
  },
  defaults: {
    VCard: { elevation: 2, rounded: 'xl' },
    VBtn: { color: 'primary', rounded: 'xl' },
  },
})