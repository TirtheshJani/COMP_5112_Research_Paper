import { BoardPanel } from "./BoardPanel";
import { CameraPanel } from "./CameraPanel";
import { ScenePanel } from "./ScenePanel";
import { StatusLine } from "./StatusLine";
import { useViewer } from "./useViewer";

export function App() {
  const { state, connected } = useViewer();
  return (
    <div className="app">
      <StatusLine status={state.status} />
      <main>
        <CameraPanel frame={state.frame} />
        <ScenePanel frame={state.frame} headPose={state.headPose} />
        <BoardPanel placed={state.placed} highlight={state.highlight} />
      </main>
      <footer>
        <span className={`connection ${connected ? "up" : "down"}`} data-testid="connection">
          {connected ? "live" : "disconnected, retrying"}
        </span>
        <button type="button" onClick={() => fetch("/reset", { method: "POST" }).catch(() => undefined)}>
          Reset board
        </button>
      </footer>
    </div>
  );
}
