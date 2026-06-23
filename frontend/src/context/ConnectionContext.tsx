import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "../api/client";
import type { ConnectionRequest, ConnectionStatus, ConnectionTestResult } from "../types";

interface ConnectionContextValue {
  status: ConnectionStatus | null;
  loading: boolean;
  connected: boolean;
  refresh: () => Promise<void>;
  connect: (req: ConnectionRequest) => Promise<ConnectionTestResult>;
  test: (req: ConnectionRequest) => Promise<ConnectionTestResult>;
  disconnect: () => Promise<void>;
}

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

export function ConnectionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const s = await api.getConnection();
    setStatus(s);
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const connect = useCallback(
    async (req: ConnectionRequest) => {
      const resp = await api.setConnection(req);
      if (resp.test.ok) {
        await refresh();
      }
      return resp.test;
    },
    [refresh],
  );

  const test = useCallback((req: ConnectionRequest) => api.testConnection(req), []);

  const disconnect = useCallback(async () => {
    const s = await api.clearConnection();
    setStatus(s);
  }, []);

  const value = useMemo<ConnectionContextValue>(
    () => ({
      status,
      loading,
      connected: Boolean(status?.connected),
      refresh,
      connect,
      test,
      disconnect,
    }),
    [status, loading, refresh, connect, test, disconnect],
  );

  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>;
}

export function useConnection(): ConnectionContextValue {
  const ctx = useContext(ConnectionContext);
  if (!ctx) {
    throw new Error("useConnection must be used within a ConnectionProvider");
  }
  return ctx;
}
