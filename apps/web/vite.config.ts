import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import {readFileSync} from 'node:fs';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    https:process.env.QH_WEB_TLS_KEY&&process.env.QH_WEB_TLS_CERT?{
      key:readFileSync(process.env.QH_WEB_TLS_KEY),cert:readFileSync(process.env.QH_WEB_TLS_CERT)}:undefined,
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['frontend'],
    strictPort: true,
    watch: { usePolling: true },
    proxy: {
      // Development transport only. Backend policy remains authoritative.
      '/api': {
        xfwd:!!process.env.QH_WEB_TLS_KEY,
        target: process.env.QH_WEB_API_TARGET || loadEnv(mode, process.cwd(), '').QH_WEB_API_TARGET || 'http://backend:8000',
        rewrite: path => path.replace(/^\/api/, ''),
        configure(proxy) { proxy.on('error', () => { /* Never log requests/tokens. */ }); }
      }
    }
  }
}));
