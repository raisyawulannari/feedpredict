<template>
  <div class="admin-riwayat">
    <h1>Riwayat Proses Prediksi</h1>
    <p>Halaman ini menampilkan riwayat prediksi yang dilakukan user beserta nama usernya.</p>

    <table class="riwayat-table">
      <thead>
        <tr>
          <th>No</th>
          <th>Nama User</th>
          <th>Tanggal Mulai</th>
          <th>Tanggal Selesai</th>
          <th>Durasi</th>
          <th>Total Karung</th>
          <th>MAPE</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in riwayatList" :key="item.id">
          <td>{{ index + 1 }}</td>
          <td>{{ item.user_name }}</td>
          <td>{{ item.tanggal_mulai }}</td>
          <td>{{ item.tanggal_selesai }}</td>
          <td>{{ item.durasi }} hari</td>
          <td>{{ item.total_karung }}</td>
          <td>{{ item.mape }}</td>
          <td>
            <RouterLink :to="`/admin/prediksi/${item.id}`" class="btn-detail">Detail</RouterLink>
            <button @click="deleteRiwayat(item.id)" class="btn-delete">Hapus</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"
import Swal from "sweetalert2"

const riwayatList = ref([])

async function fetchRiwayat() {
  try {
    const token = localStorage.getItem("token")
    const res = await axios.get("http://localhost:8000/api/admin/riwayat", {
      headers: { Authorization: `Bearer ${token}` }
    })
    // Pastikan backend mengirim array data di res.data.data
    riwayatList.value = res.data.data || []
  } catch (err) {
    console.error(err)
    Swal.fire("Error", "Gagal memuat data riwayat.", "error")
  }
}

async function deleteRiwayat(id) {
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
      fetchRiwayat() // refresh tabel
    } catch (err) {
      console.error(err)
      Swal.fire("Error", "Gagal menghapus riwayat.", "error")
    }
  }
}

onMounted(() => {
  fetchRiwayat()
})
</script>


<style scoped>
.riwayat-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
.riwayat-table th, .riwayat-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: center;
}
.btn-detail {
  margin-right: 5px;
  padding: 4px 8px;
  background-color: #28a745;
  color: #fff;
  border-radius: 4px;
  text-decoration: none;
}
.btn-delete {
  padding: 4px 8px;
  background-color: #dc3545;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
}
</style>
