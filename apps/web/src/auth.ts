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
function browserManager() {
  return new UserManager(oidcSettings(window.location.origin, import.meta.env.VITE_OIDC_ISSUER));
}
export function completeSilentCallback() {
  return browserManager().signinSilentCallback();
}
export function createSession(manager = browserManager(),
    renewalEnabled = import.meta.env.VITE_QH_DEVELOPMENT_SESSION === '1'): BrowserSession {
  let state: SessionState = 'starting';
  let user: User | null = null;
  let initializing: Promise<void> | undefined;
  const listeners = new Set<() => void>();
  const set = (next: SessionState) => { state = next; listeners.forEach(listener => listener()); };
  let started=0,epoch=0,timer:ReturnType<typeof setTimeout>|undefined,renewing:Promise<string>|undefined;
  const resumeKey = 'qh.oidc.resume.' + (manager.settings?.authority ?? window.location.origin);
  type ResumeHint = {started: number; subject: string; issuer: string};
  const forget = () => {try {sessionStorage.removeItem(resumeKey);} catch {/* Storage is optional. */}};
  const hint = (): ResumeHint | null => {
    try {
      const value = JSON.parse(sessionStorage.getItem(resumeKey) ?? 'null');
      return value && Number.isFinite(value.started) && typeof value.subject === 'string' && typeof value.issuer === 'string' ? value : null;
    } catch {return null;}
  };
  const remember = () => {
    // This is a restoration hint, never a credential or evidence of authentication.
    try {sessionStorage.setItem(resumeKey, JSON.stringify({started, subject: user!.profile.sub, issuer: user!.profile.iss}));} catch {/* Tokens remain memory-only. */}
  };
  const clear = (next: SessionState) => { epoch++;clearTimeout(timer);user = null;forget();void manager.removeUser();set(next); };
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
        const callback = window.location.pathname === '/oidc/callback' ? window.location.href : null;
        const previous = callback ? null : hint(), generation = epoch;
        if (!callback && !previous) {set('anonymous'); return;}
        if (previous && (previous.started > Date.now() || Date.now() - previous.started >= 8 * 3600000)) {clear('expired'); return;}
        if (callback) window.history.replaceState(null, '', '/');
        try {
          await manager.clearStaleState();
          const next = callback ? await manager.signinRedirectCallback(callback) : (await manager.getUser?.()) ?? await manager.signinSilent();
          if (generation !== epoch) {void manager.removeUser(); return;}
          if (!next || next.expired || !next.access_token) throw new Error('Expired session');
          if (previous && (next.profile.sub !== previous.subject || next.profile.iss !== previous.issuer)) throw new Error('Session changed');
          user = next;
          // QH-52: an explicitly requested domain or Space survives reauthentication.
          // Ordinary login still lands home; never restore an implicit last Space.
          if (callback) {
            const target=safeReturnPath(user.state);
            window.history.replaceState(null, '', renewalEnabled||target.startsWith('/domains/')?target:'/');
            window.dispatchEvent(new PopStateEvent('popstate'));
          }
          const authenticatedAt=user.profile.auth_time;
          started=previous?.started ?? (typeof authenticatedAt==='number'&&authenticatedAt>0&&authenticatedAt*1000<=Date.now()?authenticatedAt*1000:Date.now());
          if(renewalEnabled&&Date.now()>=started+8*3600000){clear('expired');return;}
          remember();set('authenticated');schedule();
        } catch { if (generation === epoch) clear('error'); }
      })();
      return initializing;
    },
    async login() {
      if(state==='starting')return;
      set('starting');
      try {
        await manager.clearStaleState();
        await manager.signinRedirect({ state: safeReturnPath(window.location.pathname), nonce: crypto.randomUUID() });
      } catch { clear('error'); }
    },
    async logout() {
      const idToken = user?.id_token;
      epoch++;clearTimeout(timer);user=null;forget();set('signed-out');
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
