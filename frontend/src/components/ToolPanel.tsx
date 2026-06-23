import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { runTool, type ToolRunHandle } from "../api/ws";
import type { PreviewResponse, RunEvent, ToolSpec } from "../types";
import CommandPreview from "./CommandPreview";
import OutputConsole, { type ConsoleLine } from "./OutputConsole";
import ToolForm, { initialValues, type FormValues } from "./ToolForm";

interface ToolPanelProps {
  spec: ToolSpec;
}

export default function ToolPanel({ spec }: ToolPanelProps) {
  const [values, setValues] = useState<FormValues>(() => initialValues(spec));
  const [preview, setPreview] = useState<PreviewResponse>({ argv: [], errors: [], connected: false });
  const [lines, setLines] = useState<ConsoleLine[]>([]);
  const [running, setRunning] = useState(false);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const runHandle = useRef<ToolRunHandle | null>(null);

  useEffect(() => {
    setValues(initialValues(spec));
    setLines([]);
    setExitCode(null);
    setRunning(false);
  }, [spec]);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      api
        .preview(spec.name, values)
        .then((p) => !cancelled && setPreview(p))
        .catch(() => undefined);
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [spec.name, values]);

  const onChange = useCallback((key: string, value: unknown) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const append = useCallback((line: ConsoleLine) => {
    setLines((prev) => [...prev, line]);
  }, []);

  const handleEvent = useCallback(
    (event: RunEvent) => {
      switch (event.type) {
        case "command":
          append({ kind: "info", text: `$ ${event.data.join(" ")}` });
          break;
        case "stdout":
          append({ kind: "stdout", text: event.data });
          break;
        case "stderr":
          append({ kind: "stderr", text: event.data });
          break;
        case "error":
          append({ kind: "error", text: event.data });
          break;
        case "exit":
          setExitCode(event.code);
          setRunning(false);
          append({
            kind: event.code === 0 ? "info" : "error",
            text: `Process exited with code ${event.code}.`,
          });
          runHandle.current?.close();
          runHandle.current = null;
          break;
      }
    },
    [append],
  );

  const handleRun = () => {
    setLines([]);
    setExitCode(null);
    setRunning(true);
    runHandle.current = runTool(spec.name, values, handleEvent);
  };

  const handleCancel = () => {
    runHandle.current?.cancel();
    append({ kind: "info", text: "Cancellation requested…" });
  };

  useEffect(() => () => runHandle.current?.close(), []);

  const canRun = useMemo(
    () => preview.errors.length === 0 && !running,
    [preview.errors.length, running],
  );

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-arango-text">{spec.title}</h2>
        <p className="mt-1 text-sm text-arango-muted">
          {spec.description}{" "}
          <a
            href={spec.doc_url}
            target="_blank"
            rel="noreferrer"
            className="text-arango-green hover:underline"
          >
            docs ↗
          </a>
        </p>
      </div>

      <div className="grid flex-1 grid-cols-1 gap-6 overflow-hidden lg:grid-cols-2">
        <div className="flex flex-col gap-4 overflow-auto pr-1">
          <ToolForm spec={spec} values={values} onChange={onChange} />
          <CommandPreview argv={preview.argv} errors={preview.errors} />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleRun}
              disabled={!canRun}
              className="rounded-md bg-arango-green px-4 py-2 text-sm font-medium text-white hover:bg-arango-green-hover disabled:opacity-50"
            >
              Run
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={!running}
              className="rounded-md border border-arango-border px-4 py-2 text-sm text-arango-text hover:bg-arango-panel disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>

        <div className="min-h-[300px] overflow-hidden lg:h-full">
          <OutputConsole lines={lines} running={running} exitCode={exitCode} />
        </div>
      </div>
    </div>
  );
}
