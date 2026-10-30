import type {WorkspaceMessageInput,WorkspaceRegenerationInput,WorkspaceMessageReceipt} from '../../../packages/shared/src/context-space';
import type {PortableContext,ContextIntake,WorkspaceState} from '../../../packages/shared/src/context-space';
import type {AIDiagnostic} from './AIDiagnostics';
import {DIMENSIONS} from './uum';
import type {PrimaryDimension} from './uum';
export interface DimensionPresence {context_id:string;view:'current'|'proposed';dimensions:Record<PrimaryDimension,boolean>;unclassified:boolean}
import type {SelectedConversationTurn,EnrichmentReceipt} from './EnrichConversation';
import type {ReviewStatus} from './ReviewControls';
import {organization} from './environment';
import type {Organization} from './environment';
import {capabilities,providerSession} from './provider-session';
import {chatAnswer} from './chat';
import type {ChatAnswer,DialogueMessage} from './chat';
import { revisionPage } from './understanding';
import type { BrowseQuery, RevisionPage, RevisionQuery } from './understanding';
import {NavigationReads} from './navigation-reads';
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
function workspaceState(state:WorkspaceState,scope:string):WorkspaceState {
    if(!state||state.context_id!==scope||!['empty','pending','running','current','failed'].includes(state.state)||!Array.isArray(state.intake)||!Number.isInteger(state.pending_count))throw new ApiError(502);
    if(state.recap&&(!state.current||state.recap.version_id!==state.current.id||typeof state.recap.title!=='string'||!state.recap.title.trim()||typeof state.recap.text!=='string'||!state.recap.text.trim()||state.recap.text.trim().split(/\s+/).length>(state.current.has_recap?100:150)||!Array.isArray(state.recap.support_revision_ids)||!state.recap.support_revision_ids.length||state.recap.support_revision_ids.some(id=>!state.current!.revision_ids.includes(id))))throw new ApiError(502);
    return state;
}
export class QhApi {
  private readonly navigationReads=new NavigationReads();
  private readonly prefetching=new Set<string>();
  private navigationOwner:string|null=null;
  private readonly organizationWrites=new Set<Promise<Organization>>();
  private readonly openingWrites=new Map<string,Promise<void>>();
  private readonly providerGrants=new Map<string,string>();
  private closing=false;
  revokeSessionsBeforeLogout(credential?:string|null) {
    this.navigationReads.clear();this.navigationOwner=null;
    // Start revocation with the current in-memory token before local logout clears it.
    if(credential!==null)for(const [id,scope] of this.providerGrants)void this.revokeSession(scope,id,credential).catch(()=>{});
    this.closing=true;this.providerGrants.clear();
  }
  constructor(private readonly token: () => string|Promise<string>, private readonly expired: () => void) {}
  private async request(path: string, method = 'GET', body?: unknown, credential?:string): Promise<unknown> {
    const mutation=method!=='GET'&&!path.endsWith('/open');
    if(mutation)this.navigationReads.clear();
    const token = credential??await this.token();
    let response: Response;
    try {
      response = await fetch('/api' + path, {
        method, headers: { Authorization: 'Bearer ' + token, ...(body ? { 'Content-Type': 'application/json' } : {}) },
        body: body ? JSON.stringify(body) : undefined, credentials: 'omit', cache: 'no-store', redirect: 'error',
        keepalive: method === 'DELETE'
      });
    } catch { if(mutation)this.navigationReads.clear();throw new ApiError(503); }
    const missingSpace=response.status===404&&/^\/context-spaces\/[^/]+(?:\/workspace)?$/.test(path);
    if(mutation||[401,403].includes(response.status)||missingSpace)this.navigationReads.clear();
    if (response.status === 401) this.expired();
    if (!response.ok) throw new ApiError(response.status);
    if(response.status===204)return null;
    try { return await response.json(); } catch { throw new ApiError(502); }
  }
  workspace(scope:string,fresh=false):Promise<WorkspaceState & {understanding:import('./understanding').CanonicalRevision[]}>{
    if(fresh)this.navigationReads.remove('workspace:'+scope);
    return this.navigationReads.read('workspace:'+scope,()=>this.readWorkspace(scope),10_000);
  }
  prefetchWorkspace(scope:string):void{
    if(!this.navigationOwner||this.closing||this.prefetching.has(scope)||this.prefetching.size>=2)return;
    this.prefetching.add(scope);
    void this.workspace(scope).catch(()=>{}).finally(()=>this.prefetching.delete(scope));
  }
  private async readWorkspace(scope:string):Promise<WorkspaceState & {understanding:import('./understanding').CanonicalRevision[]}>{
    const state=await this.sharing<WorkspaceState & {understanding:import('./understanding').CanonicalRevision[]}>(scope,'workspace');
    workspaceState(state,scope);
    if(!Array.isArray(state.understanding))throw new ApiError(502);
    return state;
  }
  async importPdf(scope:string,file:File,operation:string,displayName?:string):Promise<WorkspaceState>{
    this.navigationReads.clear();
    const response=await fetch('/api/context-spaces/'+scope+'/workspace/documents/'+operation,{
      method:'PUT',headers:{Authorization:'Bearer '+await this.token(),'Content-Type':'application/pdf','X-Document-Name':encodeURIComponent(file.name),...(displayName!==undefined?{'X-Document-Display-Name':encodeURIComponent(displayName)}:{})},
      body:file,credentials:'omit',cache:'no-store',redirect:'error'});
    if(!response.ok){
      if(response.status===401)this.expired();
      const detail=await response.json().catch(()=>null);
      if([413,422].includes(response.status)&&typeof detail?.detail==='string')throw new Error(detail.detail);
      throw new ApiError(response.status);
    }
    return workspaceState(await response.json(),scope);
  }
  async downloadDocument(scope:string,revision:string,name:string):Promise<void>{
    const response=await fetch('/api/context-spaces/'+scope+'/workspace/documents/'+revision,{
      headers:{Authorization:'Bearer '+await this.token()},credentials:'omit',cache:'no-store',redirect:'error'});
    if(response.status===401)this.expired();
    if(!response.ok)throw new ApiError(response.status);
    const url=URL.createObjectURL(await response.blob()),anchor=document.createElement('a');
    anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async addIntake(scope:string,input:ContextIntake):Promise<WorkspaceState>{return this.sharing(scope,'workspace/intake','POST',input);}
  async consolidate(scope:string):Promise<WorkspaceState>{return workspaceState(await this.sharing(scope,'workspace/consolidate','POST'),scope);}
  async exportContext(scope:string):Promise<PortableContext>{return this.sharing(scope,'workspace/export');}
  async regenerate(scope:string,operation:string):Promise<WorkspaceState>{return workspaceState(await this.sharing(scope,'workspace/regenerate','POST',{operation_id:operation} satisfies WorkspaceRegenerationInput),scope);}
  async workspaceChat(scope:string,question:string,operation:string):Promise<void>{
    const receipt=await this.sharing<WorkspaceMessageReceipt>(scope,'workspace/messages','POST',{question_id:question,operation_id:operation} satisfies WorkspaceMessageInput);
    if(receipt?.state!=='completed')throw new ApiError(502);
  }
  async sharing<T>(scope:string,suffix:string,method='GET',body?:unknown):Promise<T>{
    if(!isUuid(scope))throw new ApiError(404);
    return await this.request('/context-spaces/'+scope+'/'+suffix,method,body) as T;
  }
  async enrich(scope:string,payload:{conversation_id:string;operation_id:string;turns:SelectedConversationTurn[];persist_consent:boolean;extraction_mode?:'semantic'}):Promise<EnrichmentReceipt>{
    if(!isUuid(scope))throw new ApiError(404);
    return this.enrichmentReceipt(await this.request('/context-spaces/'+scope+'/enrichments','POST',payload),scope);
  }
  async enrichmentCapabilities(scope:string):Promise<{semantic:boolean;external_disclosure:boolean}> {
    if(!isUuid(scope))throw new ApiError(404);
    const value=await this.request('/context-spaces/'+scope+'/enrichments/capabilities') as {semantic:boolean;external_disclosure:boolean};
    if(!value||typeof value.semantic!=='boolean'||typeof value.external_disclosure!=='boolean')throw new ApiError(502);
    return value;
  }
  async aiDiagnostics(scope:string):Promise<AIDiagnostic[]> {
    if(!isUuid(scope))throw new ApiError(404);
    const value=await this.request('/context-spaces/'+scope+'/ai/diagnostics') as {retention_seconds:number;items:AIDiagnostic[]};
    if(!value||value.retention_seconds!==3600||!Array.isArray(value.items)||value.items.length>100||value.items.some(r=>!r||!isUuid(r.id)||r.context_id!==scope||!Number.isFinite(r.expires_at)||!Array.isArray(r.checks)))throw new ApiError(502);
    return value.items;
  }
  async deleteAIDiagnostic(scope:string,id:string):Promise<void> {
    if(!isUuid(scope)||!isUuid(id))throw new ApiError(404);
    await this.request('/context-spaces/'+scope+'/ai/diagnostics/'+id,'DELETE');
  }
  async automaticChat(scope:string,messages:DialogueMessage[],include:boolean):Promise<ChatAnswer>{
    if(!isUuid(scope))throw new ApiError(404);
    return chatAnswer(await this.request('/context-spaces/'+scope+'/ai/messages','POST',{messages,include_proposed:include}),scope,include,messages,true);
  }
  async proposeWithAI(scope:string,payload:Parameters<QhApi['enrich']>[1]):Promise<EnrichmentReceipt>{
    if(!isUuid(scope))throw new ApiError(404);
    const receipt=this.enrichmentReceipt(await this.request('/context-spaces/'+scope+'/ai/proposals','POST',payload),scope);
    if(receipt.provider_mode!=='uum-mistral/3')throw new ApiError(502);return receipt;
  }
  private enrichmentReceipt(raw:unknown,scope:string):EnrichmentReceipt{
    const r=raw as EnrichmentReceipt;
    if(!r||r.context_id!==scope||!isUuid(r.source_revision_id)||!Array.isArray(r.revision_ids)||r.revision_ids.length>100||r.revision_ids.some(id=>!isUuid(id))||new Set(r.revision_ids).size!==r.revision_ids.length||typeof r.replayed!=='boolean'||!['offline-literal/1','semantic-simulated/2','uum-offline-literal/3','uum-simulated/3','uum-mistral/3'].includes(r.provider_mode))throw new ApiError(502);
    return r;
  }
  async reviewStatus(scope:string,revision:string):Promise<ReviewStatus>{
    if(!isUuid(scope)||!isUuid(revision))throw new ApiError(404);
    const s=await this.request('/context-spaces/'+scope+'/understanding/'+revision+'/review') as ReviewStatus;
    if(!s||s.revision_id!==revision||!isUuid(s.latest_revision_id)||typeof s.pending!=='boolean'||!(s.current_revision_id===null||isUuid(s.current_revision_id))||!(s.successor_revision_id===null||isUuid(s.successor_revision_id)))throw new ApiError(502);
    return s;
  }
  async review(scope:string,revision:string,operation:{operation_id:string;action:'confirm'|'reject'|'correct'|'review_assignments'|'review_primary';primary_decision?:{state:'proposed'|'accepted'|'rejected';value?:string;evidence_refs?:number[]};assignment_decisions?:{index:number;state:'accepted'|'rejected';reuse_value?:string}[];expected_latest_revision_id:string;expected_current_revision_id:string|null;text:string|null}){
    if(!isUuid(scope)||!isUuid(revision))throw new ApiError(404);
    const r=await this.request('/context-spaces/'+scope+'/understanding/'+revision+'/review','POST',operation) as {revision_id:string;action:string;replayed:boolean};
    if(!r||!isUuid(r.revision_id)||r.action!==operation.action||typeof r.replayed!=='boolean')throw new ApiError(502);return r;
  }
  async dimensionPresence(scope:string,view:'current'|'proposed'):Promise<DimensionPresence>{
    if(!isUuid(scope))throw new ApiError(404);
    const r=await this.request('/context-spaces/'+scope+'/understanding-presence?view='+view) as DimensionPresence;
    if(!r||r.context_id!==scope||r.view!==view||typeof r.unclassified!=='boolean'||!r.dimensions||Object.keys(r.dimensions).length!==6||DIMENSIONS.some(([id])=>typeof r.dimensions[id]!=='boolean'))throw new ApiError(502);
    return r;
  }
  async pendingReview(scope:string,limit=20,after?:string){
    if(!isUuid(scope))throw new ApiError(404);
    return revisionPage(await this.request('/context-spaces/'+scope+'/review?limit='+limit+(after?'&after_revision_id='+encodeURIComponent(after):'')),{context_ids:[scope],view:'proposed',limit});
  }
  async resumeSpaces(sort:'recent'|'used',domain:string|null,after?:string):Promise<SpacePage>{
    return this.navigationReads.read('spaces:'+sort+':'+domain+':'+after,()=>this.readResumeSpaces(sort,domain,after));
  }
  private async readResumeSpaces(sort:'recent'|'used',domain:string|null,after?:string):Promise<SpacePage>{
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
    this.navigationReads.remove('organization');this.navigationReads.removePrefix('spaces:');
    const write=this.request('/environment/spaces/'+scope+'/open','POST',{event_id}).then(()=>{});this.openingWrites.set(event_id,write);
    try{await write;}finally{if(this.openingWrites.get(event_id)===write)this.openingWrites.delete(event_id);}
  }
  organization():Promise<Organization>{return this.navigationReads.read('organization',async()=>{await Promise.allSettled([...this.openingWrites.values(),...this.organizationWrites]);return organization(await this.request('/environment'));});}
  async organize(document:Organization):Promise<Organization>{
    const write=this.request('/environment','PUT',{version:document.version,domains:document.domains,memberships:document.memberships,primary_domains:document.primary_domains,...(document.space_descriptions?{space_descriptions:document.space_descriptions}:{})}).then(organization);
    this.organizationWrites.add(write);try{return await write;}finally{this.organizationWrites.delete(write);}
  }
  async chat(scope:string,messages:DialogueMessage[],includeProposed:boolean):Promise<ChatAnswer> {
    if(!isUuid(scope))throw new ApiError(404);
    return chatAnswer(await this.request('/context-spaces/'+scope+'/chat','POST',{
      messages,include_proposed:includeProposed}),scope,includeProposed,messages);
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
    return chatAnswer(await this.request('/context-spaces/'+scope+'/chat-sessions/'+id+'/messages','POST',{messages,include_proposed:include}),scope,include,messages);
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
    if(this.navigationOwner!==v.user_id)this.navigationReads.clear();
    this.navigationOwner=v.user_id!;
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
    return this.navigationReads.read('space:'+id,async()=>space(await this.request('/context-spaces/' + id)));
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
  if (error instanceof ApiError && error.status === 403) return 'Ton compte ne dispose pas des autorisations nécessaires.';
  if (error instanceof ApiError && error.status === 422) return 'Vérifie les informations saisies.';
  return 'Le service est indisponible. Réessaie dans un instant.';
}
