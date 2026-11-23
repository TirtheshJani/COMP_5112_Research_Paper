import type { Status } from "./state";

export function StatusLine({ status }: { status: Status }) {
  return (
    <header className={`status ${status?.kind ?? "idle"}`} data-testid="status" aria-live="polite">
      {status ? status.text : "Show Reachy the back of a piece."}
    </header>
  );
}
