<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>Mequatling Farm Manager</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container class="py-8" max-width="1000">
        <v-card class="mb-6">
          <v-card-title>Add Animal</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="createAnimal" @keydown.enter.prevent="createAnimal">
              <v-text-field v-model="form.name" label="Name" required />
              <v-text-field v-model="form.tag_number" label="Tag number" />
              <v-text-field v-model="form.sex" label="Sex" />
              <v-text-field v-model="form.birth_date" label="Birth date (YYYY-MM-DD)" />
              <v-text-field v-model.number="form.camp_id" label="Camp ID" type="number" />
              <v-textarea v-model="form.stats" label="Stats (notes)" />
              <v-btn type="submit" color="primary" class="mt-2">Create</v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title class="d-flex align-center">
            <span class="text-h6">Animals</span>
            <v-spacer />
            <v-btn variant="text" @click="fetchAnimals">Refresh</v-btn>
          </v-card-title>

          <v-data-table :headers="headers" :items="animals" :items-per-page="10">
            <template #item.photo_path="{ item }">
              <div v-if="item.photo_path">
                <a :href="backendBase + item.photo_path" target="_blank">View</a>
              </div>
              <div v-else>—</div>
            </template>

            <template #item.upload="{ item }">
              <v-file-input
                accept="image/*"
                density="compact"
                show-size
                prepend-icon="mdi-camera"
                v-model="uploadFiles[item.id]"
                style="max-width: 320px"
              />
              <v-btn class="mt-2" @click="uploadPhoto(item.id)" :disabled="!uploadFiles[item.id]">
                Upload
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const backendBase = 'http://127.0.0.1:8000'
const api = axios.create({ baseURL: backendBase })

const headers = [
  { title: 'ID', value: 'id' },
  { title: 'Name', value: 'name' },
  { title: 'Tag', value: 'tag_number' },
  { title: 'Sex', value: 'sex' },
  { title: 'Birth date', value: 'birth_date' },
  { title: 'Camp ID', value: 'camp_id' },
  { title: 'Photo', value: 'photo_path' },
  { title: 'Upload', value: 'upload', sortable: false },
]

const animals = ref([])
const uploadFiles = ref({})
const form = ref({ name: '', tag_number: '', sex: '', birth_date: '', camp_id: null, stats: '' })

async function fetchAnimals() {
  const { data } = await api.get('/animals/')
  animals.value = data
}

async function createAnimal() {
  const payload = { ...form.value }
  Object.keys(payload).forEach(k => { if (payload[k] === '') payload[k] = null })
  await api.post('/animals/', payload)
  await fetchAnimals()
  form.value = { name: '', tag_number: '', sex: '', birth_date: '', camp_id: null, stats: '' }
}

async function uploadPhoto(animalId) {
  const file = uploadFiles.value[animalId]?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  await api.post(`/animals/${animalId}/upload-photo`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  uploadFiles.value[animalId] = null
  await fetchAnimals()
}

onMounted(fetchAnimals)
</script>
