import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    outDir: '../static',         // Output hasil build ke folder backend/static
    emptyOutDir: true,           // Hapus isi folder outDir sebelum build
    chunkSizeWarningLimit: 1500, // Naikkan limit chunk warning dari default (500 KB)
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue'],
          chartjs: ['chart.js', 'vue-chartjs'], // Pisahkan chartjs agar cepat
          sweetalert: ['sweetalert2']          // Pisahkan SweetAlert
        }
      }
    }
  }
})
