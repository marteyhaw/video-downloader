import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const root = path.resolve(__dirname, "..");
  const env = loadEnv(mode, root, "");
  const host = env.VD_HOST ?? "127.0.0.1";
  const apiPort = env.VD_PORT ?? "8000";
  const devPort = Number(env.VD_DEV_PORT ?? "5175");
  const strictPort = (env.VD_STRICT_DEV_PORT ?? "true") !== "false";

  return {
    plugins: [react(), tailwindcss()],
    envDir: root,
    server: {
      port: devPort,
      strictPort,
      proxy: {
        "/api": {
          target: `http://${host}:${apiPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});
