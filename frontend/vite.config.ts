import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    allowedHosts: [
      'dev.tristia-club.site',
    ],

    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,

        // FastAPI сейчас имеет /users/login,
        // поэтому внутри прокси убираем /api
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
