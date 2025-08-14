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
  { title: 'Actions', value: 'actions', sortable: false },
]
const groupsView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return Array.isArray(groups.value)
    ? groups.value
      .map(g => ({
        ...g,
        camp: campName(g.camp_id),
        count: g.animal_count ?? animals.value.filter(a => a.group_id === g.id && !a.deceased).length,
      }))
      .filter(g => (needle ? (g.name || '').toLowerCase().includes(needle) || (g.camp || '').toLowerCase().includes(needle) : true))
    : []
})

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

onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="1100">
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

      <v-data-table
        :items="groupsView"
        :headers="headers"
        v-model="selected"
        show-select
        :items-per-page="20"
        :loading="loading"
      >
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openEdit(item)">Edit</v-btn>
          <v-btn variant="text" @click="openMove(item)">Move to camp</v-btn>
          <v-btn variant="text" color="error" @click="askDelete(item)">Delete</v-btn>
        </template>
      </v-data-table>
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
  </v-container>
</template>