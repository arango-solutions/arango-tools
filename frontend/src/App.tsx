import { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import ConnectionPanel from "./components/ConnectionPanel";
import Sidebar, { CONNECTION_KEY } from "./components/Sidebar";
import ToolPanel from "./components/ToolPanel";
import { useConnection } from "./context/ConnectionContext";
import type { ToolSpec } from "./types";

export default function App() {
  const { connected, loading } = useConnection();
  const [tools, setTools] = useState<ToolSpec[]>([]);
  const [active, setActive] = useState<string>(CONNECTION_KEY);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getTools()
      .then(setTools)
      .catch((e) => setError(String(e)));
  }, []);

  const activeTool = useMemo(
    () => tools.find((t) => t.name === active) ?? null,
    [tools, active],
  );

  // If the active tool needs a connection that was lost, fall back to Connection.
  useEffect(() => {
    if (activeTool?.connects && !connected) {
      setActive(CONNECTION_KEY);
    }
  }, [activeTool, connected]);

  return (
    <div className="flex h-screen overflow-hidden bg-arango-page">
      <Sidebar tools={tools} active={active} onSelect={setActive} connected={connected} />
      <main className="flex-1 overflow-hidden">
        <div className="h-full overflow-auto p-8">
          {error && (
            <div className="mb-4 rounded-md border border-arango-error bg-red-50 px-4 py-3 text-sm text-arango-error">
              {error}
            </div>
          )}
          {loading ? (
            <div className="text-sm text-arango-muted">Loading…</div>
          ) : active === CONNECTION_KEY || !activeTool ? (
            <ConnectionPanel />
          ) : (
            <div className="h-full">
              <ToolPanel key={activeTool.name} spec={activeTool} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
