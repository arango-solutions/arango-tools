import type { RunEvent } from "../types";

export interface ToolRunHandle {
  cancel: () => void;
  close: () => void;
}

/**
 * Open a WebSocket to run a tool and stream events back via `onEvent`.
 * Returns a handle to cancel (terminate the process) or close the socket.
 */
export function runTool(
  name: string,
  params: Record<string, unknown>,
  onEvent: (event: RunEvent) => void,
): ToolRunHandle {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${window.location.host}/api/tools/${name}/run`;
  const ws = new WebSocket(url);

  ws.onopen = () => {
    ws.send(JSON.stringify({ params }));
  };

  ws.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as RunEvent);
    } catch {
      onEvent({ type: "stderr", data: String(msg.data) });
    }
  };

  ws.onerror = () => {
    onEvent({ type: "error", data: "WebSocket connection error." });
  };

  return {
    cancel: () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "cancel" }));
      }
    },
    close: () => ws.close(),
  };
}
