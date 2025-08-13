<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'

const apiBase = import.meta?.env?.VITE_API_URL || window.location.origin
const api = axios.create({ baseURL: apiBase })

const herd = ref({ total: 0, bulls: 0, cows: 0, heifers: 0, calves: 0, unknown: 0 })
const camps = ref([])
const stocks = ref({ totals_by_category: {}, low_stock: [], total_items: 0 })
const loading = ref(true)
const errorMsg = ref('')

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    const [h, c, s] = await Promise.all([
      api.get('/stats/herd-summary'),
      api.get('/stats/camps-summary'),
      api.get('/stats/stocks-summary'),
    ])
    herd.value = h.data
    camps.value = c.data
    stocks.value = s.data
  } catch (e) {
    console.error(e)
    errorMsg.value = e?.message || 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <v-container class="py-8">
    <h1 class="text-h5 mb-6">Dashboard</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <!-- Herd overview -->
    <v-card class="mb-6">
      <v-card-title>Herd Overview</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Total</div>
              <div class="text-h5">{{ herd.total }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Bulls</div>
              <div class="text-h5">{{ herd.bulls }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Cows</div>
              <div class="text-h5">{{ herd.cows }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Heifers</div>
              <div class="text-h5">{{ herd.heifers }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Calves</div>
              <div class="text-h5">{{ herd.calves }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="6" md="2">
            <v-sheet class="pa-4 text-center" elevation="1" rounded>
              <div class="text-overline">Unknown</div>
              <div class="text-h5">{{ herd.unknown }}</div>
            </v-sheet>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Camps overview -->
    <v-card class="mb-6">
      <v-card-title class="d-flex align-center">
        <span>Camps Overview</span>
        <v-spacer />
        <v-btn variant="text" @click="load" :loading="loading">Refresh</v-btn>
      </v-card-title>
      <v-data-table
        :headers="[
          { title: 'Camp', value: 'name' },
          { title: 'Animals', value: 'animal_count' }
        ]"
        :items="camps"
        :items-per-page="10"
        density="comfortable"
      />
    </v-card>

    <!-- Stocks overview -->
    <v-card>
      <v-card-title>Stocks Overview</v-card-title>
      <v-card-text>
        <div class="mb-4">
          <v-chip
            v-for="(qty, cat) in stocks.totals_by_category"
            :key="cat"
            class="ma-1"
            color="primary"
            variant="tonal"
          >
            {{ cat }}: {{ qty }}
          </v-chip>
          <v-chip class="ma-1" color="secondary" variant="tonal">
            Total items: {{ stocks.total_items }}
          </v-chip>
        </div>

        <div v-if="stocks.low_stock?.length">
          <div class="text-subtitle-1 mb-2">Low stock</div>
          <v-data-table
            :headers="[
              { title: 'Item', value: 'name' },
              { title: 'Category', value: 'category' },
              { title: 'Qty', value: 'quantity' },
              { title: 'Threshold', value: 'min_threshold' },
              { title: 'Unit', value: 'unit' },
            ]"
            :items="stocks.low_stock"
            :items-per-page="5"
            density="compact"
          />
        </div>
        <div v-else class="text-medium-emphasis">No low stock items 🎉</div>
      </v-card-text>
    </v-card>
  </v-container>
</template>