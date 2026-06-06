<template>
  <div class="app">
    <header>
      <h1>M5 What-If Profit Simulator</h1>
      <p>Simulate how selling more or less of a product affects your revenue</p>
    </header>

    <main>
      <div class="top-row">
        <ScenarioForm :loading="loading" @submit="runScenario" />
        <ResultChart :result="result" :duration="duration" :stores="stores" />
      </div>
      <HistoryPanel :history="history" />
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getHistory, predict } from './api.js'
import HistoryPanel from './components/HistoryPanel.vue'
import ResultChart  from './components/ResultChart.vue'
import ScenarioForm from './components/ScenarioForm.vue'

const result   = ref(null)
const history  = ref([])
const loading  = ref(false)
const duration = ref(1)
const stores   = ref(1)

async function runScenario(form) {
  loading.value  = false
  duration.value = form.duration
  stores.value   = form.stores

  loading.value = true
  try {
    const res    = await predict(form.category, form.store, form.month, form.pctChange, form.itemId)
    result.value = res.data
    const hist   = await getHistory()
    history.value = hist.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await getHistory()
  history.value = res.data
})
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, sans-serif;
  background: #0a0f1e;
  color: #e2e8f0;
  min-height: 100vh;
}

.app    { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

header  { margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid #1e293b; }
header h1 {
  font-size: 2rem; font-weight: 700; letter-spacing: -0.5px;
  background: linear-gradient(135deg, #f1f5f9 0%, #6366f1 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
header p { color: #64748b; margin-top: 8px; font-size: 15px; }

.top-row { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }

.form-card, .chart-card, .history-card {
  background: #111827;
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

.form-card    { flex: 1; min-width: 300px; }
.chart-card   { flex: 1.5; min-width: 300px; }
.history-card { width: 100%; }

h2 {
  font-size: 13px; font-weight: 600; letter-spacing: 1px;
  text-transform: uppercase; color: #64748b; margin-bottom: 20px;
}

.divider { height: 1px; background: #1e293b; margin: 16px 0; }

.field        { margin-bottom: 16px; }
.field label  {
  display: block; font-size: 11px; font-weight: 600;
  color: #64748b; margin-bottom: 8px;
  text-transform: uppercase; letter-spacing: 0.8px;
}
.field label strong { color: #e2e8f0; font-weight: 700; }

select {
  width: 100%; padding: 10px 12px;
  background: #0f172a; border: 1px solid #1e3a5f;
  border-radius: 8px; color: #e2e8f0; font-size: 14px;
  transition: border-color 0.15s;
}
select:focus { outline: none; border-color: #6366f1; }

input[type=range] { width: 100%; cursor: pointer; accent-color: #6366f1; margin-top: 4px; }
.range-labels {
  display: flex; justify-content: space-between;
  font-size: 10px; color: #334155; margin-top: 4px;
}

button {
  width: 100%; padding: 13px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white; border: none; border-radius: 10px;
  font-size: 15px; font-weight: 600; cursor: pointer;
  margin-top: 12px; letter-spacing: 0.3px;
  transition: opacity 0.15s, transform 0.1s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}
button:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
button:active:not(:disabled) { transform: translateY(0); }
button:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }

/* Stats */
.stat-row   { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat {
  flex: 1; padding: 14px 16px;
  background: #0f172a; border-radius: 10px;
  border-left: 3px solid #334155;
}
.stat.stat-delta-pos { border-left-color: #4ade80; }
.stat.stat-delta-neg { border-left-color: #f87171; }
.stat.stat-neutral   { border-left-color: #6366f1; }
.stat-value { font-size: 1.4rem; font-weight: 700; display: block; line-height: 1.2; }
.stat-label { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; display: block; }
.chart-meta { font-size: 12px; color: #475569; margin-bottom: 16px; }

/* Colors */
.positive { color: #4ade80; }
.negative { color: #f87171; }
.neutral  { color: #94a3b8; }

/* Empty */
.empty {
  color: #334155; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  min-height: 200px; gap: 12px; font-size: 14px;
}
.empty-icon { font-size: 2.5rem; opacity: 0.4; }

/* Table */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead tr { border-bottom: 1px solid #1e293b; }
th { padding: 10px 14px; color: #475569; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
td { padding: 12px 14px; border-bottom: 1px solid #0f172a; }
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: #0f172a; }
tbody tr:last-child td { border-bottom: none; }

/* Badges */
.badge { display: inline-block; padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 600; }
.badge-FOODS     { background: #052e16; color: #4ade80; }
.badge-HOBBIES   { background: #0c1a3a; color: #60a5fa; }
.badge-HOUSEHOLD { background: #1e1040; color: #c084fc; }
</style>