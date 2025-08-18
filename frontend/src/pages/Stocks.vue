<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

// State
const loading = ref(false)
const errorMsg = ref('')
const vaccines = ref([]) // [{id,name,default_dose,unit,methods[],current_stock}]
const search = ref('')

// --- Vaccine Create/Edit ---
const createOpen = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  default_dose: null,
  unit: '',
  methods: [],
  current_stock: null,
  notes: '',
})

// For dropdown logic
function onMethodChange(val) {
  if (!val.includes('other')) form.value.otherMethod = ''
}

const editOpen = ref(false)
const savingEdit = ref(false)
const editing = ref(null)
const editForm = ref({
  name: '',
  default_dose: null,
  unit: '',
  methods: [],
  current_stock: null,
  notes: '',
})

const confirmDelete = ref(false)
const toDelete = ref(null)
const deleting = ref(false)

// Methods chip model
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

// --- Vaccine Create ---
async function createVaccine() {
  try {
    creating.value = true
    // Combine dropdown and "other" input
    const payload = {
      ...form.value,
      methods: (form.value.methods || [])
        .filter(m => m !== 'other')
        .concat(form.value.otherMethod ? [form.value.otherMethod] : [])
    }
    const { data } = await api.post('/stocks/vaccines', payload)
    vaccines.value = [data, ...vaccines.value]
    form.value = { name: '', default_dose: null, unit: '', methods: [], otherMethod: '', current_stock: null, notes: '' }
    createOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  } finally {
    creating.value = false
  }
}

// --- Vaccine Edit ---
function openEdit(item) {
  editing.value = item
  editForm.value = { ...item }
  editOpen.value = true
}
async function saveEdit() {
  try {
    savingEdit.value = true
    const payload = { ...editForm.value }
    const { data } = await api.patch(`/stocks/vaccines/${editing.value.id}`, payload)
    const idx = vaccines.value.findIndex(x => x.id === editing.value.id)
    if (idx !== -1) vaccines.value.splice(idx, 1, data)
    editOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  } finally {
    savingEdit.value = false
  }
}

// --- Vaccine Delete ---
function askDelete(item) {
  toDelete.value = item
  confirmDelete.value = true
}
async function doDelete() {
  try {
    deleting.value = true
    await api.delete(`/stocks/vaccines/${toDelete.value.id}`)
    vaccines.value = vaccines.value.filter(x => x.id !== toDelete.value.id)
    confirmDelete.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deleting.value = false
  }
}

// --- Waste Dialog ---
const wasteDialogOpen = ref(false)
const wasteForm = ref({ amount: null, date: '', reason: '', vaccine_id: null })
function openWasteDialog(item) {
  wasteForm.value = { amount: null, date: '', reason: '', vaccine_id: item.id }
  wasteDialogOpen.value = true
}
async function recordWaste() {
  try {
    const payload = {
      vaccine_id: wasteForm.value.vaccine_id,
      amount: Number(wasteForm.value.amount) || 0,
      date: wasteForm.value.date,
      reason: wasteForm.value.reason || '',
    }
    await api.post('/stocks/vaccines/waste', payload)
    await fetchVaccines()
    wasteDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record waste')
  }
}

// --- Feed Table ---
const feedsView = ref([])
const feedCreateOpen = ref(false)
const feedForm = ref({ name: '', unit: '', current_stock: 0, notes: '' })
function openFeedCreate() {
  feedForm.value = { name: '', unit: '', current_stock: 0, notes: '' }
  feedCreateOpen.value = true
}
async function createFeed() {
  try {
    const payload = { ...feedForm.value }
    const { data } = await api.post('/stocks/feeds', payload)
    feedsView.value = [data, ...feedsView.value]
    feedCreateOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  }
}
const feedEditOpen = ref(false)
const feedEditForm = ref({ id: null, name: '', unit: '', current_stock: 0, notes: '' })
function openFeedEdit(item) {
  feedEditForm.value = { ...item }
  feedEditOpen.value = true
}
async function saveFeedEdit() {
  try {
    const payload = { ...feedEditForm.value }
    const { data } = await api.patch(`/stocks/feeds/${feedEditForm.value.id}`, payload)
    const idx = feedsView.value.findIndex(x => x.id === feedEditForm.value.id)
    if (idx !== -1) feedsView.value.splice(idx, 1, data)
    feedEditOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  }
}
const confirmFeedDelete = ref(false)
const toFeedDelete = ref(null)
const deletingFeed = ref(false)

function askFeedDelete(item) {
  toFeedDelete.value = item
  confirmFeedDelete.value = true
}
async function doFeedDelete() {
  try {
    deletingFeed.value = true
    await api.delete(`/stocks/feeds/${toFeedDelete.value.id}`)
    feedsView.value = feedsView.value.filter(x => x.id !== toFeedDelete.value.id)
    confirmFeedDelete.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deletingFeed.value = false
  }
}


