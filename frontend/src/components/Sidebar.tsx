import type { ToolSpec } from "../types";

interface SidebarProps {
  tools: ToolSpec[];
  active: string;
  onSelect: (key: string) => void;
  connected: boolean;
}

const CONNECTION_KEY = "__connection__";
const HOWTO_KEY = "__howto__";

function Mark() {
  return (
    <div className="flex items-center gap-2 px-4 py-5">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-arango-green-brand text-sm font-bold text-white">
        A
      </div>
      <div className="leading-tight">
        <div className="text-sm font-semibold text-white">Arango</div>
        <div className="text-[11px] text-white/60">Tools</div>
      </div>
    </div>
  );
}

export default function Sidebar({ tools, active, onSelect, connected }: SidebarProps) {
  const itemClass = (isActive: boolean, disabled: boolean) =>
    [
      "flex w-full items-center justify-between gap-2 px-4 py-2 text-left text-sm transition-colors",
      isActive ? "bg-white/15 text-white" : "text-white/80 hover:bg-white/10 hover:text-white",
      disabled ? "cursor-not-allowed opacity-40 hover:bg-transparent" : "cursor-pointer",
    ].join(" ");

  return (
    <nav className="flex h-full w-60 flex-col bg-arango-menu" aria-label="Tools">
      <Mark />
      <button
        type="button"
        className={itemClass(active === CONNECTION_KEY, false)}
        onClick={() => onSelect(CONNECTION_KEY)}
      >
        <span>Connection</span>
        <span
          className={[
            "h-2 w-2 rounded-full",
            connected ? "bg-arango-green-brand" : "bg-arango-error",
          ].join(" ")}
          aria-hidden
        />
      </button>
      <button
        type="button"
        className={itemClass(active === HOWTO_KEY, false)}
        onClick={() => onSelect(HOWTO_KEY)}
      >
        <span>How To</span>
      </button>

      <div className="mt-3 px-4 pb-1 text-[11px] uppercase tracking-wide text-white/40">
        Tools
      </div>
      <div className="flex-1 overflow-y-auto pb-4">
        {tools.map((tool) => {
          const disabled = tool.connects && !connected;
          return (
            <button
              key={tool.name}
              type="button"
              disabled={disabled}
              className={itemClass(active === tool.name, disabled)}
              onClick={() => !disabled && onSelect(tool.name)}
              title={disabled ? "Connect to an instance first" : tool.description}
            >
              <span>{tool.title}</span>
              <span className="font-mono text-[10px] text-white/40">{tool.binary}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

export { CONNECTION_KEY, HOWTO_KEY };
