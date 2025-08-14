// src/main.js
import { createApp } from 'vue'
import App from './App.vue'

// Vuetify
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import vuetify from './plugins/vuetify'

// Router
import router from './router'

createApp(App).use(vuetify).use(router).mount('#app')
