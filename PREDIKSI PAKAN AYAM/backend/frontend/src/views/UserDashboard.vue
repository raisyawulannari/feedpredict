<template>
  <div class="dashboard-container">
    <h1 class="dashboard-title">User Dashboard</h1>

    <!-- Cards Summary -->
    <div class="cards">
      <div class="card total-prediksi">
        <div class="icon">📊</div>
        <div class="info">
          <h2>{{ totalPrediksi }}</h2>
          <p>Jumlah prediksi yang telah dilakukan</p>
        </div>
      </div>

      <div class="card riwayat-prediksi">
        <div class="icon">📝</div>
        <div class="info">
          <h2>{{ totalRiwayat }}</h2>
          <p>Total riwayat prediksi dan penggunaan pakan</p>
        </div>
      </div>

      <div class="card prediksi-hari-ini">
        <div class="icon">⏰</div>
        <div class="info">
          <h2>{{ prediksiHariIni }}</h2>
          <p>Prediksi yang dilakukan pada hari ini</p>
        </div>
      </div>
    </div>

    <!-- Histori Prediksi Terakhir -->
    <div class="recent-predictions mt-8">
      <h2 class="recent-title">Histori Prediksi Terakhir</h2>
      <ul>
        <li v-for="(item, index) in recentPredictions" :key="index" class="recent-item">
          <span class="prediction-date">{{ item.date }}</span>
          <span class="prediction-value">{{ item.value }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const totalPrediksi = ref(0)
const totalRiwayat = ref(0)
const prediksiHariIni = ref(0)
const recentPredictions = ref([]) // array histori prediksi terakhir

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('http://127.0.0.1:8000/api/user/dashboard', {
      headers: { Authorization: `Bearer ${token}` }
    })

    totalPrediksi.value = res.data.totalPrediksi
    totalRiwayat.value = res.data.totalRiwayat
    prediksiHariIni.value = res.data.prediksiHariIni
    recentPredictions.value = res.data.recentPredictions // ambil data historis dari API
  } catch (err) {
    console.error('Gagal memuat data dashboard:', err)
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 2rem;
  font-family: 'Poppins', sans-serif;
}

.dashboard-title {
  font-size: 2rem;
  margin-bottom: 2rem;
  color: #5d2d1d;
}

.cards {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.card {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  border-radius: 12px;
  color: #fff;
  flex: 1;
  min-width: 220px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.card:hover {
  transform: translateY(-5px);
}

.icon {
  font-size: 2.5rem;
  margin-right: 1rem;
}

.info h2 {
  margin: 0;
  font-size: 1.8rem;
}

.info p {
  margin: 0.2rem 0 0;
  font-size: 0.9rem;
}

/* WARNA CARD */
.total-prediksi {
  background-color: #5d2d1d;
}

.riwayat-prediksi {
  background-color: #a35d2d;
}

.prediksi-hari-ini {
  background-color: #e67e22;
}

/* Histori Prediksi */
.recent-predictions {
  margin-top: 2rem;
}

.recent-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #5d2d1d;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background-color: #f4f4f4;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.prediction-date {
  font-weight: 500;
  color: #333;
}

.prediction-value {
  font-weight: 600;
  color: #5d2d1d;
}
</style>
