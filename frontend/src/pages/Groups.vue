<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')
const groups = ref([])    // [{id, name, camp_id, animal_count}]
const camps = ref([])     // [{id, name}]
const animals = ref([])   // used for membership editing

const search = ref('')
const selected = ref([])  // selected groups in table (optional)

// Create
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  camp_id: null,
  animal_ids: [],
  notes: '',
})

// Edit
const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({
  id: null,
  name: '',
  camp_id: null,
  animal_ids: [],
  notes: '',
})
const membersPick = ref([]) // [{...animal, selected:bool}] for edit modal

// Move camp
const moveOpen = ref(false)
const moving = ref(false)
const moveForm = ref({
  id: null,
  camp_id: null,
})

// Delete
const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)

// Loaders
async function fetchGroups() {
  try {
    const { data } = await api.get('/groups/')
    groups.value = Array.isArray(data) ? data : (data.groups || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load groups'
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
async function fetchAnimals() {
  try {
    const { data } = await api.get('/animals/')
    animals.value = Array.isArray(data) ? data : (data.animals || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load animals'
  }
}
async function loadAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    await Promise.all([fetchGroups(), fetchCamps(), fetchAnimals()])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load groups'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// Helpers
function campName(id) {
  const c = camps.value.find(x => x.id === id)
  return c ? c.name : '—'
}
const headers = [
  { title: 'Group', value: 'name' },
  { title: 'Camp', value: 'camp' },
  { title: 'Animals', value: 'count' },
  { title: 'Notes', value: 'notes' },
  { title: 'Actions', value: 'actions', sortable: false },
]

// Create
function openCreate() {
  form.value = { name: '', camp_id: null, animal_ids: [] }
  createOpen.value = true
}
async function createGroup() {
  creating.value = true
  try {
    const payload = {
      name: (form.value.name || '').trim(),
      camp_id: form.value.camp_id ?? null,
      animal_ids: Array.isArray(form.value.animal_ids) ? form.value.animal_ids : [],
      notes: form.value.notes || '',
    }
    if (!payload.name) throw new Error('Group name is required')
    const { data } = await api.post('/groups/', payload)
    groups.value = [data, ...groups.value]
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Create group failed')
  } finally {
    creating.value = false
  }
}

// Edit (name/camp/members)
function openEdit(g) {
  editing.value = g
  editForm.value = {
    id: g.id,
    name: g.name || '',
    camp_id: g.camp_id ?? null,
    animal_ids: [],
    notes: g.notes || '',
  }
  // Seed pick list with all animals; select members of this group
  const memberIds = new Set(animals.value.filter(a => a.group_id === g.id && !a.deceased).map(a => a.id))
  membersPick.value = animals.value
    .filter(a => !a.deceased)
    .map(a => ({ ...a, selected: memberIds.has(a.id) }))
  editOpen.value = true
}
async function saveEdit() {
  if (!editing.value) return
  savingEdit.value = true
  try {
    const animal_ids = membersPick.value.filter(x => x.selected).map(x => x.id)
    const payload = {
      name: (editForm.value.name || '').trim() || null,
      camp_id: editForm.value.camp_id ?? null,
      animal_ids,
      notes: editForm.value.notes || '',
    }
    await api.patch(`/groups/${editForm.value.id}`, payload)
    await Promise.all([fetchGroups(), fetchAnimals()])
    editOpen.value = false
    editing.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Save failed')
  } finally {
    savingEdit.value = false
  }
}

// Move camp (en-masse)
function openMove(g) {
  moveForm.value = { id: g.id, camp_id: g.camp_id ?? null }
  moveOpen.value = true
}
async function moveGroup() {
  moving.value = true
  try {
    await api.post(`/groups/${moveForm.value.id}/move-camp`, { camp_id: moveForm.value.camp_id ?? null })
    await Promise.all([fetchGroups(), fetchAnimals()])
    moveOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Move failed')
  } finally {
    moving.value = false
  }
}

// Delete
function askDelete(g) { toDelete.value = g; confirmDelete.value = true }
async function doDelete() {
  if (!toDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/groups/${toDelete.value.id}`)
    groups.value = groups.value.filter(x => x.id !== toDelete.value.id)
    confirmDelete.value = false
    toDelete.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Delete failed')
  } finally {
    deleting.value = false
  }
}

// View group vaccinations
const vaccHistoryGroupOpen = ref(false)
const vaccHistoryGroup = ref(null)
const vaccHistoryGroupRecords = ref([])
const loadingVaccHistoryGroup = ref(false)
const vaccHistoryGroupError = ref('')

async function openGroupVaccHistory(group) {
  vaccHistoryGroup.value = group
  vaccHistoryGroupOpen.value = true
  vaccHistoryGroupRecords.value = []
  vaccHistoryGroupError.value = ''
  loadingVaccHistoryGroup.value = true
  try {
    const { data } = await api.get('/vaccinations/', { params: { group_id: group.id } })
    vaccHistoryGroupRecords.value = Array.isArray(data) ? data : []
  } catch (e) {
    vaccHistoryGroupError.value = e?.response?.data?.detail || e.message || 'Failed to load group vaccination history'
  } finally {
    loadingVaccHistoryGroup.value = false
  }
}

const expandedGroups = ref([])

// Add computed avgWeight and animals to each group
const groupsView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return Array.isArray(groups.value)
    ? groups.value
      .map(g => {
        const groupAnimals = animals.value.filter(a => a.group_id === g.id && !a.deceased)
        const weights = groupAnimals.map(a => a.current_weight).filter(w => w !== undefined && w !== null)
        const avgWeight = weights.length ? (weights.reduce((a, b) => a + b, 0) / weights.length).toFixed(1) : null
        return {
          ...g,
          camp: campName(g.camp_id),
          count: g.animal_count ?? groupAnimals.length,
          notes: g.notes || '',
          avgWeight,
          animals: groupAnimals,
        }
      })
      .filter(g => (needle ? (g.name || '').toLowerCase().includes(needle) || (g.camp || '').toLowerCase().includes(needle) : true))
    : []
})

// Save weight
async function saveAnimalWeight(animal) {
  try {
    await api.patch(`/animals/${animal.id}`, { ...animal, weight_date: new Date().toISOString().slice(0, 10) })
    await fetchAnimals()
  } catch (e) {
    alert('Failed to save weight')
  }
}

// Save pregnancy status
async function savePregnancyStatus(animal) {
  try {
    await api.patch(`/animals/${animal.id}`, {
      pregnant: animal.pregnant,
      pregnancy_duration: animal.pregnancy_duration,
      pregnancy_date: animal.pregnancy_date,
    })
    await fetchAnimals()
  } catch (e) {
    alert('Failed to save pregnancy status')
  }
}

// Weight history dialogs
const weightHistoryOpen = ref(false)
const weightHistoryAnimal = ref(null)
const weightHistoryRecords = ref([])
const loadingWeightHistory = ref(false)
const weightHistoryError = ref('')

async function openAnimalWeightHistory(animal) {
  weightHistoryAnimal.value = animal
  weightHistoryOpen.value = true
  weightHistoryRecords.value = []
  loadingWeightHistory.value = true
  try {
    const { data } = await api.get('/weights/', { params: { animal_id: animal.id } })
    weightHistoryRecords.value = Array.isArray(data) ? data : []
  } catch (e) {
    weightHistoryError.value = e?.response?.data?.detail || e.message || 'Failed to load weight history'
  } finally {
    loadingWeightHistory.value = false
  }
}

// Group weight history
const groupWeightHistoryOpen = ref(false)
const groupWeightHistoryGroup = ref(null)
const groupWeightHistoryRecords = ref([])
const loadingGroupWeightHistory = ref(false)
const groupWeightHistoryError = ref('')

async function openGroupWeightHistory(group) {
  groupWeightHistoryGroup.value = group
  groupWeightHistoryOpen.value = true
  groupWeightHistoryRecords.value = []
  loadingGroupWeightHistory.value = true
  try {
    const { data } = await api.get('/weights/', { params: { group_id: group.id } })
    groupWeightHistoryRecords.value = Array.isArray(data) ? data : []
  } catch (e) {
    groupWeightHistoryError.value = e?.response?.data?.detail || e.message || 'Failed to load group weight history'
  } finally {
    loadingGroupWeightHistory.value = false
  }
}

const recordWeightsOpen = ref(false)
const recordWeightsGroup = ref(null)
const recordWeightsAnimals = ref([])
const recordWeightsDate = ref(new Date().toISOString().slice(0, 10))
const recordWeightsSaving = ref(false)
const recordWeightsError = ref('')

function openRecordWeightsDialog(group) {
  recordWeightsGroup.value = group
  // Deep copy animals so editing doesn't affect the main list until saved
  recordWeightsAnimals.value = group.animals.map(a => ({
    ...a,
    new_weight: a.current_weight ?? ''
  }))
  recordWeightsDate.value = new Date().toISOString().slice(0, 10)
  recordWeightsOpen.value = true
  recordWeightsError.value = ''
}

async function saveGroupWeights() {
  recordWeightsSaving.value = true
  recordWeightsError.value = ''
  try {
    // Save each animal's weight
    for (const animal of recordWeightsAnimals.value) {
      if (animal.new_weight !== '') {
        await api.post('/weights/', {
          animal_id: animal.id,
          weight: Number(animal.new_weight),
          date: recordWeightsDate.value
        })
      }
    }
    await Promise.all([fetchGroups(), fetchAnimals()])
    recordWeightsOpen.value = false
  } catch (e) {
    recordWeightsError.value = e?.response?.data?.detail || e.message || 'Failed to record weights'
  } finally {
    recordWeightsSaving.value = false
  }
}

const vaccHistoryAnimalOpen = ref(false)
const vaccHistoryAnimal = ref(null)
const vaccHistoryAnimalRecords = ref([])
const loadingVaccHistoryAnimal = ref(false)
const vaccHistoryAnimalError = ref('')

async function openVaccinationHistory(animal) {
  vaccHistoryAnimal.value = animal
  vaccHistoryAnimalOpen.value = true
  vaccHistoryAnimalRecords.value = []
  vaccHistoryAnimalError.value = ''
  loadingVaccHistoryAnimal.value = true
  try {
    const { data } = await api.get('/vaccinations/', { params: { animal_id: animal.id } })
    vaccHistoryAnimalRecords.value = Array.isArray(data) ? data : []
  } catch (e) {
    vaccHistoryAnimalError.value = e?.response?.data?.detail || e.message || 'Failed to load vaccination history'
  } finally {
    loadingVaccHistoryAnimal.value = false
  }
}

const recordPregnancyOpen = ref(false)
const recordPregnancyGroup = ref(null)
const recordPregnancyAnimals = ref([])
const recordPregnancyDate = ref(new Date().toISOString().slice(0, 10))
const recordPregnancySaving = ref(false)
const recordPregnancyError = ref('')

function openRecordPregnancyDialog(group) {
  recordPregnancyGroup.value = group
  recordPregnancyAnimals.value = group.animals.map(a => ({
    ...a,
    pregnant: a.pregnant ?? false,
    pregnancy_duration: a.pregnancy_duration ?? '',
    pregnancy_date: a.pregnancy_date ?? recordPregnancyDate.value,
  }))
  recordPregnancyDate.value = new Date().toISOString().slice(0, 10)
  recordPregnancyOpen.value = true
  recordPregnancyError.value = ''
}

async function saveGroupPregnancy() {
  recordPregnancySaving.value = true
  recordPregnancyError.value = ''
  try {
    // Save each animal's pregnancy status
    for (const animal of recordPregnancyAnimals.value) {
      await api.patch(`/animals/${animal.id}`, {
        pregnant: animal.pregnant,
        pregnancy_duration: animal.pregnancy_duration,
        pregnancy_date: recordPregnancyDate.value
      })
    }
    await Promise.all([fetchGroups(), fetchAnimals()])
    console.log('Refreshed animals:', animals.value)
    console.log('Refreshed groups:', groups.value)
    console.log('First group animals:', groupsView.value[0].animals)
    recordPregnancyOpen.value = false
  } catch (e) {
    recordPregnancyError.value = e?.response?.data?.detail || e.message || 'Failed to record pregnancy tests'
  } finally {
    recordPregnancySaving.value = false
  }
}

const groupSlaughterOpen = ref(false)
const groupSlaughterGroup = ref(null)
const groupSlaughterDate = ref(new Date().toISOString().slice(0, 10))
const groupSlaughterReason = ref('')
const groupSlaughterSaving = ref(false)
const groupSlaughterError = ref('')

function openGroupSlaughterDialog(group) {
  groupSlaughterGroup.value = group
  groupSlaughterDate.value = new Date().toISOString().slice(0, 10)
  groupSlaughterReason.value = ''
  groupSlaughterOpen.value = true
  groupSlaughterError.value = ''
}

async function saveGroupSlaughter() {
  groupSlaughterSaving.value = true
  groupSlaughterError.value = ''
  try {
    await api.post(`/groups/${groupSlaughterGroup.value.id}/slaughter`, {
      date: groupSlaughterDate.value,
      reason: groupSlaughterReason.value,
    })
    await Promise.all([fetchGroups(), fetchAnimals()])
    groupSlaughterOpen.value = false
  } catch (e) {
    groupSlaughterError.value = e?.response?.data?.detail || e.message || 'Failed to send group to slaughter'
  } finally {
    groupSlaughterSaving.value = false
  }
}

const recordVaccinationOpen = ref(false)
const recordVaccinationVaccineId = ref(null)
const recordVaccinationAnimal = ref(null)
const recordVaccinationDate = ref(new Date().toISOString().slice(0, 10))
const recordVaccinationName = ref('')
const recordVaccinationDose = ref('')
const recordVaccinationUnit = ref('')
const recordVaccinationMethod = ref('')
const recordVaccinationSource = ref('')
const recordVaccinationNotes = ref('')
const recordVaccinationSaving = ref(false)
const recordVaccinationError = ref('')

function openRecordVaccinationDialog(animal) {
  recordVaccinationAnimal.value = animal
  recordVaccinationDate.value = new Date().toISOString().slice(0, 10)
  recordVaccinationName.value = ''
  recordVaccinationDose.value = ''
  recordVaccinationUnit.value = ''
  recordVaccinationMethod.value = ''
  recordVaccinationSource.value = ''
  recordVaccinationNotes.value = ''
  recordVaccinationOpen.value = true
  recordVaccinationError.value = ''
}

async function saveRecordVaccination() {
  recordVaccinationSaving.value = true
  recordVaccinationError.value = ''
  try {
    await api.post('/vaccinations/animal', {
      animal_id: recordVaccinationAnimal.value.id,
      vaccine_id: recordVaccinationVaccineId.value,
      date: recordVaccinationDate.value,
      dose: recordVaccinationDose.value,
      unit: recordVaccinationUnit.value,
      method: recordVaccinationMethod.value,
      source: recordVaccinationSource.value,
      notes: recordVaccinationNotes.value,
    })
    await fetchAnimals()
    recordVaccinationOpen.value = false
  } catch (e) {
    recordVaccinationError.value = e?.response?.data?.detail || e.message || 'Failed to record vaccination'
  } finally {
    recordVaccinationSaving.value = false
  }
}

const vaccines = ref([]) // [{id, name, methods, ...}]
const vaccineMethods = ref([]) // e.g. ["subcut", "IM", "SC"]

async function fetchVaccines() {
  try {
    const { data } = await api.get('/vaccines/')
    // Parse methods for each vaccine
    vaccines.value = Array.isArray(data)
      ? data.map(v => ({
          ...v,
          methods: Array.isArray(v.methods)
            ? v.methods
            : typeof v.methods === 'string'
              ? JSON.parse(v.methods)
              : []
        }))
      : []
    // Flatten all methods into a unique array
    vaccineMethods.value = [
      ...new Set(
        vaccines.value.flatMap(v => v.methods).filter(Boolean)
      )
    ]
  } catch (e) {
    console.error('Failed to fetch vaccines:', e)
  }
}
async function deleteVaccinationRecord(record) {
  if (!confirm('Delete this vaccination record?')) return
  try {
    await api.delete(`/vaccinations/${record.id}`)
    // Refresh the correct dialog
    if (vaccHistoryAnimalOpen.value) {
      await openVaccinationHistory(vaccHistoryAnimal.value)
    } else if (vaccHistoryGroupOpen.value) {
      await openGroupVaccHistory(vaccHistoryGroup.value)
    }
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Delete failed')
  }
}

onMounted(() => {
  loadAll()
  fetchVaccines()
})
</script>

<template>
  <v-container class="py-8" fluid>
    <h1 class="text-h5 mb-4">Groups</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <v-card>
      <v-card-title class="d-flex align-center">
        <span>Group List</span>
        <v-spacer />
        <v-text-field
          v-model="search"
          placeholder="Search groups/camps"
          density="compact"
          hide-details
          style="max-width: 260px"
        />
        <v-btn class="ml-2" color="primary" @click="openCreate">New group</v-btn>
      </v-card-title>

      <v-expansion-panels v-model="expandedGroups" multiple>
        <v-expansion-panel
          v-for="group in groupsView"
          :key="group.id"
          :value="group.id"
        >
          <v-expansion-panel-title>
            <span class="font-weight-bold">{{ group.name }}</span>
            <span class="ml-4">Camp: {{ group.camp }}</span>
            <span class="ml-4">Animals: {{ group.count }}</span>
            <span class="ml-4">Avg Weight: {{ group.avgWeight ?? '—' }} kg</span>
            <span class="ml-4">Notes: {{ group.notes }}</span>
            <v-spacer />
            <v-btn variant="text" color="primary" @click.stop="openRecordWeightsDialog(group)">Record Group Weights</v-btn>
            <v-btn variant="text" color="primary" @click.stop="openRecordPregnancyDialog(group)">Record Group Pregnancy Tests</v-btn>
            <v-btn variant="text" color="primary" @click.stop="openGroupVaccHistory(group)">Vaccination history</v-btn>
            <v-btn variant="text" color="primary" @click.stop="openGroupWeightHistory(group)">Weight history</v-btn>
            <v-btn variant="text" color="primary" @click.stop="openGroupSlaughterDialog(group)">Send group to slaughter</v-btn>
            <v-btn variant="text" @click.stop="openEdit(group)">Edit</v-btn>
            <v-btn variant="text" color="primary" @click.stop="askDelete(group)">Delete</v-btn>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="mb-2 font-weight-medium">Animals in group:</div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Tag</th>
                  <th>Sex</th>
                  <th>Current Weight (kg)</th>
                  <th>Pregnant?</th>
                  <th>Pregnancy Duration</th>
                  <th>Pregnancy Checked Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="animal in group.animals" :key="animal.id">
                  <td>{{ animal.tag_number }}</td>
                  <td>{{ animal.sex }}</td>
                  <td>{{ animal.current_weight }}</td>
                  <td v-if="animal.sex === 'F'">
                    {{ animal.pregnant ? 'Y' : 'N' }}</td>
                  <td v-else>—</td>
                  <td v-if="animal.sex === 'F' && animal.pregnant">
                    {{ animal.pregnancy_duration }}</td>
                  <td v-else>—</td>
                  <td v-if="animal.sex === 'F' && animal.pregnant">
                    {{ animal.pregnancy_date }}</td>
                  <td v-else>—</td>
                  <td>
                    <v-btn variant="text" color="primary" @click="openAnimalWeightHistory(animal)">Weight history</v-btn>
                    <v-btn variant="text" color="primary" @click="openVaccinationHistory(animal)">Vaccination history</v-btn>
                    <v-btn variant="text" color="primary" @click="openRecordVaccinationDialog(animal)">Record vaccination</v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>

    <!-- Create -->
    <v-dialog v-model="createOpen" max-width="640" persistent>
      <v-card>
        <v-card-title>Create group</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createGroup" @keydown.enter.prevent="createGroup">
            <v-row dense>
              <v-col cols="12" md="6"><v-text-field v-model="form.name" label="Group name" /></v-col>
              <v-col cols="12" md="6">
                <v-autocomplete
                  v-model="form.camp_id"
                  :items="camps"
                  item-title="name"
                  item-value="id"
                  label="Camp (optional)"
                  clearable
                />
              </v-col>
              <v-col cols="12">
                <v-textarea v-model="form.notes" label="Notes" />
              </v-col>
            </v-row>
            <div class="text-caption">
              You can add/remove members later from “Edit”.
            </div>
            <div class="d-flex justify-end mt-3">
              <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="creating">Create</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Edit (name, camp, members) -->
    <v-dialog v-model="editOpen" max-width="880" persistent>
      <v-card>
        <v-card-title>Edit group</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12" md="6"><v-text-field v-model="editForm.name" label="Group name" /></v-col>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="editForm.camp_id"
                :items="camps"
                item-title="name"
                item-value="id"
                label="Camp (optional)"
                clearable
              />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="editForm.notes" label="Notes" />
            </v-col>
          </v-row>

          <div class="text-subtitle-2 mt-2 mb-1">Members</div>
          <v-sheet class="pa-2" elevation="1" rounded>
            <v-virtual-scroll :items="membersPick" height="360">
              <template #default="{ item }">
                <div class="d-flex align-center py-1 px-2">
                  <v-checkbox v-model="item.selected" class="mr-3" density="compact" />
                  <div class="mr-4" style="width: 90px">{{ item.tag_number || '—' }}</div>
                  <div class="mr-4" style="width: 50px">{{ item.sex }}</div>
                  <div class="mr-4" style="width: 140px">{{ (camps.find(c => c.id === item.camp_id)?.name) || '—' }}</div>
                  <div class="mr-4">{{ item.name || '—' }}</div>
                </div>
              </template>
            </v-virtual-scroll>
          </v-sheet>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveEdit" :loading="savingEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Move to camp -->
    <v-dialog v-model="moveOpen" max-width="520" persistent>
      <v-card>
        <v-card-title>Move group to camp</v-card-title>
        <v-card-text>
          <v-autocomplete
            v-model="moveForm.camp_id"
            :items="camps"
            item-title="name"
            item-value="id"
            label="Destination camp"
            clearable
          />
          <div class="text-caption mt-2">
            All current members of the group will be moved to the selected camp. You can still override an individual animal later.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="moveOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="moveGroup" :loading="moving">Move</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete -->
    <v-dialog v-model="confirmDelete" max-width="420">
      <v-card>
        <v-card-title>Delete {{ toDelete?.name }}?</v-card-title>
        <v-card-text>This will unassign animals from this group.</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete=false">Cancel</v-btn>
          <v-btn color="error" @click="doDelete" :loading="deleting">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Group Vaccination History Dialog -->
    <v-dialog v-model="vaccHistoryGroupOpen" max-width="900">
      <v-card>
        <v-card-title>
          Vaccination history for group: {{ vaccHistoryGroup?.name || '—' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="vaccHistoryGroupError" type="error">{{ vaccHistoryGroupError }}</v-alert>
          <v-data-table
            v-if="vaccHistoryGroupRecords.length"
            :items="vaccHistoryGroupRecords"
            :headers="[
              { title: 'Date', value: 'date' },
              { title: 'Vaccine', value: 'vaccine_name' },
              { title: 'Dose', value: 'dose' },
              { title: 'Unit', value: 'unit' },
              { title: 'Method', value: 'method' },
              { title: 'Source', value: 'source' },
              { title: 'Notes', value: 'notes' },
              { title: 'Actions', value: 'actions', sortable: false }
            ]"
            :items-per-page="25"
            :loading="loadingVaccHistoryGroup"
          >
            <template #item.date="{ item }">
              {{ item.date ? item.date.split('T')[0] : '—' }}
            </template>
            <template #item.dose="{ item }">
              {{ item.dose }} {{ item.unit || '' }}
            </template>
            <template #item.actions="{ item }">
              <v-btn
                icon
                color="error"
                size="small"
                @click="deleteVaccinationRecord(item)"
                title="Delete vaccination record"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
          <div v-else-if="!loadingVaccHistoryGroup" class="text-caption">No vaccination records found.</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="vaccHistoryGroupOpen = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Animal Weight History Dialog -->
    <v-dialog v-model="weightHistoryOpen" max-width="700">
      <v-card>
        <v-card-title>
          Weight history for {{ weightHistoryAnimal?.tag_number || 'animal' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="weightHistoryError" type="error">{{ weightHistoryError }}</v-alert>
          <v-data-table
            v-if="weightHistoryRecords.length"
            :items="weightHistoryRecords"
            :headers="[
              { title: 'Date', value: 'date' },
              { title: 'Weight (kg)', value: 'weight' }
            ]"
            :items-per-page="25"
            :loading="loadingWeightHistory"
          />
          <div v-else-if="!loadingWeightHistory" class="text-caption">No weight records found.</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="weightHistoryOpen = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Group Weight History Dialog -->
    <v-dialog v-model="groupWeightHistoryOpen" max-width="700">
      <v-card>
        <v-card-title>
          Average group weight history for {{ groupWeightHistoryGroup?.name || 'group' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="groupWeightHistoryError" type="error">{{ groupWeightHistoryError }}</v-alert>
          <v-data-table
            v-if="groupWeightHistoryRecords.length"
            :items="groupWeightHistoryRecords"
            :headers="[
              { title: 'Date', value: 'date' },
              { title: 'Average Weight (kg)', value: 'avg_weight' }
            ]"
            :items-per-page="25"
            :loading="loadingGroupWeightHistory"
          />
          <div v-else-if="!loadingGroupWeightHistory" class="text-caption">No group weight records found.</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="groupWeightHistoryOpen = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Record Group Weight Dialogue -->
    <v-dialog v-model="recordWeightsOpen" max-width="700">
      <v-card>
        <v-card-title>
          Record weights for group: {{ recordWeightsGroup?.name || '—' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="recordWeightsError" type="error">{{ recordWeightsError }}</v-alert>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="recordWeightsDate"
                label="Date"
                type="date"
                density="compact"
                style="max-width: 350px"
              />
            </v-col>
          </v-row>
          <v-table density="compact">
            <thead>
              <tr>
                <th>Tag</th>
                <th>Sex</th>
                <th>Weight (kg)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="animal in recordWeightsAnimals" :key="animal.id">
                <td>{{ animal.tag_number }}</td>
                <td>{{ animal.sex }}</td>
                <td>
                  <v-text-field
                    v-model="animal.new_weight"
                    type="number"
                    density="compact"
                    style="max-width: 350px"
                    :placeholder="String(animal.current_weight ?? '—')"
                  />
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="recordWeightsOpen = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveGroupWeights" :loading="recordWeightsSaving">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="vaccHistoryAnimalOpen" max-width="900">
      <v-card>
        <v-card-title>
          Vaccination history for animal: {{ vaccHistoryAnimal?.tag_number || '—' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="vaccHistoryAnimalError" type="error">{{ vaccHistoryAnimalError }}</v-alert>
          <v-data-table
            v-if="vaccHistoryAnimalRecords.length"
            :items="vaccHistoryAnimalRecords"
            :headers="[
              { title: 'Date', value: 'date' },
              { title: 'Vaccine', value: 'vaccine_name' },
              { title: 'Dose', value: 'dose' },
              { title: 'Unit', value: 'unit' },
              { title: 'Method', value: 'method' },
              { title: 'Source', value: 'source' },
              { title: 'Notes', value: 'notes' },
              { title: 'Actions', value: 'actions', sortable: false }
            ]"
            :items-per-page="25"
            :loading="loadingVaccHistoryAnimal"
          >
            <template #item.date="{ item }">
              {{ item.date ? item.date.split('T')[0] : '—' }}
            </template>
            <template #item.dose="{ item }">
              {{ item.dose }} {{ item.unit || '' }}
            </template>
            <template #item.actions="{ item }">
              <v-btn
                icon
                color="error"
                size="small"
                @click="deleteVaccinationRecord(item)"
                title="Delete vaccination record"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
          <div v-else-if="!loadingVaccHistoryAnimal" class="text-caption">No vaccination records found.</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="vaccHistoryAnimalOpen = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Group Pregnancy Record Dialogue -->
    <v-dialog v-model="recordPregnancyOpen" max-width="1000">
      <v-card>
        <v-card-title>
          Record pregnancy tests for group: {{ recordPregnancyGroup?.name || '—' }}
        </v-card-title>
        <v-card-text>
          <v-alert v-if="recordPregnancyError" type="error">{{ recordPregnancyError }}</v-alert>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="recordPregnancyDate"
                label="Test Date"
                type="date"
                density="compact"
                style="max-width: 350px"
              />
            </v-col>
          </v-row>
          <v-table density="compact">
            <thead>
              <tr>
                <th>Tag</th>
                <th>Sex</th>
                <th>Pregnant?</th>
                <th>Pregnancy Duration</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="animal in recordPregnancyAnimals" :key="animal.id">
                <td>{{ animal.tag_number }}</td>
                <td>{{ animal.sex }}</td>
                <td>
                  <v-select
                    v-model="animal.pregnant"
                    :items="[{title:'Yes', value:true},{title:'No', value:false}]"
                    density="compact"
                    style="max-width: 350px"
                  />
                </td>
                <td>
                  <v-text-field
                    v-model="animal.pregnancy_duration"
                    density="compact"
                    style="max-width: 350px"
                    placeholder="e.g. 2.5 months"
                  />
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="recordPregnancyOpen = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveGroupPregnancy" :loading="recordPregnancySaving">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Group Slaughter Dialogue-->
    <!-- Group Slaughter Dialog -->
    <v-dialog v-model="groupSlaughterOpen" max-width="520">
      <v-card>
        <v-card-title>
          Send group "{{ groupSlaughterGroup?.name || '—' }}" to slaughter
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="groupSlaughterDate"
            type="date"
            label="Date"
            style="max-width: 220px"
          />
          <v-textarea
            v-model="groupSlaughterReason"
            label="Reason / details"
            auto-grow
          />
          <v-alert v-if="groupSlaughterError" type="error">{{ groupSlaughterError }}</v-alert>
          <p class="text-caption mt-2">
            All animals in this group will be marked as slaughtered and recorded in history.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="groupSlaughterOpen = false">Cancel</v-btn>
          <v-btn color="error" @click="saveGroupSlaughter" :loading="groupSlaughterSaving">Send to slaughter</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="recordVaccinationOpen" max-width="600">
      <v-card>
        <v-card-title>
          Record vaccination for animal: {{ recordVaccinationAnimal?.tag_number || '—' }}
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field v-model="recordVaccinationDate" label="Date" type="date" />
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="recordVaccinationVaccineId"
                :items="vaccines"
                item-title="name"
                item-value="id"
                label="Vaccine name"
                clearable
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="recordVaccinationDose" label="Dose" />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field v-model="recordVaccinationUnit" label="Unit" />
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="recordVaccinationMethod"
                :items="vaccineMethods"
                label="Vaccine method"
                clearable
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="recordVaccinationSource" label="Source" />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="recordVaccinationNotes" label="Notes" auto-grow />
            </v-col>
          </v-row>
          <v-alert v-if="recordVaccinationError" type="error">{{ recordVaccinationError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="recordVaccinationOpen = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveRecordVaccination" :loading="recordVaccinationSaving">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>