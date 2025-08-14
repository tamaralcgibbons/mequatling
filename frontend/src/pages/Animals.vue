<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/lib/api'

// ===================== DATA =====================
const herd = ref({ total: 0, bulls: 0, cows: 0, heifers: 0, calves: 0, unknown: 0 })
const camps = ref([])           // [{id, name}]
const animals = ref([])         // raw from API
const groups = ref([])          // [{id, name, camp_id, animal_count}]
const vaccines = ref([])        // [{id, name, default_dose, unit, methods:[]}]
const vaccinations = ref([])    // (optional) if you show history later

// ===================== UI STATE =====================
const loading = ref(false)
const errorMsg = ref('')
const search = ref('')
const filterSex = ref(null)      // 'M' | 'F' | null
const filterCamp = ref(null)     // camp id | null
const filterGroup = ref(null)    // group id | null
const showDeceased = ref(false)  // toggle showing deceased animals in table

// ---------- Create animal ----------
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  tag_number: '',
  sex: '',
  birth_date: '',
  pregnancy_status: '',
  camp_id: null,
  group_id: null,
  notes: '',
  // NEW: parity / calves
  has_calved: false,
  calves_count: null,
  calves_tags: [''], // array of strings; allow 'unknown'
})

// ---------- Edit animal ----------
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
  group_id: null,
  notes: '',
  // NEW: parity / calves
  has_calved: false,
  calves_count: null,
  calves_tags: [''],
})

// ---------- Upload state ----------
const uploadFiles = ref({})   // { [animalId]: File | File[] }
const uploadingId = ref(null)

// ---------- Delete / Deceased ----------
const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)
// mode: 'deceased' | 'hard'
const deleteMode = ref('deceased')
const killed = ref(false)
const deathReason = ref('')

// ---------- Groups: create / edit / move ----------
const groupCreateOpen = ref(false)
const groupEditOpen = ref(false)
const groupMoveOpen = ref(false)
const creatingGroup = ref(false)
const savingGroup = ref(false)
const movingGroup = ref(false)
const groupForm = ref({
  id: null,
  name: '',
  camp_id: null,
  animal_ids: [],
})
const groupMoveForm = ref({
  id: null,
  camp_id: null,
})
const selectedAnimals = ref([]) // used in groups create/edit picklist

// ---------- Vaccinations (group & individual) ----------
const vaccGroupOpen = ref(false)
const vaccAnimalOpen = ref(false)
const recordingVaccGroup = ref(false)
const recordingVaccAnimal = ref(false)
const vaccGroupForm = ref({
  group_id: null,
  vaccine_id: null,
  date: '',
  dose_per_animal: null,
  method: '',
})
const vaccAnimalForm = ref({
  animal_id: null,
  vaccine_id: null,
  date: '',
  dose: null,
  method: '',
  source: 'manual', // or 'group'
})

