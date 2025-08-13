<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// CHANGE THIS if your backend port differs
const apiBase =
  import.meta.env?.VITE_API_URL ||
  (location.port === '5173' ? 'http://127.0.0.1:8001' : window.location.origin)

const api = axios.create({ baseURL: apiBase })

// DATA
const herd = ref({ total: 0, bulls: 0, cows: 0, heifers: 0, calves: 0, unknown: 0 })
const camps = ref([])      // [{id, name}]
const animals = ref([])    // raw from API

// UI state
const loading = ref(false)
const errorMsg = ref('')
const search = ref('')
const filterSex = ref(null)   // 'M' | 'F' | null
const filterCamp = ref(null)  // camp id | null

// Create dialog state
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  tag_number: '',
  sex: '',
  birth_date: '',
  pregnancy_status: '',
  camp_id: null,
  notes: '',
})

// Edit dialog state
const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({
  name: '',
  tag_number: '',
  sex: '',
  birth_date: '',
  pregnancy_status: '',
  camp_id: null,
  notes: '',
})

// Upload state
const uploadFiles = ref({})   // { [animalId]: File | File[] }
const uploadingId = ref(null)

// HELPERS
function campName(id) {
  const c = camps.value.find(x => x.id === id)
  return c ? c.name : '—'
}
function ageMonths(yyyy_mm_dd) {
  if (!yyyy_mm_dd) return 0
  const d = new Date(yyyy_mm_dd)
  if (isNaN(+d)) return 0
  const now = new Date()
  let years = now.getFullYear() - d.getFullYear()
  let months = now.getMonth() - d.getMonth()
  if (now.getDate() < d.getDate()) months -= 1
  const total = years * 12 + months
  return total < 0 ? 0 : total
}
function ageLabel(yyyy_mm_dd) {
  const total = ageMonths(yyyy_mm_dd)
  if (total < 12) return `${total} mo`
  const y = Math.floor(total / 12)
  const m = total % 12
  const yLabel = `${y} yr${y === 1 ? '' : 's'}`
  return m > 0 ? `${yLabel} ${m} mo` : yLabel
}
function capFirst(s) { return s ? s[0].toUpperCase() + s.slice(1) : s }

const headers = [
  { title: 'Tag', value: 'tag_number' },
  { title: 'Sex', value: 'sex' },
  { title: 'Birth date', value: 'birth_date' },
  { title: 'Age', value: 'age_label' },
  { title: 'Pregnancy', value: 'pregnancy_status' },
  { title: 'Name', value: 'name' },
  { title: 'Camp', value: 'camp' },
  { title: 'Notes', value: 'notes' },
  { title: 'Photo', value: 'photo_path' },
  { title: 'Upload', value: 'upload', sortable: false },
  { title: 'Actions', value: 'actions', sortable: false },
]

// Derived view
const animalsView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return animals.value
    .map(a => ({
      ...a,
      age_label: ageLabel(a.birth_date),
      camp: campName(a.camp_id),
    }))
    .filter(a => {
      if (filterSex.value && (a.sex || '').toUpperCase() !== filterSex.value) return false
      if (filterCamp.value != null && a.camp_id !== filterCamp.value) return false
      if (!needle) return true
      return (
        (a.tag_number || '').toLowerCase().includes(needle) ||
        (a.name || '').toLowerCase().includes(needle) ||
        (a.camp || '').toLowerCase().includes(needle)
      )
    })
})

// Show pregnancy field only for females >= 6 months
const showPregnancyCreate = computed(() =>
  (form.value.sex || '').toUpperCase() === 'F' && ageMonths(form.value.birth_date) >= 6
)
const showPregnancyEdit = computed(() =>
  (editForm.value.sex || '').toUpperCase() === 'F' && ageMonths(editForm.value.birth_date) >= 6
)

