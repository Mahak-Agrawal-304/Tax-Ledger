import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev-time proxy so the React app can call same-origin `/api/...` paths
// while FastAPI runs separately on port 8000 (uvicorn main:app --reload).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
