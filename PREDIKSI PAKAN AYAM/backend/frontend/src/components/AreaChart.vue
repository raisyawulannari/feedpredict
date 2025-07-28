<template>
  <div ref="chartRef" class="echart-area" />
</template>

<script setup>
import * as echarts from 'echarts'
import { onMounted, watch, ref, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  labels: Array,
  actualData: Array,
  predictedData: Array,
  periodeEdges: Array
})

const chartRef = ref(null)
let chartInstance = null

// 🔹 Fungsi ubah format tanggal ke "11 Januari 2025"
function formatTanggalIndonesia(dateStr) {
  const options = { day: '2-digit', month: 'long', year: 'numeric' }
  const date = new Date(dateStr)
  return date.toLocaleDateString('id-ID', options)
}

// 🔹 Label tanggal sudah diformat
const formattedLabels = computed(() =>
  props.labels.map(label => formatTanggalIndonesia(label))
)

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        const rawLabelIndex = params[0]?.dataIndex ?? 0
        const tanggal = formattedLabels.value[rawLabelIndex] || ''
        let result = `<strong>${tanggal}</strong><br/>`

        result += params.map(item => {
          const karung = item.data ?? 0
          const kg = (karung * 50).toFixed(2)

          if (item.seriesName === 'Pakan Aktual') {
            return `${item.marker} Pakan Pakai: ${karung} karung (${kg} kg)`
          } else if (item.seriesName === 'Prediksi') {
            return `${item.marker} Pakan Prediksi: ${karung} karung (${kg} kg)`
          } else {
            return `${item.marker} ${item.seriesName}: ${karung} karung (${kg} kg)`
          }
        }).join('<br/>')

        return result
      }
    },
    legend: {
      data: ['Pakan Aktual', 'Prediksi']
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: formattedLabels.value,
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: 'Pakan (kg)',
      axisLabel: {
        formatter: value => `${value}`
      }
    },
    series: [
      {
        name: 'Pakan Aktual',
        type: 'line',
        smooth: true,
        data: props.actualData,
        areaStyle: {
          color: 'rgba(0, 128, 0, 0.3)'
        },
        lineStyle: {
          color: 'green'
        },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: 'Prediksi',
        type: 'line',
        smooth: true,
        data: props.predictedData,
        areaStyle: {
          color: 'rgba(255, 215, 0, 0.3)'
        },
        lineStyle: {
          color: 'gold',
          type: 'dashed'
        },
        symbol: 'circle',
        symbolSize: 6
      }
    ]
  }

  chartInstance.setOption(option)
  chartInstance.resize() // 🟢 Pastikan chart tampil penuh
}

onMounted(() => {
  renderChart()

  // 🟢 Resize otomatis saat window resize
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})

watch(() => [props.labels, props.actualData, props.predictedData], () => {
  renderChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.echart-area {
  width: 100%;
  height: 480px;
}
</style>
