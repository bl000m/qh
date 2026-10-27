import {ApiError,isUuid} from './transport';
import {revisionPage} from './understanding';
import type {CanonicalRevision} from './understanding';
export interface SessionCapabilities {automatic?:boolean;plafond_reached?:boolean;accounting_blocked?:boolean;enabled:boolean;model:string|null;max_seconds:number|null;max_calls:number|null;max_usd:string;provider_expires_at:number|null;remaining_calls:number|null;remaining_usd:string}
export interface ProviderSession {
 session_id:string;context_id:string;model:string;state:'preview'|'active'|'closed'|'revoked';expires_at:number;
 include_proposed:boolean;snapshot_sha256:string;max_calls:number;max_usd:string;
 accounting:{calls:number;committed_usd:string;blocked:boolean};provided_revisions:CanonicalRevision[];
 provider_messages:{role:string;content:string}[];partial_coverage:boolean;input_bound:number;context_bytes:number;
}
export function capabilities(raw:unknown):SessionCapabilities {
 const v=raw as SessionCapabilities;
 if(v?.max_calls===null&&(!v.automatic||v.remaining_calls!==null||v.max_seconds!==null))throw new ApiError(502);
 if(!v||typeof v.enabled!=='boolean'||v.automatic!==undefined&&typeof v.automatic!=='boolean'||v.plafond_reached!==undefined&&typeof v.plafond_reached!=='boolean'||v.accounting_blocked!==undefined&&typeof v.accounting_blocked!=='boolean'||!(v.enabled?v.model==='mistral-small-2603':v.model===null)||
  (v.enabled?(!Number.isFinite(v.provider_expires_at)||!v.provider_expires_at):v.provider_expires_at!==null)||
  !(v.automatic&&v.max_calls===null&&v.remaining_calls===null)&&(!Number.isInteger(v.remaining_calls)||v.remaining_calls!<0||v.remaining_calls!>(v.automatic?100:8))||
  typeof v.remaining_usd!=='string'||!Number.isFinite(Number(v.remaining_usd))||Number(v.remaining_usd)<0||Number(v.remaining_usd)>(v.automatic?(v.max_calls===null?5:2.50):.20)||
  !(v.automatic&&v.max_calls===null&&v.max_seconds===null)&&![300,1800].includes(v.max_seconds!)||!(v.automatic&&v.max_calls===null)&&(!Number.isInteger(v.max_calls)||v.max_calls!<1||v.max_calls!>(v.automatic?100:8))||
  typeof v.max_usd!=='string'||!Number.isFinite(Number(v.max_usd))||Number(v.max_usd)<=0||Number(v.max_usd)>(v.automatic?(v.max_calls===null?5:2.50):.20))throw new ApiError(502);
 return v;
}
export function providerSession(raw:unknown,scope:string,include:boolean):ProviderSession {
 const v=raw as ProviderSession;
 if(!v||!isUuid(v.session_id??'')||v.context_id!==scope||v.model!=='mistral-small-2603'||
  !['preview','active','closed','revoked'].includes(v.state)||!Number.isFinite(v.expires_at)||v.expires_at<=0||
  v.include_proposed!==include||!/^([a-f0-9]{64})$/.test(v.snapshot_sha256)||
  typeof v.max_usd!=='string'||!Number.isFinite(Number(v.max_usd))||Number(v.max_usd)<=0||Number(v.max_usd)>.20||
  !Number.isInteger(v.max_calls)||v.max_calls<1||v.max_calls>8||!v.accounting||
  !Number.isInteger(v.accounting.calls)||v.accounting.calls<0||v.accounting.calls>v.max_calls||
  typeof v.accounting.committed_usd!=='string'||!Number.isFinite(Number(v.accounting.committed_usd))||Number(v.accounting.committed_usd)<0||
  typeof v.accounting.blocked!=='boolean'||!Array.isArray(v.provider_messages)||v.provider_messages.length>9||
  v.provider_messages.some(m=>!m||!['system','user','assistant'].includes(m.role)||typeof m.content!=='string')||
  typeof v.partial_coverage!=='boolean'||!Number.isInteger(v.input_bound)||v.input_bound<0||v.input_bound>12000||
  !Number.isInteger(v.context_bytes)||v.context_bytes<0||v.context_bytes>8000)throw new ApiError(502);
 const rows=revisionPage({view:'history',items:v.provided_revisions,next_after_revision_id:null},{context_ids:[scope],view:'history',limit:40}).items;
 if(!rows.length||rows.some(r=>!(r.validation_state==='confirmed'&&r.is_current_confirmed||include&&r.validation_state==='proposed')))throw new ApiError(502);
 return v;
}
