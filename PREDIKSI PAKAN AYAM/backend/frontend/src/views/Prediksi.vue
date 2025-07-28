<template>
  <div class="container">
    <h1 class="title">Prediksi Kebutuhan Pakan Ayam</h1>

    <!-- Form Input -->
    <div class="form-row">
      <div class="form-group">
        <label>Mode Prediksi:</label>
        <select v-model="mode" class="input">
          <option value="per_ayam">Prediksi Per Ayam</option>
          <option value="per_periode">Prediksi Harian</option>
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
        <input v-model.number="jumlah_ayam_awal" type="number" class="input" min="1" placeholder="wajib diisi" />
      </div>

      <div class="form-group">
        <label>Tipe Grafik:</label>
        <select v-model="chartType" class="input">
          <option value="line">Line</option>
          <option value="bar">Bar</option>
          <option value="area">Area</option>
        </select>
      </div>

      <div class="form-group">
        <label>Data CSV:</label>
        <select v-model="file_id" class="input">
          <option :value="null">Data Default</option>
          <option v-for="file in files" :key="file.id" :value="file.id">
            {{ file.fileName }} - {{ file.uploadDate }}
          </option>
        </select>
      </div>

      <div class="form-group full-width">
        <button @click="getPrediksi" class="btn">Tampilkan Prediksi</button>
      </div>
    </div>

    <!-- Grafik -->
    <div class="chart-container" v-if="chartData">
      <component :is="selectedChartComponent" :labels="labels" :actualData="chartData.aktual"
        :predictedData="chartData.prediksi" :periodeEdges="periodeEdges" />
    </div>


    <!-- Ringkasan -->
    <div class="summary" v-if="summary">
      <h3>Ringkasan Prediksi</h3>
      <table class="summary-table">
        <tbody>
          <tr>
            <th>Rata-rata Error (MAPE)</th>
            <td>
              <span :style="{ color: mapeWarna, fontWeight: 'bold' }">
                {{ mape }}%
              </span>
              ➜ Akurasi:
              <span :style="{ color: mapeWarna, fontWeight: 'bold' }">
                {{ mapeInterpretasi }}
              </span>
            </td>
          </tr>
          <tr>
            <th>Total Pakan</th>
            <td>{{ Math.round(summary.total_prediksi_kg).toLocaleString('id-ID') }} kg</td>
          </tr>
          <tr>
            <th>Total Karung (50kg)</th>
            <td>{{ Math.ceil(summary.total_prediksi_karung).toLocaleString('id-ID') }} karung</td>
          </tr>
          <tr v-if="mode === 'per_ayam' && summary.rata_per_ayam_kg_per_hari">
            <th>Konsumsi Harian per Ekor</th>
            <td>{{ summary.rata_per_ayam_kg_per_hari }} kg/ekor/hari</td>
          </tr>
          <tr v-if="mode === 'per_ayam' && summary.jumlah_ayam_awal">
            <th>Jumlah Ayam Awal</th>
            <td>{{ summary.jumlah_ayam_awal.toLocaleString('id-ID') }} ekor</td>
          </tr>
          <tr v-if="mode === 'per_ayam' && summary.perkiraan_akhir_ayam">
            <th>Perkiraan Ayam Hidup di Akhir</th>
            <td>{{ summary.perkiraan_akhir_ayam?.toLocaleString('id-ID') }} ekor</td>
          </tr>
          <tr v-if="mode === 'per_periode' && summary.prediksi_jumlah_ayam">
            <th>Jumlah Ayam yang Diprediksi</th>
            <td>{{ summary.prediksi_jumlah_ayam }} ekor</td>
          </tr>
          <tr v-if="summary.rata_mati_per_hari !== undefined">
            <th>Rata-rata Ayam Mati per Hari</th>
            <td>{{ Math.round(summary.rata_mati_per_hari || 0).toLocaleString('id-ID') }} ekor</td>
          </tr>
          <tr v-if="summary.durasi_hari">
            <th>Durasi (Hari)</th>
            <td>{{ summary.durasi_hari }} hari</td>
          </tr>
          <tr v-if="summary.catatan">
            <th>Catatan</th>
            <td>{{ summary.catatan }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from "axios"
import Swal from "sweetalert2"
import LineChart from "@/components/LineChart.vue"
import BarChart from "@/components/BarChart.vue"
import AreaChart from "@/components/AreaChart.vue"

export default {
  computed: {
    selectedChartComponent() {
      if (this.chartType === "line") return "LineChart"
      if (this.chartType === "bar") return "BarChart"
      if (this.chartType === "area") return "AreaChart"
      return "LineChart"
    },

    isRiwayatMode() {
      return this.$route.name === 'RiwayatGrafik'
    },

    mape() {
      if (!this.chartData || !Array.isArray(this.chartData.aktual) || !Array.isArray(this.chartData.prediksi)) {
        return "0.00";
      }

      const actualData = this.chartData.aktual.filter(d => d && d.x != null && d.kg != null);
      const predictedData = this.chartData.prediksi.filter(d => d && d.x != null && d.kg != null);

      let totalError = 0;
      let n = 0;

      for (let i = 0; i < predictedData.length; i++) {
        const pred = predictedData[i];
        if (!pred || pred.x == null || pred.kg == null) continue;

        const actual = actualData.find(d => d && d.x === pred.x && d.kg != null);
        if (actual && actual.kg > 0) {
          const error = Math.abs((pred.kg - actual.kg) / actual.kg);
          totalError += error;
          n++;
        }
      }

      const hasil = n > 0 ? (totalError / n) * 100 : 0;

      console.log("MAPE calculation → n:", n, "totalError:", totalError, "MAPE:", hasil);
      console.log("Actual Data:", actualData);
      console.log("Predicted Data:", predictedData);

      return hasil.toFixed(2); // return selalu aman string "0.00" dst
    },


    mapeInterpretasi() {
      const nilai = this.mape;
      if (nilai < 10) return 'Sangat Baik';
      else if (nilai < 20) return 'Baik';
      else if (nilai < 50) return 'Cukup';
      else return 'Buruk';
    },

    mapeWarna() {
      const nilai = this.mape;
      if (nilai < 10) return 'green';
      else if (nilai < 20) return 'limegreen';
      else if (nilai < 50) return 'orange';
      else return 'red';
    }
  },

  components: { LineChart, BarChart, AreaChart },
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
      periodeEdges: [],
      chartType: "line",
      files: [],
      predictedData: [],
      actualData: [],
    }
  },
  async mounted() {
    this.files = []
    try {
      const res = await axios.get("http://localhost:8000/list_csv_files")
      this.files = res.data.files || []
    } catch (err) {
      console.error("Gagal memuat daftar file CSV:", err)
    }

    const id = this.$route.params.id
    if (id !== undefined) {
      const riwayat = JSON.parse(localStorage.getItem("riwayatPrediksi") || "[]")
      const item = riwayat[parseInt(id)]
      if (item) {
        this.mode = item.mode || "per_ayam"
        this.tanggal_mulai = item.tanggal_mulai
        this.tanggal_selesai = item.tanggal_selesai
        this.jumlah_ayam_awal = item.jumlahAyam ?? 0  // Gunakan fallback jika null/undefined

        // Validasi khusus: pastikan jumlah ayam terisi jika mode per_ayam
        if (this.mode === "per_ayam" && (!this.jumlah_ayam_awal || this.jumlah_ayam_awal < 1)) {
          Swal.fire({
            icon: "warning",
            title: "Data Tidak Lengkap",
            text: "Jumlah ayam tidak tersedia di riwayat, mohon isi secara manual.",
          })
          return
        }

        await this.getPrediksi(false) // ambil prediksi tanpa simpan lagi
      }
    }
  },

  methods: {
    async getPrediksi(simpan = true) {
      if (!this.isRiwayatMode && this.mode === "per_ayam" && (!this.jumlah_ayam_awal || this.jumlah_ayam_awal < 1)) {
        Swal.fire({
          icon: "warning",
          title: "Jumlah ayam awal wajib diisi",
          text: "Mohon isi jumlah ayam awal minimal 1",
        });
        return;
      }

      if (!this.tanggal_mulai || !this.tanggal_selesai) {
        Swal.fire({
          icon: "warning",
          title: "Tanggal belum lengkap",
          text: "Mohon isi tanggal mulai dan tanggal selesai",
        });
        return;
      }

      const endpoint = this.mode === "per_ayam" ? "predict_per_ayam" : "predict_periode"

      try {
        const payload = {
          tanggal_mulai: this.tanggal_mulai,
          tanggal_selesai: this.tanggal_selesai,
          ...(this.mode === "per_ayam" ? { jumlah_ayam_awal: this.jumlah_ayam_awal } : {}),
          ...(this.file_id ? { file_id: this.file_id } : {})
        }

        console.log("Payload yang dikirim:", payload);


        const res = await axios.post(`http://localhost:8000/${endpoint}`, payload)


        const prediksi = res.data.data_prediksi || []
        const aktual = res.data.data_aktual || []

        console.log("Respon dari backend:", res.data)
        console.log("Prediksi:", prediksi)
        console.log("Aktual:", aktual)


        const semuaTanggal = [...aktual.map(a => a.x), ...prediksi.map(p => p.x)]
        const tanggalUnik = [...new Set(semuaTanggal.map(t => t.split("T")[0]))].sort()

        const actualMap = Object.fromEntries(aktual.map(a => [a.x.split("T")[0], a.y]))
        const predictedMap = Object.fromEntries(prediksi.map(p => [p.x.split("T")[0], p.y]))

        const actualData = tanggalUnik.map(label => actualMap[label] ?? null)
        const predictedData = tanggalUnik.map(label => predictedMap[label] ?? null)

        this.labels = tanggalUnik

        const periodeEdges = []
        for (let i = 0; i < tanggalUnik.length; i += 7) {
          periodeEdges.push(i)
          const akhir = Math.min(i + 6, tanggalUnik.length - 1)
          periodeEdges.push(akhir)
        }
        this.periodeEdges = periodeEdges

        this.chartData = {
          aktual: actualData,
          prediksi: predictedData,
        }

        this.summary = res.data.summary || {}

        if (simpan && this.summary?.total_prediksi_kg) {
          const tanggal = new Date().toLocaleDateString("id-ID")

          const jumlahAyam = this.mode === "per_ayam"
            ? this.jumlah_ayam_awal
            : this.summary.prediksi_jumlah_ayam

          const prediksiPakan = this.summary.total_prediksi_kg
          this.simpanRiwayat(tanggal, prediksiPakan)
        }
      }
      catch (err) {
        console.error("Gagal memuat prediksi", err);
        if (err.response && err.response.data) {
          console.error("Error detail:", err.response.data);
          Swal.fire({
            icon: "error",
            title: "Gagal memuat prediksi",
            text: err.response.data.message || "Terjadi kesalahan.",
          });
        } else {
          Swal.fire({
            icon: "error",
            title: "Kesalahan",
            text: "Terjadi kesalahan saat mengambil data.",
          });
        }
      }
    },

    simpanRiwayat(tanggal, prediksiPakan) {
      const durasi = this.tanggal_mulai && this.tanggal_selesai
        ? Math.ceil((new Date(this.tanggal_selesai) - new Date(this.tanggal_mulai)) / (1000 * 60 * 60 * 24)) + 1
        : 0

      const asalData = this.file_id === null ? 'default' : 'upload'

      // ⬇️ Ambil nama file CSV jika asal upload
      let namaFile = null
      if (asalData === 'upload') {
        const fileObj = this.files.find(f => f.id === this.file_id)
        namaFile = fileObj ? fileObj.fileName : 'Tidak Diketahui'
      }

      const data = {
        tanggal,
        prediksiPakan,
        mode: this.mode,
        tanggal_mulai: this.tanggal_mulai,
        tanggal_selesai: this.tanggal_selesai,
        durasi: durasi,
        jumlahAyam: this.jumlah_ayam_awal,
        asalData: asalData,
        namaFile: namaFile,
      mape: parseFloat(this.mape)
      }

      const riwayat = JSON.parse(localStorage.getItem("riwayatPrediksi") || "[]")
      riwayat.push(data)
      localStorage.setItem("riwayatPrediksi", JSON.stringify(riwayat))
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 900px;
  margin: 0 auto;
  padding-top: 0px;
}

.title {
  text-align: center;
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #0a660a;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  align-items: flex-end;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  min-width: 140px;
  max-width: 180px;
  flex: 1 1 auto;
}

.full-width {
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
}

.form-group label {
  margin-bottom: 4px;
  font-weight: 500;
  font-size: 13px;
}

.input {
  padding: 6px 8px;
  font-size: 13px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.btn {
  padding: 8px 14px;
  font-size: 13px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.chart-container {
  margin-top: 10px;
}

.summary {
  margin-top: 32px;
  text-align: center;
}

.summary-table {
  margin: 0 auto;
  margin-top: 12px;
  border-collapse: collapse;
  width: 90%;
  max-width: 900px;
}

.summary-table th,
.summary-table td {
  border: 1px solid #ccc;
  padding: 6px 10px;
  font-size: 13px;
  text-align: left;
}

.summary-table th {
  background-color: #f5f5f5;
  width: 60%;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }

  .form-group,
  .full-width {
    max-width: 100%;
  }

  .btn {
    width: 100%;
  }

  .summary-table {
    font-size: 12px;
  }
}
</style>