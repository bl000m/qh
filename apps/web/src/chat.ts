import type {OwnerSupportBasis} from '../../../packages/shared/src/context-space';
import {ApiError} from './transport';
import {revisionPage} from './understanding';
import type {CanonicalRevision} from './understanding';
export interface DialogueMessage {role:'user'|'assistant';content:string}
export interface ChatAnswer {
  context_id:string;answer:string;model:string;references:CanonicalRevision[];provided_revisions:CanonicalRevision[];
  support_basis:OwnerSupportBasis;insufficient_context:boolean;partial_coverage:boolean;input_bound:number;context_bytes:number;generation_seconds:number|null;
}
export function chatAnswer(raw:unknown,scope:string,includeProposed:boolean,dialogue:DialogueMessage[],automatic=false,consolidated=false):ChatAnswer {
  const a=raw as ChatAnswer;
  if(!a || a.context_id!==scope || typeof a.answer!=='string' || !a.answer.trim() || [...a.answer].length>(automatic?1_000_000:4096) ||
    typeof a.model!=='string' || !a.model || a.model.length>128 || typeof a.insufficient_context!=='boolean' || typeof a.partial_coverage!=='boolean' ||
    !Number.isInteger(a.input_bound) || a.input_bound<0 || !automatic&&a.input_bound>12000 || !Number.isInteger(a.context_bytes) || a.context_bytes<0 || a.context_bytes>(consolidated?1_000_000:8000) ||
    !(a.generation_seconds===null || typeof a.generation_seconds==='number' && Number.isFinite(a.generation_seconds) && a.generation_seconds>=0))throw new ApiError(502);
  const query={context_ids:[scope],view:'history' as const,limit:consolidated?100:40};
  const provided=revisionPage({view:'history',items:a.provided_revisions,next_after_revision_id:null},query).items;
  const references=revisionPage({view:'history',items:a.references,next_after_revision_id:null},query).items;
  for(const r of provided)if(!(r.validation_state==='confirmed' && r.is_current_confirmed || includeProposed && r.validation_state==='proposed'))throw new ApiError(502);
  for(const r of references)if(!provided.some(p=>p.revision_id===r.revision_id && JSON.stringify(p)===JSON.stringify(r)))throw new ApiError(502);
  if(!['general','dialogue','canonical','mixed','insufficient'].includes(a.support_basis)||
    ['canonical','mixed'].includes(a.support_basis)&&!references.length||
    ['general','dialogue'].includes(a.support_basis)&&references.length||
    ['dialogue','mixed'].includes(a.support_basis)&&!dialogue.some(m=>m.role==='user'&&m.content.trim()))throw new ApiError(502);
  return a;
}
