import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { site } from './site.mjs';

const root = fileURLToPath(new URL('.', import.meta.url));
export default defineConfig(() => ({
  plugins: [react()],
  base: process.env.RELEVO_BASE_PATH || '/',
  build: {
    rolldownOptions: {
      input: Object.fromEntries([...site.pages.map(({ slug }) => [slug || 'home', resolve(root, slug, 'index.html')]), ['404', resolve(root, '404.html')]]),
    },
  },
  server: { host: '127.0.0.1', port: 5173, strictPort: true },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true },
}));
