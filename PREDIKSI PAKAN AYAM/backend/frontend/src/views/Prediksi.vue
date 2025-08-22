<template>
  <div class="container">
    <h1 class="title">Prediksi Kebutuhan Pakan Ayam</h1>

    <!-- Form Input -->
    <div class="form-row">
      <div class="form-group">
        <label>Mode Prediksi:</label>
        <select v-model="mode" class="input">
          <option value="per_ayam">Prediksi Per Ayam</option>
          <option value="per_periode">Prediksi Periode</option>
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
<div class="summary">
  <h3>Ringkasan Prediksi</h3>

  <template v-if="summary && summary.total_prediksi_kg">
    <table class="summary-table">
      <tbody>
        <tr>
          <th>Rata-rata Error (MAPE)</th>
          <td>
            <span :style="{ color: mapeWarna, fontWeight: 'bold' }">{{ mape }}%</span>
            ➜ Akurasi:
            <span :style="{ color: mapeWarna, fontWeight: 'bold' }">{{ mapeInterpretasi }}</span>
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

    <div class="download-buttons">
      <button class="btn" @click="downloadCSV">Download CSV</button>
      <button class="btn" @click="downloadPDF">Download PDF</button>
    </div>
  </template>

  <div v-else class="text-gray-500 italic text-center p-4">
    Belum ada hasil prediksi, silakan pilih mode lalu klik <b>Tampilkan Prediksi</b>.
  </div>
</div>

  </div>
</template>