// ===================== HELPERS =====================
function campName(id) {
  const c = camps.value.find(x => x.id === id)
  return c ? c.name : '—'
}
function groupName(id) {
  const g = groups.value.find(x => x.id === id)
  return g ? g.name : '—'
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
function femaleClass(a) {
  if ((a.sex || '').toUpperCase() !== 'F') return null
  return a.has_calved ? 'Cow' : 'Heifer'
}

// ===================== TABLE HEADERS =====================
const headers = [
  { title: 'Tag', value: 'tag_number' },
  { title: 'Sex', value: 'sex' },
  { title: 'Class', value: 'female_class' },
  { title: 'Birth date', value: 'birth_date' },
  { title: 'Age', value: 'age_label' },
  { title: 'Pregnancy', value: 'pregnancy_status' },
  { title: 'Name', value: 'name' },
  { title: 'Camp', value: 'camp' },
  { title: 'Group', value: 'group' },
  { title: 'Notes', value: 'notes' },
  { title: 'Photo', value: 'photo_path' },
  { title: 'Upload', value: 'upload', sortable: false },
  { title: 'Actions', value: 'actions', sortable: false },
]

// ===================== DERIVED VIEW =====================
const animalsView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return Array.isArray(animals.value)
    ? animals.value
      .filter(a => showDeceased.value ? true : !a.deceased)
      .map(a => ({
        ...a,
        age_label: ageLabel(a.birth_date),
        camp: campName(a.camp_id),
        group: groupName(a.group_id),
        female_class: femaleClass(a),
      }))
      .filter(a => {
        // Sex/Class filter logic
        if (filterSex.value === 'F') {
          if ((a.sex || '').toUpperCase() !== 'F') return false
        } else if (filterSex.value === 'M') {
          if ((a.sex || '').toUpperCase() !== 'M') return false
        } else if (filterSex.value === 'heifer') {
          if (a.female_class !== 'Heifer') return false
        } else if (filterSex.value === 'cow') {
          if (a.female_class !== 'Cow') return false
        }
        if (filterCamp.value != null && a.camp_id !== filterCamp.value) return false
        if (filterGroup.value != null && a.group_id !== filterGroup.value) return false
        if (!needle) return true
        return (
          (a.tag_number || '').toLowerCase().includes(needle) ||
          (a.name || '').toLowerCase().includes(needle) ||
          (a.camp || '').toLowerCase().includes(needle) ||
          (a.group || '').toLowerCase().includes(needle)
        )
      })
    : []
})

// Pregnancy field only for females >= 6 months (kept from your original logic)
const showPregnancyCreate = computed(() =>
  (form.value.sex || '').toUpperCase() === 'F' && ageMonths(form.value.birth_date) >= 6
)
const showPregnancyEdit = computed(() =>
  (editForm.value.sex || '').toUpperCase() === 'F' && ageMonths(editForm.value.birth_date) >= 6
)

// Show calving fields when female
const showCalvingCreate = computed(() => (form.value.sex || '').toUpperCase() === 'F')
const showCalvingEdit = computed(() => (editForm.value.sex || '').toUpperCase() === 'F')

// Keep calves_tags aligned with calves_count
watch(() => form.value.calves_count, n => {
  const c = Number(n ?? 0)
  if (!Number.isFinite(c) || c < 0) return
  if (!Array.isArray(form.value.calves_tags)) form.value.calves_tags = []
  while (form.value.calves_tags.length < c) form.value.calves_tags.push('')
  while (form.value.calves_tags.length > c) form.value.calves_tags.pop()
})
watch(() => editForm.value.calves_count, n => {
  const c = Number(n ?? 0)
  if (!Number.isFinite(c) || c < 0) return
  if (!Array.isArray(editForm.value.calves_tags)) editForm.value.calves_tags = []
  while (editForm.value.calves_tags.length < c) editForm.value.calves_tags.push('')
  while (editForm.value.calves_tags.length > c) editForm.value.calves_tags.pop()
})

