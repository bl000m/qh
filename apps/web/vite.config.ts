import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['frontend'],
    strictPort: true,
    watch: { usePolling: true },
    proxy: {
      // Development transport only. Backend policy remains authoritative.
      '/api': {
        target: process.env.QH_WEB_API_TARGET || loadEnv(mode, process.cwd(), '').QH_WEB_API_TARGET || 'http://backend:8000',
        rewrite: path => path.replace(/^\/api/, ''),
        configure(proxy) { proxy.on('error', () => { /* Never log requests/tokens. */ }); }
      }
    }
  }
}));