// LOADERS
async function fetchAnimals() {
  const { data } = await api.get('/animals/')
  animals.value = data
}
async function fetchHerd() {
  const { data } = await api.get('/stats/herd-summary')
  herd.value = data
}
async function fetchCamps() {
  const { data } = await api.get('/camps/')
  camps.value = data
}
async function loadAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    await Promise.all([fetchAnimals(), fetchHerd(), fetchCamps()])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ACTIONS
async function createAnimal() {
  creating.value = true
  try {
    const payload = { ...form.value }
    // trim + '' -> null
    for (const k of Object.keys(payload)) {
      if (typeof payload[k] === 'string') payload[k] = payload[k].trim()
      if (payload[k] === '') payload[k] = null
    }
    if (payload.sex) payload.sex = String(payload.sex).toUpperCase()
    if (Number.isNaN(payload.camp_id)) payload.camp_id = null
    if (payload.birth_date && !/^\d{4}-\d{2}-\d{2}$/.test(payload.birth_date)) {
      throw new Error('Birth date must be YYYY-MM-DD')
    }
    if (!showPregnancyCreate.value) payload.pregnancy_status = null

    // create and update UI immediately
    const { data: created } = await api.post('/animals/', payload)
    animals.value = [created, ...animals.value]   // optimistic
    await fetchHerd()                             // refresh counts

    // reset form & close
    form.value = {
      name: '',
      tag_number: '',
      sex: '',
      birth_date: '',
      pregnancy_status: '',
      camp_id: null,
      notes: '',
    }
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  } finally {
    creating.value = false
  }
}

function getFirstFile(val) {
  if (!val) return null
  return Array.isArray(val) ? val[0] : val
}
function hasFile(id) {
  return !!getFirstFile(uploadFiles.value[id])
}
async function uploadPhoto(animalId) {
  const file = getFirstFile(uploadFiles.value[animalId])
  if (!file) { alert('Pick a file first'); return }
  const fd = new FormData()
  fd.append('file', file, file.name)
  try {
    uploadingId.value = animalId
    await api.post(`/animals/${animalId}/upload-photo`, fd) // let Axios set boundary
    uploadFiles.value[animalId] = null
    await fetchAnimals()
  } catch (e) {
    console.error('Upload failed:', e)
    alert(e?.response?.data?.detail || e.message || 'Upload failed')
  } finally {
    uploadingId.value = null
  }
}

function openEdit(item) {
  editing.value = item
  editForm.value = {
    name: item.name || '',
    tag_number: item.tag_number || '',
    sex: (item.sex || '').toUpperCase(),
    birth_date: item.birth_date || '',
    pregnancy_status: item.pregnancy_status || '',
    camp_id: item.camp_id ?? null,
    notes: item.notes || '',
  }
  editOpen.value = true
}

async function saveEdit() {
  if (!editing.value) return
  savingEdit.value = true
  try {
    const payload = { ...editForm.value }
    for (const k of Object.keys(payload)) {
      if (typeof payload[k] === 'string') payload[k] = payload[k].trim()
      if (payload[k] === '') payload[k] = null
    }
    if (payload.sex) payload.sex = String(payload.sex).toUpperCase()
    if (payload.birth_date && !/^\d{4}-\d{2}-\d{2}$/.test(payload.birth_date)) {
      throw new Error('Birth date must be YYYY-MM-DD')
    }
    if (!showPregnancyEdit.value) payload.pregnancy_status = null

    const { data: updated } = await api.patch(`/animals/${editing.value.id}`, payload)

    // update row locally
    const idx = animals.value.findIndex(a => a.id === editing.value.id)
    if (idx !== -1) animals.value.splice(idx, 1, updated)

    await fetchHerd()
    editOpen.value = false
    editing.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  } finally {
    savingEdit.value = false
  }
}

