<template>
  <div class="history-card">
    <h2>Recent Scenarios</h2>
    <div v-if="!history.length" class="empty">
      <span class="empty-icon">🕑</span>
      <p>No scenarios yet — run one above</p>
    </div>
    <table v-else>
      <thead>
        <tr>
          <th>Category</th>
          <th>Product</th>
          <th>Store</th>
          <th>Month</th>
          <th>Change</th>
          <th>Delta</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in history" :key="row.id">
          <td>
            <span :class="`badge badge-${row.category}`">{{ row.category }}</span>
          </td>
          <td style="color:#64748b; font-size:12px;">{{ row.item_id }}</td>
          <td>{{ row.store }}</td>
          <td>{{ monthName(row.month) }}</td>
          <td :class="row.pct_change > 0 ? 'positive' : row.pct_change < 0 ? 'negative' : 'neutral'">
            {{ row.pct_change > 0 ? '+' : '' }}{{ row.pct_change }}%
          </td>
          <td :class="row.delta >= 0 ? 'positive' : 'negative'" style="font-weight:600;">
            {{ row.delta >= 0 ? '+' : '' }}€{{ row.delta.toFixed(2) }}
          </td>
          <td style="color:#475569;">{{ timeAgo(row.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ history: { type: Array, default: () => [] } })

function monthName(m) {
  return new Date(2024, m - 1).toLocaleString('default', { month: 'short' })
}

function timeAgo(ts) {
  const secs = Math.floor((Date.now() - new Date(ts)) / 1000)
  if (secs < 60)   return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  return `${Math.floor(secs / 3600)}h ago`
}
</script>