/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The Flask server (jigsaw/viewer/server.py) serves the build from jigsaw/viewer/static.
// In development, run scripts/replay_events.py and `npm run dev`; the API is proxied to it.
const api = "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react()],
  test: { include: ["src/**/*.test.ts"] },
  build: { outDir: "../jigsaw/viewer/static", emptyOutDir: true },
  server: {
    proxy: { "/events": api, "/frame.jpg": api, "/picture.png": api, "/reset": api },
  },
});
