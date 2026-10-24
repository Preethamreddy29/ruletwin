import { FormEvent, useEffect, useRef, useState } from "react";

type ServiceState = "checking" | "ready" | "unavailable";
type WorkflowState =
  "draft" | "creating" | "queued" | "running" | "completed" | "reviewed" | "decided" | "failed";

interface IdentityOption {
  key: string;
  display_name: string;
  tenant_id: string;
  tenant: string;
  role: "author" | "reviewer" | "release_approver" | "auditor";
}

interface SessionResponse {
  user: { id: string; display_name: string; email: string };
  tenant: { id: string; slug: string; display_name: string };
  roles: string[];
}

interface Scenario {
  tenant_id: string;
  tenant_display_name: string;
  rule_definition_id: string;
  baseline_rule_version_id: string;
  dataset_manifest_id: string;
  risk_policy_version_id: string;
  engine_version: string;
  seed: number;
  event_count: number;
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

async function api<T>(
  path: string,
  token?: string | null,
  init?: RequestInit,
): Promise<{ body: T; etag: string | null }> {
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    const problem = (await response.json()) as { detail?: string; status?: number };
    const error = new Error(problem.detail ?? "The request could not be completed.");
    Object.assign(error, { status: response.status });
    throw error;
  }
  return { body: (await response.json()) as T, etag: response.headers.get("ETag") };
}

function newKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function App() {
  const [service, setService] = useState<ServiceState>("checking");
  const [workflow, setWorkflow] = useState<WorkflowState>("draft");
  const [identities, setIdentities] = useState<IdentityOption[]>([]);
  const [identityKey, setIdentityKey] = useState("novabill-analyst");
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [increment, setIncrement] = useState(10);
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [workflowTenantId, setWorkflowTenantId] = useState<string | null>(null);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [approvalId, setApprovalId] = useState<string | null>(null);
  const [gate, setGate] = useState<Gate | null>(null);
  const [isolationProof, setIsolationProof] = useState<string | null>(null);
  const [auditCount, setAuditCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollTimer = useRef<number | null>(null);

  const scenario = scenarios.find((item) => item.tenant_id === session?.tenant.id) ?? null;
  const sameTenant = Boolean(session && workflowTenantId === session.tenant.id);
  const role = session?.roles[0] ?? "";

  const signIn = async (key: string) => {
    setError(null);
    setIsolationProof(null);
    setAuditCount(null);
    const issued = (
      await api<{ access_token: string }>("/v1/dev/token", null, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity_key: key }),
      })
    ).body;
    const active = (await api<SessionResponse>("/v1/dev/session", issued.access_token)).body;
    setIdentityKey(key);
    setToken(issued.access_token);
    setSession(active);
  };

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api<{ status: string }>("/health/ready", null, { signal: controller.signal }),
      api<{ items: IdentityOption[] }>("/v1/dev/identities", null, {
        signal: controller.signal,
      }),
      api<{ items: Scenario[] }>("/v1/dev/scenarios", null, { signal: controller.signal }),
    ])
      .then(async ([, identityResult, scenarioResult]) => {
        setIdentities(identityResult.body.items);
        setScenarios(scenarioResult.body.items);
        await signIn("novabill-analyst");
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

  const poll = async (id: string, accessToken: string) => {
    try {
      const current = (await api<Simulation>(`/v1/simulations/${id}`, accessToken)).body;
      setSimulation(current);
      if (current.status === "completed") {
        setImpact((await api<Impact>(`/v1/simulations/${id}/impact`, accessToken)).body);
        setWorkflow("completed");
      } else if (current.status === "failed" || current.status === "cancelled") {
        setWorkflow("failed");
        setError("The worker did not complete this simulation.");
      } else {
        setWorkflow(current.status === "running" ? "running" : "queued");
        pollTimer.current = window.setTimeout(() => void poll(id, accessToken), 500);
      }
    } catch (reason) {
      setWorkflow("failed");
      setError((reason as Error).message);
    }
  };

  const startSimulation = async (event: FormEvent) => {
    event.preventDefault();
    if (!scenario || !token || role !== "author") return;
    setWorkflow("creating");
    setError(null);
    setImpact(null);
    setApprovalId(null);
    setGate(null);
    setIsolationProof(null);
    try {
      const candidate = (
        await api<{ id: string }>(`/v1/tenants/${scenario.tenant_id}/rule-versions`, token, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
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
      const created = (
        await api<Simulation>("/v1/simulations", token, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
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
      setWorkflowTenantId(scenario.tenant_id);
      setSimulation(created);
      setWorkflow("queued");
      await poll(created.id, token);
    } catch (reason) {
      setWorkflow("failed");
      setError((reason as Error).message);
    }
  };

  const proveIsolation = async () => {
    if (!simulation || !token || sameTenant) return;
    setError(null);
    try {
      await api<Simulation>(`/v1/simulations/${simulation.id}`, token);
      setIsolationProof("Isolation failed: the foreign object was visible.");
    } catch (reason) {
      const status = (reason as Error & { status?: number }).status;
      setIsolationProof(
        status === 404
          ? "Protected: the foreign simulation is indistinguishable from an absent object (404)."
          : (reason as Error).message,
      );
    }
  };

  const reviewEvidence = async () => {
    if (!simulation || !impact || !token || !sameTenant || role !== "reviewer") return;
    setError(null);
    try {
      const current = (await api<Simulation>(`/v1/simulations/${simulation.id}`, token)).body;
      setSimulation(current);
      const approval = (
        await api<{ id: string }>(`/v1/simulations/${simulation.id}/approvals`, token, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": newKey("approval"),
            "If-Match": `"${current.version}"`,
          },
          body: JSON.stringify({
            result_checksum: impact.result_checksum,
            policy_version_id: impact.risk.policy_version_id,
            decision: "approve",
            rationale: "Reviewed by the tenant-scoped Phase 4A QA persona.",
          }),
        })
      ).body;
      setApprovalId(approval.id);
      setWorkflow("reviewed");
    } catch (reason) {
      setError((reason as Error).message);
    }
  };

  const evaluateRelease = async () => {
    if (!simulation || !impact || !approvalId || !token || !sameTenant) return;
    setError(null);
    try {
      const result = (
        await api<Gate>("/v1/release-gates/evaluate", token, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": newKey("gate"),
          },
          body: JSON.stringify({
            simulation_id: simulation.id,
            approval_id: approvalId,
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

  const inspectAudit = async () => {
    if (!token || role !== "auditor") return;
    try {
      const result = (await api<{ items: object[] }>("/v1/audit-events", token)).body;
      setAuditCount(result.items.length);
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
          <p className="eyebrow">Phase 4A · executable tenant isolation</p>
          <h1>Prove who can see and decide each rule change.</h1>
          <p className="lede">
            Signed development identities exercise server-resolved tenant membership, roles, and
            object authorization.
          </p>
        </div>
        <aside className="identity">
          <label htmlFor="identity">Active synthetic persona</label>
          <select
            id="identity"
            value={identityKey}
            onChange={(event) => void signIn(event.target.value)}
          >
            {identities.map((item) => (
              <option key={item.key} value={item.key}>
                {item.display_name} · {item.tenant}
              </option>
            ))}
          </select>
          <strong>{session?.user.display_name ?? "Loading identity"}</strong>
          <small>
            {session ? `${session.tenant.display_name} · ${role}` : "Resolving membership"}
          </small>
        </aside>
      </section>

      {simulation && !sameTenant ? (
        <section className="isolation-card" aria-label="Tenant isolation proof">
          <div>
            <p className="eyebrow">Foreign tenant boundary</p>
            <h2>Evidence is hidden after the tenant switch</h2>
            <p>The active persona cannot read the simulation created in the other tenant.</p>
          </div>
          <button type="button" onClick={() => void proveIsolation()}>
            Attempt cross-tenant access
          </button>
          {isolationProof && (
            <p className="proof" role="status">
              {isolationProof}
            </p>
          )}
        </section>
      ) : (
        <section className="workflow" aria-label="Rule simulation workflow">
          <form className="panel proposal" onSubmit={(event) => void startSimulation(event)}>
            <div className="step">
              <span>01</span> Propose
            </div>
            <h2>Invoice rounding</h2>
            <p>Only the tenant analyst can create the candidate rule.</p>
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
              <small>
                {scenario ? `${scenario.event_count} events · seed ${scenario.seed}` : "Loading"}
              </small>
            </div>
            <button
              type="submit"
              disabled={
                service !== "ready" ||
                role !== "author" ||
                ["creating", "queued", "running"].includes(workflow)
              }
            >
              {workflow === "creating"
                ? "Creating evidence…"
                : workflow === "queued" || workflow === "running"
                  ? "Simulation running…"
                  : "Run comparison"}
            </button>
            {role !== "author" && (
              <small className="role-hint">Switch to this tenant’s analyst to propose.</small>
            )}
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
              </>
            )}
          </section>

          <section className="panel decision">
            <div className="step">
              <span>03</span> Decide
            </div>
            <h2>Separated duties</h2>
            <p>QA review and release evaluation require distinct tenant-scoped roles.</p>
            <button
              type="button"
              onClick={() => void reviewEvidence()}
              disabled={!impact || role !== "reviewer" || Boolean(approvalId)}
            >
              {approvalId ? "Evidence reviewed" : "Approve evidence as QA"}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => void evaluateRelease()}
              disabled={!approvalId || role !== "release_approver" || Boolean(gate)}
            >
              Evaluate release gate
            </button>
            {gate && (
              <div className={`gate gate-${gate.decision}`}>
                <span>Release gate</span>
                <strong>{gate.decision}</strong>
                <p>{gate.reasons[0]}</p>
              </div>
            )}
            {role === "auditor" && (
              <button type="button" className="secondary" onClick={() => void inspectAudit()}>
                Inspect tenant audit trail
              </button>
            )}
            {auditCount !== null && <p className="proof">Authorized audit events: {auditCount}</p>}
          </section>
        </section>
      )}

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
    </main>
  );
}
