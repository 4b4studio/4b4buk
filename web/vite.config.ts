import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs separately (uvicorn on port 8000) and is proxied.
// In production the backend serves the built files from web/dist (BUK_WEB_DIST).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
  build: { outDir: "dist", sourcemap: false },
});
