import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Prediksi from '../views/Prediksi.vue'
import Riwayat from '../views/Riwayat.vue'
import Notifikasi from '../views/Notifikasi.vue'
import DataPakan from '../views/DataPakan.vue'
import KelolaPakan from '../views/KelolaPakan.vue'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/prediksi', name: 'Prediksi', component: () => import('../views/Prediksi.vue') },
  { path: '/riwayat', name: 'Riwayat', component: () => import('../views/Riwayat.vue') },
  { path: '/notifikasi', name: 'Notifikasi', component: () => import('../views/Notifikasi.vue') },
  { path: '/data-pakan', name: 'DataPakan', component: () => import('../views/DataPakan.vue') },
  { path: '/kelola-pakan', name: 'KelolaPakan', component: () => import('../views/KelolaPakan.vue') },
  { path: '/riwayat/:id/grafik', name: 'RiwayatGrafik', component: () => import('../views/Prediksi.vue') }
]


const router = createRouter({
  history: createWebHistory(),
  routes
})


export default router
