<template>
  <div class="container">
    <h1 class="title">Prediksi Kebutuhan Pakan Ayam</h1>

    <div class="form-row">
      <div class="form-group">
        <label>Mode Prediksi:</label>
        <select v-model="mode" class="input">
          <option value="per_ayam">Prediksi Per Ayam</option>
          <option value="per_periode">Prediksi Per Periode</option>
        </select>
      </div>

      <div class="form-group">
        <label>Tanggal Mulai:</label>
        <input v-model="tanggal_mulai" type="date" class="input" />
      </div>

      <div class="form-group">
        <label>Tanggal Selesai:</label>
        <input v-model="tanggal_selesai" type="date" class="input" />
      </div>

      <div class="form-group" v-if="mode === 'per_ayam'">
        <label>Jumlah Ayam Awal:</label>
        <input v-model.number="jumlah_ayam_awal" type="number" class="input" min="1" />
      </div>

      <div class="form-group">
        <button @click="getPrediksi" class="btn">Tampilkan Prediksi</button>
      </div>
    </div>

    <div class="chart-container" v-if="chartData">
      <LineChart
        :labels="labels"
        :actualData="chartData.aktual"
        :predictedData="chartData.prediksi"
      />
    </div>

    <div class="summary" v-if="summary">
      <h3>Ringkasan Prediksi</h3>
      <table class="summary-table">
        <tbody>
          <tr>
            <th>Total Pakan</th>
            <td>{{ summary.total_prediksi_kg }} kg</td>
          </tr>
          <tr>
            <th>Total Karung (50kg)</th>
            <td>{{ summary.total_prediksi_karung }} karung</td>
          </tr>
          <tr v-if="mode === 'per_ayam'">
            <th>Konsumsi Harian per Ekor</th>
            <td>{{ konsumsiPerEkor }} kg/ekor/hari</td>
          </tr>
          <tr v-if="mode === 'per_periode' && summary.jumlah_ayam_diprediksi">
            <th>Jumlah Ayam yang Diprediksi</th>
            <td>{{ summary.jumlah_ayam_diprediksi }} ekor</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from "axios"
import LineChart from "../components/LineChart.vue"

export default {
  components: { LineChart },
  data() {
    return {
      mode: "per_ayam",
      tanggal_mulai: "",
      tanggal_selesai: "",
      jumlah_ayam_awal: null,
      chartData: null,
      labels: [],
      summary: null,
      konsumsiPerEkor: null,
    }
  },
  methods: {
    async getPrediksi() {
      const endpoint = this.mode === "per_ayam" ? "predict_per_ayam" : "predict_periode"

      try {
        const res = await axios.post(`http://localhost:8000/${endpoint}`, {
          tanggal_mulai: this.tanggal_mulai,
          tanggal_selesai: this.tanggal_selesai,
          jumlah_ayam_awal: this.mode === "per_ayam" ? this.jumlah_ayam_awal : undefined,
        })

        const prediksi = res.data.data_prediksi || []
        const aktual = res.data.data_aktual || []

        const semuaTanggal = [...aktual.map(a => a.x), ...prediksi.map(p => p.x)]
        const tanggalUnik = [...new Set(semuaTanggal.map(t => t.split("T")[0]))].sort()

        const actualMap = Object.fromEntries(aktual.map(a => [a.x.split("T")[0], a.y]))
        const predictedMap = Object.fromEntries(prediksi.map(p => [p.x.split("T")[0], p.y]))

        const actualData = tanggalUnik.map(label => actualMap[label] ?? null)
        const predictedData = tanggalUnik.map(label => predictedMap[label] ?? null)

        this.labels = tanggalUnik
        this.chartData = {
          aktual: actualData,
          prediksi: predictedData
        }

        this.summary = res.data.summary || {}

        if (this.mode === 'per_periode' && res.data.summary?.prediksi_jumlah_ayam) {
          this.summary.jumlah_ayam_diprediksi = res.data.summary.prediksi_jumlah_ayam
        }

        // Hitung konsumsi per ekor per hari jika perlu
        if (this.mode === 'per_ayam') {
          const totalKg = parseFloat(this.summary.total_prediksi_kg || 0)
          const jumlahHari = this.hitungJumlahHari(this.tanggal_mulai, this.tanggal_selesai)
          const jumlahAyam = parseFloat(this.jumlah_ayam_awal || 1)

          if (jumlahHari > 0 && jumlahAyam > 0) {
            const konsumsi = totalKg / jumlahHari / jumlahAyam
            this.konsumsiPerEkor = konsumsi.toFixed(4)
          } else {
            this.konsumsiPerEkor = "-"
          }
        }

      } catch (error) {
        console.error("Gagal memuat prediksi:", error)
        alert("Terjadi kesalahan saat mengambil data.")
      }
    },

    hitungJumlahHari(start, end) {
      try {
        const tglMulai = new Date(start)
        const tglSelesai = new Date(end)
        const selisih = Math.ceil((tglSelesai - tglMulai) / (1000 * 60 * 60 * 24)) + 1
        return selisih > 0 ? selisih : 0
      } catch {
        return 0
      }
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 960px;
  margin: auto;
  padding: 20px;
}
.title {
  text-align: center;
  font-size: 24px;
  margin-bottom: 20px;
}
.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  margin-bottom: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
}
.input {
  padding: 6px 10px;
  width: 180px;
}
.btn {
  margin-top: 22px;
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 14px;
  cursor: pointer;
}
.chart-container {
  margin-top: 30px;
}
.summary-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}
.summary-table th,
.summary-table td {
  border: 1px solid #ccc;
  padding: 8px 12px;
  text-align: left;
}
.summary-table th {
  background-color: #f5f5f5;
  width: 50%;
}
</style>
