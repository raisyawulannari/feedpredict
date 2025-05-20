<template>
  <div>
    <h1>Grafik Prediksi Kebutuhan Pakan Ayam</h1>
    <canvas id="myChart"></canvas>
    <p v-if="error" style="color:red">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'

const error = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/prediksi')
    const data = await res.json()

    const ctx = document.getElementById('myChart')

    if (!ctx) {
      error.value = 'Elemen canvas tidak ditemukan.'
      return
    }

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.periode,
        datasets: [{
          label: 'Kebutuhan Pakan',
          data: data.hasil,
          fill: false,
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1
        }]
      }
    })
  } catch (err) {
    console.error(err)
    error.value = 'Gagal mengambil data dari API.'
  }
})
</script>
