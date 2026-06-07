<template>
  <div class="chart-card">
    <div v-if="result">
      <h2>Revenue Impact</h2>

      <div class="stat-row">
        <div class="stat" :class="totalDelta >= 0 ? 'stat-delta-pos' : 'stat-delta-neg'">
          <span class="stat-value" :class="totalDelta >= 0 ? 'positive' : 'negative'">
            {{ totalDelta >= 0 ? '+' : '' }}€{{ totalDelta.toFixed(2) }}
          </span>
          <span class="stat-label">revenue delta</span>
        </div>
        <div class="stat stat-neutral">
          <span class="stat-value neutral">{{ totalBaselineUnits.toFixed(0) }}</span>
          <span class="stat-label">baseline units</span>
        </div>
        <div class="stat" :class="totalScenarioUnits >= totalBaselineUnits ? 'stat-delta-pos' : 'stat-delta-neg'">
          <span class="stat-value" :class="totalScenarioUnits >= totalBaselineUnits ? 'positive' : 'negative'">
            {{ totalScenarioUnits.toFixed(0) }}
          </span>
          <span class="stat-label">scenario units</span>
        </div>
      </div>

      <div class="chart-meta">
        Over {{ duration }} week{{ duration > 1 ? 's' : '' }} × {{ stores }} store{{ stores > 1 ? 's' : '' }}
      </div>

      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="empty">
      <span class="empty-icon">📊</span>
      <p>Run a scenario to see results</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip)

const props = defineProps({
  result:   { type: Object, default: null },
  duration: { type: Number, default: 1 },
  stores:   { type: Number, default: 1 },
})

const multiplier         = computed(() => props.duration * 7 * props.stores)
const totalBaseline      = computed(() => props.result ? props.result.baseline_revenue * multiplier.value : 0)
const totalScenario      = computed(() => props.result ? props.result.scenario_revenue * multiplier.value : 0)
const totalDelta         = computed(() => props.result ? props.result.delta * multiplier.value : 0)
const totalBaselineUnits = computed(() => props.result ? props.result.baseline_qty * multiplier.value : 0)
const totalScenarioUnits = computed(() => props.result ? props.result.scenario_qty * multiplier.value : 0)

const chartData = computed(() => ({
  labels: ['Baseline', 'Scenario'],
  datasets: [{
    label: 'Revenue (€)',
    data: props.result ? [totalBaseline.value, totalScenario.value] : [],
    backgroundColor: [
      'rgba(99, 102, 241, 0.8)',
      totalDelta.value >= 0 ? 'rgba(74, 222, 128, 0.8)' : 'rgba(248, 113, 113, 0.8)',
    ],
    borderColor: [
      '#6366f1',
      totalDelta.value >= 0 ? '#4ade80' : '#f87171',
    ],
    borderWidth: 1,
    borderRadius: 8,
  }],
}))

const chartOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: {
    x: {
      grid:  { color: '#1e293b' },
      ticks: { color: '#64748b', font: { size: 12 } },
    },
    y: {
      beginAtZero: true,
      grid:  { color: '#1e293b' },
      ticks: { color: '#64748b', font: { size: 12 } },
    },
  },
}
</script>