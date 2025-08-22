<template>
  <div class="data-container">
    <!-- Upload CSV -->
    <div class="upload-row">
      <label class="custom-file-upload">
        <input type="file" @change="handleFileUpload" accept=".csv" />
        Pilih File CSV
      </label>
      <a :href="templateUrl" download class="download-link">Template CSV</a>
    </div>

    <!-- Preview CSV -->
    <div v-if="showPreview" class="preview-csv">
      <h3>Preview Data CSV</h3>
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
      <div class="button-group">
        <button @click="saveCsvData" :disabled="savingPreview">Simpan Data CSV</button>
        <button @click="cancelPreview" :disabled="savingPreview">Batal</button>
      </div>
    </div>

    <!-- Daftar Data Pakan -->
    <div class="csv-list-container">
      <h3>Daftar Data Pakan</h3>
      <table>
        <thead>
          <tr>
            <th>Nama File</th>
            <th>Tanggal Upload</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="dataPakan.length === 0">
            <td colspan="3" class="no-data">Belum ada data pakan.</td>
          </tr>
          <tr v-for="(row, idx) in dataPakan" :key="row.id">
            <td>{{ row.nama_file }}</td>
            <td>{{ row.tanggal }}</td>
            <td class="aksi-cell">
              <button @click="editCsv(row)">Ubah</button>
              <button @click="deleteData(row.nama_file)">Hapus</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Update CSV -->
    <div v-if="showEditModal" class="modal">
      <div class="modal-content">
        <h3>Ubah Data CSV</h3>
        <label>Nama File Baru:</label>
        <input v-model="editName" placeholder="Nama file" />

        <label>Upload File Baru (opsional):</label>
        <input type="file" @change="handleEditFile" accept=".csv" />

        <div class="button-group">
          <button @click="updateCsv" :disabled="savingEdit">Simpan</button>
          <button @click="cancelEdit" :disabled="savingEdit">Batal</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Swal from "sweetalert2";
import Papa from "papaparse";
import axios from "axios";

const templateUrl = ref("/template/template_data_pakan.csv");
const showPreview = ref(false);
const previewData = ref([]);
const previewHeaders = ref([]);
const previewFileName = ref(""); // simpan nama file asli user
const savingPreview = ref(false);
const dataPakan = ref([]);

// EDIT CSV
const showEditModal = ref(false);
const editId = ref(null);
const editName = ref("");
const editFile = ref(null);
const savingEdit = ref(false);

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  if (!token) {
    Swal.fire("Error", "Token tidak ditemukan, silakan login ulang", "error");
    throw new Error("Token tidak ditemukan");
  }
  return { Authorization: `Bearer ${token}` };
}

function loadDataPakan() {
  axios.get("/list_csv_files", { headers: getAuthHeaders() })
    .then(res => {
      dataPakan.value = res.data.files;
    })
    .catch(err => {
      console.error(err);
      Swal.fire("Error", "Gagal memuat data pakan", "error");
    });
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  previewFileName.value = file.name; // simpan nama file asli user

  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      previewData.value = results.data;
      previewHeaders.value = results.meta.fields || [];
      showPreview.value = true;
    },
    error: (err) => {
      Swal.fire("Error", "Gagal membaca file CSV: " + err.message, "error");
    }
  });
}

function saveCsvData() {
  if (previewData.value.length < 1) {
    Swal.fire("Error", "Data CSV tidak boleh kosong", "error");
    return;
  }

  // Cek nama file unik
  const namaFileBaru = previewFileName.value;
  const sudahAda = dataPakan.value.some(row => row.nama_file === namaFileBaru);
  if (sudahAda) {
    Swal.fire("Error", "Nama file sudah ada. Gunakan nama lain.", "error");
    return;
  }

  savingPreview.value = true;

  const formData = new FormData();
  const csvBlob = new Blob([Papa.unparse(previewData.value)], { type: "text/csv" });
  formData.append("file", csvBlob, namaFileBaru);

  axios.post("/upload_csv", formData, { headers: { ...getAuthHeaders(), "Content-Type": "multipart/form-data" } })
    .then(res => {
      Swal.fire("Sukses", "Data CSV berhasil disimpan", "success");
      showPreview.value = false;
      previewData.value = [];
      previewHeaders.value = [];
      previewFileName.value = "";
      loadDataPakan(); // refresh tabel
    })
    .catch(err => {
      Swal.fire("Error", err.response?.data?.error || "Gagal menyimpan data", "error");
    })
    .finally(() => savingPreview.value = false);
}

