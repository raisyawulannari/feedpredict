<template>
  <div class="container">
    <h1 class="title">Riwayat Prediksi Pakan Ayam</h1>

    <button v-if="riwayat.length" @click="hapusSemua" class="btn-hapus">Hapus Semua</button>

    <table class="riwayat-table">
      <thead>
        <tr>
          <th>No</th>
          <th>Tanggal</th>
          <th>Durasi (Hari)</th>
          <th>Prediksi Pakan</th>
          <th>MAPE</th>
          <th>Asal Data</th> 
          <th>Nama File</th> 
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="riwayat.length === 0">
          <td colspan="7" class="text-center">Belum ada data riwayat.</td>
        </tr>
        <tr v-for="(item, index) in riwayat" :key="index">
          <td class="text-center">{{ index + 1 }}</td>
          <td class="text-center">{{ item.tanggal }}</td>
          <td class="text-center">{{ item.durasi ?? '-' }} hari</td>
          <td class="text-center">{{ formatAngka(item.prediksiPakan) }} kg</td>
            <td class="text-center" :class="mapeClass(item.mape)">
              {{ formatPersen(item.mape) }}
            </td>
          <td class="text-center">{{ formatAsalData(item.asalData) }}</td>
          <td class="text-center">
            {{ item.asalData === 'upload' ? item.namaFile : 'default' }}
          </td>
          <td>
            <div class="action-buttons">
              <RouterLink :to="`/riwayat/${item.id || index}/grafik`" class="btn-detail">
                Detail
              </RouterLink>
              <button @click="hapusItem(index)" class="btn-hapus-item">Hapus</button>
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

const riwayat = ref([])

onMounted(() => {
  const data = localStorage.getItem('riwayatPrediksi')
  if (data) {
    riwayat.value = JSON.parse(data).map((item, index) => ({
      ...item,
      id: item.id ?? index, // fallback id jika belum ada
      asalData: item.asalData ?? 'default' // fallback default asal data
    }))
  }
})

function hapusItem(index) {
  if (confirm('Yakin ingin menghapus data ini?')) {
    riwayat.value.splice(index, 1)
    localStorage.setItem('riwayatPrediksi', JSON.stringify(riwayat.value))
  }
}

function hapusSemua() {
  if (confirm('Yakin ingin menghapus semua data riwayat?')) {
    localStorage.removeItem('riwayatPrediksi')
    riwayat.value = []
  }
}

function formatAngka(value) {
  return value?.toLocaleString('id-ID') ?? '-'
}

function formatPersen(value) {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2) + '%'
}

function mapeClass(mape) {
  if (mape < 10) return 'mape-baik'
  else if (mape < 20) return 'mape-cukup'
  else return 'mape-buruk'
}

function formatAsalData(value) {
  if (value === 'upload') return 'Upload'
  return 'Default'
}
</script>

<style scoped>
.container {
  max-width: 850px;
  margin: 0 auto;
  padding: 1.5rem;
  text-align: center;
  padding-top: 0px;
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
  font-size: 16px;
}

.riwayat-table th,
.riwayat-table td {
  border: 1px solid #ccc;
  padding: 0.75rem;
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
