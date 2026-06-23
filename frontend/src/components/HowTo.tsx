import type { ReactNode } from "react";

function Code({ children }: { children: string }) {
  return <code className="rounded bg-arango-panel px-1.5 py-0.5 font-mono text-[13px]">{children}</code>;
}

function Block({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto rounded-md border border-arango-border bg-arango-panel p-3 font-mono text-xs text-arango-text">
      {children}
    </pre>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h3 className="text-base font-semibold text-arango-text">{title}</h3>
      {children}
    </section>
  );
}

export default function HowTo() {
  return (
    <div className="max-w-3xl space-y-8 pb-8">
      <div>
        <h2 className="text-xl font-semibold text-arango-text">How To</h2>
        <p className="mt-1 text-sm text-arango-muted">
          What this app does and what it needs in order to actually run the Arango tools.
        </p>
      </div>

      <Section title="What this app is">
        <p className="text-sm leading-relaxed text-arango-text">
          This is a <strong>GUI wrapper around the real Arango command-line programs</strong>. It
          does not reimplement what <Code>arangodump</Code>, <Code>arangoimport</Code>, and the other
          tools do. When you press <strong>Run</strong> on a tool tab, the backend spawns the actual{" "}
          <Code>arango*</Code> executable as a child process and streams its output back to this page
          in real time.
        </p>
      </Section>

      <Section title="The binaries must be on the backend host">
        <p className="text-sm leading-relaxed text-arango-text">
          Because the backend shells out to the real programs, those binaries must physically exist on
          the machine running the FastAPI backend — not on the machine where your browser is open. If a
          binary cannot be found, the run fails gracefully with an error and exit code{" "}
          <Code>127</Code> ("command not found") rather than crashing.
        </p>
      </Section>

      <Section title="1. Install the Arango client tools">
        <p className="text-sm leading-relaxed text-arango-text">
          Install them on the backend host. They ship with a full Arango installation, or you can
          install the client-only package.{" "}
          <a
            className="text-arango-green hover:underline"
            href="https://docs.arango.ai/arangodb/stable/components/tools/"
            target="_blank"
            rel="noreferrer"
          >
            Arango tools documentation ↗
          </a>
        </p>
      </Section>

      <Section title="2. Make them discoverable">
        <p className="text-sm leading-relaxed text-arango-text">
          The backend looks for each binary in <Code>ARANGO_TOOLS_BIN</Code> first, then falls back to
          your system <Code>PATH</Code>. Do one of:
        </p>
        <p className="text-sm text-arango-text">
          Confirm they are on <Code>PATH</Code>:
        </p>
        <Block>which arangodump</Block>
        <p className="text-sm text-arango-text">
          …or point the backend at the install directory in your <Code>.env</Code>:
        </p>
        <Block>ARANGO_TOOLS_BIN=/path/to/arangodb/bin</Block>
      </Section>

      <Section title="3. Connect to an instance">
        <p className="text-sm leading-relaxed text-arango-text">
          Open the <strong>Connection</strong> tab and either use your <Code>.env</Code> defaults or
          enter the endpoint/URI, database, username, and password manually, then{" "}
          <strong>Test connection</strong>. Tools that operate on a server stay disabled until a
          connection succeeds. <Code>http(s)://</Code> endpoints are converted to the tools'{" "}
          <Code>tcp://</Code>/<Code>ssl://</Code> form automatically.
        </p>
      </Section>

      <Section title="Things to keep in mind">
        <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-arango-text">
          <li>
            <strong>Host-dependent:</strong> the installed tools must match the operating system and
            architecture of the backend host.
          </li>
          <li>
            <strong>Paths are the backend's, not yours:</strong> path options (dump output directory,
            import source file, etc.) and the file-only tools <Code>arangovpack</Code> and{" "}
            <Code>arangodb</Code> (Starter) operate on the <em>backend</em> host's filesystem.
          </li>
          <li>
            <strong>Run in a trusted environment:</strong> credentials are passed to the tools as
            command-line flags. They are masked in the command preview and never logged, but the
            backend should run somewhere you trust.
          </li>
          <li>
            <strong>Reproducible deployments:</strong> a common approach is to run the backend inside a
            Docker image that bundles the Arango client tools so they are always present and
            version-matched.
          </li>
        </ul>
      </Section>

      <Section title="Why a tool tab might be disabled">
        <p className="text-sm leading-relaxed text-arango-text">
          Server-backed tools (Dump, Restore, Backup, Import, Export, Bench, Inspect, Shell) require an
          active connection. <Code>arangovpack</Code> (VPack) and <Code>arangodb</Code> (Starter) do
          not connect to a server and are always available.
        </p>
      </Section>
    </div>
  );
}
