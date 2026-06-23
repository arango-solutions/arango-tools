import type {
  ConnectionRequest,
  ConnectionResponse,
  ConnectionStatus,
  ConnectionTestResult,
  PreviewResponse,
  ToolSpec,
} from "../types";

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Request failed (${resp.status}): ${text}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  getConnection: () => jsonFetch<ConnectionStatus>("/api/connection"),

  testConnection: (req: ConnectionRequest) =>
    jsonFetch<ConnectionTestResult>("/api/connection/test", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  setConnection: (req: ConnectionRequest) =>
    jsonFetch<ConnectionResponse>("/api/connection", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  clearConnection: () =>
    jsonFetch<ConnectionStatus>("/api/connection", { method: "DELETE" }),

  getTools: () => jsonFetch<ToolSpec[]>("/api/tools"),

  preview: (name: string, params: Record<string, unknown>) =>
    jsonFetch<PreviewResponse>(`/api/tools/${name}/preview`, {
      method: "POST",
      body: JSON.stringify({ params }),
    }),
};