// --- Mix Feed Dialog ---
const mixDialogOpen = ref(false)
const mixForm = ref({
  components: [], // [{feed_id, amount}]
  output_feed_id: null,
  output_amount: null,
  date: '',
  reason: '',
})
function openMixDialog() {
  mixForm.value = { components: [], output_feed_id: null, output_amount: null, date: '', reason: '' }
  mixDialogOpen.value = true
}
async function recordMix() {
  try {
    const payload = {
      components: Object.fromEntries(
        mixForm.value.components
          .filter(c => c.feed_id && c.amount)
          .map(c => [c.feed_id, Number(c.amount)])
      ),
      output_feed_id: mixForm.value.output_feed_id,
      output_amount: Number(mixForm.value.output_amount) || 0,
      date: mixForm.value.date,
      reason: mixForm.value.reason || '',
    }
    await api.post('/stocks/feeds/mix', payload)
    await fetchFeeds()
    mixDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Mix failed')
  }
}

// --- Fertiliser Table ---
const fertilisersView = ref([])
const fertCreateOpen = ref(false)
const fertForm = ref({ name: '', unit: '', current_stock: 0, notes: '' })
function openFertCreate() {
  fertForm.value = { name: '', unit: '', current_stock: 0, notes: '' }
  fertCreateOpen.value = true
}
async function createFert() {
  try {
    const payload = { ...fertForm.value }
    const { data } = await api.post('/stocks/fertilisers', payload)
    fertilisersView.value = [data, ...fertilisersView.value]
    fertCreateOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  }
}
const fertEditOpen = ref(false)
const fertEditForm = ref({ id: null, name: '', unit: '', current_stock: 0, notes: '' })
function openFertEdit(item) {
  fertEditForm.value = { ...item }
  fertEditOpen.value = true
}
async function saveFertEdit() {
  try {
    const payload = { ...fertEditForm.value }
    const { data } = await api.patch(`/stocks/fertilisers/${fertEditForm.value.id}`, payload)
    const idx = fertilisersView.value.findIndex(x => x.id === fertEditForm.value.id)
    if (idx !== -1) fertilisersView.value.splice(idx, 1, data)
    fertEditOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  }
}
const confirmFertDelete = ref(false)
const toFertDelete = ref(null)
const deletingFert = ref(false)

function askFertDelete(item) {
  toFertDelete.value = item
  confirmFertDelete.value = true
}
async function doFertDelete() {
  try {
    deletingFert.value = true
    await api.delete(`/stocks/fertilisers/${toFertDelete.value.id}`)
    fertilisersView.value = fertilisersView.value.filter(x => x.id !== toFertDelete.value.id)
    confirmFertDelete.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deletingFert.value = false
  }
}

// --- Fertiliser Event Dialog ---
const fertEventDialogOpen = ref(false)
const fertEventForm = ref({ amount: null, date: '', reason: '', fertiliser_id: null, event_type: 'out' })
function openFertEvent(item) {
  fertEventForm.value = { amount: null, date: '', reason: '', fertiliser_id: item.id, event_type: 'out' }
  fertEventDialogOpen.value = true
}
async function recordFertEvent() {
  try {
    const payload = {
      amount: Number(fertEventForm.value.amount) || 0,
      date: fertEventForm.value.date,
      reason: fertEventForm.value.reason || '',
      event_type: fertEventForm.value.event_type,
    }
    await api.post(`/stocks/fertilisers/${fertEventForm.value.fertiliser_id}/event`, payload)
    await fetchFertilisers()
    fertEventDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Event failed')
  }
}

// --- Fuel Table ---
const fuelView = ref([])
const fuelCreateOpen = ref(false)
const fuelForm = ref({ type: '', unit: '', current_stock: 0, notes: '' })
function openFuelCreate() {
  fuelForm.value = { type: '', unit: '', current_stock: 0, notes: '' }
  fuelCreateOpen.value = true
}
async function createFuel() {
  try {
    const payload = { ...fuelForm.value }
    const { data } = await api.post('/stocks/fuels', payload)
    fuelView.value = [data, ...fuelView.value]
    fuelCreateOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Create failed')
  }
}
const fuelEditOpen = ref(false)
const fuelEditForm = ref({ id: null, type: '', unit: '', current_stock: 0, notes: '' })
function openFuelEdit(item) {
  fuelEditForm.value = { ...item }
  fuelEditOpen.value = true
}
async function saveFuelEdit() {
  try {
    const payload = { ...fuelEditForm.value }
    const { data } = await api.patch(`/stocks/fuels/${fuelEditForm.value.id}`, payload)
    const idx = fuelView.value.findIndex(x => x.id === fuelEditForm.value.id)
    if (idx !== -1) fuelView.value.splice(idx, 1, data)
    fuelEditOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Update failed')
  }
}

const confirmFuelDelete = ref(false)
const toFuelDelete = ref(null)
const deletingFuel = ref(false)

function askFuelDelete(item) {
  toFuelDelete.value = item
  confirmFuelDelete.value = true
}
async function doFuelDelete() {
  try {
    deletingFuel.value = true
    await api.delete(`/stocks/fuels/${toFuelDelete.value.id}`)
    fuelView.value = fuelView.value.filter(x => x.id !== toFuelDelete.value.id)
    confirmFuelDelete.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Delete failed')
  } finally {
    deletingFuel.value = false
  }
}

