import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/',
  plugins: [vue()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Hapus bagian external agar axios ikut di-bundle
  },
  optimizeDeps: {
    include: ['axios', 'chart.js'],
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  }
})
