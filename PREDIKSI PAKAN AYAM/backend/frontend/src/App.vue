<template>
  <div @click="closeDropdownOnOutsideClick">
    <header class="navbar">
      <div class="logo">
        <img :src="logoUrl" alt="Logo Feed Predict" />
      </div>

      <nav class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">Beranda</router-link>
        <router-link to="/prediksi" class="nav-link" exact-active-class="active">Prediksi</router-link>
        <router-link to="/data-pakan" class="nav-link" exact-active-class="active">Data Pakan</router-link>
        <router-link to="/kelola-pakan" class="nav-link">Kelola Pakan</router-link>
        <router-link to="/riwayat" class="nav-link" exact-active-class="active">Riwayat</router-link>
      </nav>

      <!-- 🔔 Icon Notifikasi -->
      <div class="notification-wrapper" ref="dropdownRef">
        <button @click.stop="toggleDropdown" class="notification-btn">
          🔔
          <span v-if="notificationCount > 0" class="badge">{{ notificationCount }}</span>
        </button>

        <div v-if="showDropdown" class="notification-dropdown">
          <p v-if="notifications.length === 0">Tidak ada notifikasi</p>
          <p v-for="(notif, index) in notifications" :key="index">{{ notif }}</p>
        </div>
      </div>
    </header>

    <router-view @update-notifikasi="handleUpdateNotifikasi" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Swal from 'sweetalert2'
import logo from '@/assets/FEEDPREDICT.png'

// Logo binding
const logoUrl = logo

const notifications = ref([])
const notificationCount = ref(0)
const showDropdown = ref(false)
const dropdownRef = ref(null)

// ⬇ Fungsi untuk menerima emit dari KelolaPakan.vue
const handleUpdateNotifikasi = (payload) => {
  updateNotifications(payload.stokKg, payload.jumlahAyam)
  saveToLocalStorage()
}

// Hitung dan tampilkan notifikasi berdasarkan data pakan
function updateNotifications(stokKg, jumlahAyam) {
  const konsumsiPerEkor = 0.08 // kg/ekor/hari
  const totalKonsumsiPerHari = jumlahAyam * konsumsiPerEkor
  const hariCukup = Math.floor(stokKg / totalKonsumsiPerHari)
  const karungTersisa = Math.floor(stokKg / 50)

  notifications.value = []

  if (hariCukup <= 3) {
    notifications.value.push(`⚠️ Pakan hanya cukup ${hariCukup} hari`)
  } else {
    notifications.value.push(`✅ Pakan cukup untuk ${hariCukup} hari`)
  }

  notifications.value.push(`📦 Pakan tersisa ${karungTersisa} karung`)
  notificationCount.value = notifications.value.length

  // SweetAlert tampil
  Swal.fire({
    icon: 'success',
    title: 'Notifikasi diperbarui!',
    showConfirmButton: false,
    timer: 1500
  })
}

// Simpan notifikasi ke localStorage
function saveToLocalStorage() {
  localStorage.setItem('notifikasi', JSON.stringify(notifications.value))
}

// Ambil notifikasi dari localStorage saat halaman dimuat
function loadFromLocalStorage() {
  const saved = localStorage.getItem('notifikasi')
  if (saved) {
    notifications.value = JSON.parse(saved)
    notificationCount.value = notifications.value.length
  }
}

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const closeDropdownOnOutsideClick = (e) => {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeDropdownOnOutsideClick)
  loadFromLocalStorage()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeDropdownOnOutsideClick)
})
</script>

<style scoped>
.navbar {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  padding-bottom: 1.5rem;
}

.logo img {
  height: 70px;
}

.nav-links {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  position: relative;
}

.nav-link {
  text-decoration: none;
  font-weight: bold;
  color: #5d2d1d;
  background: none;
  border: none;
  cursor: pointer;
}

.nav-link.active {
  border-bottom: 2px solid #5d2d1d;
}

.notification-wrapper {
  position: relative;
  margin-right: 20px;
}

.notification-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  position: relative;
}

.badge {
  position: absolute;
  top: -5px;
  right: -10px;
  background: red;
  color: white;
  font-size: 0.7rem;
  border-radius: 50%;
  padding: 3px 6px;
}

.notification-dropdown {
  position: absolute;
  top: 35px;
  right: 0;
  background-color: #fff;
  border: 1px solid #ccc;
  padding: 10px;
  width: 240px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
  border-radius: 5px;
}

.notification-dropdown p {
  margin: 5px 0;
  font-size: 0.9rem;
  color: #333;
}
</style>
