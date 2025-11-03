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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

* {
  font-family: 'Poppins', sans-serif;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.admin-data-pakan {
  padding: 1.5rem;
  background-color: #f9f9f9;
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
  transition: all 0.2s;
}
.search-input:focus {
  border-color: #2e7d32;
  box-shadow: 0 0 5px rgba(46,125,50,0.3);
}

/* Card & Table */
.card {
  background: #fff;
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
  color: #1b1b1b;
}

.data-table th {
  background: #2e7d32;
  color: white;
  text-transform: uppercase;
}

.data-table tr:nth-child(even) {
  background: #f1fdf1;
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

/* Responsive */
@media (max-width: 768px) {
  .search-input {
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.4rem 0.6rem;
    font-size: 0.8rem;
  }

  .btn-delete {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
  }
}
</style>
