import { defineConfig } from 'vite'

export default defineConfig({
  // Dev server config
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['leopardcat-tarot.milkcat.org', 'leopard.milkcat.org', 'localhost'],
    // Proxy /api calls to the Python backend so dev matches prod behaviour
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
      }
    }
  },
  // Serve public files correctly (content.json, manifest.json, etc.)
  publicDir: 'public',
  // Build output goes into dist/ which nginx reads
  build: {
    outDir: 'dist',
  }
})
