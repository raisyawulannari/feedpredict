<template>
  <div class="data-pakan-container">
    <!-- Upload + Preview -->
    <div class="card upload-card">
      <div class="table-header">
        <button class="btn-upload" @click="fileInput.click()">📂 Tambahkan Data CSV</button>
        <input type="file" ref="fileInput" accept=".csv" @change="handleFileUpload" hidden />
        <a :href="templateUrl" download class="download-link">
          Contoh Data CSV Yang Benar
        </a>
      </div>

      <!-- Daftar File -->
      <div class="table-wrapper">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Nama File</th>
              <th>Tanggal Upload</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="uploadedFiles.length === 0">
              <td colspan="4" class="empty-message">Belum ada data yang diupload.</td>
            </tr>
            <tr v-for="file in uploadedFiles" :key="file.id">
              <td>{{ file.file_name }}</td>
              <td>{{ file.upload_date }}</td>
              <td>
                <button class="btn-update" @click="editFile(file)">Update</button>
                <button class="btn-delete" @click="deleteFile(file)">Hapus</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Preview CSV & Edit -->
    <div v-if="previewData.length" class="card">
      <h2>Preview Data CSV</h2>
      <div class="table-wrapper">
        <table class="custom-table">
          <thead>
            <tr>
              <th v-for="(header, index) in previewHeaders" :key="index">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rowIndex) in previewData" :key="rowIndex">
              <td v-for="(value, colIndex) in row" :key="colIndex">
                <input v-model="previewData[rowIndex][colIndex]" class="cell-input" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="preview-actions">
        <button class="btn-save" @click="savePreview">✅ Simpan</button>
        <button class="btn-cancel" @click="cancelPreview">❌ Batal</button>
      </div>
    </div>
  </div>
</template>

<script>
import Swal from "sweetalert2";
import Papa from "papaparse";
import { ref, onMounted } from "vue";

