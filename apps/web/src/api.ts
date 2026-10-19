import {capabilities,providerSession} from './provider-session';
import {chatAnswer} from './chat';
import type {ChatAnswer,DialogueMessage} from './chat';
import { revisionPage } from './understanding';
import type { BrowseQuery, RevisionPage, RevisionQuery } from './understanding';
// QH-9 wire contract; never import backend implementation or accept a UI owner.
export interface ContextSpace {
  id: string; owner_id: string; name: string; status: string;
  created_at: string; updated_at: string;
}
export interface SpacePage { items: ContextSpace[]; next_after_id: string | null }
export { ApiError, isUuid } from './transport';
import { ApiError, isUuid } from './transport';
export const validName = (v: string) => v.trim().length > 0 && [...v].length <= 256 && !v.includes('\0');
function space(value: unknown): ContextSpace {
  const v = value as ContextSpace | null;
  if (!v || !isUuid(v.id ?? '') || !isUuid(v.owner_id ?? '') || typeof v.name !== 'string' ||
      typeof v.status !== 'string' || !Number.isFinite(Date.parse(v.created_at)) ||
      !Number.isFinite(Date.parse(v.updated_at))) throw new ApiError(502);
  return v;
}
export class QhApi {
  private readonly providerGrants=new Map<string,string>();
  private closing=false;
  revokeSessionsBeforeLogout() {
    // Start revocation with the current in-memory token before local logout clears it.
    for(const [id,scope] of this.providerGrants)void this.revokeSession(scope,id).catch(()=>{});
    this.closing=true;this.providerGrants.clear();
  }
  constructor(private readonly token: () => string, private readonly expired: () => void) {}
  private async request(path: string, method = 'GET', body?: unknown): Promise<unknown> {
    const token = this.token();
    let response: Response;
    try {
      response = await fetch('/api' + path, {
        method, headers: { Authorization: 'Bearer ' + token, ...(body ? { 'Content-Type': 'application/json' } : {}) },
        body: body ? JSON.stringify(body) : undefined, credentials: 'omit', cache: 'no-store', redirect: 'error',
        keepalive: method === 'DELETE'
      });
    } catch { throw new ApiError(503); }
    if (response.status === 401) this.expired();
    if (!response.ok) throw new ApiError(response.status);
    try { return await response.json(); } catch { throw new ApiError(502); }
  }
  async chat(scope:string,messages:DialogueMessage[],includeProposed:boolean):Promise<ChatAnswer> {
    if(!isUuid(scope))throw new ApiError(404);
    return chatAnswer(await this.request('/context-spaces/'+scope+'/chat','POST',{
      messages,include_proposed:includeProposed}),scope,includeProposed);
  }
  async chatCapabilities(scope:string) {
    if(!isUuid(scope))throw new ApiError(404);
    return capabilities(await this.request('/context-spaces/'+scope+'/chat-sessions'));
  }
  async previewSession(scope:string,messages:DialogueMessage[],include:boolean) {
    if(!isUuid(scope))throw new ApiError(404);
    const view=providerSession(await this.request('/context-spaces/'+scope+'/chat-sessions/preview','POST',{messages,include_proposed:include}),scope,include);
    this.providerGrants.set(view.session_id,scope);return view;
  }
  async consentSession(scope:string,id:string,hash:string,include:boolean) {
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    const view=providerSession(await this.request('/context-spaces/'+scope+'/chat-sessions/'+id+'/consent','POST',{snapshot_sha256:hash,disclosure_consent:true}),scope,include);
    if(view.session_id!==id)throw new ApiError(502);return view;
  }
  async sessionStatus(scope:string,id:string,include:boolean) {
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    const view=providerSession(await this.request('/context-spaces/'+scope+'/chat-sessions/'+id),scope,include);
    if(view.session_id!==id)throw new ApiError(502);return view;
  }
  async revokeSession(scope:string,id:string) {
    if(this.closing)return;
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    const receipt=await this.request('/context-spaces/'+scope+'/chat-sessions/'+id,'DELETE') as {session_id?:string;state?:string};
    if(!receipt||receipt.session_id!==id||receipt.state!=='revoked')throw new ApiError(502);
    this.providerGrants.delete(id);
  }
  async sessionChat(scope:string,id:string,messages:DialogueMessage[],include:boolean):Promise<ChatAnswer> {
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    return chatAnswer(await this.request('/context-spaces/'+scope+'/chat-sessions/'+id+'/messages','POST',{messages,include_proposed:include}),scope,include);
  }
  async query(query: RevisionQuery): Promise<RevisionPage> {
    return revisionPage(await this.request('/context-spaces/query', 'POST', query), query);
  }
  async browse(scope: string, query: BrowseQuery): Promise<RevisionPage> {
    if (!isUuid(scope)) throw new ApiError(404);
    const params = new URLSearchParams();
    for (const [key,value] of Object.entries(query)) if (value !== undefined) params.set(key,String(value));
    return revisionPage(await this.request('/context-spaces/' + scope + '/understanding?' + params),
      {context_ids:[scope],view:query.view,limit:query.limit});
  }
  async me(): Promise<string> {
    this.closing=false;
    const v = await this.request('/auth/me') as { user_id?: string };
    if (!v || !isUuid(v.user_id ?? '')) throw new ApiError(502);
    return v.user_id!;
  }
  async list(after?: string): Promise<SpacePage> {
    if (after && !isUuid(after)) throw new ApiError(422);
    const page = await this.request('/context-spaces?limit=20' + (after ? '&after_id=' + after : '')) as SpacePage;
    if (!page || !Array.isArray(page.items) || !(page.next_after_id === null || typeof page.next_after_id === 'string' && isUuid(page.next_after_id))) throw new ApiError(502);
    return { items: page.items.map(space), next_after_id: page.next_after_id };
  }
  async get(id: string): Promise<ContextSpace> {
    if (!isUuid(id)) throw new ApiError(404);
    return space(await this.request('/context-spaces/' + id));
  }
  async create(name: string): Promise<ContextSpace> {
    if (!validName(name)) throw new ApiError(422);
    return space(await this.request('/context-spaces', 'POST', { name }));
  }
}
export function apiMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) return 'Ce Context Space est introuvable ou inaccessible.';
  if (error instanceof ApiError && error.status === 403) return 'Votre compte ne dispose pas des autorisations nécessaires.';
  if (error instanceof ApiError && error.status === 422) return 'Vérifiez les informations saisies.';
  return 'Le service est indisponible. Réessayez dans un instant.';
}