const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)
function askDelete(item) { toDelete.value = item; confirmDelete.value = true }
async function doDelete() {
  if (!toDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/animals/${toDelete.value.id}`)
    animals.value = animals.value.filter(a => a.id !== toDelete.value.id)
    await fetchHerd()
    confirmDelete.value = false
    toDelete.value = null
  } finally {
    deleting.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="1200">
    <h1 class="text-h5 mb-4">Animals</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <!-- OVERVIEW -->
    <v-row class="mb-6" dense>
      <v-col cols="6" md="2" v-for="k in ['total','bulls','cows','heifers','calves','unknown']" :key="k">
        <v-sheet class="pa-4 text-center" elevation="1" rounded>
          <div class="text-overline">{{ k[0].toUpperCase() + k.slice(1) }}</div>
          <div class="text-h6">{{ herd[k] }}</div>
        </v-sheet>
      </v-col>
    </v-row>

    <!-- CAMPS OVERVIEW + CONTROLS -->
    <v-row class="mb-4" align="stretch">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Camps Overview</span>
            <v-spacer />
            <v-btn variant="text" @click="loadAll" :loading="loading">Refresh</v-btn>
          </v-card-title>
          <v-data-table
            :headers="[{ title:'Camp', value:'name' }, { title:'Animals', value:'animal_count' }]"
            :items="camps.map(c => ({...c, animal_count: c.animal_count ?? animals.filter(a => a.camp_id === c.id).length }))"
            :items-per-page="8"
            density="comfortable"
          />
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Filters</span>
            <v-spacer />
            <v-btn variant="text" @click="search=''; filterSex=null; filterCamp=null">Clear</v-btn>
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12">
                <v-text-field v-model="search" label="Search tag / name / camp" />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="filterSex"
                  :items="[{title:'All', value:null},{title:'Female', value:'F'},{title:'Male', value:'M'}]"
                  label="Sex"
                />
              </v-col>
              <v-col cols="6">
                <v-autocomplete
                  v-model="filterCamp"
                  :items="[{id:null, name:'All camps'}, ...camps]"
                  item-title="name"
                  item-value="id"
                  label="Camp"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ANIMALS TABLE -->
    <v-card class="mb-6">
      <v-card-title class="d-flex align-center">
        <span class="text-h6">Animals</span>
        <v-spacer />
        <v-btn color="primary" @click="createOpen = true">Create animal</v-btn>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="animalsView"
        :items-per-page="25"
        :sort-by="[{ key: 'tag_number', order: 'asc' }]"
        must-sort
      >
        <template #item.pregnancy_status="{ item }">
          {{ item.pregnancy_status ? capFirst(item.pregnancy_status) : '—' }}
        </template>

        <template #item.photo_path="{ item }">
          <div v-if="item.photo_path">
            <a :href="apiBase + item.photo_path" target="_blank">View</a>
          </div>
          <div v-else>—</div>
        </template>

        <template #item.upload="{ item }">
          <v-file-input
            accept="image/*"
            :multiple="false"
            density="compact"
            show-size
            prepend-icon="mdi-camera"
            v-model="uploadFiles[item.id]"
            style="max-width: 320px"
          />
          <v-btn class="mt-2"
                 @click="uploadPhoto(item.id)"
                 :loading="uploadingId === item.id"
                 :disabled="!hasFile(item.id)">
            Upload
          </v-btn>
        </template>

        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openEdit(item)">Edit</v-btn>
          <v-btn color="error" variant="text" @click="askDelete(item)">Delete</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- CREATE DIALOG -->
    <v-dialog v-model="createOpen" max-width="640" persistent>
      <v-card>
        <v-card-title>Create animal</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createAnimal" @keydown.enter.prevent="createAnimal">
            <v-text-field v-model="form.tag_number" label="Tag number" />
            <v-select v-model="form.sex" :items="['F','M']" label="Sex" clearable />
            <v-text-field v-model="form.birth_date" type="date" label="Birth date" />
            <v-text-field v-model="form.name" label="Name" />
            <v-autocomplete
              v-model="form.camp_id"
              :items="camps"
              item-title="name"
              item-value="id"
              label="Camp"
              clearable
            />
            <v-select
              v-if="showPregnancyCreate"
              v-model="form.pregnancy_status"
              :items="[{title:'Pregnant', value:'pregnant'}, {title:'Open', value:'open'}]"
              label="Pregnancy status"
              clearable
            />
            <v-textarea v-model="form.notes" label="Notes" />
            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="creating">Create</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- EDIT DIALOG -->
    <v-dialog v-model="editOpen" max-width="640" persistent>
      <v-card>
        <v-card-title>Edit animal</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveEdit" @keydown.enter.prevent="saveEdit">
            <v-text-field v-model="editForm.tag_number" label="Tag number" />
            <v-text-field v-model="editForm.name" label="Name" />
            <v-select v-model="editForm.sex" :items="['F','M']" label="Sex" clearable />
            <v-text-field v-model="editForm.birth_date" type="date" label="Birth date" />
            <v-autocomplete
              v-model="editForm.camp_id"
              :items="camps"
              item-title="name"
              item-value="id"
              label="Camp"
              clearable
            />
            <v-select
              v-if="showPregnancyEdit"
              v-model="editForm.pregnancy_status"
              :items="[{title:'Pregnant', value:'pregnant'}, {title:'Open', value:'open'}]"
              label="Pregnancy status"
              clearable
            />
            <v-textarea v-model="editForm.notes" label="Notes" />
            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="editOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="savingEdit">Save</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- DELETE CONFIRM -->
    <v-dialog v-model="confirmDelete" max-width="420">
      <v-card>
        <v-card-title>
          Delete {{ (toDelete && (toDelete.tag_number || toDelete.name || ('#' + toDelete.id))) || '' }}?
        </v-card-title>
        <v-card-text>This cannot be undone.</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete = false">Cancel</v-btn>
          <v-btn color="error" @click="doDelete" :loading="deleting">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
