
<template>
  <div class="container">
    <h1 class="title">Riwayat Prediksi</h1>

    <div v-if="riwayat.length === 0" class="empty">
      Belum ada riwayat prediksi.
    </div>

    <table v-else class="riwayat-table">
      <thead>
        <tr>
          <th>No</th>
          <th>Tanggal Prediksi</th>
          <th>Mode</th>
          <th>Tanggal Awal</th>
          <th>Tanggal Akhir</th>
          <th>Jumlah Hari</th>
          <th>Total (kg)</th>
          <th>ARIMA</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in riwayat" :key="index">
          <td>{{ index + 1 }}</td>
          <td>{{ formatDate(item.timestamp) }}</td>
          <td>{{ item.mode }}</td>
          <td>{{ item.tanggal_mulai }}</td>
          <td>{{ item.tanggal_selesai }}</td>
          <td>{{ item.jumlah_hari }}</td>
          <td>{{ item.total_kg.toFixed(2) }} kg</td>
          <td>{{ item.order ? '(' + item.order.join(',') + ')' : '-' }}</td>
          <td>
            <button @click="lihat(item)">Lihat</button>
            <button @click="hapus(index)">Hapus</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="terpilih" class="preview">
      <h2>Detail Prediksi Terpilih</h2>
      <p><strong>Tanggal Prediksi:</strong> {{ formatDate(terpilih.timestamp) }}</p>
      <p><strong>Mode:</strong> {{ terpilih.mode }}</p>
      <p><strong>Tanggal:</strong> {{ terpilih.tanggal_mulai }} → {{ terpilih.tanggal_selesai }}</p>
      <p><strong>Total Prediksi:</strong> {{ terpilih.total_kg.toFixed(2) }} kg</p>
      <p><strong>Jumlah Hari:</strong> {{ terpilih.jumlah_hari }}</p>
      <p v-if="terpilih.order"><strong>ARIMA:</strong> ({{ terpilih.order.join(', ') }})</p>
      <p v-if="terpilih.jumlah_ayam_awal">
        <strong>Jumlah Ayam Awal (input):</strong> {{ terpilih.jumlah_ayam_awal }}
      </p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      riwayat: [],
      terpilih: null,
    }
  },
  created() {
    this.ambilRiwayat()
  },
  methods: {
    async ambilRiwayat() {
      try {
        const res = await axios.get('http://localhost:8000/riwayat')
        this.riwayat = res.data.reverse() // tampilkan terbaru di atas
      } catch (err) {
        console.error('Gagal ambil riwayat:', err)
        this.riwayat = []
      }
    },
    lihat(item) {
      this.terpilih = item
    },
    async hapus(index) {
      if (confirm('Yakin ingin menghapus riwayat ini?')) {
        this.riwayat.splice(index, 1)
        try {
          await axios.post('http://localhost:8000/riwayat', this.riwayat)
          this.terpilih = null
        } catch (e) {
          alert('Gagal menyimpan perubahan riwayat ke backend.')
        }
      }
    },
    formatDate(dateStr) {
      const d = new Date(dateStr)
      return d.toLocaleString()
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}
.title {
  font-size: 1.8rem;
  font-weight: bold;
  color: #7ca221;
  margin-bottom: 1rem;
}
.riwayat-table {
  width: 100%;
  border-collapse: collapse;
}
.riwayat-table th,
.riwayat-table td {
  border: 1px solid #ccc;
  padding: 8px 10px;
  text-align: center;
}
.riwayat-table th {
  background-color: #f5f5f5;
}
.empty {
  text-align: center;
  font-style: italic;
  color: #666;
  margin-top: 2rem;
}
button {
  margin: 2px 4px;
  padding: 5px 10px;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:hover {
  background-color: #1e40af;
}
.preview {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px dashed #ccc;
  background-color: #fafafa;
}
</style>