<script>
import axios from "axios";
import Swal from "sweetalert2";
import LineChart from "@/components/LineChart.vue";
import BarChart from "@/components/BarChart.vue";
import AreaChart from "@/components/AreaChart.vue";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default {
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
      periodeEdges: [],
      chartType: "line",
      files: [],
      predictedDetail: [],
    };
  },
  computed: {
    selectedChartComponent() {
      return this.chartType === "bar"
        ? "BarChart"
        : this.chartType === "area"
          ? "AreaChart"
          : "LineChart";
    },
    mape() {
      return this.summary?.mape?.toFixed(2) ?? "0.00";
    },
    mapeInterpretasi() {
      const nilai = parseFloat(this.mape);
      if (nilai < 10) return "Sangat Baik";
      else if (nilai < 20) return "Baik";
      else if (nilai < 50) return "Cukup";
      return "Buruk";
    },
    mapeWarna() {
      const nilai = parseFloat(this.mape);
      if (nilai < 10) return "green";
      else if (nilai < 20) return "limegreen";
      else if (nilai < 50) return "orange";
      return "red";
    },
  },
  async mounted() {
    const token = localStorage.getItem("token");
    if (!token) {
      Swal.fire("Belum Login", "Silakan login terlebih dahulu", "warning").then(() => {
        this.$router.push("/login");
      });
      return;
    }

    try {
      const res = await api.get("/list_csv_files");
      this.files = res.data.files || [];
    } catch (err) {
      console.error("Gagal memuat daftar file CSV:", err);
      localStorage.removeItem("token");
      Swal.fire("Gagal", "Token tidak valid atau CSV gagal dimuat", "error").then(() => {
        this.$router.push("/login");
      });
      return;
    }

    const riwayat_id = this.$route.query.riwayat_id || this.$route.params.id;
    const isAdmin = localStorage.getItem("role") === "admin";
    if (riwayat_id) this.loadRiwayat(riwayat_id, isAdmin);
  },

  methods: {
    async loadRiwayat(id, isAdmin = false) {
      try {
        const endpoint = isAdmin ? `/api/admin/riwayat/${id}/detail` : `/riwayat/${id}/detail`;
        const res = await api.get(endpoint);
        const riwayat = res.data;

        // --- Set form ---
        this.mode = riwayat.mode || "per_ayam";
        this.tanggal_mulai = riwayat.tanggal_mulai;
        this.tanggal_selesai = riwayat.tanggal_selesai;
        this.jumlah_ayam_awal = riwayat.jumlah_ayam_awal ?? 0;

        // --- Data prediksi dan aktual ---
        const aktual = riwayat.data_aktual || [];
const prediksi = riwayat.prediksi || [];

// --- Semua tanggal unik ---
const semuaTanggal = Array.from(new Set([
  ...aktual.map(a => a.x.split("T")[0]),
  ...prediksi.map(p => p.x.split("T")[0])
])).sort();

// --- Mapping aktual dan prediksi ---
const actualMap = {};
aktual.forEach(a => {
  const date = a.x.split("T")[0];
  actualMap[date] = a.kg ?? a.y ?? 0;  // pastikan ada fallback
});

const predictedMap = {};
prediksi.forEach(p => {
  const date = p.x.split("T")[0];
  predictedMap[date] = p.y ?? 0;
});

// --- Chart Data ---
this.labels = semuaTanggal;
this.chartData = {
  aktual: semuaTanggal.map(d => actualMap[d] ?? null),  // pakai null biar garis putus jika kosong
  prediksi: semuaTanggal.map(d => predictedMap[d] ?? null)
};


        // --- Detail prediksi untuk tabel CSV/PDF ---
        this.predictedDetail = semuaTanggal.map(date => {
          const pred = prediksi.find(p => p.x.split("T")[0] === date);
          return {
            date,
            value: pred?.y ?? 0,
            karung: Math.ceil((pred?.y ?? 0) / 50)
          };
        });


        // --- Periode edges (highlight per minggu) ---
        const periodeEdges = [];
        for (let i = 0; i < semuaTanggal.length; i += 7) {
          periodeEdges.push(i);
          periodeEdges.push(Math.min(i + 6, semuaTanggal.length - 1));
        }
        this.periodeEdges = periodeEdges;

        // --- Summary ---
        this.summary = riwayat.summary || {};

      } catch (err) {
        console.error("Gagal ambil detail riwayat:", err);
        if (err.response?.status === 401) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        } else {
          Swal.fire("Gagal", "Tidak bisa memuat detail riwayat", "error");
        }
      }
    },

    async getPrediksi(simpan = true) {
  // --- Validasi form ---
  if (!this.tanggal_mulai || !this.tanggal_selesai) {
    return Swal.fire("Tanggal belum lengkap", "Mohon isi tanggal mulai dan selesai", "warning");
  }

  if (this.mode === "per_ayam" && (!this.jumlah_ayam_awal || this.jumlah_ayam_awal < 1)) {
    return Swal.fire("Jumlah ayam wajib diisi", "Minimal 1 ayam", "warning");
  }

  if (new Date(this.tanggal_selesai) < new Date(this.tanggal_mulai)) {
    return Swal.fire("Tanggal salah", "Tanggal selesai tidak boleh sebelum tanggal mulai", "warning");
  }

  try {
    const endpoint = this.mode === "per_ayam" ? "/predict_per_ayam" : "/predict_periode";

    // --- Payload untuk backend ---
    const payload = {
      tanggal_mulai: this.tanggal_mulai,
      tanggal_selesai: this.tanggal_selesai,
      file_id: this.file_id != null ? String(this.file_id) : "default", // pastikan string
    };

    if (this.mode === "per_ayam") {
      payload.jumlah_ayam_awal = this.jumlah_ayam_awal ?? 1;
    }

    console.log("Payload prediksi:", payload);

    const res = await api.post(endpoint, payload);

    const prediksi = res.data.data_prediksi || [];
    const aktual = res.data.data_aktual || [];
    const apiSummary = res.data.summary || {};

    // --- Semua tanggal unik ---
    const semuaTanggal = Array.from(
      new Set([...aktual.map(a => a.x.split("T")[0]), ...prediksi.map(p => p.x.split("T")[0])])
    ).sort();

    // --- Mapping data untuk chart ---
    const actualMap = Object.fromEntries(
      aktual.map(a => [a.x.split("T")[0], a.kg ?? a.y ?? 0])
    );
    const predictedMap = Object.fromEntries(
      prediksi.map(p => [p.x.split("T")[0], p.y ?? 0])
    );

    this.labels = semuaTanggal;
    this.chartData = {
      aktual: semuaTanggal.map(d => actualMap[d] ?? null),
      prediksi: semuaTanggal.map(d => predictedMap[d] ?? null)
    };

    // --- Detail prediksi untuk CSV/PDF ---
    this.predictedDetail = semuaTanggal.map(date => {
      const pred = prediksi.find(p => p.x.split("T")[0] === date);
      return {
        date,
        value: pred?.y ?? 0,
        karung: Math.ceil((pred?.y ?? 0) / 50)
      };
    });

    // --- Periode edges (highlight per minggu) ---
    const periodeEdges = [];
    for (let i = 0; i < semuaTanggal.length; i += 7) {
      periodeEdges.push(i);
      periodeEdges.push(Math.min(i + 6, semuaTanggal.length - 1));
    }
    this.periodeEdges = periodeEdges;

    // --- Summary disesuaikan per mode ---
    this.summary = {
      ...apiSummary,
      jumlah_ayam_awal: this.mode === 'per_ayam' ? apiSummary.jumlah_ayam_awal : undefined,
      perkiraan_akhir_ayam: this.mode === 'per_ayam' ? apiSummary.perkiraan_akhir_ayam : undefined,
      rata_per_ayam_kg_per_hari: this.mode === 'per_ayam' ? apiSummary.konsumsi_harian_per_ekor : undefined,
      prediksi_jumlah_ayam: this.mode === 'per_periode' ? apiSummary.prediksi_jumlah_ayam : undefined,
      catatan: apiSummary.catatan || ""
    };

    // --- Simpan riwayat backend jika valid ---
    if (simpan && this.summary?.total_prediksi_kg) {
      await this.simpanRiwayatBackend();
    }

  } catch (err) {
    console.error("Gagal memuat prediksi:", err);
    const msg = err.response?.data?.detail || err.response?.data?.message || "Gagal memuat prediksi";
    Swal.fire("Error", typeof msg === "string" ? msg : JSON.stringify(msg), "error");
  }
},

    async simpanRiwayatBackend() {
  try {
    const payload = {
      tanggal_mulai: this.tanggal_mulai,
      tanggal_selesai: this.tanggal_selesai,
      mode_prediksi: this.mode, // tambahkan ini
      jumlah_ayam_awal: this.mode === "per_ayam" ? this.jumlah_ayam_awal || 1 : null,
      file_id: this.file_id || "default",
      prediksi: this.predictedDetail, // data prediksi per tanggal
      total_karung: this.summary?.total_prediksi_karung || 0,
      data_aktual: this.chartData?.aktual || null,
      activity: `Prediksi ${this.mode} dari ${this.tanggal_mulai} sampai ${this.tanggal_selesai}` // log sederhana
    };

    await api.post("/riwayat", payload);
  } catch (err) {
    console.error("Gagal simpan riwayat:", err);
  }
},

    downloadCSV() {
      const rows = this.predictedDetail.map(d => [d.date, d.value, d.karung]);
      let csvContent = "data:text/csv;charset=utf-8,Date,Prediksi (kg),Karung (50kg)\n";
      rows.forEach(r => { csvContent += r.join(",") + "\n"; });
      const link = document.createElement("a");
      link.setAttribute("href", encodeURI(csvContent));
      link.setAttribute("download", "prediksi.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    downloadPDF() {
      if (!this.tanggal_mulai || !this.tanggal_selesai) {
        return Swal.fire("Tanggal belum lengkap", "Mohon isi tanggal mulai dan selesai", "warning");
      }

      if (!this.predictedDetail || this.predictedDetail.length === 0) {
        return Swal.fire("Data kosong", "Prediksi belum tersedia, tampilkan prediksi terlebih dahulu", "warning");
      }

      // Pastikan value terisi dengan angka
      const pdfData = this.predictedDetail.map(d => ({
        date: d.date,
        value: Number(d.value ?? 0)
      }));

      api.post("/download-prediksi-pdf", {
        predicted_detail: pdfData,
        summary: this.summary,
        tanggal_mulai: this.tanggal_mulai,
        tanggal_selesai: this.tanggal_selesai
      }, { responseType: "blob" })
        .then(res => {
          const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", "prediksi.pdf");
          document.body.appendChild(link);
          link.click();
          link.remove();
        })
        .catch(err => {
          console.error("Gagal download PDF:", err);
          Swal.fire("Error", "Gagal download PDF", "error");
        });
    }



  },
};
</script>

