import { createRouter, createWebHistory } from 'vue-router'
import { jwtDecode } from 'jwt-decode'

// ===== Import Views =====
const Home = () => import('../views/Home.vue')
const Prediksi = () => import('../views/Prediksi.vue')
const Riwayat = () => import('../views/Riwayat.vue')
const DataPakan = () => import('../views/DataPakan.vue')
const Register = () => import('../views/Register.vue')
const Login = () => import('../views/Login.vue')
const ForgotPassword = () => import('../views/ForgotPassword.vue') 
const AdminDashboard = () => import('../views/AdminDashboard.vue')
const UserDashboard = () => import('../views/UserDashboard.vue')
const KelolaUser = () => import('../views/KelolaUser.vue')
const AdminRiwayat = () => import('../views/AdminRiwayat.vue')
const AdminDataPakan = () => import('../views/AdminDataPakan.vue')

// ===== Routes =====
const routes = [
  { path: '/', redirect: '/home' }, // default ke home
  { path: '/home', name: 'Home', component: Home },
  { path: '/register', name: 'Register', component: Register },
  { path: '/login', name: 'Login', component: Login },
  { path: '/forgot', name: 'ForgotPassword', component: ForgotPassword }, 


  // ===== User Routes =====
  { path: '/prediksi', name: 'Prediksi', component: Prediksi, meta: { requiresAuth: true, role: 'user' } },
  { path: '/riwayat', name: 'Riwayat', component: Riwayat, meta: { requiresAuth: true, role: 'user' } },
  { path: '/data-pakan', name: 'DataPakan', component: DataPakan, meta: { requiresAuth: true, role: 'user' } },
  { path: '/user/dashboard', name: 'UserDashboard', component: UserDashboard, meta: { requiresAuth: true, role: 'user' } },

  // ===== Admin Routes =====
  { path: '/admin/dashboard', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/users', name: 'KelolaUser', component: KelolaUser, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/data-pakan', name: 'AdminDataPakan', component: AdminDataPakan, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/prediksi/:id', name: 'AdminPrediksiDetail', component: Prediksi, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/riwayat', name: 'AdminRiwayat', component: AdminRiwayat, meta: { requiresAuth: true, role: 'admin' } },

  // fallback
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

  // 🔓 Public routes
  const publicPaths = ['/home', '/login', '/register', '/forgot']
  if (publicPaths.includes(to.path)) return next()

  // 🔑 Cek token dan expired
  if (token) {
    try {
      const decoded = jwtDecode(token)
      const now = Date.now() / 1000
      if (decoded.exp && decoded.exp < now) {
        localStorage.clear()
        return next('/login')
      }
    } catch {
      localStorage.clear()
      return next('/login')
    }
  }

  // 🚫 Kalau butuh auth tapi belum login
  if (to.meta.requiresAuth && !token) return next('/login')

  // 🚦 Role check
  if (to.meta.role && role !== to.meta.role) {
    if (role === 'admin') return next('/admin/dashboard')
    if (role === 'user') return next('/user/dashboard')
    return next('/login')
  }

  // ✅ default lanjut
  next()
})

export default router
