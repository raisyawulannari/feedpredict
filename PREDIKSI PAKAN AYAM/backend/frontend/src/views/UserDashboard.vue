<template>
  <div class="dashboard-container">
    <!-- Header -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">Welcome To User Dashboard</h1>
    </div>

    <!-- Main Cards -->
    <div class="main-cards">
      <!-- Card Total Riwayat -->
      <div class="card total-prediksi-card">
        <h2 class="count">{{ animatedTotalRiwayat }}</h2>
        <p>Total Riwayat Prediksi</p>
        <button @click="goToPrediksi" class="btn-prediksi">Lakukan Prediksi Sekarang</button>
      </div>

      <!-- Card Historis -->
      <div class="card historis-card">
        <h2 class="historis-title">Historis</h2>
        <div class="historis-table">
          <div class="historis-row header">
            <span>Tanggal</span>
            <span>Mode</span>
            <span>Total Pakan</span>
          </div>
          <div v-for="(item, index) in recentPredictions" :key="index" class="historis-row">
            <span>{{ item.tanggal_mulai }} - {{ item.tanggal_selesai }}</span>
            <span>{{ item.mode_prediksi }}</span>
            <span>{{ item.total_pakan_kg.toFixed(2) }} kg ({{ item.total_karung }} karung)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const totalRiwayat = ref(0)
const recentPredictions = ref([])
const animatedTotalRiwayat = ref(0)

const animateValue = (refValue, target, duration = 1000) => {
  target = Number(target) || 0
  let start = 0
  const stepTime = 20
  const steps = duration / stepTime
  const increment = (target - start) / steps
  const timer = setInterval(() => {
    start += increment
    if (start >= target) {
      refValue.value = target
      clearInterval(timer)
    } else {
      refValue.value = Math.floor(start)
    }
  }, stepTime)
}

const goToPrediksi = () => {
  window.location.href = "http://127.0.0.1:8000/prediksi"
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('http://127.0.0.1:8000/riwayat', {
      headers: { Authorization: `Bearer ${token}` }
    })

    const riwayat = (res.data.riwayat || []).map(item => ({
      ...item,
      total_pakan_kg: Number(item.total_pakan_kg) || 0,
      total_karung: Number(item.total_karung) || 0
    }))

    totalRiwayat.value = riwayat.length
    recentPredictions.value = riwayat.slice(0, 5)
    animateValue(animatedTotalRiwayat, totalRiwayat.value)
  } catch (err) {
    console.error('Gagal memuat riwayat:', err)
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 1.5rem;
  font-family: 'Poppins', sans-serif;
  background-color: #f2f7f0;
}

/* Header */
.dashboard-header {
  /* background-image: url('https://images.pexels.com/photos/4911679/pexels-photo-4911679.jpeg'); */
  background-image: url('https://images.pexels.com/photos/460621/pexels-photo-460621.jpeg');
  /* background-image: url('https://images.pexels.com/photos/167684/pexels-photo-167684.jpeg'); */
  /* background-image: url('@/assets/user_dashboard1.jpeg');  */
  background-size: cover;
  background-position: center;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 5rem;
}

.dashboard-title {
  color: #fff;
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  text-shadow: 1px 1px 5px rgba(0,0,0,0.5);
}

/* Main Cards */
.main-cards {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: flex-start;
}

/* Card Total Riwayat */
.total-prediksi-card {
  background: linear-gradient(135deg, #327e2b, #81c784);
  color: #fff;
  border-radius: 15px;
  flex: 1 1 280px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-height: fit-content; 
}

.total-prediksi-card .count {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.total-prediksi-card p {
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.btn-prediksi {
  padding: 0.7rem 1.5rem;
  background-color: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: 0.3s;
}

.btn-prediksi:hover {
  background-color: #388e3c;
}

/* Card Historis */
.historis-card {
  background-color: #fff;
  border-radius: 15px;
  flex: 1 1 700px;
  padding: 2rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  overflow-x: auto;
}

.historis-title {
  font-size: 1.6rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #5d2d1d;
}

/* Tabel horizontal */
.historis-table {
  display: table;
  width: 100%;
  border-collapse: collapse;
}

.historis-row {
  display: table-row;
}

.historis-row.header {
  font-weight: 600;
  border-bottom: 2px solid #5d2d1d;
}

.historis-row span {
  display: table-cell;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #eee;
  font-size: 1rem;
  color: #333;
}

/* ===== Responsiveness ===== */
@media (max-width: 900px) {
  .main-cards {
    flex-direction: column;
    gap: 1.5rem;
  }
  .total-prediksi-card,
  .historis-card {
    flex: 1 1 100%;
  }
  .historis-row span {
    display: block; /* untuk mobile, tumpuk vertical */
    border-bottom: 1px solid #eee;
  }
}
</style>
