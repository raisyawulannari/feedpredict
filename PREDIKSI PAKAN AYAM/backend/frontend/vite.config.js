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
    outDir: '../static',         
    // outDir: '../backend/static',
    emptyOutDir: true,           
    chunkSizeWarningLimit: 1500, 
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue'],
          chartjs: ['chart.js', 'vue-chartjs'], 
          sweetalert: ['sweetalert2']         
        }
      }
    }
  }
})
