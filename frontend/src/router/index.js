// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const Dashboard = () => import('../pages/Dashboard.vue')
const Animals = () => import('../pages/Animals.vue')
const Camps = () => import('../pages/Camps.vue')
const Stocks = () => import('../pages/Stocks.vue')
const Groups = () => import('../pages/Groups.vue')
const VaccinationsHistory = () => import('../pages/VaccinationsHistory.vue')

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/animals', name: 'Animals', component: Animals },
  { path: '/camps', name: 'Camps', component: Camps },
  { path: '/stocks', name: 'Stocks', component: Stocks },
  { path: '/groups', name: 'Groups', component: Groups },
  { path: '/vaccinations-history', name: 'VaccinationsHistory', component: VaccinationsHistory },
  { path: '/history', name: 'History', component: () => import('@/pages/History.vue'), }
]

const router = createRouter({
  history: createWebHistory(), // ← robust for desktop/shortcut usage
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
