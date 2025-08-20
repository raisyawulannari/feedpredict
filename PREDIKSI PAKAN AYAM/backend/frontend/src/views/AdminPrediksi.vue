<template>
  <div class="admin-prediksi">
    <h1>Hasil Prediksi User</h1>
    <table>
      <thead>
        <tr>
          <th>No</th>
          <th>Nama User</th>
          <th>Riwayat ID</th>
          <th>Tanggal Mulai</th>
          <th>Tanggal Selesai</th>
          <th>Mode Prediksi</th>
          <th>Total Karung</th>
          <th>Jumlah Ayam</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in prediksi" :key="item.id">
          <td>{{ index + 1 }}</td>
          <td>{{ item.user_name }}</td>
          <td>{{ item.riwayat_id }}</td>
          <td>{{ item.tanggal_mulai }}</td>
          <td>{{ item.tanggal_selesai }}</td>
          <td>{{ item.mode_prediksi }}</td>
          <td>{{ item.total_karung }}</td>
          <td>{{ item.jumlah_ayam ?? '-' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const prediksi = ref([]);

onMounted(async () => {
  try {
    const token = localStorage.getItem("token");
    const res = await axios.get("http://localhost:8000/api/admin/prediksi", {
      headers: { Authorization: `Bearer ${token}` }
    });
    prediksi.value = res.data.prediksi;
  } catch (err) {
    console.error("Gagal load prediksi:", err);
  }
});
</script>

<style scoped>
.admin-prediksi {
  padding: 2rem;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
th, td {
  border: 1px solid #ccc;
  padding: 6px 10px;
  text-align: center;
}
</style>
