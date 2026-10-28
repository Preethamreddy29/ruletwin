import { describe, expect, it, vi } from "vitest";

import { browserAuthConfig, createOidcManager, isSigninCallback } from "../src/auth";

describe("browser OIDC configuration", () => {
  it("keeps the local development identity flow as the default", () => {
    expect(browserAuthConfig()).toEqual({ mode: "development" });
    expect(createOidcManager({ mode: "development" })).toBeNull();
  });

  it("builds a PKCE authorization-code client from public configuration", () => {
    const manager = createOidcManager({
      mode: "oidc",
      authority: "https://identity.example/",
      audience: "ruletwin-api",
      clientId: "pilot-client",
      redirectUri: "https://pilot.example/auth/callback",
      postLogoutRedirectUri: "https://pilot.example/",
    });

    expect(manager?.settings.response_type).toBe("code");
    expect(manager?.settings.client_id).toBe("pilot-client");
    expect(manager?.settings.extraQueryParams).toEqual({ audience: "ruletwin-api" });
    expect(manager?.settings.disablePKCE).toBe(false);
    expect(manager?.settings.loadUserInfo).toBe(false);
  });

  it("recognizes only a complete sign-in callback", () => {
    expect(
      isSigninCallback({
        pathname: "/auth/callback",
        search: "?code=authorization-code&state=protected-state",
      } as Location),
    ).toBe(true);
    expect(
      isSigninCallback({ pathname: "/auth/callback", search: "?code=missing-state" } as Location),
    ).toBe(false);
    expect(
      isSigninCallback({
        pathname: "/",
        search: "?code=authorization-code&state=state",
      } as Location),
    ).toBe(false);
  });

  it("fails closed when required OIDC browser settings are absent", () => {
    vi.stubEnv("VITE_RULETWIN_AUTH_MODE", "oidc");
    expect(() => browserAuthConfig()).toThrow("OIDC authority is required");
    vi.unstubAllEnvs();
  });
});
