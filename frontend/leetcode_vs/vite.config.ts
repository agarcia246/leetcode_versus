import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  build: {
    outDir: '../../app/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/backend': 'http://127.0.0.1:8000',
    },
  },
})
