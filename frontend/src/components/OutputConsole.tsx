import { useEffect, useRef } from "react";

export interface ConsoleLine {
  kind: "stdout" | "stderr" | "error" | "info";
  text: string;
}

interface OutputConsoleProps {
  lines: ConsoleLine[];
  running: boolean;
  exitCode: number | null;
}

const kindClass: Record<ConsoleLine["kind"], string> = {
  stdout: "text-gray-100",
  stderr: "text-amber-300",
  error: "text-red-400",
  info: "text-gray-400",
};

export default function OutputConsole({ lines, running, exitCode }: OutputConsoleProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-sm font-medium text-arango-text">Output</div>
        {exitCode !== null && (
          <span
            className={[
              "rounded-full px-2 py-0.5 text-[11px]",
              exitCode === 0 ? "bg-arango-green-bg text-arango-green" : "bg-red-50 text-arango-error",
            ].join(" ")}
          >
            exit {exitCode}
          </span>
        )}
        {running && (
          <span className="rounded-full bg-arango-green-bg px-2 py-0.5 text-[11px] text-arango-green">
            running…
          </span>
        )}
      </div>
      <div className="flex-1 overflow-auto rounded-md border border-arango-border bg-[#1a1a1a] p-3 font-mono text-xs">
        {lines.length === 0 ? (
          <div className="text-arango-muted">No output yet. Run the tool to see results.</div>
        ) : (
          lines.map((line, i) => (
            <div key={i} className={`whitespace-pre-wrap break-words ${kindClass[line.kind]}`}>
              {line.text}
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