// --- Fuel Event Dialog ---
const fuelEventDialogOpen = ref(false)
const fuelEventForm = ref({ amount: null, date: '', reason: '', fuel_id: null, event_type: 'out' })
function openFuelEvent(item) {
  fuelEventForm.value = { amount: null, date: '', reason: '', fuel_id: item.id, event_type: 'out' }
  fuelEventDialogOpen.value = true
}
async function recordFuelEvent() {
  try {
    const payload = {
      amount: Number(fuelEventForm.value.amount) || 0,
      date: fuelEventForm.value.date,
      reason: fuelEventForm.value.reason || '',
      event_type: fuelEventForm.value.event_type,
    }
    await api.post(`/stocks/fuels/${fuelEventForm.value.fuel_id}/event`, payload)
    await fetchFuel()
    fuelEventDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Event failed')
  }
}

// --- Stocktake State ---
const vaccineStocktakeDialogOpen = ref(false)
const vaccineStocktakeForm = ref({ vaccine_id: null, recorded_stock: null, date: '', notes: '' })
const lastVaccineStocktakes = ref({}) // { [vaccine_id]: { recorded_stock, date, notes } }

const feedStocktakeDialogOpen = ref(false)
const feedStocktakeForm = ref({ feed_id: null, recorded_stock: null, date: '', notes: '' })
const lastFeedStocktakes = ref({}) // { [feed_id]: { recorded_stock, date, notes } }

const fertStocktakeDialogOpen = ref(false)
const fertStocktakeForm = ref({ fertiliser_id: null, recorded_stock: null, date: '', notes: '' })
const lastFertStocktakes = ref({}) // { [fertiliser_id]: { recorded_stock, date, notes } }

const fuelStocktakeDialogOpen = ref(false)
const fuelStocktakeForm = ref({ fuel_id: null, recorded_stock: null, date: '', notes: '' })
const lastFuelStocktakes = ref({}) // { [fuel_id]: { recorded_stock, date, notes } }

async function fetchLastStocktakes() {
  const { data } = await api.get('/history')
  // Vaccines
  const vaccineStocktakes = data.filter(e => e.type === 'vaccine_stocktake')
  const latestVax = {}
  for (const s of vaccineStocktakes) {
    // Always pick the event with the latest date
    if (
      !latestVax[s.item_id] ||
      new Date(s.date) > new Date(latestVax[s.item_id].date)
    ) {
      latestVax[s.item_id] = s
    }
  }
  lastVaccineStocktakes.value = latestVax

  // Feeds
  const feedStocktakes = data.filter(e => e.type === 'feed_stocktake')
  const latestFeed = {}
  for (const s of feedStocktakes) {
    if (
      !latestFeed[s.item_id] ||
      new Date(s.date) > new Date(latestFeed[s.item_id].date)
    ) {
      latestFeed[s.item_id] = s
    }
  }
  lastFeedStocktakes.value = latestFeed

  // Fertilisers
  const fertStocktakes = data.filter(e => e.type === 'fertiliser_stocktake')
  const latestFert = {}
  for (const s of fertStocktakes) {
    if (
      !latestFert[s.item_id] ||
      new Date(s.date) > new Date(latestFert[s.item_id].date)
    ) {
      latestFert[s.item_id] = s
    }
  }
  lastFertStocktakes.value = latestFert

  // Fuels
  const fuelStocktakes = data.filter(e => e.type === 'fuel_stocktake')
  const latestFuel = {}
  for (const s of fuelStocktakes) {
    if (
      !latestFuel[s.item_id] ||
      new Date(s.date) > new Date(latestFuel[s.item_id].date)
    ) {
      latestFuel[s.item_id] = s
    }
  }
  lastFuelStocktakes.value = latestFuel
}

// --- Open Stocktake Dialogs ---
function openVaccineStocktakeDialog(item) {
  vaccineStocktakeForm.value = {
    vaccine_id: item.id,
    recorded_stock: item.current_stock,
    date: new Date().toISOString().slice(0, 10),
    notes: ''
  }
  vaccineStocktakeDialogOpen.value = true
}
function openFeedStocktakeDialog(item) {
  feedStocktakeForm.value = {
    feed_id: item.id,
    recorded_stock: item.current_stock,
    date: new Date().toISOString().slice(0, 10),
    notes: ''
  }
  feedStocktakeDialogOpen.value = true
}
function openFertStocktakeDialog(item) {
  fertStocktakeForm.value = {
    fertiliser_id: item.id,
    recorded_stock: item.current_stock,
    date: new Date().toISOSt.slice(0, 10),
    notes: ''
  }
  fertStocktakeDialogOpen.value = true
}
function openFuelStocktakeDialog(item) {
  fuelStocktakeForm.value = {
    fuel_id: item.id,
    recorded_stock: item.current_stock,
    date: new Date().toISOString().slice(0, 10),
    notes: ''
  }
  fuelStocktakeDialogOpen.value = true
}

