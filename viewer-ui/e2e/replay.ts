import { type ChildProcess, spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
export const SAMPLE = join(ROOT, "tests", "data", "events_sample.jsonl");
export const sampleEvents = () =>
  readFileSync(SAMPLE, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));

const python = () => {
  const win = join(ROOT, ".venv", "Scripts", "python.exe");
  return existsSync(win) ? win : join(ROOT, ".venv", "bin", "python");
};

export type Replay = { url: string; stop: () => Promise<void> };

// Start the replay server on `port` and wait until it answers.
export async function startReplay(port: number, rate = 5): Promise<Replay> {
  const proc: ChildProcess = spawn(
    python(),
    [join(ROOT, "scripts", "replay_events.py"), SAMPLE, "--port", String(port), "--rate", String(rate)],
    { cwd: ROOT, stdio: "ignore" },
  );
  const url = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 150; i++) {
    if (proc.exitCode !== null) throw new Error(`replay server exited with ${proc.exitCode}`);
    try {
      const r = await fetch(`${url}/frame.jpg`);
      if (r.status === 200 || r.status === 204) break;
    } catch {
      // not listening yet
    }
    await new Promise((ok) => setTimeout(ok, 100));
  }
  return {
    url,
    stop: () =>
      new Promise<void>((ok) => {
        if (proc.exitCode !== null) return ok();
        proc.once("exit", () => ok());
        proc.kill();
      }),
  };
}
