export type FieldType = "string" | "int" | "bool" | "enum" | "path" | "list" | "text";

export interface FieldSpec {
  key: string;
  flag: string;
  type: FieldType;
  label: string;
  help: string;
  default: unknown;
  required: boolean;
  positional: boolean;
  repeatable: boolean;
  options: string[];
  placeholder: string;
  group: "Common" | "Advanced";
}

export interface ToolSpec {
  name: string;
  binary: string;
  title: string;
  description: string;
  connects: boolean;
  fields: FieldSpec[];
  doc_url: string;
}

export interface ConnectionTestResult {
  ok: boolean;
  message: string;
  version?: string | null;
  server?: string | null;
}

export interface EnvDefaults {
  endpoint: string;
  database: string;
  username: string;
  has_password: boolean;
}

export interface ConnectionCurrent {
  endpoint: string;
  database: string;
  username: string;
  password: string;
  source: "env" | "manual";
  has_password: boolean;
}

export interface ConnectionStatus {
  connected: boolean;
  env_available: boolean;
  env_defaults: EnvDefaults | null;
  current: ConnectionCurrent | null;
}

export interface ConnectionResponse {
  test: ConnectionTestResult;
  current: ConnectionCurrent | null;
}

export interface ConnectionRequest {
  source: "manual" | "env";
  endpoint?: string;
  database?: string;
  username?: string;
  password?: string;
}

export interface PreviewResponse {
  argv: string[];
  errors: string[];
  connected: boolean;
}

export type RunEvent =
  | { type: "stdout"; data: string }
  | { type: "stderr"; data: string }
  | { type: "error"; data: string }
  | { type: "command"; data: string[] }
  | { type: "exit"; code: number };
