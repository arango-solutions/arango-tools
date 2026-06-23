import { useEffect, useState } from "react";
import { useConnection } from "../context/ConnectionContext";
import type { ConnectionRequest, ConnectionTestResult } from "../types";

type Mode = "env" | "manual";

export default function ConnectionPanel() {
  const { status, connected, connect, test, disconnect } = useConnection();
  const envAvailable = Boolean(status?.env_available);

  const [mode, setMode] = useState<Mode>(envAvailable ? "env" : "manual");
  const [endpoint, setEndpoint] = useState("http://localhost:8529");
  const [database, setDatabase] = useState("_system");
  const [username, setUsername] = useState("root");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ConnectionTestResult | null>(null);

  useEffect(() => {
    if (envAvailable) setMode("env");
  }, [envAvailable]);

  useEffect(() => {
    const cur = status?.current;
    if (cur && cur.source === "manual") {
      setEndpoint(cur.endpoint);
      setDatabase(cur.database);
      setUsername(cur.username);
    }
  }, [status]);

  const buildRequest = (): ConnectionRequest =>
    mode === "env"
      ? { source: "env" }
      : { source: "manual", endpoint, database, username, password };

  const handleTest = async () => {
    setBusy(true);
    setResult(null);
    try {
      setResult(await test(buildRequest()));
    } catch (e) {
      setResult({ ok: false, message: String(e) });
    } finally {
      setBusy(false);
    }
  };

  const handleConnect = async () => {
    setBusy(true);
    setResult(null);
    try {
      setResult(await connect(buildRequest()));
    } catch (e) {
      setResult({ ok: false, message: String(e) });
    } finally {
      setBusy(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-arango-border bg-white px-3 py-2 text-sm text-arango-text outline-none focus:border-arango-green focus:ring-1 focus:ring-arango-green";
  const labelClass = "mb-1 block text-sm font-medium text-arango-text";

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold text-arango-text">Connection</h2>
      <p className="mt-1 text-sm text-arango-muted">
        Connect to an Arango instance using your <code className="font-mono">.env</code> file or by
        entering credentials manually.
      </p>

      {connected && status?.current && (
        <div className="mt-4 flex items-center justify-between rounded-md border border-arango-green bg-arango-green-bg px-4 py-3">
          <div className="text-sm text-arango-text">
            Connected to <span className="font-mono">{status.current.endpoint}</span> /
            <span className="font-mono"> {status.current.database}</span>
            <span className="ml-2 rounded-full bg-arango-green px-2 py-0.5 text-[11px] text-white">
              {status.current.source}
            </span>
          </div>
          <button
            type="button"
            onClick={() => disconnect()}
            className="rounded-md border border-arango-border px-3 py-1.5 text-sm text-arango-text hover:bg-arango-panel"
          >
            Disconnect
          </button>
        </div>
      )}

      <div className="mt-6 inline-flex rounded-md border border-arango-border p-1">
        <button
          type="button"
          onClick={() => setMode("env")}
          disabled={!envAvailable}
          className={[
            "rounded px-4 py-1.5 text-sm transition-colors",
            mode === "env" ? "bg-arango-green-bg text-arango-green" : "text-arango-text",
            !envAvailable ? "cursor-not-allowed opacity-40" : "",
          ].join(" ")}
        >
          Use .env {envAvailable ? "" : "(none found)"}
        </button>
        <button
          type="button"
          onClick={() => setMode("manual")}
          className={[
            "rounded px-4 py-1.5 text-sm transition-colors",
            mode === "manual" ? "bg-arango-green-bg text-arango-green" : "text-arango-text",
          ].join(" ")}
        >
          Manual
        </button>
      </div>

      {mode === "env" ? (
        <div className="mt-4 rounded-md border border-arango-border bg-arango-panel p-4 text-sm text-arango-text">
          {status?.env_defaults ? (
            <ul className="space-y-1 font-mono text-xs">
              <li>endpoint: {status.env_defaults.endpoint}</li>
              <li>database: {status.env_defaults.database}</li>
              <li>username: {status.env_defaults.username}</li>
              <li>password: {status.env_defaults.has_password ? "••••••••" : "(empty)"}</li>
            </ul>
          ) : (
            <span className="text-arango-muted">No .env defaults found on the backend.</span>
          )}
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="endpoint">
              Endpoint / URI
            </label>
            <input
              id="endpoint"
              className={inputClass}
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="http://localhost:8529"
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="database">
              Database
            </label>
            <input
              id="database"
              className={inputClass}
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className={inputClass}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass} htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className={inputClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="mt-5 flex items-center gap-3">
        <button
          type="button"
          onClick={handleConnect}
          disabled={busy}
          className="rounded-md bg-arango-green px-4 py-2 text-sm font-medium text-white hover:bg-arango-green-hover disabled:opacity-50"
        >
          {busy ? "Working…" : "Connect"}
        </button>
        <button
          type="button"
          onClick={handleTest}
          disabled={busy}
          className="rounded-md border border-arango-border px-4 py-2 text-sm text-arango-text hover:bg-arango-panel disabled:opacity-50"
        >
          Test connection
        </button>
      </div>

      {result && (
        <div
          role="status"
          className={[
            "mt-4 rounded-md px-4 py-3 text-sm",
            result.ok
              ? "border border-arango-green bg-arango-green-bg text-arango-green"
              : "border border-arango-error bg-red-50 text-arango-error",
          ].join(" ")}
        >
          {result.message}
          {result.ok && result.version && (
            <span className="ml-1">
              (Arango {result.version}
              {result.server ? `, ${result.server}` : ""})
            </span>
          )}
        </div>
      )}
    </div>
  );
}
