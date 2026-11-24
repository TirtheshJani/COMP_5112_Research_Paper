import { describe, expect, it } from "vitest";
import { describeDecision, initialState, reduce, reduceAction, type ViewerEvent } from "./state";

const run = (events: ViewerEvent[], now = 0) => events.reduce((s, e) => reduce(s, e, now), initialState);

describe("reduce", () => {
  it("fills and highlights an announced cell, once", () => {
    const a: ViewerEvent = { type: "announce", row: 3, col: 1, turn: 2, text: "Row 4, column 2." };
    const s = run([a, a], 10);
    expect(s.placed).toEqual(["3,1"]);
    expect(s.highlight).toEqual({ key: "3,1", at: 10 });
    expect(s.status).toEqual({ kind: "announce", text: "Row 4, column 2." });
  });

  it("takes the board event as the full set and an empty board clears everything", () => {
    let s = run([
      { type: "announce", row: 0, col: 4, turn: 0, text: "x" },
      { type: "board", placed: [[0, 4], [6, 2]] },
    ]);
    expect(s.placed).toEqual(["0,4", "6,2"]);
    expect(s.highlight?.key).toBe("0,4");
    s = reduce(s, { type: "board", placed: [] }, 0);
    expect(s.placed).toEqual([]);
    expect(s.highlight).toBeNull();
    expect(s.status).toBeNull();
  });

  it("shows the give-up sentence", () => {
    expect(run([{ type: "give_up", text: "Show me again." }]).status).toEqual({ kind: "give_up", text: "Show me again." });
  });
});

describe("describeDecision", () => {
  it("is one-based for reads and readable for rejects", () => {
    expect(describeDecision({ kind: "read", row: 3, col: 1, turn: 2 })).toBe("Row 4, column 2, turn 2");
    expect(describeDecision({ kind: "reject", reason: "no_grid" })).toBe("no grid");
  });
});

describe("reduceAction", () => {
  it("a reset drops a stale board and status, as after reconnecting to a restarted server", () => {
    const s = run([{ type: "announce", row: 3, col: 1, turn: 2, text: "x" }]);
    expect(s.placed).toEqual(["3,1"]);
    expect(reduceAction(s, { type: "reset" }, 0)).toEqual(initialState);
  });

  it("passes viewer events through to reduce", () => {
    const e: ViewerEvent = { type: "give_up", text: "Show me again." };
    expect(reduceAction(initialState, e, 0)).toEqual(reduce(initialState, e, 0));
  });
});
