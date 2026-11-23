import { useEffect, useReducer, useState } from "react";
import { initialState, reduce, type ViewerEvent, type ViewerState } from "./state";

export const RECONNECT_MS = 1000;

// Subscribes to /events. On any error the stream is closed and reopened after RECONNECT_MS,
// so the page recovers from a server restart without relying on the browser's own retry.
export function useViewer(url = "/events"): { state: ViewerState; connected: boolean } {
  const [state, dispatch] = useReducer(
    (s: ViewerState, a: { event: ViewerEvent; now: number }) => reduce(s, a.event, a.now),
    initialState,
  );
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let source: EventSource | null = null;
    let timer: number | undefined;
    let stopped = false;

    const open = () => {
      source = new EventSource(url);
      source.onopen = () => setConnected(true);
      source.onmessage = (m) => {
        try {
          dispatch({ event: JSON.parse(m.data) as ViewerEvent, now: performance.now() });
        } catch {
          // a malformed event is dropped; the next one replaces it
        }
      };
      source.onerror = () => {
        setConnected(false);
        source?.close();
        if (!stopped) timer = window.setTimeout(open, RECONNECT_MS);
      };
    };
    open();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      source?.close();
    };
  }, [url]);

  return { state, connected };
}
