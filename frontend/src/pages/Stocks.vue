<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')
const vaccines = ref([]) // [{id,name,default_dose,unit,methods[],current_stock}]
const search = ref('')

// create/edit
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  default_dose: null,
  unit: '',
  methods: [],       // array of strings
  current_stock: null, // starting/adjusted stock count (e.g., mL)
})

// edit
const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({
  name: '',
  default_dose: null,
  unit: '',
  methods: [],
  current_stock: null,
})

// delete
const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)

// methods input chip model
const newMethod = ref('')
function pushMethod(target) {
  const t = target === 'create' ? form.value : editForm.value
  const val = (newMethod.value || '').trim()
  if (!val) return
  if (!Array.isArray(t.methods)) t.methods = []
  if (!t.methods.includes(val)) t.methods.push(val)
  newMethod.value = ''
}
function removeMethod(target, idx) {
  const t = target === 'create' ? form.value : editForm.value
  t.methods.splice(idx, 1)
}

// Loaders
async function fetchVaccines() {
  const { data } = await api.get('/stocks/vaccines')
  vaccines.value = Array.isArray(data) ? data : []
}
async function loadAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    await fetchVaccines()
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load stocks'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// Actions
async function createVaccine() {
  creating.value = true
  try {
    const payload = {
      name: (form.value.name || '').trim(),
      default_dose: Number(form.value.default_dose) || null,
      unit: (form.value.unit || '').trim() || null,
      methods: Array.isArray(form.value.methods) ? form.value.methods : [],
      current_stock: Number(form.value.current_stock) || 0,
    }
    if (!payload.name) throw new Error('Name is required')
    const { data } = await api.post('/stocks/vaccines', payload)
    vaccines.value = [data, ...vaccines.value]
    form.value = { name: '', default_dose: null, unit: '', methods: [], current_stock: null }
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  } finally {
    creating.value = false
  }
}

function openEdit(v) {
  editing.value = v
  editForm.value = {
    name: v.name || '',
    default_dose: v.default_dose ?? null,
    unit: v.unit || '',
    methods: Array.isArray(v.methods) ? [...v.methods] : [],
    current_stock: v.current_stock ?? 0,
  }
  editOpen.value = true
}

async function saveEdit() {
  if (!editing.value) return
  savingEdit.value = true
  try {
    const payload = {
      name: (editForm.value.name || '').trim() || null,
      default_dose: Number(editForm.value.default_dose) || null,
      unit: (editForm.value.unit || '').trim() || null,
      methods: Array.isArray(editForm.value.methods) ? editForm.value.methods : [],
      current_stock: Number(editForm.value.current_stock) || 0,
    }
    const { data } = await api.patch(`/stocks/vaccines/${editing.value.id}`, payload)
    const idx = vaccines.value.findIndex(x => x.id === editing.value.id)
    if (idx !== -1) vaccines.value.splice(idx, 1, data)
    editOpen.value = false
    editing.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  } finally {
    savingEdit.value = false
  }
}

