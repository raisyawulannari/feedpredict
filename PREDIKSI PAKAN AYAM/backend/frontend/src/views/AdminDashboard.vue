<template>
  <div class="dashboard-container">
    <!-- Header -->
    <div class="dashboard-header">
      <h1 class="dashboard-title">Welcome to Admin Dashboard</h1>
    </div>

    <!-- Main Cards -->
    <div class="main-cards">
      <!-- Card Total Riwayat -->
      <div class="card total-card">
        <h2 class="count">{{ animatedTotalRiwayat }}</h2>
        <p class="card-title">Total Riwayat Prediksi</p>
        <button class="btn-card" @click="goToRiwayat">Lihat Riwayat User</button>
      </div>

      <!-- Card Total Users -->
      <div class="card total-card">
        <h2 class="count">{{ animatedTotalUsers }}</h2>
        <p class="card-title">Total User Terdaftar</p>
        <button class="btn-card" @click="goToUsers">Lihat Semua User</button>
      </div>
    </div>

    <!-- Historis Aktivitas Terbaru -->
    <div class="historis-card">
      <h2 class="historis-title">Historis Aktivitas Terbaru</h2>
      <div class="historis-table">
        <div class="historis-row header">
          <span>User</span>
          <span>Tanggal Mulai</span>
          <span>Tanggal Selesai</span>
          <span>Mode</span>
          <span>Total Karung</span>
          <span>Status</span>
          <span>Aksi</span>
        </div>
        <div v-for="(item, index) in recentActivities" :key="index" class="historis-row">
          <span>{{ item.user_name }}</span>
          <span>{{ item.tanggal_mulai }}</span>
          <span>{{ item.tanggal_selesai }}</span>
          <span>{{ item.mode_prediksi }}</span>
          <span>{{ item.total_karung }}</span>
          <span>{{ item.status || 'Selesai' }}</span>
          <span>
            <span>
              <router-link :to="{ name: 'AdminPrediksiDetail', params: { id: item.id } }" class="btn-detail">
                Detail
              </router-link>
            </span>

          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const totalRiwayat = ref(0)
const totalUsers = ref(0)
const animatedTotalRiwayat = ref(0)
const animatedTotalUsers = ref(0)
const recentActivities = ref([])

const router = useRouter()

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

const goToRiwayat = () => router.push('/admin/riwayat')
const goToUsers = () => router.push('/admin/users')

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')

    const resRiwayat = await axios.get('http://127.0.0.1:8000/api/admin/riwayat', {
      headers: { Authorization: `Bearer ${token}` }
    })
    const riwayatData = resRiwayat.data.riwayat || resRiwayat.data.data || []
    totalRiwayat.value = riwayatData.length
    recentActivities.value = riwayatData
      .sort((a, b) => new Date(b.tanggal_mulai) - new Date(a.tanggal_mulai))
      .slice(0, 5)
    animateValue(animatedTotalRiwayat, totalRiwayat.value)

    const resUsers = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${token}` }
    })
    const usersData = resUsers.data.users || resUsers.data.data || []
    totalUsers.value = usersData.length
    animateValue(animatedTotalUsers, totalUsers.value)

  } catch (err) {
    console.error('Gagal memuat data admin:', err)
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

* {
  font-family: 'Poppins', sans-serif;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.dashboard-container {
  padding: 1.5rem;
  background-color: #f2f7f0;
}

.dashboard-header {
  /* Gambar lama: https://images.pexels.com/photos/460621/pexels-photo-460621.jpeg */
  /* background-image: url('https://images.pexels.com/photos/461198/pexels-photo-461198.jpeg');  */
  /* background-image: url('https://images.pexels.com/photos/2695703/pexels-photo-2695703.jpeg'); */
  background-image: url('@/assets/Dashboard4.jpg');
  background-size: cover;
  background-position: center;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 4rem;
  min-height: 30vh;
}

.dashboard-title {
  color: #fff;
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.5);
}

.main-cards {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  justify-content: flex-start;
  margin-bottom: 2rem;
}

.card {
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

/* --- Card Warna Seragam --- */
.total-card {
  background: linear-gradient(10deg, #2e7d32, #81c784);
  color: #fff;
  flex: 1 1 180px;
}

/* --- Perbesar teks di dalam card --- */
.count {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.btn-card {
  padding: 0.6rem 1.2rem;
  background-color: #9edf96;
  color: #333;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: 0.3s;
}

.btn-card:hover {
  background-color: #e0e0e0;
}

/* Historis Aktivitas */
.historis-card {
  background-color: #fff;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
  overflow-x: auto;
  width: 100%;
}

.historis-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2e7d32;
}

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
  font-size: 1.1rem;
  color: #333;
}

.btn-detail {
  background-color: #2e7d32;
  color: white;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  text-decoration: none;
  cursor: pointer;
}

.btn-detail:hover {
  opacity: 0.9;
}

@media (max-width: 900px) {
  .main-cards {
    flex-direction: column;
  }

  .total-card,
  .historis-card {
    flex: 1 1 100%;
  }

  .historis-row span {
    display: block;
    border-bottom: 1px solid #eee;
  }
}
</style>