export default {
  setup() {
    const uploadedFiles = ref([]);
    const previewData = ref([]);
    const previewHeaders = ref([]);
    const selectedFile = ref(null);
    const editingFile = ref(null);
    const templateUrl = ref("/static/template/template_data_pakan.csv");
    const fileInput = ref(null);

    const getAuthHeaders = () => ({
      Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
    });

    const handleUnauthorized = () => {
      Swal.fire(
        "Unauthorized",
        "Token tidak valid / kadaluarsa, silakan login kembali",
        "warning"
      );
      uploadedFiles.value = [];
    };

    const fetchUploadedFiles = async () => {
  try { 
    const res = await fetch("http://localhost:8000/data_pakan/list", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`
      }
    });

    if (res.status === 401) return handleUnauthorized();

    const data = await res.json();
    uploadedFiles.value = Array.isArray(data) ? data : [];
  } catch (err) {
    uploadedFiles.value = [];
    Swal.fire("Error", "Gagal ambil data dari server", "error");
    console.error(err);
  }
};


    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      selectedFile.value = file;

      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const data = results.data;
          const headers = results.meta.fields;

          const requiredColumnsAlias = {
            tanggal: ["tanggal", "Tanggal", "tgl", "date"],
            jumlah_ayam_awal: ["jumlah_ayam_awal", "jumlah_ayam", "jml_ayam"],
            Pakan_Pakai: [
              "pakan_kg", "pakan", "pakankg", "pakanKg",
              "pakan_", "PakanKG", "pakan_Pakai", "Pakan_Pakai", "PakanPakai"
            ],
            jumlah_ayam_mati: ["jumlah_ayam_mati", "ayam_mati", "mati", "ayam_mati"],
          };

          const missingCols = [];
          for (const [mainCol, aliases] of Object.entries(requiredColumnsAlias)) {
            const found = headers.some((h) =>
              aliases.some((a) => a.toLowerCase() === h.toLowerCase())
            );
            if (!found) missingCols.push(mainCol);
          }
          if (missingCols.length) {
            Swal.fire("Gagal", `Kolom wajib hilang: ${missingCols.join(", ")}`, "error");
            selectedFile.value = null;
            return;
          }

          if (data.length < 30) {
            Swal.fire("Gagal", `Jumlah baris minimal 30, file hanya ada ${data.length} baris`, "error");
            selectedFile.value = null;
            return;
          }

          previewHeaders.value = headers;
          previewData.value = data.map((row) => Object.values(row));
        },
      });
    };

    const savePreview = async () => {
  if (!previewData.value.length) return;

  const formData = new FormData();

  if (editingFile.value) {
    // Kalau update file lama / nama file
    formData.append("file_name", editingFile.value.file_name); // selalu string
    if (selectedFile.value) {
      formData.append("file", selectedFile.value); // optional, file baru
    }

    try {
      const res = await fetch(`http://localhost:8000/data_pakan/${editingFile.value.id}`, {
        method: "PUT",
        body: formData,
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token") || ""}`
          // jangan set Content-Type, biarkan browser atur otomatis
        }
      });

      const result = await res.json();

      if (res.ok && result.message) {
        Swal.fire("Berhasil", result.message, "success");
        fetchUploadedFiles();
        cancelPreview();
      } else {
        Swal.fire("Gagal", result.detail || JSON.stringify(result), "error");
      }
    } catch (err) {
      console.error(err);
      Swal.fire("Error", err.message || "Unknown error", "error");
    }

  } else {
    // Upload file baru
    if (!selectedFile.value) return Swal.fire("Gagal", "Tidak ada file untuk diupload", "error");

    formData.append("file", selectedFile.value);

    try {
      const res = await fetch("http://localhost:8000/data_pakan/upload", {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token") || ""}`
        }
      });
      const result = await res.json();

      if (res.ok && result.message) {
        Swal.fire("Berhasil", result.message, "success");
        fetchUploadedFiles();
        cancelPreview();
      } else {
        Swal.fire("Gagal", result.detail || JSON.stringify(result), "error");
      }
    } catch (err) {
      console.error(err);
      Swal.fire("Error", err.message || "Unknown error", "error");
    }
  }
};


    const cancelPreview = () => {
      previewData.value = [];
      previewHeaders.value = [];
      selectedFile.value = null;
      editingFile.value = null;
    };

    const editFile = async (file) => {
      editingFile.value = file;
      try {
        const res = await fetch(`http://localhost:8000/data_pakan/${file.id}/read_csv`, {
          headers: getAuthHeaders(),
        });
        if (res.status === 401) return handleUnauthorized();
        const data = await res.json();
        previewHeaders.value = data.headers; 
        previewData.value = data.rows;

      } catch (err) {
        Swal.fire("Error", "Gagal baca file CSV", "error");
        console.error(err);
      }
    };

    const deleteFile = async (file) => {
      const confirm = await Swal.fire({
        title: "Hapus file?",
        text: `File: ${file.file_name}`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Ya, hapus",
        cancelButtonText: "Batal",
      });

      if (confirm.isConfirmed) {
        try {
          const res = await fetch(`http://localhost:8000/data_pakan/${file.id}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
          });
          if (res.status === 401) return handleUnauthorized();

          const result = await res.json();
          Swal.fire("Terhapus", result.message, "success");
          fetchUploadedFiles();
        } catch (err) {
          Swal.fire("Error", "Gagal hapus file", "error");
          console.error(err);
        }
      }
    };

    onMounted(fetchUploadedFiles);

    return {
      uploadedFiles,
      previewData,
      previewHeaders,
      selectedFile,
      editingFile,
      templateUrl,
      fileInput,
      handleFileUpload,
      savePreview,
      cancelPreview,
      editFile,
      deleteFile,
    };
  },
};
</script>

<style scoped>
/* Status file */
.status-exists {
  color: green;
  font-weight: bold;
}

.status-missing {
  color: red;
  font-weight: bold;
}

.data-pakan-container {
  width: 100%;
  padding: 20px;
  background: #f9fdf9;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 30px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.upload-card .table-header {
  flex-wrap: wrap;
  gap: 10px;
}

.btn-upload {
  background: #388e3c;
  color: white;
  padding: 6px 14px;
  font-size: 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-upload:hover {
  background: #2e7d32;
}

.download-link {
  color: #0a660a;
  font-weight: bold;
  text-decoration: underline;
}

.table-wrapper {
  overflow-x: auto;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  background: white;
}

.custom-table th {
  background: #388e3c;
  color: white;
  padding: 12px;
  text-align: center;
}

.custom-table td {
  padding: 12px;
  border: 1px solid #ddd;
  text-align: center;
}

.cell-input {
  width: 100%;
  border: 1px solid #ccc;
  padding: 6px;
  border-radius: 6px;
}

.preview-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.btn-save {
  background: #43a047;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-save:hover {
  background: #2e7d32;
}

.btn-cancel {
  background: #e53935;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #b71c1c;
}

.empty-message {
  text-align: center;
  color: #888;
  padding: 15px;
}

.btn-update,
.btn-delete,
.btn-download {
  margin: 0 5px;
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-update {
  background: #fbc02d;
  color: white;
}

.btn-update:hover {
  background: #f9a825;
}

.btn-delete {
  background: #e53935;
  color: white;
}

.btn-delete:hover {
  background: #c62828;
}

.btn-download {
  background: #0a660a;
  color: white;
  text-decoration: none;
}

.btn-download:hover {
  background: #043d01;
}
</style>