// --- Record Stocktake ---
async function recordVaccineStocktake() {
  try {
    const payload = { ...vaccineStocktakeForm.value }
    await api.post(`/stocks/vaccines/${payload.vaccine_id}/stocktake`, payload)
    await fetchVaccines()
    await fetchLastStocktakes()
    vaccineStocktakeDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record stocktake')
  }
}
async function recordFeedStocktake() {
  try {
    const payload = { ...feedStocktakeForm.value }
    await api.post(`/stocks/feeds/${payload.feed_id}/stocktake`, payload)
    await fetchFeeds()
    await fetchLastStocktakes()
    feedStocktakeDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record stocktake')
  }
}
async function recordFertStocktake() {
  try {
    const payload = { ...fertStocktakeForm.value }
    await api.post(`/stocks/fertilisers/${payload.fertiliser_id}/stocktake`, payload)
    await fetchFertilisers()
    await fetchLastStocktakes()
    fertStocktakeDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record stocktake')
  }
}
async function recordFuelStocktake() {
  try {
    const payload = { ...fuelStocktakeForm.value }
    await api.post(`/stocks/fuels/${payload.fuel_id}/stocktake`, payload)
    await fetchFuel()
    await fetchLastStocktakes()
    fuelStocktakeDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record stocktake')
  }
}

// --- Loaders ---
async function fetchVaccines() {
  const { data } = await api.get('/stocks/vaccines')
  vaccines.value = Array.isArray(data) ? data : []
}
async function fetchFeeds() {
  const { data } = await api.get('/stocks/feeds')
  feedsView.value = Array.isArray(data) ? data : []
}
async function fetchFertilisers() {
  const { data } = await api.get('/stocks/fertilisers')
  fertilisersView.value = Array.isArray(data) ? data : []
}
async function fetchFuel() {
  const { data } = await api.get('/stocks/fuels')
  fuelView.value = Array.isArray(data) ? data : []
}
async function loadAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    await fetchVaccines()
    await fetchFeeds()
    await fetchFertilisers()
    await fetchFuel()
    await fetchLastStocktakes()
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load stocks'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

// --- Comparison columns for tables ---
const vaccinesView = computed(() => {
  const needle = search.value.trim().toLowerCase()
  return vaccines.value.map(v => ({
    ...v,
    last_stocktake: lastVaccineStocktakes.value[v.id]?.amount ?? null,
    last_stocktake_date: lastVaccineStocktakes.value[v.id]?.date ?? null,
    stock_diff: lastVaccineStocktakes.value[v.id]
      ? (lastVaccineStocktakes.value[v.id].amount - v.current_stock)
      : null
  })).filter(v =>
    !needle ? true : (v.name || '').toLowerCase().includes(needle)
  )
})
const feedsViewWithStocktake = computed(() => {
  return feedsView.value.map(f => ({
    ...f,
    last_stocktake: lastFeedStocktakes.value[f.id]?.amount ?? null,
    last_stocktake_date: lastFeedStocktakes.value[f.id]?.date ?? null,
    stock_diff: lastFeedStocktakes.value[f.id]
      ? (lastFeedStocktakes.value[f.id].amount - f.current_stock)
      : null
  }))
})
const fertilisersViewWithStocktake = computed(() => {
  return fertilisersView.value.map(f => ({
    ...f,
    last_stocktake: lastFertStocktakes.value[f.id]?.amount ?? null,
    last_stocktake_date: lastFertStocktakes.value[f.id]?.date ?? null,
    stock_diff: lastFertStocktakes.value[f.id]
      ? (lastFertStocktakes.value[f.id].amount - f.current_stock)
      : null
  }))
})
const fuelViewWithStocktake = computed(() => {
  return fuelView.value.map(f => ({
    ...f,
    last_stocktake: lastFuelStocktakes.value[f.id]?.amount ?? null,
    last_stocktake_date: lastFuelStocktakes.value[f.id]?.date ?? null,
    stock_diff: lastFuelStocktakes.value[f.id]
      ? (lastFuelStocktakes.value[f.id].amount - f.current_stock)
      : null
  }))
})

// Universal manual stocktake dialog state
const universalStocktakeDialogOpen = ref(false)
const universalStocktakeForm = ref({
  type: '', // 'vaccine' | 'feed' | 'fertiliser' | 'fuel'
  item_id: null,
  recorded_stock: null,
  date: new Date().toISOString().slice(0, 10),
  notes: ''
})

// For dropdown options
const stockOptions = computed(() => [
  ...vaccines.value.map(v => ({ type: 'vaccine', id: v.id, name: v.name })),
  ...feedsView.value.map(f => ({ type: 'feed', id: f.id, name: f.name })),
  ...fertilisersView.value.map(f => ({ type: 'fertiliser', id: f.id, name: f.name })),
  ...fuelView.value.map(f => ({ type: 'fuel', id: f.id, name: f.type })),
])

function openUniversalStocktakeDialog() {
  universalStocktakeForm.value = {
    type: '',
    item_id: null,
    recorded_stock: null,
    date: new Date().toISOString().slice(0, 10),
    notes: ''
  }
  universalStocktakeDialogOpen.value = true
}

