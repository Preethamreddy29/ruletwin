import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import type { User } from "oidc-client-ts";

export type BrowserAuthMode = "development" | "oidc";

export interface BrowserAuthConfig {
  mode: BrowserAuthMode;
  authority?: string;
  audience?: string;
  clientId?: string;
  redirectUri?: string;
  postLogoutRedirectUri?: string;
}

let sharedManager: UserManager | undefined;
let bootstrapPromise: Promise<User | null> | undefined;

function configured(value: string | undefined, name: string): string {
  const normalized = value?.trim();
  if (!normalized) throw new Error(`${name} is required when browser OIDC is enabled.`);
  return normalized;
}

export function browserAuthConfig(): BrowserAuthConfig {
  const mode = import.meta.env.VITE_RULETWIN_AUTH_MODE === "oidc" ? "oidc" : "development";
  if (mode === "development") return { mode };

  const origin = window.location.origin;
  return {
    mode,
    authority: configured(import.meta.env.VITE_RULETWIN_OIDC_AUTHORITY, "OIDC authority"),
    audience: configured(import.meta.env.VITE_RULETWIN_OIDC_AUDIENCE, "OIDC audience"),
    clientId: configured(import.meta.env.VITE_RULETWIN_OIDC_CLIENT_ID, "OIDC client ID"),
    redirectUri:
      import.meta.env.VITE_RULETWIN_OIDC_REDIRECT_URI?.trim() || `${origin}/auth/callback`,
    postLogoutRedirectUri:
      import.meta.env.VITE_RULETWIN_OIDC_POST_LOGOUT_REDIRECT_URI?.trim() || origin,
  };
}

export function createOidcManager(config = browserAuthConfig()): UserManager | null {
  if (config.mode === "development") return null;

  if (sharedManager) return sharedManager;

  sharedManager = new UserManager({
    authority: configured(config.authority, "OIDC authority"),
    client_id: configured(config.clientId, "OIDC client ID"),
    redirect_uri: configured(config.redirectUri, "OIDC redirect URI"),
    post_logout_redirect_uri: configured(
      config.postLogoutRedirectUri,
      "OIDC post-logout redirect URI",
    ),
    response_type: "code",
    scope: "openid profile email",
    loadUserInfo: false,
    automaticSilentRenew: false,
    monitorSession: false,
    revokeTokensOnSignout: true,
    stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
    userStore: new WebStorageStateStore({ store: window.sessionStorage }),
    extraQueryParams: { audience: configured(config.audience, "OIDC audience") },
  });
  return sharedManager;
}

export function isSigninCallback(location = window.location): boolean {
  const parameters = new URLSearchParams(location.search);
  return (
    location.pathname === "/auth/callback" && parameters.has("code") && parameters.has("state")
  );
}

export function bootstrapOidc(manager: UserManager): Promise<User | null> {
  bootstrapPromise ??= (async () => {
    await manager.clearStaleState();
    const callback = isSigninCallback();
    const user = callback ? await manager.signinRedirectCallback() : await manager.getUser();
    if (callback) window.history.replaceState({}, document.title, "/");
    return user;
  })();
  return bootstrapPromise;
}
