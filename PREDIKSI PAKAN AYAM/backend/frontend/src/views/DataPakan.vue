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
              <th>Satuan</th>
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
                <select v-model="file.satuan_data" @change="updateSatuan(file)">
                  <option value="kg">kg</option>
                  <option value="karung">karung</option>
                </select>
              </td>
              <td>
                <button class="btn-update" @click="editFile(file)">Update</button>
                <span style="display:inline-block;width:0.5rem;"></span>
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
        <select v-model="selectedSatuan" class="satuan-select">
          <option value="kg">kg</option>
          <option value="karung">karung</option>
        </select>
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
    const selectedSatuan = ref("kg");

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
          headers: getAuthHeaders(),
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

      const csvBlob = new Blob(
        [Papa.unparse({ fields: previewHeaders.value, data: previewData.value })],
        { type: "text/csv" }
      );

      if (editingFile.value) {
        formData.append("file_name", editingFile.value.file_name);
        formData.append("file", csvBlob, editingFile.value.file_name);
        formData.append("satuan_data", selectedSatuan.value);

        try {
          const res = await fetch(
            `http://localhost:8000/data_pakan/${editingFile.value.id}`,
            {
              method: "PUT",
              body: formData,
              headers: getAuthHeaders(),
            }
          );

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
        // Upload baru
        formData.append("file", csvBlob, selectedFile.value.name);
        formData.append("satuan_data", selectedSatuan.value);

        try {
          const res = await fetch("http://localhost:8000/data_pakan/upload", {
            method: "POST",
            body: formData,
            headers: getAuthHeaders(),
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
      selectedSatuan.value = "kg";
    };

    const editFile = async (file) => {
      editingFile.value = file;
      selectedSatuan.value = file.satuan_data || "kg";
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

    // --- Tambahan: Update satuan per file ---
    const updateSatuan = async (file) => {
      try {
        const formData = new FormData();
        formData.append("file_name", file.file_name);
        formData.append("satuan_data", file.satuan_data);

        const res = await fetch(`http://localhost:8000/data_pakan/${file.id}`, {
          method: "PUT",
          body: formData,
          headers: getAuthHeaders(),
        });

        const result = await res.json();
        if (res.ok) {
          Swal.fire("Berhasil", "Satuan file diperbarui", "success");
        } else {
          Swal.fire("Gagal", result.detail || JSON.stringify(result), "error");
        }
      } catch (err) {
        console.error(err);
        Swal.fire("Error", "Gagal update satuan", "error");
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
      selectedSatuan,
      handleFileUpload,
      savePreview,
      cancelPreview,
      editFile,
      deleteFile,
      updateSatuan,
    };
  },
};
</script>

<style scoped>
.data-pakan-container {
  width: 100%;
  padding: 1.25rem;
  background: #f9fdf9;
  box-sizing: border-box;
}

.card {
  background: white;
  padding: 1.25rem;
  border-radius: 0.75rem;
  margin-bottom: 1.875rem;
  box-shadow: 0 0.1875rem 0.625rem rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

.table-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 0.625rem;
}

.btn-upload {
  background: #388e3c;
  color: white;
  padding: 0.375rem 0.875rem;
  font-size: 0.875rem;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
}

.btn-upload:hover {
  background: #2e7d32;
}

.download-link {
  color: #0a660a;
  font-weight: bold;
  text-decoration: underline;
  font-size: 0.875rem;
}

.satuan-select {
  padding: 0.375rem;
  border-radius: 0.375rem;
  border: 1px solid #ccc;
  font-size: 0.875rem;
}

.table-wrapper {
  overflow-x: auto;
  width: 100%;
}

.custom-table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  margin-top: 0.625rem;
  background: white;
  table-layout: auto;
}

.custom-table th,
.custom-table td {
  padding: 0.75rem;
  border: 1px solid #ddd;
  text-align: center;
  font-size: 0.875rem;
  word-break: break-word;
}

.cell-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #ccc;
  padding: 0.375rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.preview-actions {
  margin-top: 0.9375rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.625rem;
  align-items: center;
}

.btn-save, .btn-cancel {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
}

.btn-save {
  background: #43a047;
  color: white;
}

.btn-save:hover {
  background: #2e7d32;
}

.btn-cancel {
  background: #e53935;
  color: white;
}

.btn-cancel:hover {
  background: #b71c1c;
}

/* Responsive untuk layar kecil */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }
  .btn-upload,
  .download-link,
  .satuan-select {
    width: 100%;
    text-align: center;
  }
}
</style>
