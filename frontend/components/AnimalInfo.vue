<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/lib/api'

const props = defineProps({
  animalId: {
    type: Number,
    required: true
  }
})

const loading = ref(false)
const errorMsg = ref('')
const records = ref([])

async function fetchVaccinationHistory() {
  loading.value = true
  errorMsg.value = ''
  records.value = []
  try {
    const { data } = await api.get('/vaccinations', { params: { animal_id: props.animalId } })
    records.value = Array.isArray(data) ? data : []
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || e.message || 'Failed to load vaccination history'
  } finally {
    loading.value = false
  }
}

onMounted(fetchVaccinationHistory)
watch(() => props.animalId, fetchVaccinationHistory)

const headers = [
  { title: 'Date', value: 'date' },
  { title: 'Vaccine', value: 'vaccine_name' },
  { title: 'Dose', value: 'dose_display' },
  { title: 'Method', value: 'method' },
  { title: 'Source', value: 'source' },
  { title: 'Notes', value: 'notes' },
  { title: 'Group', value: 'group_name' },
  { title: 'Camp', value: 'camp_name' },
]

const tableItems = computed(() =>
  records.value.map(r => ({
    ...r,
    dose_display: r.dose != null ? `${r.dose}${r.unit ? ' ' + r.unit : ''}` : '—',
    date: r.date ? r.date.split('T')[0] : '—',
    notes: r.notes || '—',
    group_name: r.group_name || '—',
    camp_name: r.camp_name || '—',
  }))
)
</script>

<template>
  <div>
    <h2 class="text-h6 mb-2">Vaccination History</h2>
    <v-alert v-if="errorMsg" type="error" class="mb-2">{{ errorMsg }}</v-alert>
    <v-data-table
      :items="tableItems"
      :headers="headers"
      :items-per-page="10"
      :loading="loading"
      class="mb-2"
    >
      <template #item.date="{ item }">
        {{ item.date }}
      </template>
      <template #item.dose_display="{ item }">
        {{ item.dose_display }}
      </template>
      <template #item.notes="{ item }">
        <span>{{ item.notes }}</span>
      </template>
    </v-data-table>
    <div v-if="!loading && records.length === 0" class="text-caption pa-2">
      No vaccination records found for this animal.
    </div>
  </div>
</template>