<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/lib/api' // shared axios instance

const herd = ref({ total: 0, bulls: 0, cows: 0, heifers: 0, calves: 0, unknown: 0 })
const camps = ref([])
const stocks = ref({ totals_by_category: {}, low_stock: [], total_items: 0 })
const loading = ref(true)
const errorMsg = ref('')

// ensure tables always receive arrays
const asArray = (d) =>
  Array.isArray(d) ? d :
  Array.isArray(d?.data) ? d.data :
  Array.isArray(d?.items) ? d.items :
  Array.isArray(d?.results) ? d.results : []

const campRows = computed(() => asArray(camps.value))
const lowStockRows = computed(() => asArray(stocks.value?.low_stock))

async function load() {
  loading.value = true
  errorMsg.value = ''
  try {
    const [h, c, s] = await Promise.all([
      api.get('/stats/herd-summary'),
      api.get('/stats/camps-summary'),
      api.get('/stats/stocks-summary'),
    ])

    herd.value = h.data ?? herd.value
    camps.value = asArray(c.data)
    stocks.value = {
      totals_by_category: s.data?.totals_by_category ?? {},
      low_stock: asArray(s.data?.low_stock),
      total_items: s.data?.total_items ?? 0,
    }
  } catch (e) {
    console.error(e)
    errorMsg.value = e?.message || 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}

const dashboardNotes = ref('')

onMounted(load)
</script>

<template>
  <v-container class="py-8">
    <h1 class="text-h5 mb-6">Dashboard</h1>

    <v-alert v-if="errorMsg" type="error" class="mb-4">{{ errorMsg }}</v-alert>

    <!-- Herd overview -->
    <v-card class="mb-6">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-cow</v-icon>
        Herd Overview
      </v-card-title>
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
        <v-icon class="mr-2">mdi-fence</v-icon>
        Camps Overview
      </v-card-title>
      <v-data-table
        :headers="[
          { title: 'Camp', key: 'name' },
          { title: 'Group', key: 'group_name' },
          { title: 'Animals', key: 'animal_count' },
          { title: 'Notes', key: 'notes' }
        ]"
        :items="campRows"
        :items-per-page="10"
        density="comfortable"
      />
    </v-card>

    <!-- Stocks overview -->
    <v-card class="mb-6">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-warehouse</v-icon>
        Stocks Overview
      </v-card-title>
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

        <div v-if="lowStockRows.length">
          <div class="text-subtitle-1 mb-2">Low stock</div>
          <v-data-table
            :headers="[
              { title: 'Item', key: 'name' },
              { title: 'Category', key: 'category' },
              { title: 'Qty', key: 'quantity' },
              { title: 'Threshold', key: 'min_threshold' },
              { title: 'Unit', key: 'unit' },
            ]"
            :items="lowStockRows"
            :items-per-page="5"
            density="compact"
          />
        </div>
        <div v-else class="text-medium-emphasis">No low stock items 🎉</div>
      </v-card-text>
    </v-card>

    <!-- Notes Section -->
    <v-card class="mb-6">
      <v-card-title class="d-flex align-center">
      Notes
      </v-card-title>
      <v-card-text>
        <v-textarea
          v-model="dashboardNotes"
          label="General notes and comments"
          auto-grow
          rows="3"
          placeholder="Type notes here..."
        />
      </v-card-text>
    </v-card>
  </v-container>
</template>
