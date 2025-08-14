<script setup>
import { ref, watch, computed } from 'vue'

/**
 * Reusable modal for creating/editing a group and its membership.
 * Props
 *  - modelValue: Boolean (open/close)
 *  - initialGroup: { id?, name?, camp_id? } | null
 *  - camps: [{id,name}]
 *  - animals: [{id, tag_number, name, sex, camp_id, deceased?}]
 *  - saving: Boolean (show spinner on Save)
 *
 * Emits
 *  - 'update:modelValue' (Boolean)
 *  - 'save' (payload: { id?, name, camp_id?, animal_ids:[] })
 *  - 'cancel'
 */

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  initialGroup: { type: Object, default: null },
  camps: { type: Array, default: () => [] },
  animals: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

// Local form state
const form = ref({
  id: null,
  name: '',
  camp_id: null,
})
const membersPick = ref([]) // [{...animal, selected:bool}]
const search = ref('')

// Initialize whenever dialog opens or initialGroup changes
watch(
  () => [props.modelValue, props.initialGroup, props.animals],
  () => {
    if (!props.modelValue) return
    const g = props.initialGroup || {}
    form.value = {
      id: g.id ?? null,
      name: g.name || '',
      camp_id: g.camp_id ?? null,
    }
    const memberIds = new Set(
      (props.animals || [])
        .filter(a => a.group_id === g.id && !a.deceased)
        .map(a => a.id)
    )
    membersPick.value = (props.animals || [])
      .filter(a => !a.deceased)
      .map(a => ({ ...a, selected: memberIds.has(a.id) }))
  },
  { immediate: true }
)

const filteredMembers = computed(() => {
  const needle = search.value.trim().toLowerCase()
  if (!needle) return membersPick.value
  return membersPick.value.filter(a =>
    (a.tag_number || '').toLowerCase().includes(needle) ||
    (a.name || '').toLowerCase().includes(needle)
  )
})

function close() {
  emit('update:modelValue', false)
  emit('cancel')
}
function doSave() {
  const payload = {
    id: form.value.id || undefined,
    name: (form.value.name || '').trim(),
    camp_id: form.value.camp_id ?? null,
    animal_ids: membersPick.value.filter(x => x.selected).map(x => x.id),
  }
  if (!payload.name) {
    alert('Group name is required')
    return
  }
  emit('save', payload)
}
</script>

<template>
  <v-dialog :model-value="modelValue" @update:modelValue="val => emit('update:modelValue', val)" max-width="880" persistent>
    <v-card>
      <v-card-title>{{ form.id ? 'Edit group' : 'Create group' }}</v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.name" label="Group name" />
          </v-col>
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="form.camp_id"
              :items="camps"
              item-title="name"
              item-value="id"
              label="Camp (optional)"
              clearable
            />
          </v-col>
        </v-row>

        <div class="d-flex align-center mt-2 mb-1">
          <div class="text-subtitle-2">Members</div>
          <v-spacer />
          <v-text-field
            v-model="search"
            placeholder="Search tag/name"
            density="compact"
            hide-details
            style="max-width: 260px"
          />
        </div>

        <v-sheet class="pa-2" elevation="1" rounded>
          <v-virtual-scroll :items="filteredMembers" height="360">
            <template #default="{ item }">
              <div class="d-flex align-center py-1 px-2">
                <v-checkbox v-model="item.selected" class="mr-3" density="compact" />
                <div class="mr-4" style="width: 90px">{{ item.tag_number || '—' }}</div>
                <div class="mr-4" style="width: 50px">{{ item.sex }}</div>
                <div class="mr-4" style="width: 140px">
                  {{ (camps.find(c => c.id === item.camp_id)?.name) || '—' }}
                </div>
                <div class="mr-4">{{ item.name || '—' }}</div>
              </div>
            </template>
          </v-virtual-scroll>
        </v-sheet>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">Cancel</v-btn>
        <v-btn color="primary" :loading="saving" @click="doSave">Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
