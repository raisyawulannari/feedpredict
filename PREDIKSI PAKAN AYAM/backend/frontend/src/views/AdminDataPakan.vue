<template>
  <div class="admin-data-pakan">
    <h2>Data Pakan Semua User</h2>

    <!-- Search -->
    <div class="search-container">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cari data..."
        class="search-input"
      />
    </div>

    <!-- Tabel -->
    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>No</th>
            <th>Nama User</th>
            <th>File Name</th>
            <th>File Path</th>
            <th>Upload Date</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in filteredData"
            :key="item.id"
          >
            <td>{{ index + 1 }}</td>
            <td>{{ item.user_name }}</td>
            <td>{{ item.file_name }}</td>
            <td>{{ item.file_path }}</td>
            <td>{{ item.upload_date }}</td>
            <td>
              <button class="btn-delete" @click="deleteData(item.id)">
                Hapus
              </button>
            </td>
          </tr>
          <tr v-if="filteredData.length === 0">
            <td colspan="6" class="text-center">Belum ada data</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const pakanData = ref([])
const searchQuery = ref('')

// Ambil data dari backend
async function fetchPakanData() {
  try {
    const response = await axios.get('/api/admin/data-pakan') // endpoint backend
    pakanData.value = response.data
  } catch (error) {
    console.error('Gagal mengambil data pakan:', error)
    pakanData.value = []
  }
}

// Hapus data
async function deleteData(id) {
  if(!confirm('Apakah yakin ingin menghapus data ini?')) return
  try {
    await axios.delete(`/api/admin/data-pakan/${id}`)
    // refresh data setelah hapus
    fetchPakanData()
  } catch (error) {
    console.error('Gagal menghapus data:', error)
  }
}

// Filter berdasarkan search
const filteredData = computed(() => {
  if (!searchQuery.value) return pakanData.value
  return pakanData.value.filter(item =>
    item.user_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    item.file_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

onMounted(() => {
  fetchPakanData()
})
</script>

<style scoped>
.admin-data-pakan {
  padding: 1.5rem;
}

h2 {
  margin-bottom: 1rem;
  color: #2e7d32; /* hijau */
}

/* Search input */
.search-container {
  margin-bottom: 1rem;
}
.search-input {
  padding: 0.5rem 1rem;
  width: 250px;
  border: 1px solid #a5d6a7;
  border-radius: 5px;
  outline: none;
}

/* Card & Table */
.card {
  background: #e8f5e9; /* hijau muda */
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  border: 1px solid #c8e6c9;
  padding: 0.5rem 0.8rem;
  text-align: left;
  font-size: 0.9rem;
}

.data-table th {
  background: #4caf50;
  color: white;
}

.data-table tr:nth-child(even) {
  background: #c8e6c9;
}

.text-center {
  text-align: center;
}

/* Tombol hapus */
.btn-delete {
  background: #e53935;
  color: white;
  border: none;
  padding: 0.3rem 0.6rem;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-delete:hover {
  background: #b71c1c;
}
</style>
