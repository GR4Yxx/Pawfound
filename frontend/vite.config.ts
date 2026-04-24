import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "../", "");
  // VITE_API_PROXY_TARGET: where the Vite dev server forwards /api requests.
  // - local (no Docker): http://localhost:8000
  // - docker-compose.dev.yml: http://backend:8000  (service name resolves inside the network)
  const apiTarget = env.VITE_API_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      watch: {
        // Windows → Docker volume mounts don't emit inotify events — use polling
        usePolling: true,
        interval: 300,
      },
      hmr: {
        host: "localhost",
        clientPort: 80,
        protocol: "ws",
      },
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