function cancelPreview() {
  showPreview.value = false;
  previewData.value = [];
  previewHeaders.value = [];
  previewFileName.value = "";
}

function deleteData(nama_file) {
  Swal.fire({
    title: "Yakin ingin menghapus?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Ya, hapus",
    cancelButtonText: "Batal"
  }).then(result => {
    if (result.isConfirmed) {
      axios.delete(`/delete_csv/${encodeURIComponent(nama_file)}`, { headers: getAuthHeaders() })
        .then(() => {
          Swal.fire("Berhasil", "Data pakan berhasil dihapus", "success");
          loadDataPakan(); // refresh tabel
        })
        .catch(err => {
          Swal.fire("Error", "Gagal menghapus data", "error");
        });
    }
  });
}

// =================== EDIT CSV ===================
function editCsv(row) {
  editId.value = row.id;
  editName.value = row.nama_file;
  editFile.value = null;
  showEditModal.value = true;
}

function handleEditFile(event) {
  editFile.value = event.target.files[0];
}

function cancelEdit() {
  showEditModal.value = false;
  editId.value = null;
  editName.value = "";
  editFile.value = null;
}

function updateCsv() {
  if (!editId.value) return;

  const namaBaru = editName.value.trim();
  const sudahAda = dataPakan.value.some(row => row.nama_file === namaBaru && row.id !== editId.value);
  if (sudahAda) {
    Swal.fire("Error", "Nama file sudah ada. Gunakan nama lain.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("new_name", namaBaru);
  if (editFile.value) {
    formData.append("file", editFile.value);
  }

  savingEdit.value = true;

  axios.put(`/update_csv/${editId.value}`, formData, { headers: { ...getAuthHeaders(), "Content-Type": "multipart/form-data" } })
    .then(res => {
      Swal.fire("Sukses", "Data CSV berhasil diperbarui", "success");
      cancelEdit();
      loadDataPakan(); // refresh tabel
    })
    .catch(err => {
      console.error(err);
      Swal.fire("Error", "Gagal memperbarui data", "error");
    })
    .finally(() => savingEdit.value = false);
}

onMounted(() => {
  loadDataPakan();
});
</script>

<style scoped>
.data-container {
  width: 100%;
  max-width: 1400px;
  margin: 2rem auto;
  padding: 1rem 2rem;
  box-sizing: border-box;
}

.upload-row {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.custom-file-upload {
  display: inline-block;
  padding: 0.6rem 1.2rem;
  background-color: #2d6a2d;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.custom-file-upload input[type="file"] {
  display: none;
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
  table-layout: auto;
}

th,
td {
  border: 1px solid #ccc;
  padding: 0.6rem;
  text-align: center;
}

.no-data {
  color: #888;
  font-style: italic;
}

.aksi-cell button {
  min-width: 80px;
  padding: 0.4rem 0.8rem;
  background-color: #2d6a2d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 4px;
}

.aksi-cell button:hover {
  background-color: #1f4f1f;
}

.preview-csv {
  margin-top: 2rem;
}

.preview-csv table input {
  width: 100px;
  text-align: center;
}

.button-group {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-start;
  gap: 1rem;
}

.button-group button {
  padding: 0.5rem 1rem;
  font-weight: bold;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  background-color: #2d6a2d;
  color: white;
}

.button-group button:hover {
  background-color: #1f4f1f;
}

/* Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 6px;
  width: 400px;
  max-width: 90%;
}

.modal-content input {
  width: 100%;
  margin-bottom: 1rem;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}
</style>