// ===================== LOADERS =====================
async function fetchAnimals() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get('/animals/')
    animals.value = Array.isArray(data) ? data : (data.animals || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load animals'
  } finally {
    loading.value = false
  }
}
async function fetchHerd() {
  try {
    const { data } = await api.get('/stats/herd-summary')
    herd.value = data
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load herd summary'
  }
}
async function fetchCamps() {
  try {
    const { data } = await api.get('/camps/')
    camps.value = Array.isArray(data) ? data : (data.camps || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load camps'
  }
}
async function fetchGroups() {
  try {
    const { data } = await api.get('/groups/')
    groups.value = Array.isArray(data) ? data : (data.groups || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load groups'
  }
}
async function fetchVaccines() {
  try {
    const { data } = await api.get('/stocks/vaccines')
    vaccines.value = Array.isArray(data) ? data : (data.vaccines || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load vaccines'
  }
}
async function loadAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    await Promise.all([fetchAnimals(), fetchHerd(), fetchCamps(), fetchGroups(), fetchVaccines()])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// ===================== ACTIONS: ANIMALS =====================
async function createAnimal() {
  creating.value = true
  try {
    const payload = { ...form.value }
    for (const k of Object.keys(payload)) {
      if (typeof payload[k] === 'string') payload[k] = payload[k].trim()
      if (payload[k] === '') payload[k] = null
    }
    if (payload.sex) payload.sex = String(payload.sex).toUpperCase()
    if (Number.isNaN(payload.camp_id)) payload.camp_id = null
    if (Number.isNaN(payload.group_id)) payload.group_id = null
    if (payload.birth_date && !/^\d{4}-\d{2}-\d{2}$/.test(payload.birth_date)) {
      throw new Error('Birth date must be YYYY-MM-DD')
    }
    // Normalize calves tags
    if (payload.has_calved) {
      payload.calves_count = Number(payload.calves_count ?? 0)
      if (payload.calves_count < 0) payload.calves_count = 0
      payload.calves_tags = (payload.calves_tags || []).slice(0, payload.calves_count).map(s => (s || '').trim() || 'unknown')
    } else {
      payload.calves_count = 0
      payload.calves_tags = []
    }
    if (!showPregnancyCreate.value) payload.pregnancy_status = null

    const { data: created } = await api.post('/animals/', payload)
    animals.value = [created, ...animals.value]
    await Promise.all([fetchHerd(), fetchGroups()])

    // reset
    form.value = {
      name: '',
      tag_number: '',
      sex: '',
      birth_date: '',
      pregnancy_status: '',
      camp_id: null,
      group_id: null,
      notes: '',
      has_calved: false,
      calves_count: null,
      calves_tags: [''],
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
function hasFile(id) { return !!getFirstFile(uploadFiles.value[id]) }

async function uploadPhoto(animalId) {
  const file = getFirstFile(uploadFiles.value[animalId])
  if (!file) { alert('Pick a file first'); return }
  const fd = new FormData()
  fd.append('file', file, file.name)
  try {
    uploadingId.value = animalId
    await api.post(`/animals/${animalId}/upload-photo`, fd)
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
    group_id: item.group_id ?? null,
    notes: item.notes || '',
    has_calved: !!item.has_calved,
    calves_count: Number.isFinite(item.calves_count) ? item.calves_count : (item.has_calved ? (item.calves_tags?.length || 1) : 0),
    calves_tags: Array.isArray(item.calves_tags) ? [...item.calves_tags] : (item.has_calved ? [''] : []),
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

    // parity normalization
    if (payload.has_calved) {
      payload.calves_count = Number(payload.calves_count ?? 0)
      if (payload.calves_count < 0) payload.calves_count = 0
      payload.calves_tags = (payload.calves_tags || []).slice(0, payload.calves_count).map(s => (s || '').trim() || 'unknown')
    } else {
      payload.calves_count = 0
      payload.calves_tags = []
    }

    const { data: updated } = await api.patch(`/animals/${editing.value.id}`, payload)
    const idx = animals.value.findIndex(a => a.id === editing.value.id)
    if (idx !== -1) animals.value.splice(idx, 1, updated)

    await Promise.all([fetchHerd(), fetchGroups()])
    editOpen.value = false
    editing.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  } finally {
    savingEdit.value = false
  }
}

function askDelete(item) {
  toDelete.value = item
  confirmDelete.value = true
  deleteMode.value = 'deceased'
  killed.value = false
  deathReason.value = ''
}

async function doDelete() {
  if (!toDelete.value) return
  deleting.value = true
  try {
    if (deleteMode.value === 'hard') {
      // permanently remove
      await api.delete(`/animals/${toDelete.value.id}`, { params: { hard: true } })
      animals.value = animals.value.filter(a => a.id !== toDelete.value.id)
    } else {
      // move to deceased (with optional killed + reason)
      await api.post(`/animals/${toDelete.value.id}/deceased`, {
        killed: !!killed.value,
        reason: deathReason.value?.trim() || null,
      })
      // refresh animals
      await fetchAnimals()
    }
    await fetchHerd()
    confirmDelete.value = false
    toDelete.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deleting.value = false
  }
}

// ===================== ACTIONS: GROUPS =====================
function openGroupCreate() {
  groupForm.value = { id: null, name: '', camp_id: null, animal_ids: [] }
  selectedAnimals.value = []
  groupCreateOpen.value = true
}
function openGroupEdit(g) {
  groupForm.value = { id: g.id, name: g.name || '', camp_id: g.camp_id ?? null, animal_ids: [] }
  // Preselect existing members
  const memberIds = new Set(animals.value.filter(a => a.group_id === g.id).map(a => a.id))
  selectedAnimals.value = animals.value
    .filter(a => !a.deceased)
    .map(a => ({ ...a, selected: memberIds.has(a.id) }))
  groupEditOpen.value = true
}
function openGroupMove(g) {
  groupMoveForm.value = { id: g.id, camp_id: g.camp_id ?? null }
  groupMoveOpen.value = true
}

async function createGroup() {
  creatingGroup.value = true
  try {
    const animal_ids = selectedAnimals.value.filter(a => a.selected).map(a => a.id)
    const payload = {
      name: (groupForm.value.name || '').trim(),
      camp_id: groupForm.value.camp_id ?? null,
      animal_ids,
    }
    if (!payload.name) throw new Error('Group name is required')
    const { data } = await api.post('/groups/', payload)
    groups.value = [data, ...groups.value]
    // Update animals (group assignment changed)
    await fetchAnimals()
    groupCreateOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create group failed')
  } finally {
    creatingGroup.value = false
  }
}

async function saveGroupEdit() {
  savingGroup.value = true
  try {
    const animal_ids = selectedAnimals.value.filter(a => a.selected).map(a => a.id)
    const payload = {
      name: (groupForm.value.name || '').trim() || null,
      camp_id: groupForm.value.camp_id ?? null,
      animal_ids,
    }
    const { data } = await api.patch(`/groups/${groupForm.value.id}`, payload)
    // refresh everything affected
    await Promise.all([fetchGroups(), fetchAnimals()])
    groupEditOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Save group failed')
  } finally {
    savingGroup.value = false
  }
}

async function moveGroupCamp() {
  movingGroup.value = true
  try {
    const payload = { camp_id: groupMoveForm.value.camp_id ?? null }
    await api.post(`/groups/${groupMoveForm.value.id}/move-camp`, payload)
    await Promise.all([fetchGroups(), fetchAnimals()])
    groupMoveOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Move group failed')
  } finally {
    movingGroup.value = false
  }
}

// ===================== ACTIONS: VACCINATIONS =====================
function openGroupVaccination() {
  vaccGroupForm.value = { group_id: null, vaccine_id: null, date: '', dose_per_animal: null, method: '' }
  vaccGroupOpen.value = true
}
function openAnimalVaccination(a) {
  vaccAnimalForm.value = { animal_id: a.id, vaccine_id: null, date: '', dose: null, method: '', source: 'manual' }
  vaccAnimalOpen.value = true
}

const groupOptions = computed(() => groups.value.map(g => ({ ...g, label: `${g.name} (${g.animal_count ?? animals.value.filter(a => a.group_id === g.id).length})` })))

const vaccineOptions = computed(() => vaccines.value.map(v => ({
  ...v, label: v.unit ? `${v.name} (${v.unit})` : v.name
})))

watch(() => vaccGroupForm.value.vaccine_id, id => {
  const v = vaccines.value.find(x => x.id === id)
  if (v && (vaccGroupForm.value.dose_per_animal == null || vaccGroupForm.value.dose_per_animal === '')) {
    vaccGroupForm.value.dose_per_animal = v.default_dose ?? null
    if (!vaccGroupForm.value.method && Array.isArray(v.methods) && v.methods.length) {
      vaccGroupForm.value.method = v.methods[0]
    }
  }
})
watch(() => vaccAnimalForm.value.vaccine_id, id => {
  const v = vaccines.value.find(x => x.id === id)
  if (v && (vaccAnimalForm.value.dose == null || vaccAnimalForm.value.dose === '')) {
    vaccAnimalForm.value.dose = v.default_dose ?? null
    if (!vaccAnimalForm.value.method && Array.isArray(v.methods) && v.methods.length) {
      vaccAnimalForm.value.method = v.methods[0]
    }
  }
})

async function recordGroupVaccination() {
  recordingVaccGroup.value = true
  try {
    const payload = { ...vaccGroupForm.value }
    payload.dose_per_animal = Number(payload.dose_per_animal)
    if (!payload.group_id) throw new Error('Select a group')
    if (!payload.vaccine_id) throw new Error('Select a vaccine')
    if (!payload.date) throw new Error('Select a date')
    if (!Number.isFinite(payload.dose_per_animal) || payload.dose_per_animal <= 0) {
      throw new Error('Enter a valid dose per animal')
    }
    await api.post('/vaccinations/group', payload)
    // Optionally refresh vaccinations or animals if state changes are reflected
    vaccGroupOpen.value = false
    // (Stock will be adjusted on the backend: dose_per_animal * group_size)
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Vaccination failed')
  } finally {
    recordingVaccGroup.value = false
  }
}

async function recordAnimalVaccination() {
  recordingVaccAnimal.value = true
  try {
    const payload = { ...vaccAnimalForm.value }
    payload.dose = Number(payload.dose)
    if (!payload.animal_id) throw new Error('Missing animal')
    if (!payload.vaccine_id) throw new Error('Select a vaccine')
    if (!payload.date) throw new Error('Select a date')
    if (!Number.isFinite(payload.dose) || payload.dose <= 0) {
      throw new Error('Enter a valid dose')
    }
    await api.post('/vaccinations/animal', payload)
    vaccAnimalOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Vaccination failed')
  } finally {
    recordingVaccAnimal.value = false
  }
}

// ===================== LIFECYCLE =====================
onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="1300">
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

    <!-- GROUPS + CONTROLS -->
    <v-row class="mb-4" align="stretch">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Groups</span>
            <v-spacer />
            <v-btn color="primary" size="small" @click="openGroupCreate">New group</v-btn>
          </v-card-title>
          <v-data-table
            :headers="[
              { title:'Group', value:'name' },
              { title:'Camp', value:'camp' },
              { title:'Animals', value:'count' },
              { title:'Actions', value:'actions', sortable:false }
            ]"
            :items="groups.map(g => ({
              ...g,
              camp: campName(g.camp_id),
              count: g.animal_count ?? animals.filter(a => a.group_id === g.id && !a.deceased).length
            }))"
            :items-per-page="8"
            density="comfortable"
          >
            <template #item.actions="{ item }">
              <v-btn size="small" variant="text" @click="openGroupEdit(item)">Edit</v-btn>
              <v-btn size="small" variant="text" @click="openGroupMove(item)">Move to camp</v-btn>
            </template>
          </v-data-table>
        </v-card>

        <v-card class="mt-4">
          <v-card-title>Vaccination Tools</v-card-title>
          <v-card-text class="text-body-2">
            Assign vaccinations to whole groups (date, dose per animal, method) from the Stocks list; stocks are adjusted on the backend.
            You can also override or add an individual vaccination from the Animals table's “More” menu.
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn variant="outlined" @click="openGroupVaccination">Record group vaccination</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span>Filters</span>
            <v-spacer />
            <v-btn variant="text" @click="search=''; filterSex=null; filterCamp=null; filterGroup=null">Clear</v-btn>
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12">
                <v-text-field v-model="search" label="Search tag / name / camp / group" />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="filterSex"
                  :items="[
                    { title: 'All', value: null },
                    { title: 'All Females', value: 'F' },
                    { title: 'Heifers', value: 'heifer' },
                    { title: 'Cows', value: 'cow' },
                    { title: 'Bulls', value: 'M' }
                  ]"
                  label="Sex / Class"
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
              <v-col cols="12">
                <v-autocomplete
                  v-model="filterGroup"
                  :items="[{id:null, name:'All groups'}, ...groups]"
                  item-title="name"
                  item-value="id"
                  label="Group"
                />
              </v-col>
              <v-col cols="12">
                <v-switch v-model="showDeceased" label="Show deceased animals" hide-details />
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
        <template #item.sex="{ item }">
          <span v-if="item.deceased" class="text-error" title="Deceased">{{ item.sex || '—' }}</span>
          <span v-else>{{ item.sex || '—' }}</span>
        </template>

        <template #item.female_class="{ item }">
          {{ item.female_class || '—' }}
        </template>

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
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="text">More</v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="openEdit(item)">Edit</v-list-item>
              <v-list-item @click="openAnimalVaccination(item)">Record vaccination</v-list-item>
              <v-list-item class="text-error" @click="askDelete(item)">Delete / mark deceased</v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </v-card>

    <!-- CREATE ANIMAL -->
    <v-dialog v-model="createOpen" max-width="720" persistent>
      <v-card>
        <v-card-title>Create animal</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createAnimal" @keydown.enter.prevent="createAnimal">
            <v-row dense>
              <v-col cols="12" md="6"><v-text-field v-model="form.tag_number" label="Tag number" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model="form.name" label="Name" /></v-col>
              <v-col cols="12" md="6"><v-select v-model="form.sex" :items="['F','M']" label="Sex" clearable /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model="form.birth_date" type="date" label="Birth date" /></v-col>

              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="form.camp_id"
                  :items="camps"
                  item-title="name"
                  item-value="id"
                  label="Camp"
                  clearable
                />
              </v-col>

              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="form.group_id"
                  :items="groups"
                  item-title="name"
                  item-value="id"
                  label="Group"
                  clearable
                />
              </v-col>

              <v-col cols="12" v-if="showPregnancyCreate">
                <v-select
                  v-model="form.pregnancy_status"
                  :items="[{title:'Pregnant', value:'pregnant'}, {title:'Open', value:'open'}]"
                  label="Pregnancy status"
                  clearable
                />
              </v-col>

              <!-- NEW: Calving / parity -->
              <v-col cols="12" v-if="showCalvingCreate">
                <v-switch v-model="form.has_calved" label="Has had a calf?" />
              </v-col>

              <template v-if="showCalvingCreate && form.has_calved">
                <v-col cols="12" md="4">
                  <v-text-field v-model.number="form.calves_count" type="number" min="0" label="Number of calves" />
                </v-col>
                <v-col cols="12" md="8" class="pt-2">
                  <div class="text-caption mb-1">Calf tag numbers (use “unknown” if not known):</div>
                  <div v-for="(t, idx) in form.calves_tags" :key="idx" class="d-flex align-center mb-2">
                    <v-text-field v-model="form.calves_tags[idx]" :label="`Calf ${idx+1} tag`" class="mr-2" />
                  </div>
                </v-col>
              </template>

              <v-col cols="12"><v-textarea v-model="form.notes" label="Notes" /></v-col>
            </v-row>

            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="creating">Create</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- EDIT ANIMAL -->
    <v-dialog v-model="editOpen" max-width="720" persistent>
      <v-card>
        <v-card-title>Edit animal</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveEdit" @keydown.enter.prevent="saveEdit">
            <v-row dense>
              <v-col cols="12" md="6"><v-text-field v-model="editForm.tag_number" label="Tag number" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model="editForm.name" label="Name" /></v-col>
              <v-col cols="12" md="6"><v-select v-model="editForm.sex" :items="['F','M']" label="Sex" clearable /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model="editForm.birth_date" type="date" label="Birth date" /></v-col>

              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="editForm.camp_id"
                  :items="camps"
                  item-title="name"
                  item-value="id"
                  label="Camp"
                  clearable
                />
              </v-col>

              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="editForm.group_id"
                  :items="groups"
                  item-title="name"
                  item-value="id"
                  label="Group"
                  clearable
                />
              </v-col>

              <v-col cols="12" v-if="showPregnancyEdit">
                <v-select
                  v-model="editForm.pregnancy_status"
                  :items="[{title:'Pregnant', value:'pregnant'}, {title:'Open', value:'open'}]"
                  label="Pregnancy status"
                  clearable
                />
              </v-col>

              <!-- NEW: Calving / parity -->
              <v-col cols="12" v-if="showCalvingEdit">
                <v-switch v-model="editForm.has_calved" label="Has had a calf (parity ≥ 1)" />
              </v-col>

              <template v-if="showCalvingEdit && editForm.has_calved">
                <v-col cols="12" md="4">
                  <v-text-field v-model.number="editForm.calves_count" type="number" min="0" label="Number of calves" />
                </v-col>
                <v-col cols="12" md="8" class="pt-2">
                  <div class="text-caption mb-1">Calf tag numbers (use “unknown” if not known):</div>
                  <div v-for="(t, idx) in editForm.calves_tags" :key="idx" class="d-flex align-center mb-2">
                    <v-text-field v-model="editForm.calves_tags[idx]" :label="`Calf ${idx+1} tag`" class="mr-2" />
                  </div>
                </v-col>
              </template>

              <v-col cols="12"><v-textarea v-model="editForm.notes" label="Notes" /></v-col>
            </v-row>

            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="editOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="savingEdit">Save</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- DELETE / DECEASED -->
    <v-dialog v-model="confirmDelete" max-width="520">
      <v-card>
        <v-card-title>
          Delete {{ (toDelete && (toDelete.tag_number || toDelete.name || ('#' + toDelete.id))) || '' }}?
        </v-card-title>
        <v-card-text>
          <v-radio-group v-model="deleteMode">
            <v-radio label="Move to Deceased folder" value="deceased" />
            <v-radio label="Permanently remove from system" value="hard" />
          </v-radio-group>

          <div v-if="deleteMode==='deceased'">
            <v-switch v-model="killed" label="Killed" hide-details />
            <v-textarea
              v-model="deathReason"
              label="Reason (optional, e.g. snake bite, injury, non-performer...)"
              auto-grow
            />
          </div>

          <p class="text-caption mt-2">
            This cannot be undone for permanent removal. Deceased animals are retained for history and reporting.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete = false">Cancel</v-btn>
          <v-btn color="error" @click="doDelete" :loading="deleting">
            {{ deleteMode==='hard' ? 'Delete permanently' : 'Mark deceased' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- GROUP CREATE -->
    <v-dialog v-model="groupCreateOpen" max-width="780" persistent>
      <v-card>
        <v-card-title>Create group</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12" md="6"><v-text-field v-model="groupForm.name" label="Group name" /></v-col>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="groupForm.camp_id"
                :items="camps"
                item-title="name"
                item-value="id"
                label="Camp (optional)"
                clearable
              />
            </v-col>
          </v-row>
          <div class="text-subtitle-2 mb-2">Select animals</div>
          <v-virtual-scroll :items="animals.filter(a => !a.deceased)" height="300">
            <template #default="{ item }">
              <div class="d-flex align-center py-1 px-2">
                <v-checkbox v-model="item.selected" class="mr-2" />
                <div class="mr-4" style="width: 90px">{{ item.tag_number || '—' }}</div>
                <div class="mr-4" style="width: 50px">{{ item.sex }}</div>
                <div class="mr-4" style="width: 120px">{{ campName(item.camp_id) }}</div>
                <div class="mr-4">{{ item.name || '—' }}</div>
              </div>
            </template>
          </v-virtual-scroll>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="groupCreateOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="createGroup" :loading="creatingGroup">Create group</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- GROUP EDIT -->
    <v-dialog v-model="groupEditOpen" max-width="780" persistent>
      <v-card>
        <v-card-title>Edit group</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12" md="6"><v-text-field v-model="groupForm.name" label="Group name" /></v-col>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="groupForm.camp_id"
                :items="camps"
                item-title="name"
                item-value="id"
                label="Camp (optional)"
                clearable
              />
            </v-col>
          </v-row>
          <div class="text-subtitle-2 mb-2">Members</div>
          <v-virtual-scroll :items="selectedAnimals" height="300">
            <template #default="{ item }">
              <div class="d-flex align-center py-1 px-2">
                <v-checkbox v-model="item.selected" class="mr-2" />
                <div class="mr-4" style="width: 90px">{{ item.tag_number || '—' }}</div>
                <div class="mr-4" style="width: 50px">{{ item.sex }}</div>
                <div class="mr-4" style="width: 120px">{{ campName(item.camp_id) }}</div>
                <div class="mr-4">{{ item.name || '—' }}</div>
              </div>
            </template>
          </v-virtual-scroll>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="groupEditOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveGroupEdit" :loading="savingGroup">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- GROUP MOVE CAMP -->
    <v-dialog v-model="groupMoveOpen" max-width="520" persistent>
      <v-card>
        <v-card-title>Move group to camp</v-card-title>
        <v-card-text>
          <v-autocomplete
            v-model="groupMoveForm.camp_id"
            :items="camps"
            item-title="name"
            item-value="id"
            label="Destination camp"
            clearable
          />
          <div class="text-caption mt-2">
            Animals in the group will be moved en masse. Individual animals can still be assigned to a different camp later if separated.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="groupMoveOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="moveGroupCamp" :loading="movingGroup">Move</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- GROUP VACCINATION -->
    <v-dialog v-model="vaccGroupOpen" max-width="640" persistent>
      <v-card>
        <v-card-title>Record group vaccination</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12">
              <v-autocomplete
                v-model="vaccGroupForm.group_id"
                :items="groupOptions"
                item-title="label"
                item-value="id"
                label="Group"
                clearable
              />
            </v-col>
            <v-col cols="12">
              <v-autocomplete
                v-model="vaccGroupForm.vaccine_id"
                :items="vaccineOptions"
                item-title="label"
                item-value="id"
                label="Vaccine (from Stocks)"
                clearable
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="vaccGroupForm.date" type="date" label="Date" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model.number="vaccGroupForm.dose_per_animal" type="number" min="0" step="0.001" label="Dose per animal" />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="vaccGroupForm.method"
                :items="(vaccines.find(v => v.id === vaccGroupForm.vaccine_id)?.methods || [])"
                label="Administration method"
                clearable
              />
            </v-col>
          </v-row>
          <div class="text-caption mt-2">
            Stock will be reduced by (dose per animal × number of animals in group). You can override per-animal later if needed.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="vaccGroupOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordGroupVaccination" :loading="recordingVaccGroup">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- INDIVIDUAL VACCINATION -->
    <v-dialog v-model="vaccAnimalOpen" max-width="520" persistent>
      <v-card>
        <v-card-title>Record individual vaccination</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12">
              <v-autocomplete
                v-model="vaccAnimalForm.vaccine_id"
                :items="vaccineOptions"
                item-title="label"
                item-value="id"
                label="Vaccine (from Stocks)"
                clearable
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="vaccAnimalForm.date" type="date" label="Date" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model.number="vaccAnimalForm.dose" type="number" min="0" step="0.001" label="Dose" />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="vaccAnimalForm.method"
                :items="(vaccines.find(v => v.id === vaccAnimalForm.vaccine_id)?.methods || [])"
                label="Administration method"
                clearable
              />
            </v-col>
          </v-row>
          <div class="text-caption mt-2">
            If this vaccination was part of a recent group vaccination but needed a different dose/date, record it here to override.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="vaccAnimalOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordAnimalVaccination" :loading="recordingVaccAnimal">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