<style scoped>
.container {
  max-width: 1400px; 
  margin: 0 auto;
  padding: 20px 40px; 
  margin-top: 0%;
  text-align: center;
}

.title {
  text-align: center;
  font-size: 26px;
  font-weight: bold;
  margin-bottom: 20px;

  background: linear-gradient(90deg, #2e7d32, #66bb6a);

  /* standar property */
  background-clip: text;

  /* prefix untuk Chrome/Safari */
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;

  /* fallback kalau gradient tidak jalan */
  color: #2e7d32;
}


/* Form */
.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  align-items: flex-end;
  margin-bottom: 28px;
  background: #e8f5e9;
  border: 1px solid #436644;
  border-radius: 10px;
  padding: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  min-width: 150px;
  max-width: 200px;
  flex: 1 1 auto;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: 600;
  font-size: 14px;
  color: #2e7d32;
}

/* Input & select */
.input {
  padding: 8px 10px;
  font-size: 14px;
  border: 1px solid #a5d6a7;
  border-radius: 6px;
  outline: none;
  transition: 0.3s;
}

.input:focus {
  border-color: #2e7d32;
  box-shadow: 0 0 4px rgba(46, 125, 50, 0.5);
}

/* Button hijau */
.btn {
  padding: 10px 16px;
  font-size: 14px;
  background: linear-gradient(135deg, #2e7d32, #43a047);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: 0.3s;
}

.btn:hover {
  background: linear-gradient(135deg, #1b5e20, #2e7d32);
}

/* Grafik */
.chart-container {
  margin-top: 20px;
}

/* Summary */
.summary {
  margin-top: 32px;
  text-align: center;
  padding: 16px;
  background: #e8f5e9;
  border: 1px solid #436644;
  border-radius: 10px;
}

.summary h3 {
  color: #2e7d32;
}

.summary-table {
  margin: 0 auto;
  margin-top: 12px;
  border-collapse: collapse;
  width: 100%;       
  max-width: 100%;   
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}


.summary-table td {
  border: 1px solid #333;
  padding: 8px 10px;
  font-size: 16px;
  text-align: left;
}

.summary-table th {
  background-color: #e8f5e9;
  border: 1px solid #333;
  color: #1b5e20;
  width: 55%;
}

/* Download buttons */
.download-buttons {
  margin-top: 18px;
  display: flex;
  gap: 14px;
  justify-content: center;
}

.download-buttons .btn {
  background: #43a047;
}

.download-buttons .btn:hover {
  background: #2e7d32;
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

