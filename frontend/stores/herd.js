// Pinia store for shared herd data (animals, camps, groups, vaccines, herd summary)
import { defineStore } from 'pinia'
import api from '@/services/api'

export const useHerdStore = defineStore('herd', {
  state: () => ({
    animals: [],
    camps: [],
    groups: [],
    vaccines: [],
    herdSummary: { total: 0, bulls: 0, cows: 0, heifers: 0, calves: 0, unknown: 0 },

    loading: {
      animals: false,
      camps: false,
      groups: false,
      vaccines: false,
      summary: false,
      all: false,
    },
    error: null,
  }),

  getters: {
    campsById: (s) => Object.fromEntries(s.camps.map(c => [c.id, c])),
    groupsById: (s) => Object.fromEntries(s.groups.map(g => [g.id, g])),
    campName: (s) => (id) => s.camps.find(c => c.id === id)?.name || '—',
    groupName: (s) => (id) => s.groups.find(g => g.id === id)?.name || '—',
    aliveAnimals: (s) => s.animals.filter(a => !a.deceased),
    groupCounts: (s) => {
      const counts = {}
      for (const a of s.animals) {
        if (a.deceased) continue
        const gid = a.group_id ?? 'none'
        counts[gid] = (counts[gid] || 0) + 1
      }
      return counts
    },
  },

  actions: {
    async fetchAnimals() {
      this.loading.animals = true
      try {
        const { data } = await api.get('/animals/')
        this.animals = Array.isArray(data) ? data : []
      } catch (e) {
        this.error = e?.response?.data?.detail || e.message || 'Failed to load animals'
        throw e
      } finally {
        this.loading.animals = false
      }
    },

    async fetchCamps() {
      this.loading.camps = true
      try {
        const { data } = await api.get('/camps/')
        this.camps = Array.isArray(data) ? data : []
      } catch (e) {
        this.error = e?.response?.data?.detail || e.message || 'Failed to load camps'
        throw e
      } finally {
        this.loading.camps = false
      }
    },

    async fetchGroups() {
      this.loading.groups = true
      try {
        const { data } = await api.get('/groups/')
        this.groups = Array.isArray(data) ? data : []
      } catch (e) {
        this.error = e?.response?.data?.detail || e.message || 'Failed to load groups'
        throw e
      } finally {
        this.loading.groups = false
      }
    },

    async fetchVaccines() {
      this.loading.vaccines = true
      try {
        const { data } = await api.get('/stocks/vaccines')
        this.vaccines = Array.isArray(data) ? data : []
      } catch (e) {
        this.error = e?.response?.data?.detail || e.message || 'Failed to load vaccines'
        throw e
      } finally {
        this.loading.vaccines = false
      }
    },

    async fetchHerdSummary() {
      this.loading.summary = true
      try {
        const { data } = await api.get('/stats/herd-summary')
        this.herdSummary = data || this.herdSummary
      } catch (e) {
        this.error = e?.response?.data?.detail || e.message || 'Failed to load herd summary'
        throw e
      } finally {
        this.loading.summary = false
      }
    },

    async loadAll() {
      this.loading.all = true
      this.error = null
      try {
        await Promise.all([
          this.fetchAnimals(),
          this.fetchCamps(),
          this.fetchGroups(),
          this.fetchVaccines(),
          this.fetchHerdSummary(),
        ])
      } finally {
        this.loading.all = false
      }
    },

    // --- Mutations that also refresh state (useful helpers) ---

    async createGroup({ name, camp_id = null, animal_ids = [] }) {
      const { data } = await api.post('/groups/', { name, camp_id, animal_ids })
      await Promise.all([this.fetchGroups(), this.fetchAnimals()])
      return data
    },

    async updateGroup(id, { name = null, camp_id = null, animal_ids = undefined }) {
      const payload = { name, camp_id }
      if (Array.isArray(animal_ids)) payload.animal_ids = animal_ids
      const { data } = await api.patch(`/groups/${id}`, payload)
      await Promise.all([this.fetchGroups(), this.fetchAnimals()])
      return data
    },

    async moveGroupToCamp(id, camp_id) {
      await api.post(`/groups/${id}/move-camp`, { camp_id })
      await Promise.all([this.fetchGroups(), this.fetchAnimals()])
    },

    async deleteGroup(id) {
      await api.delete(`/groups/${id}`)
      await Promise.all([this.fetchGroups(), this.fetchAnimals()])
    },

    async markAnimalDeceased(id, { killed = false, reason = null } = {}) {
      await api.post(`/animals/${id}/deceased`, { killed, reason })
      await Promise.all([this.fetchAnimals(), this.fetchHerdSummary()])
    },

    async hardDeleteAnimal(id) {
      await api.delete(`/animals/${id}`, { params: { hard: true } })
      await Promise.all([this.fetchAnimals(), this.fetchHerdSummary()])
    },

    async recordGroupVaccination({ group_id, vaccine_id, date, dose_per_animal, method }) {
      await api.post('/vaccinations/group', { group_id, vaccine_id, date, dose_per_animal, method })
      // stocks adjusted server-side; refresh if you surface stock values in UI
      await this.fetchVaccines().catch(() => {})
    },

    async recordAnimalVaccination({ animal_id, vaccine_id, date, dose, method, source = 'manual' }) {
      await api.post('/vaccinations/animal', { animal_id, vaccine_id, date, dose, method, source })
      await this.fetchVaccines().catch(() => {})
    },
  },
})
