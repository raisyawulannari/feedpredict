import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/css/main.css'
import 'leaflet/dist/leaflet.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import './assets/css/main.css'  // pastikan path sesuai lokasi main.css kamu

const app = createApp(App)
app.use(router)  
app.mount('#app')
