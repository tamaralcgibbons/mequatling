<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')
const camps = ref([]) // [{id, name, ...}]
const search = ref('')

// create/edit
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  greenfeed: false,
  greenfeed_planting_date: '',
  greenfeed_amount: '',
  fertilised_date: '',
  fertilised_amount: '',
  grazed_status: 'N',
  grazed_out_date: '',
})

const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({
  name: '',
  greenfeed: false,
  greenfeed_planting_date: '',
  greenfeed_amount: '',
  fertilised_date: '',
  fertilised_amount: '',
  grazed_status: 'N',
  grazed_out_date: '',
})

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
    const payload = {
      name: (form.value.name || '').trim(),
      greenfeed: !!form.value.greenfeed,
      greenfeed_planting_date: form.value.greenfeed ? form.value.greenfeed_planting_date || null : null,
      greenfeed_amount: form.value.greenfeed ? Number(form.value.greenfeed_amount) || null : null,
      fertilised_date: form.value.fertilised_date || null,
      fertilised_amount: form.value.fertilised_amount ? Number(form.value.fertilised_amount) : null,
      grazed_status: form.value.grazed_status,
      grazed_out_date: form.value.grazed_status === 'Y' ? form.value.grazed_out_date || null : null,
    }
    if (!payload.name) throw new Error('Camp name is required')
    const { data } = await api.post('/camps/', payload)
    camps.value = [data, ...camps.value]
    form.value = {
      name: '',
      greenfeed: false,
      greenfeed_planting_date: '',
      greenfeed_amount: '',
      fertilised_date: '',
      fertilised_amount: '',
      grazed_status: 'N',
      grazed_out_date: '',
    }
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e?.message || 'Create failed')
  } finally {
    creating.value = false
  }
}

function openEdit(c) {
  editing.value = c
  editForm.value = {
    name: c.name || '',
    greenfeed: !!c.greenfeed,
    greenfeed_planting_date: c.greenfeed_planting_date || '',
    greenfeed_amount: c.greenfeed_amount || '',
    fertilised_date: c.fertilised_date || '',
    fertilised_amount: c.fertilised_amount || '',
    grazed_status: c.grazed_status || 'N',
    grazed_out_date: c.grazed_out_date || '',
  }
  editOpen.value = true
}

async function saveEdit() {
  if (!editing.value) return
  savingEdit.value = true
  try {
    const payload = {
      name: (editForm.value.name || '').trim() || null,
      greenfeed: !!editForm.value.greenfeed,
      greenfeed_planting_date: editForm.value.greenfeed ? editForm.value.greenfeed_planting_date || null : null,
      greenfeed_amount: editForm.value.greenfeed ? Number(editForm.value.greenfeed_amount) || null : null,
      fertilised_date: editForm.value.fertilised_date || null,
      fertilised_amount: editForm.value.fertilised_amount ? Number(editForm.value.fertilised_amount) : null,
      grazed_status: editForm.value.grazed_status,
      grazed_out_date: editForm.value.grazed_status === 'Y' ? editForm.value.grazed_out_date || null : null,
    }
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
  <v-container class="py-8" fluid>
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
      style="min-width:1800px"
        :items="campsView"
        :headers="[
          { title:'Camp', value:'name' },
          { title:'Animals', value:'animal_count' },
          { title:'Greenfeed', value:'greenfeed' },
          { title:'Greenfeed Planting Date', value:'greenfeed_planting_date' },
          { title:'Greenfeed Amount', value:'greenfeed_amount' },
          { title:'Fertilised Date', value:'fertilised_date' },
          { title:'Fertilised Amount', value:'fertilised_amount' },
          { title:'Grazed Status', value:'grazed_status' },
          { title:'Grazed Out Date', value:'grazed_out_date' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="30"
        :loading="loading"
      >
        <template #item.greenfeed="{ item }">
          {{ item.greenfeed ? 'Y' : 'N' }}
        </template>
        <template #item.grazed_status="{ item }">
          <span v-if="item.grazed_status === 'Y'">Y</span>
          <span v-else-if="item.grazed_status === 'N'">N</span>
          <span v-else>In Progress</span>
        </template>
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
            <v-checkbox v-model="form.greenfeed" label="Contains greenfeed?" />
            <v-row v-if="form.greenfeed">
              <v-col cols="6">
                <v-text-field v-model="form.greenfeed_planting_date" label="Planting Date" type="date" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="form.greenfeed_amount" label="Greenfeed Amount" type="number" />
              </v-col>
            </v-row>
            <v-text-field v-model="form.fertilised_date" label="Fertilised Date" type="date" />
            <v-text-field v-model="form.fertilised_amount" label="Fertilised Amount" type="number" />
            <v-select
              v-model="form.grazed_status"
              :items="['Y', 'N', 'in_progress']"
              label="Grazed Status"
            />
            <v-text-field v-if="form.grazed_status === 'Y'" v-model="form.grazed_out_date" label="Grazed Out Date" type="date" />
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
            <v-checkbox v-model="editForm.greenfeed" label="Contains greenfeed?" />
            <v-row v-if="editForm.greenfeed">
              <v-col cols="6">
                <v-text-field v-model="editForm.greenfeed_planting_date" label="Planting Date" type="date" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="editForm.greenfeed_amount" label="Greenfeed Amount" type="number" />
              </v-col>
            </v-row>
            <v-text-field v-model="editForm.fertilised_date" label="Fertilised Date" type="date" />
            <v-text-field v-model="editForm.fertilised_amount" label="Fertilised Amount" type="number" />
            <v-select
              v-model="editForm.grazed_status"
              :items="['Y', 'N', 'in_progress']"
              label="Grazed Status"
            />
            <v-text-field v-if="editForm.grazed_status === 'Y'" v-model="editForm.grazed_out_date" label="Grazed Out Date" type="date" />
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