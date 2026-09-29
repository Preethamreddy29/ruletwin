import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

const scenario = {
  tenant_id: "11111111-1111-4111-8111-111111111111",
  author_id: "22222222-2222-4222-8222-222222222222",
  approver_id: "33333333-3333-4333-8333-333333333333",
  rule_definition_id: "44444444-4444-4444-8444-444444444444",
  baseline_rule_version_id: "55555555-5555-4555-8555-555555555555",
  dataset_manifest_id: "66666666-6666-4666-8666-666666666666",
  risk_policy_version_id: "77777777-7777-4777-8777-777777777777",
  engine_version: "rounding-engine-v1",
};

function response(body: object, ok = true) {
  return Promise.resolve({ ok, json: () => Promise.resolve(body), headers: new Headers() });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("shows readiness, synthetic identity, dataset, and disabled decision", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((path: string) => {
        if (path.endsWith("/health/ready")) return response({ status: "ready" });
        if (path.endsWith("/v1/dev/scenario")) return response(scenario);
        return response({
          user: { display_name: "NovaBill Analyst", email: "analyst@novabill.example" },
          tenant: { display_name: "NovaBill Sandbox" },
          roles: ["author"],
        });
      }),
    );
    render(<App />);
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("NovaBill Analyst")).toBeInTheDocument();
    expect(screen.getByText("100 events · seed 314159")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve evidence" })).toBeDisabled();
  });

  it("runs the critical flow and displays a blocking release gate", async () => {
    let simulationReads = 0;
    vi.stubGlobal("crypto", { randomUUID: () => "88888888-8888-4888-8888-888888888888" });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((path: string, init?: RequestInit) => {
        if (path.endsWith("/health/ready")) return response({ status: "ready" });
        if (path.endsWith("/v1/dev/session"))
          return response({
            user: { display_name: "Analyst" },
            tenant: { display_name: "Tenant" },
            roles: ["author"],
          });
        if (path.endsWith("/v1/dev/scenario")) return response(scenario);
        if (path.includes("/rule-versions")) return response({ id: "candidate" });
        if (path.endsWith("/v1/simulations") && init?.method === "POST")
          return response({
            id: "simulation",
            status: "queued",
            version: 2,
            result_checksum: null,
          });
        if (path.endsWith("/v1/simulations/simulation")) {
          simulationReads += 1;
          return response({
            id: "simulation",
            status: simulationReads === 1 ? "running" : "completed",
            version: simulationReads === 1 ? 3 : 4,
            result_checksum: simulationReads === 1 ? null : "sha256:test",
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
              policy_version_id: scenario.risk_policy_version_id,
              decision: "block",
              reasons: ["Threshold exceeded."],
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
        return response({}, false);
      }),
    );
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Candidate increment"), {
      target: { value: "10" },
    });
    fireEvent.click(await screen.findByRole("button", { name: "Run comparison" }));
    expect(await screen.findByText("90")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve evidence" }));
    await waitFor(() => expect(screen.getByText("Release gate")).toBeInTheDocument());
    expect(screen.getAllByText("block").length).toBeGreaterThan(0);
  });

  it("shows a problem detail when simulation creation fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((path: string) => {
        if (path.endsWith("/health/ready")) return response({ status: "ready" });
        if (path.endsWith("/v1/dev/scenario")) return response(scenario);
        if (path.endsWith("/v1/dev/session"))
          return response({
            user: { display_name: "Analyst" },
            tenant: { display_name: "Tenant" },
            roles: ["author"],
          });
        return response({ detail: "Candidate rule was rejected." }, false);
      }),
    );
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Run comparison" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Candidate rule was rejected.");
  });

  it("shows unavailable when service loading fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
  });
});
