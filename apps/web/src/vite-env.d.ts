/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RULETWIN_AUTH_MODE?: "development" | "oidc";
  readonly VITE_RULETWIN_OIDC_AUTHORITY?: string;
  readonly VITE_RULETWIN_OIDC_AUDIENCE?: string;
  readonly VITE_RULETWIN_OIDC_CLIENT_ID?: string;
  readonly VITE_RULETWIN_OIDC_REDIRECT_URI?: string;
  readonly VITE_RULETWIN_OIDC_POST_LOGOUT_REDIRECT_URI?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
