// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Prediksi from '../views/Prediksi.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/prediksi', name: 'Prediksi', component: Prediksi },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
