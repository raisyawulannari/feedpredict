<template>
  <div class="container">
    <h1 class="title">Riwayat Prediksi Pakan Ayam</h1>

    <button v-if="riwayat.length" @click="hapusSemua" class="btn-hapus">Hapus Semua</button>

    <table class="riwayat-table">
      <thead>
        <tr>
          <th>No</th>
          <th>Tanggal Mulai</th>
          <th>Tanggal Selesai</th>
          <th>Durasi (Hari)</th>
          <th>Mode Prediksi</th>
          <th>Jumlah Ayam Awal</th>
          <th>Total Pakan (kg)</th>
          <th>Total Karung</th>
          <th>MAPE</th>
          <th>Asal Data</th>
          <th>Nama File</th>
          <th>Created At</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="riwayat.length === 0">
          <td colspan="15" class="text-center">Belum ada data riwayat.</td>
        </tr>
        <tr v-for="(item, index) in riwayat" :key="item.id">
          <td class="text-center">{{ index + 1 }}</td>
          <td class="text-center">{{ formatTanggal(item.tanggal_mulai) }}</td>
          <td class="text-center">{{ formatTanggal(item.tanggal_selesai) }}</td>
          <td class="text-center">{{ item.durasi ?? '-' }} hari</td>
          <td class="text-center">{{ item.mode_prediksi ?? '-' }}</td>
          <td class="text-center">{{ item.jumlah_ayam_awal ?? '-' }}</td>
          <td class="text-center">{{ formatAngka(item.total_pakan_kg) }}</td>
          <td class="text-center">{{ formatAngka(Math.round(item.total_karung)) }}</td>
          <td class="text-center" :class="mapeClass(item.mape)">{{ formatPersen(item.mape) }}</td>
          <td class="text-center">{{ formatAsalData(item.asal_data) }}</td>
          <td class="text-center">{{ item.asal_data === 'upload' ? item.nama_file : 'Default' }}</td>
          <td class="text-center">{{ formatTanggal(item.created_at) }}</td>
          <td>
            <div class="action-buttons">
              <RouterLink :to="{ name: 'Prediksi', query: { riwayat_id: item.id } }" class="btn-detail">
                Detail
              </RouterLink>
              <button @click="hapusItem(item.id)" class="btn-hapus-item">Hapus</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import axios from 'axios'

const riwayat = ref([])

onMounted(() => {
  loadRiwayat()
})

async function loadRiwayat() {
  try {
    const token = localStorage.getItem('token')
    if (!token) { window.location.href = '/login'; return }

    const res = await axios.get('http://127.0.0.1:8000/riwayat', {
      headers: { Authorization: `Bearer ${token.trim()}` }
    })

    riwayat.value = (res.data.riwayat || []).map(item => {
      let prediksiArray = []
      let aktualArray = []

      try { prediksiArray = Array.isArray(item.prediksi) ? item.prediksi : JSON.parse(item.prediksi) } catch { prediksiArray = [] }
      try { aktualArray = Array.isArray(item.data_aktual) ? item.data_aktual : JSON.parse(item.data_aktual) } catch { aktualArray = [] }

      const totalKarung = item.total_karung != null
        ? Number(item.total_karung)
        : Math.ceil(prediksiArray.reduce((sum, p) => sum + (Number(p.y ?? p.value) || 0), 0) / 50)

      const totalPakanKg = item.total_pakan_kg != null
        ? Number(item.total_pakan_kg)
        : prediksiArray.reduce((sum, p) => sum + (Number(p.y ?? p.value) || 0), 0)

      return {
        ...item,
        prediksi: prediksiArray,
        data_aktual: aktualArray,
        mape: Number(item.mape) || 0,
        total_karung: totalKarung,
        total_pakan_kg: totalPakanKg
      }
    })

  } catch (error) {
    console.error('Gagal mengambil data:', error.response?.data || error)
    if (error.response?.status === 401) { window.location.href = '/login' }
  }
}

function formatTanggal(value) {
  if (!value) return '-'
  const d = new Date(value)
  if (isNaN(d)) return '-'
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })
}

function formatAngka(value) { return value == null ? '-' : value.toLocaleString('id-ID') }
function formatPersen(value) { return value == null ? '-' : value.toFixed(2) + '%' }
function mapeClass(mape) { return mape < 10 ? 'mape-baik' : mape < 20 ? 'mape-cukup' : 'mape-buruk' }
function formatAsalData(value) { return value === 'upload' ? 'Upload' : 'Default' }

async function hapusItem(id) {
  if (!confirm('Yakin ingin menghapus data ini?')) return;
  const token = localStorage.getItem('token'); if (!token) { window.location.href = '/login'; return; }
  try { await axios.delete(`http://127.0.0.1:8000/riwayat/${id}`, { headers: { Authorization: `Bearer ${token.trim()}` } }); await loadRiwayat() }
  catch (error) { console.error(error.response?.data || error); alert("Gagal menghapus riwayat."); }
}

async function hapusSemua() {
  if (!confirm('Yakin ingin menghapus semua data riwayat?')) return;
  const token = localStorage.getItem('token'); if (!token) { window.location.href = '/login'; return; }
  try { await axios.delete('http://127.0.0.1:8000/riwayat', { headers: { Authorization: `Bearer ${token.trim()}` } }); await loadRiwayat() }
  catch (error) { console.error(error.response?.data || error); alert("Gagal menghapus semua riwayat."); }
}
</script>

<style scoped>
.container {
  max-width: 1400px; 
  margin: 0 auto;
  padding: 20px 40px; 
  text-align: center;
}

.title {
  font-size: 26px;
  font-weight: bold;
  margin-bottom: 1.5rem;
  color: #2d6a4f;
}

.riwayat-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.riwayat-table th,
.riwayat-table td {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: center;
}

.riwayat-table th {
  background-color: #d8f3dc;
  color: #1b4332;
}

.btn-hapus {
  background-color: #e63946;
  color: #fff;
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.btn-hapus-item {
  background-color: #43a86d;
  color: white;
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-detail {
  background-color: #457b9d;
  color: white;
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
}

.btn-hapus:hover,
.btn-hapus-item:hover,
.btn-detail:hover {
  opacity: 0.9;
}

.mape-baik {
  color: green;
  font-weight: bold;
}

.mape-cukup {
  color: orange;
  font-weight: bold;
}

.mape-buruk {
  color: red;
  font-weight: bold;
}
</style>
