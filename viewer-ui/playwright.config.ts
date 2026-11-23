import { defineConfig } from "@playwright/test";

// Tests run against scripts/replay_events.py serving the committed build in jigsaw/viewer/static.
// `npm run e2e` rebuilds first. Each test starts and stops its own replay server (e2e/replay.ts).
export default defineConfig({
  testDir: "e2e",
  workers: 1,
  timeout: 30_000,
  use: { viewport: { width: 1920, height: 1080 } },
});
