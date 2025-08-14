<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')
const camps = ref([]) // [{id, name, animal_count?}]
const search = ref('')

// create/edit
const createOpen = ref(false)
const creating = ref(false)
const form = ref({ name: '' })

const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({ name: '' })

// delete
const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)

// Loaders
async function fetchCamps() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get('/camps/')
    camps.value = Array.isArray(data) ? data : (data.camps || [])
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Failed to load camps'
  } finally {
    loading.value = false
  }
}

async function loadAll() {
  await fetchCamps()
}

// Actions
async function createCamp() {
  creating.value = true
  try {
    const payload = { name: (form.value.name || '').trim() }
    if (!payload.name) throw new Error('Camp name is required')
    const { data } = await api.post('/camps/', payload)
    camps.value = [data, ...camps.value]
    form.value = { name: '' }
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Create failed')
  } finally {
    creating.value = false
  }
}

function openEdit(c) {
  editing.value = c
  editForm.value = { name: c.name || '' }
  editOpen.value = true
}

async function saveEdit() {
  if (!editing.value) return
  savingEdit.value = true
  try {
    const payload = { name: (editForm.value.name || '').trim() || null }
    const { data } = await api.patch(`/camps/${editing.value.id}`, payload)
    const idx = camps.value.findIndex(x => x.id === editing.value.id)
    if (idx !== -1) camps.value.splice(idx, 1, data)
    editOpen.value = false
    editing.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Update failed')
  } finally {
    savingEdit.value = false
  }
}

function askDelete(c) { toDelete.value = c; confirmDelete.value = true }
async function doDelete() {
  if (!toDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/camps/${toDelete.value.id}`)
    camps.value = camps.value.filter(x => x.id !== toDelete.value.id)
    confirmDelete.value = false
    toDelete.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Delete failed')
  } finally {
    deleting.value = false
  }
}

// Derived
const campsView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return Array.isArray(camps.value)
    ? camps.value
      .map(c => ({
        ...c,
        animal_count: c.animal_count ?? 0,
      }))
      .filter(c => (needle ? (c.name || '').toLowerCase().includes(needle) : true))
    : []
})

onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="900">
    <h1 class="text-h5 mb-4">Camps</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Camp List</span>
        <v-spacer />
        <v-text-field
          v-model="search"
          placeholder="Search camps"
          density="compact"
          hide-details
          style="max-width: 260px"
        />
        <v-btn class="ml-2" color="primary" @click="createOpen = true">New camp</v-btn>
      </v-card-title>

      <v-data-table
        :items="campsView"
        :headers="[
          { title:'Camp', value:'name' },
          { title:'Animals', value:'animal_count' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="15"
        :loading="loading"
      >
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askDelete(item)">Delete</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create -->
    <v-dialog v-model="createOpen" max-width="520" persistent>
      <v-card>
        <v-card-title>Create camp</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createCamp" @keydown.enter.prevent="createCamp">
            <v-text-field v-model="form.name" label="Camp name" />
            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="creating">Create</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Edit -->
    <v-dialog v-model="editOpen" max-width="520" persistent>
      <v-card>
        <v-card-title>Edit camp</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveEdit" @keydown.enter.prevent="saveEdit">
            <v-text-field v-model="editForm.name" label="Camp name" />
            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="editOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="savingEdit">Save</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Delete -->
    <v-dialog v-model="confirmDelete" max-width="420">
      <v-card>
        <v-card-title>Delete {{ toDelete?.name }}?</v-card-title>
        <v-card-text>This cannot be undone.</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete=false">Cancel</v-btn>
          <v-btn color="error" @click="doDelete" :loading="deleting">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>