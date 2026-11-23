import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "./",
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
      "/static": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
      "/output": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
      "/assets": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
      "/streetview": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 3000,
  },
});
