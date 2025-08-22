<template>
  <div class="admin-riwayat">
    <div class="header-wrapper">
      <div>
        <h1>Riwayat Proses Prediksi</h1>
        <p>Halaman ini menampilkan data riwayat prediksi yang dilakukan user.</p>
      </div>
      <div class="search-wrapper">
        <input type="text" v-model="searchQuery" placeholder="Cari..." class="search-input" />
      </div>
    </div>

    <div class="table-wrapper">
      <table class="riwayat-table">
        <thead>
          <tr>
            <th>No</th>
            <th>Nama User</th>
            <th>Mulai</th>
            <th>Selesai</th>
            <th>Durasi</th>
            <th>Ayam Awal</th>
            <th>Mode</th>
            <th>Total Pakan</th>
            <th>Karung</th>
            <th>MAPE</th>
            <th>Asal Data</th>
            <th>Nama File</th>
            <th>Created At</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in paginatedRiwayat" :key="item.id" :class="{ highlight: isMatch(item) }">
            <td>{{ (currentPage - 1) * perPage + index + 1 }}</td>
            <td>{{ item.user_name }}</td>
            <td>{{ item.tanggal_mulai }}</td>
            <td>{{ item.tanggal_selesai }}</td>
            <td>{{ item.durasi }} hari</td>
            <td>{{ item.jumlah_ayam_awal }}</td>
            <td>
              <span :class="['badge', item.mode_prediksi === 'per_ayam' ? 'badge-green' : 'badge-blue']">
                {{ item.mode_prediksi }}
              </span>
            </td>
            <td>{{ item.total_pakan_kg }} kg</td>
            <td>{{ item.total_karung }}</td>
            <td>{{ item.mape }}%</td>
            <td>{{ item.asal_data }}</td>
            <td>{{ item.nama_file }}</td>
            <td>{{ item.created_at }}</td>
            <td class="aksi-col">
              <RouterLink :to="`/admin/prediksi/${item.id}`" class="btn-detail">Detail</RouterLink>
              <button @click="deleteRiwayat(item.id)" class="btn-delete">Hapus</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination-wrapper">
      <p>Total data: {{ filteredRiwayat.length }}</p>
      <div class="pagination-buttons">
        <button @click="prevPage" :disabled="currentPage === 1">Previous</button>
        <span>Halaman {{ currentPage }} / {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import axios from "axios"
import Swal from "sweetalert2"

const riwayatList = ref([])
const searchQuery = ref("")

// Pagination
const perPage = 10
const currentPage = ref(1)

const fetchRiwayat = async () => {
  try {
    const token = localStorage.getItem("token")
    const res = await axios.get("http://localhost:8000/api/admin/riwayat", {
      headers: { Authorization: `Bearer ${token}` }
    })
    riwayatList.value = res.data.data || []
  } catch (err) {
    console.error(err)
    Swal.fire("Error", "Gagal memuat data riwayat.", "error")
  }
}

const deleteRiwayat = async (id) => {
  const confirm = await Swal.fire({
    title: "Apakah yakin ingin menghapus?",
    text: "Data riwayat yang dihapus tidak bisa dikembalikan.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Ya, hapus",
    cancelButtonText: "Batal"
  })
  if (confirm.isConfirmed) {
    try {
      const token = localStorage.getItem("token")
      await axios.delete(`http://localhost:8000/api/admin/riwayat/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      Swal.fire("Berhasil", "Riwayat berhasil dihapus.", "success")
      fetchRiwayat()
    } catch (err) {
      console.error(err)
      Swal.fire("Error", "Gagal menghapus riwayat.", "error")
    }
  }
}

onMounted(fetchRiwayat)

// Cek apakah item match dengan search query
const isMatch = (item) => {
  const query = searchQuery.value.toLowerCase().trim()
  return query && Object.values(item).some(val => val?.toString().toLowerCase().includes(query))
}

// Filter riwayat sesuai search query
const filteredRiwayat = computed(() => {
  if (!searchQuery.value) return riwayatList.value
  return riwayatList.value.filter(item => isMatch(item))
})

// Pagination computed
const totalPages = computed(() => Math.ceil(filteredRiwayat.value.length / perPage))

const paginatedRiwayat = computed(() => {
  const start = (currentPage.value - 1) * perPage
  const end = start + perPage
  return filteredRiwayat.value.slice(start, end)
})

// Pagination methods
const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}
const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}
</script>

<style scoped>
.admin-riwayat {
  padding: 1.5rem;
  font-family: "Poppins", sans-serif;
  background-color: #f0faf0;
}

.header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}

h1 {
  color: #1b4d1b;
  margin-bottom: 0.3rem;
}

p {
  margin-bottom: 0.8rem;
  color: #3e8a0b;
}

.search-wrapper {
  margin-top: 0.5rem;
}

.search-input {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #a3d9a3;
  font-size: 0.95rem;
  min-width: 200px;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #1b4d1b;
  outline: none;
  box-shadow: 0 0 5px rgba(27,77,27,0.3);
}

.table-wrapper {
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.08);
  background-color: #1a3d19;
  margin-top: 1rem;
  overflow-x: unset;
}

.riwayat-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.riwayat-table th,
.riwayat-table td {
  padding: 10px 12px;
  text-align: center;
  white-space: nowrap;
  font-size: 0.9rem;
}

.riwayat-table thead {
  background-color: #a3d9a3;
  color: #1b4d1b;
  text-transform: uppercase;
  font-weight: 600;
}

.riwayat-table tbody tr:nth-child(even) {
  background-color: #f5fdf5;
}

.riwayat-table tbody tr:nth-child(odd) {
  background-color: #eaf8ea;
}

.riwayat-table tbody tr:hover {
  background-color: #d4f0d4;
}

/* Highlight baris search */
.highlight {
  background-color: #e6c7c7 !important; 
}

.aksi-col {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.btn-detail,
.btn-delete {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  transition: all 0.2s ease-in-out;
}

.btn-detail {
  background-color: #1b4d1b;
  color: #fff;
  text-decoration: none;
}

.btn-detail:hover {
  background-color: #3e8a0b;
}

.btn-delete {
  background-color: #dc3545;
  color: #fff;
  border: none;
  cursor: pointer;
}

.btn-delete:hover {
  background-color: #ff6b6b;
}

.badge {
  padding: 4px 8px;
  border-radius: 12px;
  color: #fff;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.badge-green {
  background-color: #28a745;
}

.badge-blue {
  background-color: #007bff;
}

.pagination-wrapper {
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-buttons button {
  padding: 5px 10px;
  margin: 0 5px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background-color: #1b4d1b;
  color: white;
  transition: all 0.2s;
}

.pagination-buttons button:disabled {
  background-color: #a3d9a3;
  cursor: not-allowed;
}

.pagination-buttons span {
  font-weight: 500;
}

@media (max-width: 768px) {
  .riwayat-table th,
  .riwayat-table td {
    padding: 8px 10px;
    font-size: 0.8rem;
  }

  .btn-detail,
  .btn-delete {
    padding: 4px 8px;
    font-size: 0.75rem;
  }

  .pagination-buttons button {
    padding: 3px 8px;
    font-size: 0.75rem;
  }
}
</style>
