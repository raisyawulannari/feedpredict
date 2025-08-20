<template>
  <div class="data-container">
    <!-- Upload & Download CSV -->
    <div class="upload-template-row">
      <label class="custom-file-upload">
        <input type="file" @change="handleFileUpload" accept=".csv" />
        Pilih File CSV
      </label>
      <div class="download-buttons">
        <a :href="templateUrl" download="template_data_pakan.csv" class="download-link">
          Template CSV
        </a>
        <a href="/template/template_data_pakan.xlsx" download class="download-link">
          Template Excel
        </a>
      </div>
    </div>

    <!-- Tabel Daftar File CSV -->
    <div class="csv-list-container">
      <table>
        <thead>
          <tr>
            <th>Tanggal Upload</th>
            <th>Nama File</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="fileList.length === 0">
            <td colspan="3" class="no-file">Belum ada file CSV yang diupload.</td>
          </tr>
          <tr v-for="(file, idx) in fileList" :key="idx">
            <td>{{ file.uploadDate }}</td>
            <td>{{ file.fileName }}</td>
            <td class="aksi-cell">
              <button @click="editFile(idx)">Preview / Update</button>
              <button @click="deleteFile(idx)">Hapus</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Preview CSV -->
    <div v-if="showPreview" class="preview-csv">
      <div class="button-group">
        <button @click="savePreviewData" :disabled="savingPreview">
          {{ updatingIndex !== null ? 'Simpan Update' : 'Simpan Perubahan' }}
        </button>
        <button @click="cancelPreview" :disabled="savingPreview">Batal</button>
      </div>

      <table v-if="previewData.length > 0">
        <thead>
          <tr>
            <th v-for="(header, idx) in previewHeaders" :key="idx">{{ header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ridx) in previewData" :key="ridx">
            <td v-for="header in previewHeaders" :key="header">
              <input v-model="previewData[ridx][header]" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Swal from "sweetalert2";
import Papa from "papaparse";

const fileList = ref([]);
const showPreview = ref(false);
const previewHeaders = ref([]);
const previewData = ref([]);
const savingPreview = ref(false);
const updatingIndex = ref(null);
const currentUploadFileName = ref("");
const currentUploadDate = ref("");
const templateUrl = ref("/template/template_data_pakan.csv");

// --- Load dari localStorage saat mounted ---
function loadCsvFiles() {
  const saved = localStorage.getItem("csvFiles");
  if (saved) fileList.value = JSON.parse(saved);
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  currentUploadFileName.value = file.name;
  currentUploadDate.value = new Date().toISOString().split("T")[0];

  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      previewData.value = results.data;
      previewHeaders.value = results.meta.fields || [];
      showPreview.value = true;
      updatingIndex.value = null;
    },
    error: (err) => {
      Swal.fire("Error", "Gagal membaca file CSV: " + err.message, "error");
    }
  });
}

// --- Simpan preview ke fileList + localStorage + untuk prediksi ---
function savePreviewData() {
  if (previewData.value.length === 0) {
    Swal.fire("Error", "Tidak ada data untuk disimpan", "error");
    return;
  }

  savingPreview.value = true;
  try {
    const newFile = {
      id: updatingIndex.value !== null ? fileList.value[updatingIndex.value].id : Date.now(),
      fileName: currentUploadFileName.value,
      uploadDate: currentUploadDate.value,
      dataCSV: JSON.parse(JSON.stringify(previewData.value))
    };

    if (updatingIndex.value !== null) {
      fileList.value[updatingIndex.value] = newFile;
    } else {
      fileList.value.push(newFile);
    }

    // Simpan ke localStorage
    localStorage.setItem("csvFiles", JSON.stringify(fileList.value));
    // Simpan juga CSV terakhir dipilih untuk prediksi
    localStorage.setItem("currentCSV", JSON.stringify(newFile.dataCSV));

    Swal.fire("Sukses", "Data CSV berhasil disimpan dan ditampilkan", "success");
    cancelPreview();
  } catch (error) {
    Swal.fire("Error", error.message, "error");
  } finally {
    savingPreview.value = false;
  }
}

function cancelPreview() {
  showPreview.value = false;
  previewData.value = [];
  previewHeaders.value = [];
  updatingIndex.value = null;
  currentUploadFileName.value = "";
  currentUploadDate.value = "";
}

function editFile(idx) {
  const file = fileList.value[idx];
  previewData.value = JSON.parse(JSON.stringify(file.dataCSV));
  previewHeaders.value = Object.keys(previewData.value[0] || {});
  currentUploadFileName.value = file.fileName;
  currentUploadDate.value = file.uploadDate;
  updatingIndex.value = idx;
  showPreview.value = true;

  // Update CSV terakhir dipilih untuk prediksi
  localStorage.setItem("currentCSV", JSON.stringify(file.dataCSV));
}

function deleteFile(idx) {
  Swal.fire({
    title: "Yakin ingin menghapus file ini?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Ya, hapus",
    cancelButtonText: "Batal"
  }).then(result => {
    if (result.isConfirmed) {
      fileList.value.splice(idx, 1);
      localStorage.setItem("csvFiles", JSON.stringify(fileList.value));
      Swal.fire("Berhasil", "File CSV berhasil dihapus", "success");
    }
  });
}

onMounted(() => {
  loadCsvFiles();
});
</script>


<style scoped>
.data-container {
  padding: 1rem;
  max-width: 800px;
  margin: 2rem auto;
  text-align: center;
}

.upload-template-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.custom-file-upload {
  display: inline-block;
  padding: 0.6rem 1.2rem;
  background-color: #5d2d1d;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.custom-file-upload input[type="file"] {
  display: none;
}

.download-buttons {
  display: flex;
  gap: 1rem;
}

.download-link {
  color: #0a660a;
  font-weight: bold;
  text-decoration: underline;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

td, th {
  border: 1px solid #ccc;
  padding: 0.6rem;
  text-align: center;
}

.no-file {
  color: #888;
  font-style: italic;
}

.aksi-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
}

.aksi-cell button {
  min-width: 80px;
  padding: 0.4rem 0.8rem;
}
</style>
