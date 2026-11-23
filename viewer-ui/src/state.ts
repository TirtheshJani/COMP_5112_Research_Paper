// Viewer events (CONTRACTS v2 section 5) and the page state they drive.

export type Point = [number, number];

export type Decision =
  | { kind: "read"; row: number; col: number; turn: number }
  | { kind: "reject"; reason: string };

export type FrameEvent = {
  type: "frame";
  t: number;
  grid: Point[] | null;
  rvec: number[] | null;
  tvec: number[] | null;
  decision: Decision;
};

export type ViewerEvent =
  | FrameEvent
  | { type: "announce"; row: number; col: number; turn: number; text: string }
  | { type: "give_up"; text: string }
  | { type: "board"; placed: Point[] }
  | { type: "head"; pose: number[] };

export type Status = { kind: "announce" | "give_up"; text: string } | null;

export type ViewerState = {
  frame: FrameEvent | null;
  status: Status;
  placed: string[]; // "row,col" keys, front coordinates
  highlight: { key: string; at: number } | null;
  headPose: number[] | null;
};

export const HIGHLIGHT_MS = 2000;

export const cellKey = (row: number, col: number) => `${row},${col}`;

export const initialState: ViewerState = { frame: null, status: null, placed: [], highlight: null, headPose: null };

// `now` is passed in (ms) so the reducer stays pure and testable.
export function reduce(state: ViewerState, event: ViewerEvent, now: number): ViewerState {
  switch (event.type) {
    case "frame":
      return { ...state, frame: event };
    case "announce": {
      const key = cellKey(event.row, event.col);
      const placed = state.placed.includes(key) ? state.placed : [...state.placed, key];
      return { ...state, placed, status: { kind: "announce", text: event.text }, highlight: { key, at: now } };
    }
    case "give_up":
      return { ...state, status: { kind: "give_up", text: event.text } };
    case "board": {
      const placed = event.placed.map(([r, c]) => cellKey(r, c));
      const highlight = state.highlight && placed.includes(state.highlight.key) ? state.highlight : null;
      return { ...state, placed, highlight, status: placed.length === 0 ? null : state.status };
    }
    case "head":
      return { ...state, headPose: event.pose };
    default:
      return state;
  }
}

// A reset is page-local, never sent by the server: on every (re)connect the server replays its
// current board, so the page starts clean and a restarted server cannot leave a stale board behind.
export type ViewerAction = ViewerEvent | { type: "reset" };

export function reduceAction(state: ViewerState, action: ViewerAction, now: number): ViewerState {
  return action.type === "reset" ? initialState : reduce(state, action, now);
}

export function describeDecision(d: Decision): string {
  return d.kind === "read"
    ? `Row ${d.row + 1}, column ${d.col + 1}, turn ${d.turn}`
    : d.reason.replace(/_/g, " ");
}
