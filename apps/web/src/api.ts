import type {SelectedConversationTurn,EnrichmentReceipt} from './EnrichConversation';
import type {ReviewStatus} from './ReviewControls';
import {organization} from './environment';
import type {Organization} from './environment';
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
  private readonly organizationWrites=new Set<Promise<Organization>>();
  private readonly openingWrites=new Map<string,Promise<void>>();
  private readonly providerGrants=new Map<string,string>();
  private closing=false;
  revokeSessionsBeforeLogout(credential?:string|null) {
    // Start revocation with the current in-memory token before local logout clears it.
    if(credential!==null)for(const [id,scope] of this.providerGrants)void this.revokeSession(scope,id,credential).catch(()=>{});
    this.closing=true;this.providerGrants.clear();
  }
  constructor(private readonly token: () => string|Promise<string>, private readonly expired: () => void) {}
  private async request(path: string, method = 'GET', body?: unknown, credential?:string): Promise<unknown> {
    const token = credential??await this.token();
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
  async enrich(scope:string,payload:{conversation_id:string;operation_id:string;turns:SelectedConversationTurn[];persist_consent:boolean}):Promise<EnrichmentReceipt>{
    if(!isUuid(scope))throw new ApiError(404);
    const r=await this.request('/context-spaces/'+scope+'/enrichments','POST',payload) as EnrichmentReceipt;
    if(!r||r.context_id!==scope||!isUuid(r.source_revision_id)||!Array.isArray(r.revision_ids)||r.revision_ids.length>100||r.revision_ids.some(id=>!isUuid(id))||new Set(r.revision_ids).size!==r.revision_ids.length||typeof r.replayed!=='boolean'||r.provider_mode!=='offline-literal/1')throw new ApiError(502);
    return r;
  }
  async reviewStatus(scope:string,revision:string):Promise<ReviewStatus>{
    if(!isUuid(scope)||!isUuid(revision))throw new ApiError(404);
    const s=await this.request('/context-spaces/'+scope+'/understanding/'+revision+'/review') as ReviewStatus;
    if(!s||s.revision_id!==revision||!isUuid(s.latest_revision_id)||typeof s.pending!=='boolean'||!(s.current_revision_id===null||isUuid(s.current_revision_id))||!(s.successor_revision_id===null||isUuid(s.successor_revision_id)))throw new ApiError(502);
    return s;
  }
  async review(scope:string,revision:string,operation:{operation_id:string;action:'confirm'|'reject'|'correct';expected_latest_revision_id:string;expected_current_revision_id:string|null;text:string|null}){
    if(!isUuid(scope)||!isUuid(revision))throw new ApiError(404);
    const r=await this.request('/context-spaces/'+scope+'/understanding/'+revision+'/review','POST',operation) as {revision_id:string;action:string;replayed:boolean};
    if(!r||!isUuid(r.revision_id)||r.action!==operation.action||typeof r.replayed!=='boolean')throw new ApiError(502);return r;
  }
  async pendingReview(scope:string,limit=20,after?:string){
    if(!isUuid(scope))throw new ApiError(404);
    return revisionPage(await this.request('/context-spaces/'+scope+'/review?limit='+limit+(after?'&after_revision_id='+encodeURIComponent(after):'')),{context_ids:[scope],view:'proposed',limit});
  }
  async resumeSpaces(sort:'recent'|'used',domain:string|null,after?:string):Promise<SpacePage>{
    await Promise.allSettled([...this.openingWrites.values(),...this.organizationWrites]);
    const params=new URLSearchParams({sort,limit:'20'});if(domain)params.set('domain',domain);if(after)params.set('after_id',after);
    const raw=await this.request('/environment/spaces?'+params) as SpacePage;
    if(!raw||!Array.isArray(raw.items)||raw.items.length>20||!(raw.next_after_id===null||isUuid(raw.next_after_id)))throw new ApiError(502);
    return {items:raw.items.map(space),next_after_id:raw.next_after_id};
  }
  async createOrganized(name:string,primary_domain_id:string):Promise<ContextSpace>{
    if(!validName(name)||!isUuid(primary_domain_id))throw new ApiError(422);
    return space(await this.request('/environment/spaces','POST',{name,primary_domain_id}));
  }
  async opened(scope:string,event_id:string):Promise<void>{
    if(!isUuid(scope)||!isUuid(event_id))throw new ApiError(404);
    const pending=this.openingWrites.get(event_id);if(pending)return pending;
    const write=this.request('/environment/spaces/'+scope+'/open','POST',{event_id}).then(()=>{});this.openingWrites.set(event_id,write);
    try{await write;}finally{if(this.openingWrites.get(event_id)===write)this.openingWrites.delete(event_id);}
  }
  async organization():Promise<Organization>{await Promise.allSettled([...this.openingWrites.values(),...this.organizationWrites]);return organization(await this.request('/environment'));}
  async organize(document:Organization):Promise<Organization>{
    const write=this.request('/environment','PUT',{version:document.version,domains:document.domains,memberships:document.memberships,primary_domains:document.primary_domains,...(document.space_descriptions?{space_descriptions:document.space_descriptions}:{})}).then(organization);
    this.organizationWrites.add(write);try{return await write;}finally{this.organizationWrites.delete(write);}
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
  async revokeSession(scope:string,id:string,credential?:string) {
    if(this.closing)return;
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    const receipt=await this.request('/context-spaces/'+scope+'/chat-sessions/'+id,'DELETE',undefined,credential) as {session_id?:string;state?:string};
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
  async rename(id:string,name:string):Promise<ContextSpace> {
    if(!isUuid(id)||!validName(name))throw new ApiError(422);
    return space(await this.request('/context-spaces/'+id,'PATCH',{name}));
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
