import { InMemoryWebStorage, UserManager, WebStorageStateStore } from 'oidc-client-ts';
import {parseRoute} from './navigation';
import type { User } from 'oidc-client-ts';

export type SessionState = 'starting' | 'anonymous' | 'authenticated' | 'expired' | 'error' | 'signed-out';
export interface BrowserSession {
  subscribe(listener: () => void): () => void;
  snapshot(): SessionState;
  initialize(): Promise<void>;
  login(): Promise<void>;
  logout(): Promise<void>;
  accessToken(): string;
  readyToken?(): Promise<string>;
  preserveDrafts?: boolean;
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
    // Presentation hint only: the realm's default locale loses to browser English.
    ui_locales: 'fr',
    automaticSilentRenew: false, monitorSession: false, staleStateAgeInSeconds: 300,
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    stateStore: new WebStorageStateStore({ store: window.sessionStorage, prefix: 'qh.oidc.' })
  };
}
export function safeReturnPath(value: unknown): string {
  if(typeof value!=='string')return '/';
  const route=parseRoute(value);
  return route.kind==='domain'||route.kind==='space'?value:'/';
}
export function createSession(manager = new UserManager(oidcSettings(window.location.origin, import.meta.env.VITE_OIDC_ISSUER)),
    renewalEnabled = import.meta.env.VITE_QH_DEVELOPMENT_SESSION === '1'): BrowserSession {
  let state: SessionState = 'starting';
  let user: User | null = null;
  let initializing: Promise<void> | undefined;
  const listeners = new Set<() => void>();
  const set = (next: SessionState) => { state = next; listeners.forEach(listener => listener()); };
  let started=0,epoch=0,timer:ReturnType<typeof setTimeout>|undefined,renewing:Promise<string>|undefined;
  const clear = (next: SessionState) => { epoch++;clearTimeout(timer);user = null;void manager.removeUser();set(next); };
  const token=()=>{
    if(!user||user.expired||!user.access_token){clear('expired');throw new Error('Session expired');}
    return user.access_token;
  };
  const schedule=()=>{clearTimeout(timer);if(renewalEnabled&&user)timer=setTimeout(()=>{void ready().catch(()=>{});},Math.max(0,Math.min((user.expires_at!*1000-Date.now()-60000),started+8*3600000-Date.now())));};
  async function ready():Promise<string>{
    if(!renewalEnabled)return token();
    if(state!=='authenticated'||!user||Date.now()>=started+8*3600000){clear('expired');throw new Error('Session expired');}
    if(renewing)return renewing;
    if(user.expires_at!*1000-Date.now()>60000)return token();
    const generation=epoch,previous=user;
    // Never fall through to iframe SSO or silently sign in after logout.
    if(!user.refresh_token){clear('expired');throw new Error('Reconnect required');}
    renewing=(async()=>{
      try{
        const next=await manager.signinSilent();
        if(generation!==epoch||!next||next.expired||!next.refresh_token||next.refresh_token===previous.refresh_token||next.profile.sub!==previous.profile.sub||next.profile.iss!==previous.profile.iss||Date.now()>=started+8*3600000)throw new Error('Session expired');
        user=next;schedule();return token();
      }catch{if(generation===epoch)clear('expired');else void manager.removeUser();throw new Error('Reconnect required');}
      finally{renewing=undefined;}
    })();
    return renewing;
  }
  manager.events.addAccessTokenExpired(()=>{if(renewalEnabled&&state==='authenticated')void ready().catch(()=>{});else if(state==='authenticated')clear('expired');});
  const wake=()=>{if(state==='authenticated')void ready().catch(()=>{});};
  if(renewalEnabled){window.addEventListener('focus',wake);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')wake();});}
  return {
    preserveDrafts:renewalEnabled,
    readyToken:ready,
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
          // QH-52: an explicitly requested domain or Space survives reauthentication.
          // Ordinary login still lands home; never restore an implicit last Space.
          const target=safeReturnPath(user.state);
          window.history.replaceState(null, '', target);
          window.dispatchEvent(new PopStateEvent('popstate'));
          const authenticatedAt=user.profile.auth_time;
          started=typeof authenticatedAt==='number'&&authenticatedAt>0&&authenticatedAt*1000<=Date.now()?authenticatedAt*1000:Date.now();
          if(renewalEnabled&&Date.now()>=started+8*3600000){clear('expired');return;}
          set('authenticated');schedule();
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
      epoch++;clearTimeout(timer);user=null;set('signed-out');
      try {
        if(renewalEnabled)try{await manager.revokeTokens(['refresh_token']);}catch{/* Local logout remains effective if revocation is unavailable. */}
        await manager.removeUser();
        // No post_logout_redirect_uri: reuse the approved realm allowlist unchanged.
        await manager.signoutRedirect({ id_token_hint: idToken });
      } catch { clear('signed-out'); }
    },
    accessToken:token,
    expire: () => clear('expired')
  };
}
