interface CommandPreviewProps {
  argv: string[];
  errors: string[];
}

function quote(token: string): string {
  return /[\s"']/.test(token) ? `"${token.replace(/"/g, '\\"')}"` : token;
}

export default function CommandPreview({ argv, errors }: CommandPreviewProps) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium text-arango-text">Command preview</div>
      <pre className="overflow-x-auto rounded-md border border-arango-border bg-arango-panel p-3 font-mono text-xs text-arango-text">
        {argv.length ? argv.map(quote).join(" ") : "—"}
      </pre>
      {errors.length > 0 && (
        <ul className="space-y-1 text-xs text-arango-error">
          {errors.map((err) => (
            <li key={err}>• {err}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
