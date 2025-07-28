<template>
  <div>
    <Line :data="computedChartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import zoomPlugin from 'chartjs-plugin-zoom'
import {
  Chart as ChartJS,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
} from 'chart.js'

ChartJS.register(
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler,
  zoomPlugin
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

const predictedLabelIndexes = computed(() => {
  const indexes = []
  if (!props.labels || !props.predictedData || props.predictedData.length === 0) return indexes

  const startDate = props.predictedData[0]?.x
  const endDate = props.predictedData[props.predictedData.length - 1]?.x

  props.labels.forEach((label, idx) => {
    if (label === startDate || label === endDate) {
      indexes.push(idx)
    }
  })

  return indexes
})

const allowedLabelIndexes = computed(() => {
  return new Set([
    ...(props.periodeEdges || []),
    ...(predictedLabelIndexes.value || [])
  ])
})

const computedChartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Pakan Aktual',
      data: props.actualData,
      borderColor: 'green',
      backgroundColor: 'rgba(0, 128, 0, 0.2)',
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
      fill: true
    },
    {
      label: 'Prediksi',
      data: props.predictedData,
      borderColor: 'gold',
      backgroundColor: 'rgba(255, 215, 0, 0.2)',
      borderDash: [6, 3],
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
      fill: true
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    tooltip: {
      callbacks: {
        title: function (tooltipItems) {
          const label = tooltipItems[0]?.label
          return formatTanggalIndonesia(label)
        },
        label: function (context) {
          const dataset = context.dataset
          const karung = context.raw?.y ?? context.raw ?? 0
          const kg = context.raw?.kg ?? karung * 50
          const periode = context.raw?.periode

          if (dataset.label === 'Pakan Aktual') {
            return [
              periode ? `Periode : Periode ke-${periode}` : null,
              `Pakan Pakai : ${karung} karung (${kg} kg)`
            ].filter(Boolean)
          } else {
            return [`Pakan Prediksi : ${karung} karung (${kg} kg)`]
          }
        }
      }
    },
    legend: {
      position: 'top'
    },
    zoom: {
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: 'x'
      },
      pan: {
        enabled: true,
        mode: 'x'
      }
    }
  },
  scales: {
    x: {
      type: 'category',
      title: {
        display: true,
        text: 'Tanggal'
      },
      ticks: {
        callback: function (val, index) {
          const label = props.labels[index]
          return allowedLabelIndexes.value.has(index) ? formatTanggalIndonesia(label) : ''
        },
        autoSkip: true,
        maxTicksLimit: 12,
        maxRotation: 0,
        minRotation: 0,
        padding: 6,
        font: {
          size: 9
        }
      },
      grid: {
        display: true,
        drawTicks: true,
        drawOnChartArea: false,
        drawBorder: true
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
