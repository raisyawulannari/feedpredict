<template> 
  <div>
    <!-- NAVBAR -->
    <header class="navbar">
      <!-- LOGO -->
      <div class="logo">
        <img :src="logoUrl" alt="Feed Predict Logo" />
      </div>

      <!-- NAV LINKS -->
      <nav class="nav-links">
        <!-- Menu sebelum login -->
        <template v-if="!isLoggedIn">
          <router-link to="/" class="nav-link">Home</router-link>
          <router-link to="/login" class="nav-link auth-link">Login</router-link>
        </template>

        <!-- Menu setelah login -->
        <template v-else>
          <!-- USER MENU -->
          <router-link v-if="isUser" :to="dashboardLink" class="nav-link">Dashboard</router-link>
          <router-link v-if="isUser" to="/prediksi" class="nav-link">Prediksi</router-link>
          <router-link v-if="isUser" to="/data-pakan" class="nav-link">Data Pakan</router-link>
          <router-link v-if="isUser" to="/riwayat" class="nav-link">Riwayat</router-link>

          <!-- ADMIN MENU -->
          <router-link v-if="isAdmin" :to="dashboardLink" class="nav-link">Dashboard</router-link>
          <router-link v-if="isAdmin" to="/admin/riwayat" class="nav-link">Riwayat User</router-link>
          <router-link v-if="isAdmin" to="/admin/data-pakan" class="nav-link">Data Pakan</router-link>
          <router-link v-if="isAdmin" to="/admin/users" class="nav-link">Kelola User</router-link>
        </template>
      </nav>

      <!-- USER INFO -->
      <div v-if="isLoggedIn" class="right-section">
        <div class="auth">
          <span class="username">Hi, {{ user.name }}</span>
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
import { computed, watch, onMounted } from 'vue'
import userStore from './store/user.js'
import { useRouter } from 'vue-router'
import logo from '@/assets/FEEDPREDICT.png'

const router = useRouter()
const { userState: user, isLoggedIn, isAdmin, isUser, setUser, logout: logoutStore } = userStore
const logoUrl = logo

// Dashboard link dinamis
const dashboardLink = computed(() => isAdmin.value ? '/admin/dashboard' : '/user/dashboard')

// Logout
function logout() {
  logoutStore()
  router.push('/login')
}

// Simpan user ke LocalStorage saat login
watch(user, (newUser) => {
  if(newUser) localStorage.setItem('user', JSON.stringify(newUser))
  else localStorage.removeItem('user')
}, { deep: true })

// Sync user saat reload
onMounted(() => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    setUser(JSON.parse(savedUser))
  }
})
</script>

<style scoped>
/* NAVBAR */
.navbar {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: #fdf6f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-wrap: wrap;
  box-sizing: border-box;
  padding-bottom: 0%;
}
.logo img { height: 55px; }

/* NAV LINKS */
.nav-links {
  display: flex;
  gap: 1rem;
  flex: 1;
  justify-content: center;
  flex-wrap: wrap;
}
.nav-link {
  text-decoration: none;
  font-weight: 600;
  color: #5d2d1d;
  padding: 0.4rem 0.6rem;
  border-radius: 5px;
  transition: all 0.2s ease-in-out;
}
.nav-link:hover { background: #f3d1b0; color: #3e1f0f; }
.nav-link.active { border-bottom: 3px solid #5d2d1d; }
.auth-link:hover { color: #a35d2d; }

/* RIGHT SECTION */
.right-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}
.auth {
  display: flex;
  align-items: center;
  gap: 0.6rem;
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
.logout-link:hover { text-decoration: underline; }

/* MAIN CONTENT */
.main-content {
  padding: 2rem;
  background: #fefaf5;
  min-height: calc(100vh - 90px);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-sizing: border-box;
  overflow-x: hidden;
}

/* RESPONSIVE */
@media(max-width: 900px) {
  .navbar {
    flex-direction: column;
    align-items: center;
    gap: 0.8rem;
  }
  .right-section {
    order: 3;
    justify-content: center;
    width: 100%;
  }
  .nav-links {
    order: 2;
    width: 100%;
    justify-content: center;
    gap: 0.6rem;
  }
}
</style>
