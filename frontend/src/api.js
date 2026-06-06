import axios from 'axios'

const BASE = '/api'

export function predict(category, store, month, pctChange, itemId) {
  return axios.post(`${BASE}/predict`, {
    category,
    store,
    month,
    pct_change: pctChange,
    item_id: itemId,
  })
}

export function getHistory() {
  return axios.get(`${BASE}/history`)
}

export function getItems(category) {
  return axios.get(`${BASE}/items/${category}`)
}