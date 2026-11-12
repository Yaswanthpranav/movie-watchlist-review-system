import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend only allows CORS from http://localhost:5173 and http://127.0.0.1:5173
// (see CORS_ORIGINS in backend/app/config.py), so keep this port fixed.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
