import { InMemoryWebStorage, UserManager, WebStorageStateStore } from 'oidc-client-ts';
import type { User } from 'oidc-client-ts';

export type SessionState = 'starting' | 'anonymous' | 'authenticated' | 'expired' | 'error' | 'signed-out';
export interface BrowserSession {
  subscribe(listener: () => void): () => void;
  snapshot(): SessionState;
  initialize(): Promise<void>;
  login(): Promise<void>;
  logout(): Promise<void>;
  accessToken(): string;
  expire(): void;
}
export function oidcSettings(origin: string, authority = 'http://localhost:8080/realms/qh') {
  const issuer = new URL(authority);
  if (issuer.username || issuer.password || issuer.search || issuer.hash ||
      !(issuer.protocol === 'https:' || issuer.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(issuer.hostname))) {
    throw new Error('Invalid OIDC configuration');
  }
  return {
    authority, client_id: 'qh-web', redirect_uri: origin + '/oidc/callback',
    response_type: 'code', disablePKCE: false, scope: 'openid qh:api', loadUserInfo: false,
    automaticSilentRenew: false, monitorSession: false, staleStateAgeInSeconds: 300,
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    stateStore: new WebStorageStateStore({ store: window.sessionStorage, prefix: 'qh.oidc.' })
  };
}
export function safeReturnPath(value: unknown): string {
  return typeof value === 'string' && /^\/context-spaces\/[0-9a-f-]{36}$/i.test(value) ? value : '/';
}
export function createSession(): BrowserSession {
  const manager = new UserManager(oidcSettings(window.location.origin, import.meta.env.VITE_OIDC_ISSUER));
  let state: SessionState = 'starting';
  let user: User | null = null;
  let initializing: Promise<void> | undefined;
  const listeners = new Set<() => void>();
  const set = (next: SessionState) => { state = next; listeners.forEach(listener => listener()); };
  const clear = (next: SessionState) => { user = null; void manager.removeUser(); set(next); };
  manager.events.addAccessTokenExpired(() => clear('expired'));
  return {
    subscribe(listener) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    snapshot: () => state,
    initialize() {
      // StrictMode must never redeem a code twice.
      initializing ??= (async () => {
        if (window.location.pathname !== '/oidc/callback') { set('anonymous'); return; }
        const callback = window.location.href;
        window.history.replaceState(null, '', '/');
        try {
          await manager.clearStaleState();
          user = await manager.signinRedirectCallback(callback);
          if (user.expired || !user.access_token) throw new Error('Expired session');
          window.history.replaceState(null, '', safeReturnPath(user.state));
          window.dispatchEvent(new PopStateEvent('popstate'));
          set('authenticated');
        } catch { clear('error'); }
      })();
      return initializing;
    },
    async login() {
      try {
        await manager.clearStaleState();
        await manager.signinRedirect({ state: safeReturnPath(window.location.pathname), nonce: crypto.randomUUID() });
      } catch { clear('error'); }
    },
    async logout() {
      const idToken = user?.id_token;
      clear('signed-out');
      try {
        // No post_logout_redirect_uri: reuse the approved realm allowlist unchanged.
        await manager.signoutRedirect({ id_token_hint: idToken });
      } catch { clear('signed-out'); }
    },
    accessToken() {
      if (!user || user.expired || !user.access_token) { clear('expired'); throw new Error('Session expired'); }
      return user.access_token;
    },
    expire: () => clear('expired')
  };
}
