<template>
  <div class="kelola-pakan">
    <h2>Kelola Pakan</h2>

    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="stok">Jumlah Pakan di Gudang (karung)</label>
        <input
          id="stok"
          type="number"
          v-model.number="stokKarung"
          min="1"
          required
        />
      </div>

      <div class="form-group">
        <label for="ayam">Jumlah Ayam</label>
        <input
          id="ayam"
          type="number"
          v-model.number="jumlahAyam"
          min="1"
          required
        />
      </div>

      <button type="submit">Perbarui Notifikasi</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Swal from 'sweetalert2'

const emit = defineEmits(['update-notifikasi'])

const stokKarung = ref(1)
const jumlahAyam = ref(100)

// Muat data dari localStorage saat halaman dimuat
onMounted(() => {
  const savedStok = localStorage.getItem('stokKarung')
  const savedAyam = localStorage.getItem('jumlahAyam')

  if (savedStok) stokKarung.value = parseInt(savedStok)
  if (savedAyam) jumlahAyam.value = parseInt(savedAyam)
})

const handleSubmit = () => {
  const stokKg = stokKarung.value * 50 // 1 karung = 50kg

  // Simpan ke localStorage
  localStorage.setItem('stokKarung', stokKarung.value)
  localStorage.setItem('jumlahAyam', jumlahAyam.value)

  // Emit data ke App.vue
  emit('update-notifikasi', {
    stokKg,
    jumlahAyam: jumlahAyam.value
  })

  // SweetAlert muncul
  Swal.fire({
    icon: 'success',
    title: 'Notifikasi diperbarui!',
    showConfirmButton: false,
    timer: 1500
  })
}
</script>

<style scoped>
.kelola-pakan {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1.5rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  color: #5d2d1d;
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #333;
}

input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #aaa;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 0.6rem;
  background-color: #5d2d1d;
  color: white;
  border: none;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
}

button:hover {
  background-color: #814c36;
}
</style>
