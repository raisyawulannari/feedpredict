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
          <th>Total Karung (50kg)</th>
          <th>MAPE</th>
          <th>MAPE Harian</th>
          <th>Asal Data</th>
          <th>Nama File</th>
          <th>Created At</th>
          <th>Aksi</th>
          <th>Status</th>
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
          <td class="text-center" :class="mapeClass(item.mape)">
            {{ item.mape != null ? formatPersen(item.mape) : '-' }}
          </td>
          <td class="text-center" :class="mapeClass(item.mape_harian)">
            {{ item.mape_harian != null ? formatPersen(item.mape_harian) : '-' }}
          </td>

          <td class="text-center">{{ formatAsalData(item.asal_data) }}</td>
          <td class="text-center">{{ item.asal_data === 'User Upload' ? item.nama_file : 'Default' }}</td>
          <td class="text-center">{{ formatTanggal(item.created_at) }}</td>
          <td>
            <div class="action-buttons">
              <RouterLink :to="{ name: 'Prediksi', query: { riwayat_id: item.id } }" class="btn-detail">
                Detail
              </RouterLink>
              <button @click="hapusItem(item.id)" class="btn-hapus-item">Hapus</button>
            </div>
          </td>
          <td class="text-center">
            <span v-if="item.is_active" class="aktif-label">Aktif</span>
            <button v-else @click="setActive(item.id)" class="btn-aktifkan">Aktifkan</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
// import { ref, onMounted } from 'vue'
import { ref, onMounted, onActivated } from 'vue'
import { RouterLink } from 'vue-router'
import axios from '@/plugins/axios.js'

const riwayat = ref([])

onMounted(() => {
  loadRiwayat()
})

onActivated(() => {
  loadRiwayat()
})

async function loadRiwayat() {
  const token = localStorage.getItem('token')
  if (!token) {
    riwayat.value = []
    return
  }

  try {
    const res = await axios.get('/riwayat')
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
        mape: item.mape != null ? Number(item.mape) : null,
        mape_harian: item.mape_harian != null ? Number(item.mape_harian) : null,
        total_karung: totalKarung,
        total_pakan_kg: totalPakanKg
      }
    })

  } catch (error) {
    console.error('Gagal mengambil data:', error.response?.data || error)
    if (error.response?.status === 401) {
      riwayat.value = [] // token expired, kosongkan data tapi tetap di halaman
    }
  }
}


async function setActive(id) {
  try {
    await axios.put(`/riwayat/${id}/set_active`)
    await loadRiwayat()
  } catch (error) {
    console.error(error)
    alert("Gagal mengaktifkan riwayat.")
  }
}

async function hapusItem(id) {
  if (!confirm('Yakin ingin menghapus data ini?')) return;
  try {
    await axios.delete(`/riwayat/${id}`)
    await loadRiwayat()
  } catch (error) {
    console.error(error)
    alert("Gagal menghapus riwayat.")
  }
}

async function hapusSemua() {
  if (!confirm('Yakin ingin menghapus semua data riwayat?')) return;
  try {
    await axios.delete('/riwayat')
    await loadRiwayat()
  } catch (error) {
    console.error(error)
    alert("Gagal menghapus semua riwayat.")
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
function mapeClass(mape) {
  if (mape == null || isNaN(mape)) return ''
  return mape < 20 ? 'mape-hijau' : 'mape-coklat'
}
function formatAsalData(value) { return value === 'User Upload' ? 'Upload' : 'Default' }
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

.btn-aktifkan {
  background-color: #2a9d8f;
  color: white;
  padding: 0.3rem 0.6rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.mape-hijau {
  color: green; /* jika <20 */
  font-weight: 500;
}

.mape-coklat {
  color: #8B4513; /* coklat tua jika >=20 */
  font-weight: 500;
}

.btn-aktifkan:hover {
  opacity: 0.9;
}

.aktif-label {
  color: green;
  font-weight: bold;
}

.mape-harian {
  color: #0077b6;
  font-weight: 500;
}
</style>