function askDelete(v) { toDelete.value = v; confirmDelete.value = true }
async function doDelete() {
  if (!toDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/stocks/vaccines/${toDelete.value.id}`)
    vaccines.value = vaccines.value.filter(x => x.id !== toDelete.value.id)
    confirmDelete.value = false
    toDelete.value = null
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deleting.value = false
  }
}

// Derived
const vaccinesView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return vaccines.value.filter(v =>
    !needle ? true : (v.name || '').toLowerCase().includes(needle)
  )
})

onMounted(loadAll)
</script>

<template>
  <v-container class="py-8" max-width="1100">
    <h1 class="text-h5 mb-4">Stocks — Vaccines</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Vaccine List</span>
        <v-spacer />
        <v-text-field
          v-model="search"
          placeholder="Search vaccines"
          density="compact"
          hide-details
          style="max-width: 260px"
        />
        <v-btn class="ml-2" color="primary" @click="createOpen = true">New vaccine</v-btn>
      </v-card-title>

      <v-data-table
        :items="vaccinesView"
        :headers="[
          { title:'Name', value:'name' },
          { title:'Default dose', value:'default_dose' },
          { title:'Unit', value:'unit' },
          { title:'Methods', value:'methods' },
          { title:'In stock', value:'current_stock' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="25"
        :loading="loading"
      >
        <template #item.methods="{ item }">
          <div class="d-flex flex-wrap" style="gap:6px">
            <v-chip v-for="m in (item.methods||[])" :key="m" size="small" label>{{ m }}</v-chip>
            <span v-if="!item.methods?.length">—</span>
          </div>
        </template>
        <template #item.default_dose="{ item }">
          <span>{{ item.default_dose ?? '—' }}</span>
        </template>
        <template #item.current_stock="{ item }">
          <span>{{ item.current_stock ?? 0 }}</span>
        </template>
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askDelete(item)">Delete</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create -->
    <v-dialog v-model="createOpen" max-width="720" persistent>
      <v-card>
        <v-card-title>New vaccine</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createVaccine" @keydown.enter.prevent="createVaccine">
            <v-row dense>
              <v-col cols="12" md="6"><v-text-field v-model="form.name" label="Name" /></v-col>
              <v-col cols="6" md="3"><v-text-field v-model.number="form.default_dose" type="number" min="0" step="0.001" label="Default dose" /></v-col>
              <v-col cols="6" md="3"><v-text-field v-model="form.unit" label="Unit (e.g., mL)" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model.number="form.current_stock" type="number" min="0" step="0.001" label="Current stock" /></v-col>
              <v-col cols="12" md="6">
                <div class="text-body-2 mb-1">Administration methods</div>
                <div class="d-flex align-center" style="gap:8px">
                  <v-text-field v-model="newMethod" placeholder="e.g., IM, SC, oral" hide-details density="compact" />
                  <v-btn @click="pushMethod('create')" :disabled="!newMethod">Add</v-btn>
                </div>
                <div class="d-flex flex-wrap mt-2" style="gap:6px">
                  <v-chip
                    v-for="(m, i) in form.methods"
                    :key="m+i"
                    size="small"
                    closable
                    @click:close="removeMethod('create', i)"
                    label
                  >{{ m }}</v-chip>
                </div>
              </v-col>
            </v-row>
            <div class="d-flex justify-end mt-2">
              <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
              <v-btn type="submit" color="primary" :loading="creating">Create</v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Edit -->
    <v-dialog v-model="editOpen" max-width="720" persistent>
      <v-card>
        <v-card-title>Edit vaccine</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveEdit" @keydown.enter.prevent="saveEdit">
            <v-row dense>
              <v-col cols="12" md="6"><v-text-field v-model="editForm.name" label="Name" /></v-col>
              <v-col cols="6" md="3"><v-text-field v-model.number="editForm.default_dose" type="number" min="0" step="0.001" label="Default dose" /></v-col>
              <v-col cols="6" md="3"><v-text-field v-model="editForm.unit" label="Unit" /></v-col>
              <v-col cols="12" md="6"><v-text-field v-model.number="editForm.current_stock" type="number" min="0" step="0.001" label="Current stock" /></v-col>
              <v-col cols="12" md="6">
                <div class="text-body-2 mb-1">Administration methods</div>
                <div class="d-flex align-center" style="gap:8px">
                  <v-text-field v-model="newMethod" placeholder="e.g., IM, SC, oral" hide-details density="compact" />
                  <v-btn @click="pushMethod('edit')" :disabled="!newMethod">Add</v-btn>
                </div>
                <div class="d-flex flex-wrap mt-2" style="gap:6px">
                  <v-chip
                    v-for="(m, i) in editForm.methods"
                    :key="m+i"
                    size="small"
                    closable
                    @click:close="removeMethod('edit', i)"
                    label
                  >{{ m }}</v-chip>
                </div>
              </v-col>
            </v-row>
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
