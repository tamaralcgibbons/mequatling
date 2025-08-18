<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  item: { type: Object, required: true }, // The stock item (vaccine, feed, etc.)
  type: { type: String, required: true }, // 'vaccine' | 'feed' | 'fertiliser' | 'fuel'
})

const emit = defineEmits(['update:modelValue', 'submit'])

const form = ref({
  recorded_stock: props.item.current_stock ?? 0,
  date: new Date().toISOString().slice(0, 10),
  notes: ''
})

watch(() => props.modelValue, (val) => {
  if (val) {
    form.value = {
      recorded_stock: props.item.current_stock ?? 0,
      date: new Date().toISOString().slice(0, 10),
      notes: ''
    }
  }
})

function close() {
  emit('update:modelValue', false)
}

function submit() {
  emit('submit', {
    ...form.value,
    [`${props.type}_id`]: props.item.id
  })
  close()
}
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="420" @update:modelValue="emit('update:modelValue', $event)">
    <v-card>
      <v-card-title>
        Manual Stocktake for {{ props.item.name || props.item.type }}
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model.number="form.recorded_stock"
          label="Counted Stock"
          type="number"
          min="0"
        />
        <v-text-field
          v-model="form.date"
          label="Date"
          type="date"
        />
        <v-textarea
          v-model="form.notes"
          label="Notes"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">Cancel</v-btn>
        <v-btn color="primary" @click="submit">Record</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>