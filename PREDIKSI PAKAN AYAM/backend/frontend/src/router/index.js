import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Prediksi from '../views/Prediksi.vue'
import Riwayat from '../views/Riwayat.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/prediksi', name: 'Prediksi', component: Prediksi },
  { path: '/riwayat', name: 'Riwayat', component: Riwayat },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})


export default router
