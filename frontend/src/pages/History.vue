<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/lib/api'

const loading = ref(false)
const errorMsg = ref('')
const allEvents = ref([])
const filterType = ref('all')

const eventTypes = [
  { label: 'All', value: 'all' },
  { label: 'Animal', value: 'animal' },
  { label: 'Feed Stocktake', value: 'feed_stocktake' },
  { label: 'Fertiliser Stocktake', value: 'fertiliser_stocktake' },
  { label: 'Fuel Stocktake', value: 'fuel_stocktake' },
  { label: 'Vaccine Stocktake', value: 'vaccine_stocktake' },
  { label: 'Vaccine Waste', value: 'vaccine_waste' },
]

const fromDate = ref('')
const toDate = ref('')

const filteredEvents = computed(() => {
  let events = filterType.value === 'all'
    ? allEvents.value
    : allEvents.value.filter(e => e.type === filterType.value)

  // Date filter
  if (fromDate.value) {
    events = events.filter(e => e.date && e.date.slice(0, 10) >= fromDate.value)
  }
  if (toDate.value) {
    events = events.filter(e => e.date && e.date.slice(0, 10) <= toDate.value)
  }

  // Stocktake difference logic (unchanged)
  return events.map(e => {
    let stocktake_difference = undefined
    if (e.type && e.type.endsWith('_stocktake')) {
      const manual = e.stocktake_amount ?? e.amount
      const system = e.current_stock
      if (manual !== undefined && system !== undefined) {
        stocktake_difference = manual - system
      }
    }
    return { ...e, stocktake_difference }
  })
})

async function loadEvents() {
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get('/history/')
    allEvents.value = Array.isArray(data) ? data : []
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load history'
  } finally {
    loading.value = false
  }
}



onMounted(loadEvents)
</script>

<template>
  <v-container class="py-8" fluid>
    <h1 class="text-h5 mb-4">History</h1>
    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>
    <v-select
      v-model="filterType"
      :items="eventTypes"
      item-title="label"
      item-value="value"
      label="Filter by category"
      class="mb-4"
    />
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="6" md="3">
        <v-text-field
          v-model="fromDate"
          type="date"
          label="From date"
          density="compact"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-text-field
          v-model="toDate"
          type="date"
          label="To date"
          density="compact"
          hide-details
        />
      </v-col>
    </v-row>
    <v-data-table
        :items="filteredEvents"
        :headers="[
            { title: 'Date', value: 'date' },
            { title: 'Category', value: 'type' },
            { title: 'Item', value: 'name' },
            { title: 'Event Type', value: 'event_type' },
            { title: 'Recorded Amount', value: 'current_stock' },
            { title: 'Unit', value: 'unit' },
            { title: 'From Camp', value: 'from_camp' },
            { title: 'To Camp', value: 'to_camp' },
            { title: 'Reason/Notes', value: 'reason' },
            { title: 'Manual Stocktake Amount', value: 'stocktake_amount' },
            { title: 'Stocktake Date', value: 'stocktake_date' },
            { title: 'Difference', value: 'stocktake_difference' },
        ]"
        :items-per-page="25"
        :loading="loading"
        >
        <template #item.date="{ item }">
            {{ item.date ? item.date.split('T')[0] : '—' }}
        </template>
        <template #item.amount="{ item }">
            <span v-if="item.amount !== undefined">{{ item.amount }}</span>
            <span v-else>—</span>
        </template>
        <template #item.unit="{ item }">
            <span v-if="item.unit">{{ item.unit }}</span>
            <span v-else>—</span>
        </template>
        <template #item.reason="{ item }">
            <span>{{ item.reason || '—' }}</span>
        </template>
        <template #item.stocktake_amount="{ item }">
          <span v-if="item.type && item.type.endsWith('_stocktake')">
            {{ item.recorded_stock ?? item.amount ?? '—' }}
          </span>
          <span v-else>—</span>
        </template>
        <template #item.stocktake_date="{ item }">
          <span v-if="item.type && item.type.endsWith('_stocktake')">
            {{ item.date ? item.date.split('T')[0] : '—' }}
          </span>
          <span v-else>—</span>
        </template>
        <template #item.stocktake_difference="{ item }">
          <span v-if="item.type && item.type.endsWith('_stocktake')">
            {{ item.stocktake_difference !== undefined ? item.stocktake_difference : '—' }}
          </span>
          <span v-else>—</span>
        </template>
        <template #item.event_type="{ item }">
          <span v-if="item.type === 'animal'">
            {{ item.event_type === 'slaughtered' ? 'Slaughtered' : item.event_type === 'deceased' ? 'Deceased' : item.event_type }}
          </span>
          <span v-else>{{ item.event_type }}</span>
        </template>
    </v-data-table>
  </v-container>
</template>