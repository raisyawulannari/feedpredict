<template>
  <div class="data-container">
    <!-- Baris untuk Upload File dan Download Template -->
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

    <div v-if="showPreview" class="button-group">
      <button @click="savePreviewData" :disabled="savingPreview">
        {{ updatingIndex !== null ? 'Simpan Update' : 'Simpan Perubahan' }}
      </button>
      <button @click="cancelPreview" :disabled="savingPreview">Batal</button>
    </div>

    <!-- Preview tabel data CSV yg diupload -->
    <table v-if="showPreview && previewData.length > 0">
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

    <!-- Tabel daftar file yang sudah diupload -->
    <table v-if="fileList.length > 0">
      <thead>
        <tr>
          <th>Tanggal Upload</th>
          <th>Nama File</th>
          <th>Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(file, idx) in fileList" :key="idx">
          <td>{{ file.uploadDate }}</td>
          <td>{{ file.fileName }}</td>
          <td>
            <button @click="editFile(idx)">Update</button>
            <button @click="deleteFile(idx)">Hapus</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
// (Semua kode JavaScript tetap sama, tidak diubah)
import { ref, onMounted } from "vue";
import Swal from "sweetalert2";

const fileList = ref([]);
const showPreview = ref(false);
const previewHeaders = ref([]);
const previewData = ref([]);
const savingPreview = ref(false);
const updatingIndex = ref(null);
const currentUploadFileName = ref("");
const currentUploadDate = ref("");

const templateUrl = ref("/template/template_data_pakan.csv");

onMounted(() => {
  fetch("http://localhost:8000/list_csv_files")
    .then((res) => res.json())
    .then((data) => {
      fileList.value = data.files || [];
    })
    .catch((err) => {
      console.error("Gagal memuat daftar file:", err);
      Swal.fire("Error", "Gagal memuat daftar file dari server.", "error");
    });
});

function parseCSV(text) {
  const lines = text.trim().split("\n");
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(",").map(h => h.trim());
  const rows = lines.slice(1).map(line => {
    const values = line.split(",");
    let obj = {};
    headers.forEach((h, i) => {
      obj[h] = values[i] || "";
    });
    return obj;
  });
  return { headers, rows };
}

function validateCSVColumns(rows) {
  if (!rows.length) return { valid: false, message: "Data kosong." };

  const requiredCols = ["tanggal", "pakan_pakai", "jumlah_ayam", "jumlah_ayam_mati"];
  const fileCols = Object.keys(rows[0]).map(col => col.trim().toLowerCase());

  const missingCols = requiredCols.filter(col => !fileCols.includes(col));
  if (missingCols.length > 0) {
    return {
      valid: false,
      message: `Kolom berikut tidak ditemukan: ${missingCols.join(", ")}`,
    };
  }

  for (const row of rows) {
    const tanggal = row["tanggal"]?.trim();
    if (!tanggal) return { valid: false, message: "Ada baris tanpa tanggal." };

    const parsedDate = Date.parse(tanggal.replace(/\s+/g, " "));
    if (isNaN(parsedDate)) {
      return { valid: false, message: `Tanggal tidak valid: ${tanggal}` };
    }
  }

  return { valid: true };
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const text = await file.text();
  const { headers, rows } = parseCSV(text);

  if (headers.length === 0 || rows.length === 0) {
    Swal.fire("Error", "File CSV kosong atau format tidak benar", "error");
    return;
  }

  const validation = validateCSVColumns(rows);
  if (!validation.valid) {
    Swal.fire("Error", validation.message, "error");
    return;
  }

  currentUploadFileName.value = file.name;
  currentUploadDate.value = new Date().toISOString().slice(0, 10);
  previewHeaders.value = headers;
  previewData.value = rows;
  showPreview.value = true;
  updatingIndex.value = null;
}

function cancelPreview() {
  showPreview.value = false;
  previewHeaders.value = [];
  previewData.value = [];
  currentUploadFileName.value = "";
  currentUploadDate.value = "";
  updatingIndex.value = null;
}

async function savePreviewData() {
  savingPreview.value = true;
  try {
    const endpoint = updatingIndex.value !== null ? "update_csv_preview" : "save_csv_preview";
    const payload = {
      id: updatingIndex.value !== null ? fileList.value[updatingIndex.value].id : undefined,
      fileName: currentUploadFileName.value,
      uploadDate: currentUploadDate.value,
      rows: previewData.value,
    };

    const res = await fetch(`http://localhost:8000/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Gagal menyimpan ke server");
    const json = await res.json();

    if (updatingIndex.value !== null) {
      const idx = updatingIndex.value;
      Object.assign(fileList.value[idx], {
        fileName: currentUploadFileName.value,
        uploadDate: currentUploadDate.value,
        dataCSV: [...previewData.value],
      });
      Swal.fire("Sukses", "Data berhasil diupdate.", "success");
    } else {
      fileList.value.push({
        fileName: currentUploadFileName.value,
        uploadDate: currentUploadDate.value,
        dataCSV: [...previewData.value],
        id: json.id || null,
      });
      Swal.fire("Sukses", "Data berhasil disimpan.", "success");
    }

    cancelPreview();
  } catch (error) {
    Swal.fire("Error", error.message || "Gagal menyimpan data.", "error");
  } finally {
    savingPreview.value = false;
  }
}

function editFile(index) {
  const file = fileList.value[index];
  currentUploadFileName.value = file.fileName;
  currentUploadDate.value = file.uploadDate;
  previewHeaders.value = Object.keys(file.dataCSV[0] || {});
  previewData.value = file.dataCSV.map(r => ({ ...r }));
  showPreview.value = true;
  updatingIndex.value = index;
}

async function deleteFile(index) {
  Swal.fire({
    title: "Hapus file ini?",
    text: `File: ${fileList.value[index].fileName}`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Ya, hapus",
    cancelButtonText: "Batal",
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const fileId = fileList.value[index].id;
        const res = await fetch(`http://localhost:8000/delete_csv/${fileId}`, {
          method: "DELETE",
        });

        if (!res.ok) throw new Error("Gagal menghapus dari server");

        fileList.value.splice(index, 1);
        Swal.fire("Terhapus!", "File berhasil dihapus.", "success");
        if (updatingIndex.value === index) cancelPreview();
      } catch (err) {
        Swal.fire("Error", err.message || "Gagal hapus data.", "error");
      }
    }
  });
}
</script>

<style scoped>
.data-container {
  padding: 1rem;
  max-width: 900px;
  margin: auto;
}

.upload-template-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.custom-file-upload {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  background-color: #5d2d1d;
  color: white;
  border-radius: 5px;
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

.button-group {
  margin-top: 1rem;
}

button {
  padding: 0.6rem 1rem;
  background-color: #5d2d1d;
  color: white;
  border: none;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
  margin-right: 10px;
}

button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

td,
th {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: left;
}

input {
  width: 100%;
  padding: 0.3rem;
  box-sizing: border-box;
  border: 1px solid #aaa;
  border-radius: 3px;
}
.download-buttons {
  display: flex;
  gap: 1rem;
}

.download-link {
  color: #0a660a;
  font-weight: bold;
  text-decoration: underline;
  cursor: pointer;
}

</style>
