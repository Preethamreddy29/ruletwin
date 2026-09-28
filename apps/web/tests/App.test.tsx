import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

const responseByPath: Record<string, object> = {
  "/api/health/ready": { status: "ready", database: "reachable" },
  "/api/version": { service: "ruletwin-api", version: "0.1.0-dev-foundation" },
  "/api/v1/dev/session": {
    user: { display_name: "NovaBill Analyst", email: "analyst@novabill.example" },
    tenant: { display_name: "NovaBill Sandbox" },
    roles: ["author", "reviewer"],
    synthetic: true,
  },
};

afterEach(() => vi.restoreAllMocks());

describe("App", () => {
  it("shows readiness and the synthetic session", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((path: string) =>
          Promise.resolve({ ok: true, json: () => Promise.resolve(responseByPath[path]) }),
        ),
    );
    const { unmount } = render(<App />);
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("NovaBill Analyst")).toBeInTheDocument();
    expect(screen.getByText("NovaBill Sandbox")).toBeInTheDocument();
    unmount();
  });

  it("shows unavailable when a service check fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<App />);
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
  });

  it("shows unavailable when a service returns a failure response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, json: () => Promise.resolve({}) }),
    );
    render(<App />);
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
  });
});
