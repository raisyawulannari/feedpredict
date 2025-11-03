import axios from 'axios'

// Buat instance axios
const instance = axios.create({
  baseURL: 'http://127.0.0.1:8000', // ganti sesuai backend-mu
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Tambahkan token secara otomatis sebelum request
instance.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token.trim()}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Tangani response error global
instance.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        // Token invalid atau expired
        localStorage.clear()
        window.location.href = '/login'
      }
      // Bisa ditambahkan handling untuk status lain jika perlu
    }
    return Promise.reject(error)
  }
)

export default instance
