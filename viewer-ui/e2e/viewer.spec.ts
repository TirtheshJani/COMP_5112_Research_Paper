import { expect, type Page, test } from "@playwright/test";
import { type Replay, sampleEvents, startReplay } from "./replay";

const PORT = 8771;
const events = sampleEvents();
const gridPoints = (grid: number[][]) => grid.map(([x, y]) => `${x},${y}`).join(" ");
const READ_GREEN = "rgb(61, 220, 132)";
const AMBER = "rgb(255, 176, 32)";

let replay: Replay;
test.beforeEach(async () => {
  replay = await startReplay(PORT);
});
test.afterEach(async () => {
  await replay.stop();
});

const filledCells = (page: Page) =>
  page.locator('[data-testid^="piece-"][data-filled="true"]').evaluateAll((els) =>
    els.map((e) => e.getAttribute("data-testid")).sort(),
  );

test("W5: overlay polygon has the grid coordinates, green on a read and amber on a reject", async ({ page }) => {
  const reads = new Set(events.filter((e) => e.type === "frame" && e.decision.kind === "read").map((e) => gridPoints(e.grid)));
  const rejects = new Set(
    events.filter((e) => e.type === "frame" && e.decision.kind === "reject" && e.grid).map((e) => gridPoints(e.grid)),
  );
  expect(rejects.size).toBeGreaterThan(0);
  await page.goto(replay.url);
  const poly = page.getByTestId("grid-overlay");

  await expect(poly).toHaveAttribute("data-kind", "read", { timeout: 15_000 });
  const readPts = await poly.getAttribute("points");
  expect(reads.has(readPts!)).toBe(true);
  await expect(page.getByTestId("decision")).toContainText(/READ\s*Row \d, column \d, turn \d/);

  await expect(poly).toHaveAttribute("data-kind", "reject", { timeout: 15_000 });
  const rejectPts = await poly.getAttribute("points");
  expect(rejects.has(rejectPts!)).toBe(true);
  // stroke is checked on the same element in the same tick as its kind
  const [kind, stroke] = await poly.evaluate((el) => [el.getAttribute("data-kind"), getComputedStyle(el).stroke]);
  expect(stroke).toBe(kind === "read" ? READ_GREEN : AMBER);

  await expect(page.getByTestId("decision")).toContainText("REJECT", { timeout: 15_000 });
  await expect(page.locator(".decision .tag")).toHaveCSS("background-color", AMBER);
});

test("W5: the camera image is the server's latest frame", async ({ page }) => {
  await page.goto(replay.url);
  const img = page.locator(".camera img");
  await expect(img).toHaveAttribute("src", /\/frame\.jpg\?t=/, { timeout: 15_000 });
  expect(await img.evaluate((el: HTMLImageElement) => el.naturalWidth)).toBe(720);
});

test("W6: after the sample sequence exactly the announced cells are filled", async ({ page }) => {
  const ann = events.filter((e) => e.type === "announce");
  const announced = ann.map((e) => `piece-${e.row}-${e.col}`).sort();
  const last = page.getByTestId(`piece-${ann.at(-1).row}-${ann.at(-1).col}`);
  await page.goto(replay.url);
  await expect(last).toHaveAttribute("data-highlight", "true", { timeout: 20_000 });
  expect(await filledCells(page)).toEqual(announced);
  for (const id of announced) expect(await page.getByTestId(id).locator("image").count()).toBe(1); // its part of the picture
  // the loop restarts with an empty board
  await expect.poll(() => filledCells(page), { timeout: 15_000 }).toEqual([]);
});

test("W6: an announced piece is highlighted for 2 s", async ({ page }) => {
  // the first announce of the sample is followed by 2.2 s (at 5 events per second) before the next one
  const first = events.find((e) => e.type === "announce");
  const piece = page.getByTestId(`piece-${first.row}-${first.col}`);
  await page.goto(replay.url);
  await expect(piece).toHaveAttribute("data-highlight", "true", { timeout: 20_000 });
  const t0 = Date.now();
  await expect(page.locator('[data-highlight="true"]')).toHaveCount(1);
  await expect(piece).toHaveAttribute("data-highlight", "false", { timeout: 4_000 });
  const lit = Date.now() - t0;
  expect(lit).toBeGreaterThan(1_500);
  expect(lit).toBeLessThan(2_600);
  await expect(piece).toHaveAttribute("data-filled", "true");
});

test("W6: reset clears the board", async ({ page }) => {
  await page.goto(replay.url);
  await expect.poll(async () => (await filledCells(page)).length, { timeout: 20_000 }).toBeGreaterThan(0);
  await replay.stop(); // freeze the board so only the reset can change it
  replay = await startReplay(PORT, 0.2);
  await expect(page.getByTestId("connection")).toHaveText("live", { timeout: 10_000 });
  const before = (await filledCells(page)).length;
  expect(before).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Reset board" }).click();
  await expect.poll(() => filledCells(page), { timeout: 5_000 }).toEqual([]);
});

test("W7: the status line shows the last spoken sentence and the give-up sentence", async ({ page }) => {
  const announce = events.find((e) => e.type === "announce");
  const giveUp = events.find((e) => e.type === "give_up");
  await page.goto(replay.url);
  const status = page.getByTestId("status");
  await expect(status).toHaveText(announce.text, { timeout: 20_000 });
  await expect(status).toHaveText(giveUp.text, { timeout: 20_000 });
  await expect(status).toHaveCSS("color", AMBER);
  expect(parseFloat(await status.evaluate((el) => getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(28);
});

test("W9: shows disconnected when the server stops and recovers when it restarts", async ({ page }) => {
  await page.goto(replay.url);
  const conn = page.getByTestId("connection");
  await expect(conn).toHaveText("live", { timeout: 10_000 });

  await replay.stop();
  await expect(conn).toContainText("disconnected", { timeout: 5_000 });
  await page.waitForTimeout(2_500); // a few failed retries

  replay = await startReplay(PORT);
  await expect(conn).toHaveText("live", { timeout: 5_000 });
  const t = await page.locator(".camera img").getAttribute("src");
  await expect(page.locator(".camera img")).not.toHaveAttribute("src", t!, { timeout: 5_000 });
});
