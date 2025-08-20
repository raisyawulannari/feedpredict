<template>
  <div class="dashboard-container">
    <h1 class="dashboard-title">Admin Dashboard</h1>

    <!-- Statistik Kartu -->
    <div class="cards">
      <div class="card prediksi-user">
        <div class="icon">📊</div>
        <div class="info">
          <h2>{{ stats.prediksi }}</h2>
          <p>Jumlah prediksi yang telah dilakukan user</p>
        </div>
      </div>

      <div class="card riwayat-user">
        <div class="icon">📝</div>
        <div class="info">
          <h2>{{ stats.riwayat }}</h2>
          <p>Total riwayat prediksi dan aktivitas user</p>
        </div>
      </div>

      <div class="card kelola-user">
        <div class="icon">👥</div>
        <div class="info">
          <h2>{{ stats.users }}</h2>
          <p>Total user terdaftar dalam sistem</p>
        </div>
      </div>
    </div>

    <!-- Aktivitas Terbaru -->
    <div class="recent-activities">
      <h2>Aktivitas Terbaru</h2>
      <ul>
        <li v-for="(item, index) in recentActivities" :key="index" @click="openModal(item)" class="clickable">
          <div class="activity-icon">
            <span v-if="item.type === 'prediksi'">📊</span>
            <span v-else-if="item.type === 'riwayat'">📝</span>
            <span v-else>⚡</span>
          </div>
          <div class="activity-info">
            <p>
              <strong>{{ item.user_name }}</strong> {{ item.activity }}
              <span class="badge" :class="item.type">{{ item.status || 'Selesai' }}</span>
            </p>
            <small>{{ formatDateTime(item.created_at) }}</small>
          </div>
        </li>
      </ul>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3>Detail Aktivitas</h3>
        <p><strong>User:</strong> {{ modalData.user_name }}</p>
        <p><strong>Tipe:</strong> {{ modalData.type }}</p>
        <div v-if="modalData.type === 'prediksi'">
          <p><strong>Tanggal Mulai:</strong> {{ modalData.tanggal_mulai }}</p>
          <p><strong>Tanggal Selesai:</strong> {{ modalData.tanggal_selesai }}</p>
          <p><strong>Mode Prediksi:</strong> {{ modalData.mode_prediksi }}</p>
          <p><strong>Total Karung:</strong> {{ modalData.total_karung }}</p>
          <p><strong>Jumlah Ayam:</strong> {{ modalData.jumlah_ayam }}</p>
        </div>
        <div v-else-if="modalData.type === 'riwayat'">
          <p><strong>Tanggal Mulai:</strong> {{ modalData.tanggal_mulai }}</p>
          <p><strong>Tanggal Selesai:</strong> {{ modalData.tanggal_selesai }}</p>
          <p><strong>Durasi:</strong> {{ modalData.durasi }} hari</p>
          <p><strong>Total Karung:</strong> {{ modalData.total_karung }}</p>
          <p><strong>MAPE:</strong> {{ modalData.mape }}</p>
          <p><strong>Prediksi:</strong> {{ modalData.prediksi }}</p>
          <p><strong>Data Aktual:</strong> {{ modalData.data_aktual }}</p>
        </div>
        <button class="btn-close" @click="closeModal">Tutup</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stats = ref({ prediksi: 0, riwayat: 0, users: 0 })
const recentActivities = ref([])

const showModal = ref(false)
const modalData = ref({})

const formatDateTime = (dtString) => {
  const dt = new Date(dtString)
  return dt.toLocaleString('id-ID', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const openModal = (item) => {
  modalData.value = item
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  modalData.value = {}
}

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get("http://127.0.0.1:8000/api/admin/dashboard", {
      headers: { Authorization: `Bearer ${token}` }
    })

    stats.value = res.data.stats || { prediksi: 0, riwayat: 0, users: 0 }
    recentActivities.value = res.data.recent || []
  } catch (err) {
    console.error(err)
  }
})
</script>

<style scoped>
.dashboard-container { padding: 2rem; font-family: 'Poppins', sans-serif; }
.dashboard-title { font-size: 2rem; margin-bottom: 2rem; color: #5d2d1d; }
.cards { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 2rem; }
.card { display: flex; align-items: center; padding: 1.5rem; border-radius: 12px; color: #fff; flex: 1; min-width: 220px; box-shadow: 0 6px 18px rgba(0,0,0,0.1); transition: transform 0.2s ease; }
.card:hover { transform: translateY(-5px); }
.icon { font-size: 2.5rem; margin-right: 1rem; }
.info h2 { margin: 0; font-size: 1.8rem; }
.info p { margin: 0.2rem 0 0; font-size: 0.9rem; }
.prediksi-user { background-color: #5d2d1d; }
.riwayat-user { background-color: #a35d2d; }
.kelola-user { background-color: #e67e22; }
.recent-activities h2 { font-size: 1.2rem; margin-bottom: 1rem; }
.recent-activities ul { list-style: none; padding: 0; max-height: 400px; overflow-y: auto; border: 1px solid #ccc; border-radius: 8px; }
.recent-activities li { display: flex; align-items: flex-start; gap: 0.8rem; padding: 0.8rem 1rem; border-bottom: 1px solid #eee; cursor: pointer; }
.activity-icon { font-size: 1.8rem; line-height: 1; }
.activity-info p { margin: 0; font-size: 0.95rem; }
.activity-info small { color: #666; font-size: 0.75rem; }
.badge { padding: 2px 6px; font-size: 0.7rem; border-radius: 4px; margin-left: 6px; font-weight: bold; color: #fff; }
.badge.prediksi { background-color: #28a745; }
.badge.riwayat { background-color: #f39c12; }
.badge.default { background-color: #7f8c8d; }

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center;
  z-index: 1000;
}
.modal-content {
  background-color: #fff; padding: 1.5rem; border-radius: 10px; width: 90%; max-width: 500px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.modal-content h3 { margin-top: 0; color: #5d2d1d; }
.btn-close {
  margin-top: 1rem; padding: 0.5rem 1rem; background-color: #5d2d1d; color: #fff; border: none; border-radius: 6px; cursor: pointer;
}
.btn-close:hover { background-color: #7a4325; }
</style>
