<template>
  <div>
    <Line :data="computedChartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
} from 'chart.js'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale
)

const props = defineProps({
  labels: Array,
  actualData: Array,
  predictedData: Array
})

// 🧠 Gunakan `computed` agar reactive
const computedChartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Data Aktual',
      data: props.actualData,
      borderColor: 'blue',
      backgroundColor: 'rgba(0,0,255,0.1)',
      tension: 0.3,
      pointRadius: 3,
      pointHoverRadius: 5,
    },
    {
      label: 'Prediksi',
      data: props.predictedData,
      borderColor: 'red',
      backgroundColor: 'rgba(255,0,0,0.1)',
      borderDash: [6, 3],
      tension: 0.3,
      pointRadius: 3,
      pointHoverRadius: 5,
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    title: {
      display: true,
      text: 'Grafik Prediksi vs Aktual',
    },
    tooltip: {
      callbacks: {
        label: function (ctx) {
          const value = ctx.parsed.y
          return `${ctx.dataset.label}: ${value} kg (${(value / 50).toFixed(2)} karung)`
        }
      }
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Tanggal'
      },
      ticks: {
        autoSkip: true,
        maxRotation: 45,
      }
    },
    y: {
      title: {
        display: true,
        text: 'Pakan (kg)'
      }
    }
  }
}
</script>

<style scoped>
div {
  height: 400px;
}
</style>
