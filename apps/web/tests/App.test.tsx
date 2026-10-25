import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

const tenantA = "11111111-1111-4111-8111-111111111111";
const tenantB = "99999999-9999-4999-8999-999999999999";
const identities = [
  {
    key: "novabill-analyst",
    display_name: "NovaBill Analyst",
    tenant_id: tenantA,
    tenant: "NovaBill Sandbox",
    role: "author",
  },
  {
    key: "novabill-reviewer",
    display_name: "NovaBill QA Reviewer",
    tenant_id: tenantA,
    tenant: "NovaBill Sandbox",
    role: "reviewer",
  },
  {
    key: "novabill-approver",
    display_name: "NovaBill Release Approver",
    tenant_id: tenantA,
    tenant: "NovaBill Sandbox",
    role: "release_approver",
  },
  {
    key: "novabill-auditor",
    display_name: "NovaBill Auditor",
    tenant_id: tenantA,
    tenant: "NovaBill Sandbox",
    role: "auditor",
  },
  {
    key: "brightline-reviewer",
    display_name: "Brightline QA Reviewer",
    tenant_id: tenantB,
    tenant: "Brightline Sandbox",
    role: "reviewer",
  },
];
const scenarios = [tenantA, tenantB].map((tenant_id, index) => ({
  tenant_id,
  tenant_display_name: index ? "Brightline Sandbox" : "NovaBill Sandbox",
  rule_definition_id: "44444444-4444-4444-8444-444444444444",
  baseline_rule_version_id: "55555555-5555-4555-8555-555555555555",
  dataset_manifest_id: "66666666-6666-4666-8666-666666666666",
  risk_policy_version_id: "77777777-7777-4777-8777-777777777777",
  engine_version: "rounding-engine-v1",
  seed: index ? 271828 : 314159,
  event_count: 100,
}));

function response(body: object, ok = true, status = ok ? 200 : 404) {
  return Promise.resolve({ ok, status, json: () => Promise.resolve(body), headers: new Headers() });
}

function roleFor(key: string) {
  return identities.find((identity) => identity.key === key)!;
}

function installFetch() {
  let simulationReads = 0;
  vi.stubGlobal("crypto", { randomUUID: () => "88888888-8888-4888-8888-888888888888" });
  vi.stubGlobal("URL", {
    createObjectURL: vi.fn(() => "blob:ruletwin-evidence"),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((path: string, init?: RequestInit) => {
      if (path.endsWith("/health/ready")) return response({ status: "ready" });
      if (path.endsWith("/v1/dev/identities")) return response({ items: identities });
      if (path.endsWith("/v1/dev/scenarios")) return response({ items: scenarios });
      if (path.endsWith("/v1/dev/token")) {
        const body = typeof init?.body === "string" ? init.body : "{}";
        const key = (JSON.parse(body) as { identity_key: string }).identity_key;
        return response({ access_token: `token-${key}` });
      }
      if (path.endsWith("/v1/dev/session")) {
        const auth = new Headers(init?.headers).get("Authorization")!;
        const identity = roleFor(auth.replace("Bearer token-", ""));
        return response({
          user: { id: "user", display_name: identity.display_name, email: "synthetic@example" },
          tenant: { id: identity.tenant_id, slug: "sandbox", display_name: identity.tenant },
          roles: [identity.role],
        });
      }
      if (path.includes("/rule-versions")) return response({ id: "candidate" });
      if (path.endsWith("/v1/simulations") && init?.method === "POST")
        return response({ id: "simulation", status: "queued", version: 2, result_checksum: null });
      if (path.endsWith("/v1/simulations/simulation")) {
        const auth = new Headers(init?.headers).get("Authorization");
        if (auth === "Bearer token-brightline-reviewer")
          return response({ detail: "Resource not found." }, false, 404);
        simulationReads += 1;
        return response({
          id: "simulation",
          status: simulationReads === 1 ? "running" : "completed",
          version: 4,
          result_checksum: `sha256:${"a".repeat(64)}`,
        });
      }
      if (path.endsWith("/impact"))
        return response({
          simulation_id: "simulation",
          result_checksum: `sha256:${"a".repeat(64)}`,
          summary: {
            event_count: 100,
            changed_event_count: 90,
            total_financial_delta_minor_units: 15,
            maximum_financial_delta_minor_units: 5,
            currency: "USD",
          },
          risk: {
            policy_version_id: scenarios[0].risk_policy_version_id,
            decision: "block",
            reasons: ["Threshold exceeded."],
          },
        });
      if (path.endsWith("/evidence-export"))
        return response({
          export_checksum: `sha256:${"e".repeat(64)}`,
          evidence: {
            schema_version: "ruletwin-evidence-export-v1",
            tenant_id: tenantA,
            simulation: { id: "simulation" },
          },
        });
      if (path.endsWith("/approvals")) return response({ id: "approval" });
      if (path.endsWith("/release-gates/evaluate"))
        return response({
          id: "gate",
          decision: "block",
          evidence_checksum: "sha256:gate",
          reasons: ["Policy blocked the evidence."],
        });
      if (path.endsWith("/audit-events")) return response({ items: [{ id: "event" }] });
      return response({ detail: "Unexpected request" }, false, 500);
    }),
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows the signed synthetic persona and deterministic dataset", async () => {
    installFetch();
    render(<App />);
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("NovaBill Analyst")).toBeInTheDocument();
    expect(screen.getByText("100 events · seed 314159")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve evidence as QA" })).toBeDisabled();
  });

  it("demonstrates cross-tenant denial and separated review and release roles", async () => {
    installFetch();
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Run comparison" }));
    expect(await screen.findByText("90")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Active synthetic persona"), {
      target: { value: "brightline-reviewer" },
    });
    expect(
      await screen.findByText("Evidence is hidden after the tenant switch"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Attempt cross-tenant access" }));
    expect(await screen.findByText(/indistinguishable from an absent object/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Active synthetic persona"), {
      target: { value: "novabill-reviewer" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "Approve evidence as QA" }));
    expect(await screen.findByRole("button", { name: "Evidence reviewed" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Download evidence bundle" }));
    expect(await screen.findByText(/Evidence bundle ready/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Active synthetic persona"), {
      target: { value: "novabill-approver" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "Evaluate release gate" }));
    expect(await screen.findByText("Release gate")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Active synthetic persona"), {
      target: { value: "novabill-auditor" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "Inspect tenant audit trail" }));
    await waitFor(() => expect(screen.getByText("Authorized audit events: 1")).toBeInTheDocument());
  });

  it("shows unavailable when service loading fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
  });
});
