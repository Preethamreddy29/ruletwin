import { useEffect, useState } from "react";

type ServiceState = "checking" | "ready" | "unavailable";

interface VersionResponse {
  service: string;
  version: string;
}

interface SessionResponse {
  user: { display_name: string; email: string };
  tenant: { display_name: string };
  roles: string[];
  synthetic: boolean;
}

export function App() {
  const [state, setState] = useState<ServiceState>("checking");
  const [version, setVersion] = useState<VersionResponse | null>(null);
  const [session, setSession] = useState<SessionResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        const [healthResponse, versionResponse, sessionResponse] = await Promise.all([
          fetch("/api/health/ready", { signal: controller.signal }),
          fetch("/api/version", { signal: controller.signal }),
          fetch("/api/v1/dev/session", { signal: controller.signal }),
        ]);
        if (!healthResponse.ok || !versionResponse.ok || !sessionResponse.ok) {
          throw new Error("Foundation service is not ready");
        }
        setVersion((await versionResponse.json()) as VersionResponse);
        setSession((await sessionResponse.json()) as SessionResponse);
        setState("ready");
      } catch (error) {
        if ((error as Error).name !== "AbortError") setState("unavailable");
      }
    };
    void load();
    return () => controller.abort();
  }, []);

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="/" aria-label="RuleTwin home">
          <span className="brand-mark">RT</span>
          <span>RuleTwin</span>
        </a>
        <span className={`status status-${state}`} role="status">
          <span className="status-dot" />
          {state === "checking" ? "Checking services" : state === "ready" ? "Ready" : "Unavailable"}
        </span>
      </header>

      <section className="hero">
        <p className="eyebrow">Decision integrity infrastructure</p>
        <h1>Understand a rule change before it reaches production.</h1>
        <p className="lede">
          RuleTwin will replay synthetic events against baseline and candidate rule versions,
          compare their effects, and produce reproducible release evidence.
        </p>
      </section>

      <section className="grid" aria-label="Foundation status">
        <article className="card card-primary">
          <p className="card-label">Current milestone</p>
          <h2>Engineering foundation</h2>
          <p>
            The service shell, database migration path, outbox worker, health checks and delivery
            controls are connected. Product simulation begins in Phase 3.
          </p>
          <div className="version">{version?.version ?? "Waiting for API"}</div>
        </article>

        <article className="card">
          <p className="card-label">Development identity</p>
          <h2>{session?.user.display_name ?? "Synthetic user"}</h2>
          <dl>
            <div>
              <dt>Tenant</dt>
              <dd>{session?.tenant.display_name ?? "Waiting for session"}</dd>
            </div>
            <div>
              <dt>Roles</dt>
              <dd>{session?.roles.join(" · ") ?? "—"}</dd>
            </div>
          </dl>
          <p className="synthetic-note">Synthetic development data only</p>
        </article>

        <article className="card">
          <p className="card-label">Foundation signals</p>
          <ul className="signal-list">
            <li>
              <span>API</span>
              <strong>{state}</strong>
            </li>
            <li>
              <span>Database</span>
              <strong>{state === "ready" ? "reachable" : "unknown"}</strong>
            </li>
            <li>
              <span>Worker</span>
              <strong>heartbeat enabled</strong>
            </li>
            <li>
              <span>Metrics</span>
              <strong>exposed</strong>
            </li>
          </ul>
        </article>
      </section>
    </main>
  );
}
