import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 2,
  use: { baseURL: "http://127.0.0.1:3100", ...devices["Desktop Chrome"] },
  webServer: {
    command: "pnpm dev --hostname 127.0.0.1 --port 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: false,
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://auth.example.test",
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "public-test-key",
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:8100",
      NEXT_TELEMETRY_DISABLED: "1",
      AUTH_E2E: "1",
    },
  },
});
