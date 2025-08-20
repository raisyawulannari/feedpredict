import { createRouter, createWebHistory } from 'vue-router'
import { jwtDecode } from 'jwt-decode'

// ===== Import Views =====
const Home = () => import('../views/Home.vue')
const Prediksi = () => import('../views/Prediksi.vue')
const Riwayat = () => import('../views/Riwayat.vue')
const DataPakan = () => import('../views/DataPakan.vue')
const Register = () => import('../views/Register.vue')
const Login = () => import('../views/Login.vue')
const AdminDashboard = () => import('../views/AdminDashboard.vue')
const UserDashboard = () => import('../views/UserDashboard.vue')
const KelolaUser = () => import('../views/KelolaUser.vue')
const AdminPrediksi = () => import('../views/AdminPrediksi.vue')   
const AdminRiwayat = () => import('../views/AdminRiwayat.vue')    

// ===== Routes =====
const routes = [
  { path: '/', redirect: '/home' }, // default buka home (About)
  { path: '/home', name: 'Home', component: Home },
  { path: '/prediksi', name: 'Prediksi', component: Prediksi, meta: { requiresAuth: true, role: 'user' } },
  { path: '/riwayat', name: 'Riwayat', component: Riwayat, meta: { requiresAuth: true, role: 'user' } },
  { path: '/data-pakan', name: 'DataPakan', component: DataPakan, meta: { requiresAuth: true, role: 'user' } },
  { path: '/register', name: 'Register', component: Register },
  { path: '/login', name: 'Login', component: Login },

  // ===== User Dashboard =====
  { path: '/user/dashboard', name: 'UserDashboard', component: UserDashboard, meta: { requiresAuth: true, role: 'user' } },

  // ===== Admin Dashboard =====
  { path: '/admin/dashboard', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/users', name: 'KelolaUser', component: KelolaUser, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/prediksi', name: 'AdminPrediksi', component: AdminPrediksi, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/prediksi/:id', name: 'AdminPrediksiDetail', component: Prediksi, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/riwayat', name: 'AdminRiwayat', component: AdminRiwayat, meta: { requiresAuth: true, role: 'admin' } },

  // fallback: redirect ke home
  { path: '/:pathMatch(.*)*', redirect: '/home' }
]

// ===== Create Router =====
const router = createRouter({
  history: createWebHistory(),
  routes
})

// ===== Route Guard =====
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  // Kalau ada token, cek apakah expired
  if (token) {
    try {
      const decoded = jwtDecode(token)
      const now = Date.now() / 1000
      if (decoded.exp && decoded.exp < now) {
        // Token expired → hapus semua data & paksa login
        localStorage.clear()
        return next('/login')
      }
    } catch {
      // Token rusak → hapus semua data & paksa login
      localStorage.clear()
      return next('/login')
    }
  }

  // Jika rute membutuhkan login tapi token tidak ada
  if (to.meta.requiresAuth && !token) return next('/login')

  // Jika role tidak sesuai
  if (to.meta.role && role !== to.meta.role) {
    if (role === 'admin') return next('/admin/dashboard')
    if (role === 'user') return next('/user/dashboard')
    return next('/login')
  }

  next()
})

export default router
