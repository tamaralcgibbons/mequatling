import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../pages/Dashboard.vue'
import Animals from '../pages/Animals.vue'
import Camps from '../pages/Camps.vue'
import Stocks from '../pages/Stocks.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/animals', name: 'animals', component: Animals },
  { path: '/camps', name: 'camps', component: Camps },
  { path: '/stocks', name: 'stocks', component: Stocks },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})