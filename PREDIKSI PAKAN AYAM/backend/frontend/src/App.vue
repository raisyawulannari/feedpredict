<template>
  <div>
    <!-- NAVBAR -->
    <header class="navbar">
      <!-- LOGO + TEXT -->
      <div class="logo-section">
        <img :src="logoUrl" alt="Feed Predict Logo" class="logo" />
      </div>

      <!-- NAV LINKS -->
      <nav :class="['nav-links', { 'right-align': !isLoggedIn }]">
        <template v-if="!isLoggedIn">
          <router-link to="/" class="nav-link" :class="{ active: isActive('/') }">Home</router-link>
          <router-link to="/login" class="nav-link auth-link"
            :class="{ active: isActive('/login') }">Login</router-link>
          <router-link to="/register" class="nav-link auth-link register-btn"
            :class="{ active: isActive('/register') }">Register</router-link>
        </template>

        <template v-else>
          <router-link v-if="isUser" :to="dashboardLink" class="nav-link"
            :class="{ active: isActive(dashboardLink) }">Dashboard</router-link>
          <router-link v-if="isUser" to="/prediksi" class="nav-link"
            :class="{ active: isActive('/prediksi') }">Prediksi</router-link>
          <router-link v-if="isUser" to="/data-pakan" class="nav-link" :class="{ active: isActive('/data-pakan') }">Data
            Pakan</router-link>
          <router-link v-if="isUser" to="/riwayat" class="nav-link"
            :class="{ active: isActive('/riwayat') }">Riwayat</router-link>

          <router-link v-if="isAdmin" :to="dashboardLink" class="nav-link"
            :class="{ active: isActive(dashboardLink) }">Dashboard</router-link>
          <router-link v-if="isAdmin" to="/admin/riwayat" class="nav-link"
            :class="{ active: isActive('/admin/riwayat') }">Riwayat User</router-link>
          <router-link v-if="isAdmin" to="/admin/data-pakan" class="nav-link"
            :class="{ active: isActive('/admin/data-pakan') }">Data Pakan</router-link>
          <router-link v-if="isAdmin" to="/admin/users" class="nav-link"
            :class="{ active: isActive('/admin/users') }">Kelola User</router-link>
        </template>
      </nav>

      <!-- USER INFO -->
      <div v-if="isLoggedIn" class="right-section">
        <div class="auth">
          <div class="relative" @mouseenter="showDropdown = true; markNotificationsRead()"
            @mouseleave="showDropdown = false">
            <span class="notif-icon">
              🔔
              <span v-if="unreadCount" class="badge">{{ unreadCount }}</span>
            </span>

            <div v-if="showDropdown" class="notif-dropdown">
              <p v-if="!notifications.length">Tidak ada notifikasi</p>
              <ul v-else>
                <li v-for="(n, index) in notifications" :key="index" :class="['notif-item',
                  n.message.includes('⚠️') ? 'expired' :
                    n.message.includes('Aktif') ? 'active' :
                      'normal']">
                  {{ n.message }}
                  <small class="date">{{ new Date(n.created_at).toLocaleDateString() }}</small>
                </li>
              </ul>
            </div>
          </div>

          <span class="username"> Hi, {{ user.name }}</span>
          <a href="#" class="nav-link logout-link" @click.prevent="logout">Logout</a>
        </div>
      </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="main-content">
      <router-view @login-success="setUser" />
    </main>
  </div>
</template>

<script setup>
import { computed, watch, onMounted, ref } from 'vue'
import userStore from './store/user.js'
import { useRouter, useRoute } from 'vue-router'
import logo from '@/assets/FEED PREDICT logo.png'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const { userState: user, isLoggedIn, isAdmin, isUser, setUser, logout: logoutStore } = userStore
const logoUrl = logo

const unreadCount = ref(0)
const notifications = ref([])
const showDropdown = ref(false)
const dashboardLink = computed(() => isAdmin.value ? '/admin/dashboard' : '/user/dashboard')

function isActive(path) {
  return route.path === path
}

async function fetchNotifications() {
  const token = localStorage.getItem("token")
  if (!token) return

  try {
    const res = await axios.get("http://127.0.0.1:8000/notifications", {
      headers: { Authorization: `Bearer ${token.trim()}` }
    })
    notifications.value = res.data.notifications || []
    unreadCount.value = notifications.value.length
  } catch (err) {
    console.error("Gagal ambil notifikasi:", err.response?.data || err)
    notifications.value = []
    unreadCount.value = 0
  }
}

function markNotificationsRead() {
  unreadCount.value = 0
  const token = localStorage.getItem("token")
  if (!token) return
  axios.post("http://127.0.0.1:8000/notifications/mark-read", {}, {
    headers: { Authorization: `Bearer ${token.trim()}` }
  }).catch(err => console.error(err))
}

function logout() {
  logoutStore()
  router.push('/login')
}

onMounted(() => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) setUser(JSON.parse(savedUser))
  fetchNotifications()
})

watch(user, (newUser) => {
  if (newUser) localStorage.setItem('user', JSON.stringify(newUser))
  else localStorage.removeItem('user')
}, { deep: true })
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

* {
  font-family: 'Poppins', sans-serif;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.navbar {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: #fdf6f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-wrap: wrap;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  min-width: 250px;
}

.logo-section .logo {
  height: 80px;
  max-width: 200px;
  object-fit: contain;
}

.nav-links {
  display: flex;
  gap: 1rem;
  flex: 1;
  flex-wrap: wrap;
  justify-content: center;
  /* default center */
}

.nav-links.right-align {
  justify-content: flex-end;
  /* belum login: kanan */
}

.nav-link {
  text-decoration: none;
  font-weight: 600;
  padding: 0.4rem 0.6rem;
  border-radius: 5px;
  transition: color 0.2s ease;
  color: #888888;
  /* abu-abu default */
}

.nav-link.active {
  color: #5d2d1d;
  /* menu aktif */
}

.nav-link:hover {
  color: #3e1f0f;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
  min-width: 180px;
}

.auth {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.username {
  font-weight: 500;
  color: #5d2d1d;
}

.logout-link {
  cursor: pointer;
  font-weight: 600;
  color: #a0352d;
}

.logout-link:hover {
  text-decoration: underline;
}

.main-content {
  padding: 2rem;
  background: #fefaf5;
  min-height: calc(100vh - 90px);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-x: hidden;
}

.notif-icon {
  cursor: pointer;
  font-size: 1.3rem;
  position: relative;
}

.badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: red;
  color: white;
  font-size: 11px;
  border-radius: 50%;
  padding: 2px 6px;
}

.notif-dropdown {
  position: absolute;
  top: 30px;
  right: 0;
  width: 280px;
  max-width: 90vw;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 200;
}

.notif-dropdown ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.notif-item {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}

.notif-item.expired {
  color: #b58900;
  font-weight: 600;
}

.notif-item.active {
  color: #2d6a4f;
  font-weight: 600;
}

.notif-item.normal {
  color: #1d4ed8;
  font-weight: 600;
}

.notif-dropdown .date {
  display: block;
  font-size: 11px;
  color: #888;
}

@media(max-width: 1100px) {
  .nav-links {
    gap: 0.5rem;
  }
}

@media(max-width: 900px) {
  .navbar {
    flex-direction: column;
  }
}

@media(max-width: 600px) {
  .logo-section .logo {
    height: 45px;
  }
}
</style>
