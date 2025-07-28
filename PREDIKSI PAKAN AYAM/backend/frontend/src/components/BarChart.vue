<template>
  <div>
    <Bar :data="computedChartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
)

// 🔹 Format tanggal ke "11 Januari 2025"
function formatTanggalIndonesia(dateStr) {
  const options = { day: '2-digit', month: 'long', year: 'numeric' }
  const date = new Date(dateStr)
  return date.toLocaleDateString('id-ID', options)
}

const props = defineProps({
  labels: Array,
  actualData: Array,
  predictedData: Array,
  periodeEdges: Array
})

const computedChartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Pakan Aktual',
      data: props.actualData,
      backgroundColor: 'green'
    },
    {
      label: 'Prediksi',
      data: props.predictedData,
      backgroundColor: 'gold'
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    tooltip: {
      callbacks: {
        title: function (tooltipItems) {
          const label = tooltipItems[0]?.label
          return formatTanggalIndonesia(label)
        },
        label: function (context) {
          const karung = context.raw ?? 0
          const kg = karung * 50
          return `${context.dataset.label} : ${karung} karung (${kg} kg)`
        }
      }
    },
    legend: {
      position: 'top'
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Tanggal'
      },
      ticks: {
        callback: function (val, index) {
          const label = props.labels[index]
          return formatTanggalIndonesia(label)
        },
        font: {
          size: 9
        }
      }
    },
    y: {
      beginAtZero: true,
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
  height: 480px;
  width: 100%;
}
</style>