async function recordUniversalStocktake() {
  const { type, item_id, recorded_stock, date, notes } = universalStocktakeForm.value
  let endpoint = ''
  let payload = {}
  if (type === 'vaccine') {
    endpoint = `/stocks/vaccines/${item_id}/stocktake`
    payload = { vaccine_id: item_id, recorded_stock, date, notes }
  } else if (type === 'feed') {
    endpoint = `/stocks/feeds/${item_id}/stocktake`
    payload = { feed_id: item_id, recorded_stock, date, notes }
  } else if (type === 'fertiliser') {
    endpoint = `/stocks/fertilisers/${item_id}/stocktake`
    payload = { fertiliser_id: item_id, recorded_stock, date, notes }
  } else if (type === 'fuel') {
    endpoint = `/stocks/fuels/${item_id}/stocktake`
    payload = { fuel_id: item_id, recorded_stock, date, notes }
  } else {
    alert('Please select a stock type and item.')
    return
  }
  try {
    await api.post(endpoint, payload)
    await loadAll()
    universalStocktakeDialogOpen.value = false
  } catch (e) {
    alert(e?.response?.data?.detail || e.message || 'Failed to record stocktake')
  }
}

const filteredStockOptions = computed(() =>
  (stockOptions.value ?? []).filter(opt => opt.type === universalStocktakeForm.value.type)
)

</script>

