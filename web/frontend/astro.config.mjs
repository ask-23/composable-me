// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  integrations: [svelte()],
  server: {
    port: 4321,
    host: true,
  },
  vite: {
    define: {
      'import.meta.env.BACKEND_URL': JSON.stringify(
        process.env.BACKEND_URL || 'http://localhost:8000'
      ),
    },
  },
});
