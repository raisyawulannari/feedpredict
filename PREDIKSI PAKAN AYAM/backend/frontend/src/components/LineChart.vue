<template>
  <div>
    <canvas ref="chart"></canvas>
  </div>
</template>

<script>
import { Chart } from 'chart.js';
// import { Line } from 'chart.js';
import { onMounted, ref } from 'vue';

export default {
  name: 'LineChart',
  props: {
    data: {
      type: Array,
      required: true,
    },
  },
  setup(props) {
    const chartRef = ref(null);

    onMounted(() => {
      const ctx = chartRef.value.getContext('2d');
      new Line(ctx, {
        type: 'line',
        data: {
          labels: props.data.labels,  // X-axis
          datasets: [
            {
              label: 'Prediksi Pakan',
              data: props.data.values,  // Y-axis
              borderColor: '#4CAF50',
              fill: false,
            },
          ],
        },
      });
    });

    return { chartRef };
  },
};
</script>