<template>   
  <v-container class="py-8" fluid>
    <h1 class="text-h5 mb-4">Stocks</h1>
    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <!-- Manual Stocktake Button -->
    <v-btn color="secondary" class="mb-4" @click="universalStocktakeDialogOpen = true">
      Manual Stocktake
    </v-btn>

    <!-- Vaccines Table -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Vaccine List</span>
        <v-spacer />
        <v-btn class="ml-2" color="primary" @click="createOpen = true">New vaccine</v-btn>
      </v-card-title>
      <v-data-table
      style="min-width:1800px"
        :items="vaccinesView"
        :headers="[
          { title:'Name', value:'name' },
          { title:'Default dose', value:'default_dose' },
          { title:'Unit', value:'unit' },
          { title:'Methods', value:'methods' },
          { title:'In stock', value:'current_stock' },
          { title:'Last stocktake', value:'last_stocktake' },
          { title:'Stocktake date', value:'last_stocktake_date' },
          { title:'Difference', value:'stock_diff' },
          { title:'Notes', value: 'notes' },
          { title:'Waste', value:'waste', width: '120px' },
          { title:'Actions', value:'actions', sortable:false, width: '220px' },
        ]"
        :items-per-page="25"
        :loading="loading"
      >
        <template #item.methods="{ item }">
          <span v-if="Array.isArray(item.methods)">{{ item.methods.join(', ') }}</span>
          <span v-else>{{ item.methods }}</span>
        </template>
        <template #item.last_stocktake="{ item }">
          <span v-if="item.last_stocktake !== null">{{ item.last_stocktake }}</span>
          <span v-else>—</span>
        </template>
        <template #item.last_stocktake_date="{ item }">
          <span v-if="item.last_stocktake_date">{{ item.last_stocktake_date.split('T')[0] }}</span>
          <span v-else>—</span>
        </template>
        <template #item.stock_diff="{ item }">
          <span v-if="item.stock_diff !== null">{{ item.stock_diff.toFixed(2) }}</span>
          <span v-else>—</span>
        </template>
        <template #item.waste="{ item }">
          <v-btn size="small" @click="openWasteDialog(item)">Record waste</v-btn>
        </template>
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askDelete(item)">Delete</v-btn>
          <v-btn variant="text" color="secondary" @click="openVaccineStocktakeDialog(item)">Stocktake</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Vaccine Create Dialog -->
    <v-dialog v-model="createOpen" max-width="520">
      <v-card>
        <v-card-title>New Vaccine</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createVaccine">
            <v-text-field v-model="form.name" label="Name" />
            <v-text-field v-model.number="form.default_dose" label="Default Dose" type="number" />
            <v-text-field v-model="form.unit" label="Unit" />
            <v-select
              v-model="form.methods"
              :items="['subcut', 'intramuscular', 'other']"
              label="Method"
              multiple
              @update:modelValue="onMethodChange"
            />
            <v-text-field
              v-if="form.methods && form.methods.includes('other')"
              v-model="form.otherMethod"
              label="Specify other method"
            />
            <v-text-field v-model.number="form.current_stock" label="Starting Stock" type="number" />
            <v-textarea v-model="form.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createOpen=false">Cancel</v-btn>
          <v-btn color="primary" :loading="creating" @click="createVaccine">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Vaccine Edit Dialog -->
    <v-dialog v-model="editOpen" max-width="520">
      <v-card>
        <v-card-title>Edit Vaccine</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveEdit">
            <v-text-field v-model="editForm.name" label="Name" />
            <v-text-field v-model.number="editForm.default_dose" label="Default Dose" type="number" />
            <v-text-field v-model="editForm.unit" label="Unit" />
            <v-select
              v-model="editForm.methods"
              :items="['subcut', 'intramuscular', 'other']"
              label="Method"
              multiple
              @update:modelValue="onEditMethodChange"
            />
            <v-text-field
              v-if="editForm.methods && editForm.methods.includes('other')"
              v-model="editForm.otherMethod"
              label="Specify other method"
            />
            <v-text-field v-model.number="editForm.current_stock" label="Stock" type="number" />
            <v-textarea v-model="editForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="editOpen=false">Cancel</v-btn>
          <v-btn color="primary" :loading="savingEdit" @click="saveEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Vaccine Delete Dialog -->
    <v-dialog v-model="confirmDelete" max-width="420">
      <v-card>
        <v-card-title>Delete Vaccine?</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ toDelete?.name }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete=false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="doDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Waste Dialog -->
    <v-dialog v-model="wasteDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Record Vaccine Waste</v-card-title>
        <v-card-text>
          <v-text-field v-model.number="wasteForm.amount" label="Amount wasted (mL)" type="number" />
          <v-text-field v-model="wasteForm.date" label="Date" type="date" />
          <v-textarea v-model="wasteForm.reason" label="Reason" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="wasteDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordWaste">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Feed Table -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Feed Products</span>
        <v-spacer />
        <v-btn color="primary" @click="openFeedCreate">New feed</v-btn>
        <v-btn color="secondary" @click="openMixDialog">Mix feed</v-btn>
      </v-card-title>
      <v-data-table
        :items="feedsViewWithStocktake"
        :headers="[
          { title:'Name', value:'name' },
          { title:'Unit', value:'unit' },
          { title:'In stock', value:'current_stock' },
          { title:'Last stocktake', value:'last_stocktake' },
          { title:'Stocktake date', value:'last_stocktake_date' },
          { title:'Difference', value:'stock_diff' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="15"
      >
        <template #item.last_stocktake="{ item }">
          <span v-if="item.last_stocktake !== null">{{ item.last_stocktake }}</span>
          <span v-else>—</span>
        </template>
        <template #item.last_stocktake_date="{ item }">
          <span v-if="item.last_stocktake_date">{{ item.last_stocktake_date.split('T')[0] }}</span>
          <span v-else>—</span>
        </template>
        <template #item.stock_diff="{ item }">
          <span v-if="item.stock_diff !== null">{{ item.stock_diff.toFixed(2) }}</span>
          <span v-else>—</span>
        </template>
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openFeedEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askFeedDelete(item)">Delete</v-btn>
          <v-btn variant="text" color="secondary" @click="openFeedStocktakeDialog(item)">Stocktake</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Feed Create Dialog -->
    <v-dialog v-model="feedCreateOpen" max-width="520">
      <v-card>
        <v-card-title>New Feed Product</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createFeed">
            <v-text-field v-model="feedForm.name" label="Name" />
            <v-text-field v-model="feedForm.unit" label="Unit" />
            <v-text-field v-model.number="feedForm.current_stock" label="Starting Stock" type="number" />
            <v-textarea v-model="feedForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="feedCreateOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="createFeed">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Feed Edit Dialog -->
    <v-dialog v-model="feedEditOpen" max-width="520">
      <v-card>
        <v-card-title>Edit Feed Product</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveFeedEdit">
            <v-text-field v-model="feedEditForm.name" label="Name" />
            <v-text-field v-model="feedEditForm.unit" label="Unit" />
            <v-text-field v-model.number="feedEditForm.current_stock" label="Stock" type="number" />
            <v-textarea v-model="feedEditForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="feedEditOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveFeedEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Feed Delete Dialog -->
    <v-dialog v-model="confirmFeedDelete" max-width="420">
      <v-card>
        <v-card-title>Delete Feed?</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ toFeedDelete?.name }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmFeedDelete=false">Cancel</v-btn>
          <v-btn color="error" :loading="deletingFeed" @click="doFeedDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Mix Feed Dialog -->
    <v-dialog v-model="mixDialogOpen" max-width="520">
      <v-card>
        <v-card-title>Mix Feed Components</v-card-title>
        <v-card-text>
          <v-row dense>
            <v-col cols="12">
              <div class="mb-2">Select components and amounts:</div>
              <div v-for="(comp, idx) in mixForm.components" :key="idx" class="d-flex align-center mb-2">
                <v-select
                  v-model="comp.feed_id"
                  :items="feedsView"
                  item-title="name"
                  item-value="id"
                  label="Feed"
                  style="max-width: 180px"
                />
                <v-text-field
                  v-model.number="comp.amount"
                  label="Amount"
                  type="number"
                  style="max-width: 120px"
                  class="mx-2"
                />
                <v-btn icon="mdi-delete" @click="mixForm.components.splice(idx,1)" />
              </div>
              <v-btn size="small" @click="mixForm.components.push({feed_id:null,amount:null})">Add component</v-btn>
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="mixForm.output_feed_id"
                :items="feedsView"
                item-title="name"
                item-value="id"
                label="Output Product"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model.number="mixForm.output_amount" label="Output Amount" type="number" />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="mixForm.date" label="Date" type="date" />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="mixForm.reason" label="Notes/Reason" />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="mixDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordMix">Mix</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fertiliser Table -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Fertiliser</span>
        <v-spacer />
        <v-btn color="primary" @click="openFertCreate">New fertiliser</v-btn>
      </v-card-title>
      <v-data-table
        :items="fertilisersViewWithStocktake"
        :headers="[
          { title:'Name', value:'name' },
          { title:'Unit', value:'unit' },
          { title:'In stock', value:'current_stock' },
          { title:'Last stocktake', value:'last_stocktake' },
          { title:'Stocktake date', value:'last_stocktake_date' },
          { title:'Difference', value:'stock_diff' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="15"
      >
        <template #item.last_stocktake="{ item }">
          <span v-if="item.last_stocktake !== null">{{ item.last_stocktake }}</span>
          <span v-else>—</span>
        </template>
        <template #item.last_stocktake_date="{ item }">
          <span v-if="item.last_stocktake_date">{{ item.last_stocktake_date.split('T')[0] }}</span>
          <span v-else>—</span>
        </template>
        <template #item.stock_diff="{ item }">
          <span v-if="item.stock_diff !== null">{{ item.stock_diff.toFixed(2) }}</span>
          <span v-else>—</span>
        </template>
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openFertEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askFertDelete(item)">Delete</v-btn>
          <v-btn variant="text" color="secondary" @click="openFertStocktakeDialog(item)">Stocktake</v-btn>
          <v-btn variant="text" color="secondary" @click="openFertEvent(item)">Record event</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Fertiliser Create Dialog -->
    <v-dialog v-model="fertCreateOpen" max-width="520">
      <v-card>
        <v-card-title>New Fertiliser</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createFert">
            <v-text-field v-model="fertForm.name" label="Name" />
            <v-text-field v-model="fertForm.unit" label="Unit" />
            <v-text-field v-model.number="fertForm.current_stock" label="Starting Stock" type="number" />
            <v-textarea v-model="fertForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fertCreateOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="createFert">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fertiliser Edit Dialog -->
    <v-dialog v-model="fertEditOpen" max-width="520">
      <v-card>
        <v-card-title>Edit Fertiliser</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveFertEdit">
            <v-text-field v-model="fertEditForm.name" label="Name" />
            <v-text-field v-model="fertEditForm.unit" label="Unit" />
            <v-text-field v-model.number="fertEditForm.current_stock" label="Stock" type="number" />
            <v-textarea v-model="fertEditForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fertEditOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveFertEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fertiliser Delete Dialog -->
    <v-dialog v-model="confirmFertDelete" max-width="420">
      <v-card>
        <v-card-title>Delete Fertiliser?</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ toFertDelete?.name }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmFertDelete=false">Cancel</v-btn>
          <v-btn color="error" :loading="deletingFert" @click="doFertDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fertiliser Event Dialog -->
    <v-dialog v-model="fertEventDialogOpen" max-width="520">
      <v-card>
        <v-card-title>Record Fertiliser Event</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="recordFertEvent">
            <v-text-field v-model.number="fertEventForm.amount" label="Amount (kg/L)" type="number" />
            <v-text-field v-model="fertEventForm.date" label="Date" type="date" />
            <v-textarea v-model="fertEventForm.reason" label="Reason (e.g. applied to Losberg camp)" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fertEventDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordFertEvent">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fuel Table -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span>Fuel</span>
        <v-spacer />
        <v-btn color="primary" @click="openFuelCreate">New fuel</v-btn>
      </v-card-title>
      <v-data-table
        :items="fuelViewWithStocktake"
        :headers="[
          { title:'Type', value:'type' },
          { title:'Unit', value:'unit' },
          { title:'In stock', value:'current_stock' },
          { title:'Last stocktake', value:'last_stocktake' },
          { title:'Stocktake date', value:'last_stocktake_date' },
          { title:'Difference', value:'stock_diff' },
          { title:'Actions', value:'actions', sortable:false },
        ]"
        :items-per-page="15"
      >
        <template #item.last_stocktake="{ item }">
          <span v-if="item.last_stocktake !== null">{{ item.last_stocktake }}</span>
          <span v-else>—</span>
        </template>
        <template #item.last_stocktake_date="{ item }">
          <span v-if="item.last_stocktake_date">{{ item.last_stocktake_date.split('T')[0] }}</span>
          <span v-else>—</span>
        </template>
        <template #item.stock_diff="{ item }">
          <span v-if="item.stock_diff !== null">{{ item.stock_diff.toFixed(2) }}</span>
          <span v-else>—</span>
        </template>
        <template #item.actions="{ item }">
          <v-btn variant="text" @click="openFuelEdit(item)">Edit</v-btn>
          <v-btn variant="text" color="error" @click="askFuelDelete(item)">Delete</v-btn>
          <v-btn variant="text" color="secondary" @click="openFuelStocktakeDialog(item)">Stocktake</v-btn>
          <v-btn variant="text" color="secondary" @click="openFuelEvent(item)">Record event</v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Fuel Create Dialog -->
    <v-dialog v-model="fuelCreateOpen" max-width="520">
      <v-card>
        <v-card-title>New Fuel</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="createFuel">
            <v-text-field v-model="fuelForm.type" label="Type" />
            <v-text-field v-model="fuelForm.unit" label="Unit" />
            <v-text-field v-model.number="fuelForm.current_stock" label="Starting Stock" type="number" />
            <v-textarea v-model="fuelForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fuelCreateOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="createFuel">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fuel Edit Dialog -->
    <v-dialog v-model="fuelEditOpen" max-width="520">
      <v-card>
        <v-card-title>Edit Fuel</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveFuelEdit">
            <v-text-field v-model="fuelEditForm.type" label="Type" />
            <v-text-field v-model="fuelEditForm.unit" label="Unit" />
            <v-text-field v-model.number="fuelEditForm.current_stock" label="Stock" type="number" />
            <v-textarea v-model="fuelEditForm.notes" label="Notes" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fuelEditOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveFuelEdit">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fuel Delete Dialog -->
    <v-dialog v-model="confirmFuelDelete" max-width="420">
      <v-card>
        <v-card-title>Delete Fuel?</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ toFuelDelete?.name }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmFuelDelete=false">Cancel</v-btn>
          <v-btn color="error" :loading="deletingFuel" @click="doFuelDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fuel Event Dialog -->
    <v-dialog v-model="fuelEventDialogOpen" max-width="520">
      <v-card>
        <v-card-title>Record Fuel Event</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="recordFuelEvent">
            <v-text-field v-model.number="fuelEventForm.amount" label="Amount (L)" type="number" />
            <v-text-field v-model="fuelEventForm.date" label="Date" type="date" />
            <v-textarea v-model="fuelEventForm.reason" label="Reason (e.g. vehicle used)" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fuelEventDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordFuelEvent">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Vaccine Stocktake Dialog -->
    <v-dialog v-model="vaccineStocktakeDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Manual Vaccine Stocktake</v-card-title>
        <v-card-text>
          <v-text-field v-model.number="vaccineStocktakeForm.recorded_stock" label="Counted Stock" type="number" />
          <v-text-field v-model="vaccineStocktakeForm.date" label="Date" type="date" />
          <v-textarea v-model="vaccineStocktakeForm.notes" label="Notes" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="vaccineStocktakeDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordVaccineStocktake">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Feed Stocktake Dialog -->
    <v-dialog v-model="feedStocktakeDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Manual Feed Stocktake</v-card-title>
        <v-card-text>
          <v-text-field v-model.number="feedStocktakeForm.recorded_stock" label="Counted Stock" type="number" />
          <v-text-field v-model="feedStocktakeForm.date" label="Date" type="date" />
          <v-textarea v-model="feedStocktakeForm.notes" label="Notes" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="feedStocktakeDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordFeedStocktake">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fertiliser Stocktake Dialog -->
    <v-dialog v-model="fertStocktakeDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Manual Fertiliser Stocktake</v-card-title>
        <v-card-text>
          <v-text-field v-model.number="fertStocktakeForm.recorded_stock" label="Counted Stock" type="number" />
          <v-text-field v-model="fertStocktakeForm.date" label="Date" type="date" />
          <v-textarea v-model="fertStocktakeForm.notes" label="Notes" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fertStocktakeDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordFertStocktake">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Fuel Stocktake Dialog -->
    <v-dialog v-model="fuelStocktakeDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Manual Fuel Stocktake</v-card-title>
        <v-card-text>
          <v-text-field v-model.number="fuelStocktakeForm.recorded_stock" label="Counted Stock" type="number" />
          <v-text-field v-model="fuelStocktakeForm.date" label="Date" type="date" />
          <v-textarea v-model="fuelStocktakeForm.notes" label="Notes" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fuelStocktakeDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordFuelStocktake">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>


    <!-- Manual Stocktake Dialog -->
    <v-dialog v-model="universalStocktakeDialogOpen" max-width="420">
      <v-card>
        <v-card-title>Manual Stocktake</v-card-title>
        <v-card-text>
          <v-select
            v-model="universalStocktakeForm.type"
            :items="['vaccine', 'feed', 'fertiliser', 'fuel']"
            label="Stock Type"
            required
          />
          <v-select
            v-model="universalStocktakeForm.item_id"
            :items="filteredStockOptions"
            item-title="name"
            item-value="id"
            label="Component"
            :disabled="!universalStocktakeForm.type"
            required
          />
          <v-text-field v-model.number="universalStocktakeForm.recorded_stock" label="Counted Stock" type="number" />
          <v-text-field v-model="universalStocktakeForm.date" label="Date" type="date" />
          <v-textarea v-model="universalStocktakeForm.notes" label="Notes" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="universalStocktakeDialogOpen=false">Cancel</v-btn>
          <v-btn color="primary" @click="recordUniversalStocktake">Record</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>