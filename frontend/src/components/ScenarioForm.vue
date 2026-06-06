<template>
  <div class="form-card">
    <h2>What-If Scenario</h2>

    <div class="field">
      <label>Category</label>
      <select v-model="form.category" @change="onCategoryChange">
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <div class="field">
      <label>Product</label>
      <select v-model="form.itemId">
        <option v-for="item in availableItems" :key="item" :value="item">{{ item }}</option>
      </select>
    </div>

    <div class="field">
      <label>Store</label>
      <select v-model="form.store">
        <option v-for="s in stores" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <div class="field">
      <label>Month</label>
      <select v-model="form.month">
        <option v-for="m in 12" :key="m" :value="m">{{ monthName(m) }}</option>
      </select>
    </div>

    <div class="divider"></div>

    <div class="field">
      <label>Sales change &nbsp;<strong>{{ form.pctChange > 0 ? '+' : '' }}{{ form.pctChange }}%</strong></label>
      <input type="range" min="-50" max="100" step="5" v-model.number="form.pctChange" />
      <div class="range-labels"><span>-50%</span><span>0%</span><span>+100%</span></div>
    </div>

    <div class="divider"></div>

    <div class="field">
      <label>Duration &nbsp;<strong>{{ form.duration }} week{{ form.duration > 1 ? 's' : '' }}</strong></label>
      <input type="range" min="1" max="52" step="1" v-model.number="form.duration" />
      <div class="range-labels"><span>1w</span><span>26w</span><span>52w</span></div>
    </div>

    <div class="field">
      <label>Stores &nbsp;<strong>{{ form.stores }} store{{ form.stores > 1 ? 's' : '' }}</strong></label>
      <input type="range" min="1" max="10" step="1" v-model.number="form.stores" />
      <div class="range-labels"><span>1</span><span>5</span><span>10</span></div>
    </div>

    <button @click="$emit('submit', { ...form })" :disabled="loading">
      {{ loading ? 'Calculating…' : 'Run Scenario' }}
    </button>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

defineProps({ loading: { type: Boolean, default: false } })
defineEmits(['submit'])

const categories = ['FOODS', 'HOBBIES', 'HOUSEHOLD']
const stores     = ['CA_1', 'CA_2', 'TX_1']

const itemsByCategory = {
  FOODS:     Array.from({ length: 17 }, (_, i) => `FOODS_1_${(i * 3 + 1).toString().padStart(3, '0')}`),
  HOBBIES:   Array.from({ length: 17 }, (_, i) => `HOBBIES_1_${(i * 3 + 2).toString().padStart(3, '0')}`),
  HOUSEHOLD: Array.from({ length: 16 }, (_, i) => `HOUSEHOLD_1_${(i * 3 + 3).toString().padStart(3, '0')}`),
}

const form = reactive({
  category:  'FOODS',
  itemId:    itemsByCategory['FOODS'][0],
  store:     'CA_1',
  month:     1,
  pctChange: 0,
  duration:  4,
  stores:    1,
})

const availableItems = computed(() => itemsByCategory[form.category] || [])

function onCategoryChange() {
  form.itemId = itemsByCategory[form.category][0]
}

function monthName(m) {
  return new Date(2024, m - 1).toLocaleString('default', { month: 'long' })
}
</script>