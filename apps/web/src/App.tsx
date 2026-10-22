import { FormEvent, useEffect, useRef, useState } from "react";

type ServiceState = "checking" | "ready" | "unavailable";
type WorkflowState =
  "draft" | "creating" | "queued" | "running" | "completed" | "decided" | "failed";

interface SessionResponse {
  user: { display_name: string; email: string };
  tenant: { display_name: string };
  roles: string[];
}

interface Scenario {
  tenant_id: string;
  author_id: string;
  approver_id: string;
  rule_definition_id: string;
  baseline_rule_version_id: string;
  dataset_manifest_id: string;
  risk_policy_version_id: string;
  engine_version: string;
}

interface Simulation {
  id: string;
  status: string;
  version: number;
  result_checksum: string | null;
}

interface Impact {
  simulation_id: string;
  result_checksum: string;
  summary: {
    event_count: number;
    changed_event_count: number;
    total_financial_delta_minor_units: number;
    maximum_financial_delta_minor_units: number;
    currency: string;
  };
  risk: { policy_version_id: string; decision: "allow" | "block" | "error"; reasons: string[] };
}

interface Gate {
  id: string;
  decision: "allow" | "block";
  evidence_checksum: string;
  reasons: string[];
}

async function api<T>(path: string, init?: RequestInit): Promise<{ body: T; etag: string | null }> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const problem = (await response.json()) as { detail?: string };
    throw new Error(problem.detail ?? "The request could not be completed.");
  }
  return { body: (await response.json()) as T, etag: response.headers.get("ETag") };
}

function newKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function App() {
  const [service, setService] = useState<ServiceState>("checking");
  const [workflow, setWorkflow] = useState<WorkflowState>("draft");
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [increment, setIncrement] = useState(10);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [gate, setGate] = useState<Gate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollTimer = useRef<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api<{ status: string }>("/health/ready", { signal: controller.signal }),
      api<SessionResponse>("/v1/dev/session", { signal: controller.signal }),
      api<Scenario>("/v1/dev/scenario", { signal: controller.signal }),
    ])
      .then(([, sessionResult, scenarioResult]) => {
        setSession(sessionResult.body);
        setScenario(scenarioResult.body);
        setService("ready");
      })
      .catch((reason: unknown) => {
        if ((reason as Error).name !== "AbortError") setService("unavailable");
      });
    return () => controller.abort();
  }, []);

  useEffect(
    () => () => {
      if (pollTimer.current !== null) window.clearTimeout(pollTimer.current);
    },
    [],
  );

  const poll = async (id: string) => {
    try {
      const current = (await api<Simulation>(`/v1/simulations/${id}`)).body;
      setSimulation(current);
      if (current.status === "completed") {
        setImpact((await api<Impact>(`/v1/simulations/${id}/impact`)).body);
        setWorkflow("completed");
      } else if (current.status === "failed" || current.status === "cancelled") {
        setWorkflow("failed");
        setError("The worker did not complete this simulation.");
      } else {
        setWorkflow(current.status === "running" ? "running" : "queued");
        pollTimer.current = window.setTimeout(() => void poll(id), 500);
      }
    } catch (reason) {
      setWorkflow("failed");
      setError((reason as Error).message);
    }
  };

  const startSimulation = async (event: FormEvent) => {
    event.preventDefault();
    if (!scenario) return;
    setWorkflow("creating");
    setError(null);
    setImpact(null);
    setGate(null);
    setCandidateId(null);
    try {
      const candidate = (
        await api<{ id: string }>(`/v1/tenants/${scenario.tenant_id}/rule-versions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Actor-ID": scenario.author_id,
            "Idempotency-Key": newKey("rule"),
          },
          body: JSON.stringify({
            definition_id: scenario.rule_definition_id,
            family: "rounding",
            effective_from: "2026-10-01",
            effective_until: null,
            timezone: "UTC",
            rule: { increment_minor_units: increment, mode: "half_up" },
            dependency_version_ids: [],
          }),
        })
      ).body;
      setCandidateId(candidate.id);
      const created = (
        await api<Simulation>("/v1/simulations", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Actor-ID": scenario.author_id,
            "Idempotency-Key": newKey("simulation"),
          },
          body: JSON.stringify({
            tenant_id: scenario.tenant_id,
            baseline_rule_version_id: scenario.baseline_rule_version_id,
            candidate_rule_version_id: candidate.id,
            dataset_manifest_id: scenario.dataset_manifest_id,
            engine_version: scenario.engine_version,
            risk_policy_version_id: scenario.risk_policy_version_id,
          }),
        })
      ).body;
      setSimulation(created);
      setWorkflow("queued");
      await poll(created.id);
    } catch (reason) {
      setWorkflow("failed");
      setError((reason as Error).message);
    }
  };

  const decide = async (decision: "approve" | "reject") => {
    if (!scenario || !simulation || !impact) return;
    setError(null);
    try {
      const approval = (
        await api<{ id: string }>(`/v1/simulations/${simulation.id}/approvals`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Actor-ID": scenario.approver_id,
            "Idempotency-Key": newKey("approval"),
            "If-Match": `"${simulation.version}"`,
          },
          body: JSON.stringify({
            result_checksum: impact.result_checksum,
            policy_version_id: impact.risk.policy_version_id,
            decision,
            rationale: "Reviewed against the Phase 3 deterministic scenario pack.",
          }),
        })
      ).body;
      const result = (
        await api<Gate>("/v1/release-gates/evaluate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Actor-ID": scenario.approver_id,
            "Idempotency-Key": newKey("gate"),
          },
          body: JSON.stringify({
            simulation_id: simulation.id,
            approval_id: approval.id,
            result_checksum: impact.result_checksum,
            policy_version_id: impact.risk.policy_version_id,
          }),
        })
      ).body;
      setGate(result);
      setWorkflow("decided");
    } catch (reason) {
      setError((reason as Error).message);
    }
  };

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="/" aria-label="RuleTwin home">
          <span className="brand-mark">RT</span>
          <span>RuleTwin</span>
        </a>
        <span className={`status status-${service}`} role="status">
          <span className="status-dot" />
          {service === "checking"
            ? "Checking services"
            : service === "ready"
              ? "Ready"
              : "Unavailable"}
        </span>
      </header>

      <section className="hero compact">
        <div>
          <p className="eyebrow">First vertical slice · deterministic evidence</p>
          <h1>Test the rule before the rule tests your customers.</h1>
          <p className="lede">
            Compare a proposed rounding rule against the current version across 100 versioned
            synthetic events.
          </p>
        </div>
        <aside className="identity">
          <span>Working as</span>
          <strong>{session?.user.display_name ?? "Synthetic analyst"}</strong>
          <small>{session?.tenant.display_name ?? "Loading tenant"}</small>
        </aside>
      </section>

      <section className="workflow" aria-label="Rule simulation workflow">
        <form className="panel proposal" onSubmit={(event) => void startSimulation(event)}>
          <div className="step">
            <span>01</span> Propose
          </div>
          <h2>Invoice rounding</h2>
          <p>Baseline rounds to the nearest cent. Choose the candidate cash-rounding increment.</p>
          <label htmlFor="increment">Candidate increment</label>
          <select
            id="increment"
            value={increment}
            onChange={(event) => setIncrement(Number(event.target.value))}
          >
            <option value={5}>5 minor units · expected allow</option>
            <option value={10}>10 minor units · expected block</option>
          </select>
          <div className="dataset-row">
            <span>Dataset</span>
            <strong>rounding-boundaries-v1</strong>
            <small>100 events · seed 314159</small>
          </div>
          <button
            type="submit"
            disabled={service !== "ready" || ["creating", "queued", "running"].includes(workflow)}
          >
            {workflow === "creating"
              ? "Creating evidence…"
              : workflow === "queued" || workflow === "running"
                ? "Simulation running…"
                : "Run comparison"}
          </button>
        </form>

        <section className="panel results" aria-live="polite">
          <div className="step">
            <span>02</span> Inspect
          </div>
          {!impact ? (
            <div className="empty-state">
              <div className="pulse-ring" />
              <h2>
                {workflow === "queued" || workflow === "running"
                  ? "Replaying both versions"
                  : "Evidence will appear here"}
              </h2>
              <p>
                {workflow === "queued" || workflow === "running"
                  ? `Worker state: ${workflow}`
                  : "Run the comparison to inspect deterministic impact and risk."}
              </p>
            </div>
          ) : (
            <>
              <div className={`risk-banner risk-${impact.risk.decision}`}>
                <span>Policy result</span>
                <strong>{impact.risk.decision}</strong>
              </div>
              <div className="metrics">
                <div>
                  <strong>{impact.summary.changed_event_count}</strong>
                  <span>events changed</span>
                </div>
                <div>
                  <strong>{impact.summary.maximum_financial_delta_minor_units}¢</strong>
                  <span>maximum delta</span>
                </div>
                <div>
                  <strong>{impact.summary.total_financial_delta_minor_units}¢</strong>
                  <span>net delta</span>
                </div>
              </div>
              <p className="reason">{impact.risk.reasons[0]}</p>
              <code className="checksum">{impact.result_checksum}</code>
              <dl className="evidence-list" aria-label="Immutable evidence tuple">
                <div>
                  <dt>Simulation ID</dt>
                  <dd>{simulation?.id}</dd>
                </div>
                <div>
                  <dt>Baseline rule ID</dt>
                  <dd>{scenario?.baseline_rule_version_id}</dd>
                </div>
                <div>
                  <dt>Candidate rule ID</dt>
                  <dd>{candidateId}</dd>
                </div>
                <div>
                  <dt>Dataset ID</dt>
                  <dd>{scenario?.dataset_manifest_id}</dd>
                </div>
                <div>
                  <dt>Policy ID</dt>
                  <dd>{impact.risk.policy_version_id}</dd>
                </div>
                <div>
                  <dt>Engine version</dt>
                  <dd>{scenario?.engine_version}</dd>
                </div>
              </dl>
            </>
          )}
        </section>

        <section className="panel decision">
          <div className="step">
            <span>03</span> Decide
          </div>
          <h2>Bind a decision to this evidence</h2>
          <p>The separate synthetic approver signs the exact result checksum and policy version.</p>
          <div className="decision-actions">
            <button
              className="secondary"
              disabled={!impact || workflow === "decided"}
              onClick={() => void decide("reject")}
            >
              Reject
            </button>
            <button
              disabled={!impact || workflow === "decided"}
              onClick={() => void decide("approve")}
            >
              Approve evidence
            </button>
          </div>
          {gate && (
            <div className={`gate gate-${gate.decision}`} role="status">
              <span>Release gate</span>
              <strong>{gate.decision}</strong>
              <small>{gate.reasons[0]}</small>
            </div>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </section>
      </section>
    </main>
  );
}
