<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')

const records = ref([])   // vaccination records
const groups = ref([])
const vaccines = ref([])
const animals = ref([]) // optional (used for dropdown of animals if needed)

// Filters
const q = ref('')                 // free text search (tag, name, vaccine)
const filterGroup = ref(null)     // group_id
const filterVaccine = ref(null)   // vaccine_id
const dateFrom = ref('')          // yyyy-mm-dd
const dateTo = ref('')
const source = ref('group')          // 'group' | 'manual' | null

// Paging (client-side)
const page = ref(1)
const itemsPerPage = ref(50)

// Loaders
async function fetchGroups() {
  const { data } = await api.get('/groups/')
  groups.value = Array.isArray(data) ? data : []
}
async function fetchVaccines() {
  const { data } = await api.get('/stocks/vaccines')
  vaccines.value = Array.isArray(data) ? data : []
}
async function fetchAnimals() {
  const { data } = await api.get('/animals/')
  animals.value = Array.isArray(data) ? data : []
}

// Server-side fetch for history; supports query params if your backend does
async function fetchHistory() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = {}
    if (filterGroup.value) params.group_id = filterGroup.value
    if (filterVaccine.value) params.vaccine_id = filterVaccine.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (source.value) params.source = source.value
    if (q.value?.trim()) params.q = q.value.trim()
    const { data } = await api.get('/vaccinations/', { params })
    records.value = Array.isArray(data) ? data : []
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load vaccination history'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadAll() {
  await Promise.all([fetchGroups(), fetchVaccines(), fetchAnimals()])
  await fetchHistory()
}

// Derived / table view
const headers = [
  { title: 'Date', value: 'date' },
  { title: 'Group', value: 'group' },
  { title: 'Vaccine', value: 'vaccine' },
  { title: 'Dose', value: 'dose_display' },
  { title: 'Method', value: 'method' },
  { title: 'Camp', value: 'camp' },
  { title: 'Notes', value: 'notes' },
]
const tableItems = computed(() => {
  const needle = q.value.trim().toLowerCase()
  const start = dateFrom.value ? new Date(dateFrom.value) : null
  const end = dateTo.value ? new Date(dateTo.value) : null
  return records.value
    .map(r => ({
      ...r,
      animal: r.animal_tag ? `${r.animal_tag}${r.animal_name ? ' — ' + r.animal_name : ''}` : (r.animal_name || '—'),
      group: r.group_name || '—',
      vaccine: r.vaccine_name || '—',
      dose_display: r.dose != null ? `${r.dose}${r.unit ? ' ' + r.unit : ''}` : '—',
      camp: r.camp_name || '—',
      notes: r.notes || '—', // <-- Map notes for display
      dateObj: r.date ? new Date(r.date) : null,
    }))
    .filter(r => (filterGroup.value ? r.group_id === filterGroup.value : true))
    .filter(r => (filterVaccine.value ? r.vaccine_id === filterVaccine.value : true))
    .filter(r => (source.value ? r.source === source.value : true))
    .filter(r => (start ? (r.dateObj && r.dateObj >= start) : true))
    .filter(r => (end ? (r.dateObj && r.dateObj <= end) : true))
    .filter(r => {
      if (!needle) return true
      return (
        (r.animal || '').toLowerCase().includes(needle) ||
        (r.group || '').toLowerCase().includes(needle) ||
        (r.vaccine || '').toLowerCase().includes(needle) ||
        (r.notes || '').toLowerCase().includes(needle) // <-- Allow searching notes
      )
    })
})

const groupVaccinations = computed(() =>
  allVaccinations.value.filter(v => v.source === 'group')
)

// Watch filters to refetch (if using server-side filtering)
watch([filterGroup, filterVaccine, dateFrom, dateTo, source], fetchHistory)
watch(q, () => { /* client-side only by default */ })

onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="1300">
    <h1 class="text-h5 mb-4">Vaccination History</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Filters</span>
        <v-spacer />
        <v-btn variant="text" @click="q=''; filterGroup=null; filterVaccine=null; dateFrom=''; dateTo=''; source=null">Clear</v-btn>
        <v-btn variant="text" @click="fetchHistory" :loading="loading">Refresh</v-btn>
      </v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="4">
            <v-text-field v-model="q" label="Search (tag, name, vaccine, notes)" />
          </v-col>
          <v-col cols="12" md="4">
            <v-autocomplete
              v-model="filterGroup"
              :items="[{id:null, name:'All groups'}, ...groups]"
              item-title="name"
              item-value="id"
              label="Group"
              clearable
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-autocomplete
              v-model="filterVaccine"
              :items="[{id:null, label:'All vaccines'}, ...vaccines.map(v => ({...v, label:v.name}))]"
              item-title="label"
              item-value="id"
              label="Vaccine"
              clearable
            />
          </v-col>
          <v-col cols="6" md="2">
            <v-text-field v-model="dateFrom" type="date" label="From" />
          </v-col>
          <v-col cols="6" md="2">
            <v-text-field v-model="dateTo" type="date" label="To" />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="source"
              :items="[{title:'All sources', value:null},{title:'Group', value:'group'},{title:'Manual', value:'manual'}]"
              label="Source"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- History Table -->
    <v-card>
      <v-data-table
        :items="tableItems"
        :headers="headers"
        :items-per-page="itemsPerPage"
        :page="page"
        :loading="loading"
        :sort-by="[{ key: 'date', order: 'desc' }]"
        class="mb-2"
      >
        <template #item.date="{ item }">
          {{ item.date || '—' }}
        </template>
        <template #item.source="{ item }">
          <v-chip size="small" :color="item.source === 'group' ? 'primary' : 'grey' " variant="flat">
            {{ item.source }}
          </v-chip>
        </template>
        <template #item.notes="{ item }">
          <span>{{ item.notes }}</span>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>