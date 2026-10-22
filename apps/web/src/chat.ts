import {ApiError} from './transport';
import {revisionPage} from './understanding';
import type {CanonicalRevision} from './understanding';
export interface DialogueMessage {role:'user'|'assistant';content:string}
export interface ChatAnswer {
  context_id:string;answer:string;model:string;references:CanonicalRevision[];provided_revisions:CanonicalRevision[];
  support_basis:'dialogue'|'canonical'|'mixed'|'insufficient';insufficient_context:boolean;partial_coverage:boolean;input_bound:number;context_bytes:number;generation_seconds:number|null;
}
export function chatAnswer(raw:unknown,scope:string,includeProposed:boolean,dialogue:DialogueMessage[]):ChatAnswer {
  const a=raw as ChatAnswer;
  if(!a || a.context_id!==scope || typeof a.answer!=='string' || !a.answer.trim() || [...a.answer].length>4096 ||
    typeof a.model!=='string' || !a.model || a.model.length>128 || typeof a.insufficient_context!=='boolean' || typeof a.partial_coverage!=='boolean' ||
    !Number.isInteger(a.input_bound) || a.input_bound<0 || a.input_bound>12000 || !Number.isInteger(a.context_bytes) || a.context_bytes<0 || a.context_bytes>8000 ||
    !(a.generation_seconds===null || typeof a.generation_seconds==='number' && Number.isFinite(a.generation_seconds) && a.generation_seconds>=0))throw new ApiError(502);
  const query={context_ids:[scope],view:'history' as const,limit:40};
  const provided=revisionPage({view:'history',items:a.provided_revisions,next_after_revision_id:null},query).items;
  const references=revisionPage({view:'history',items:a.references,next_after_revision_id:null},query).items;
  for(const r of provided)if(!(r.validation_state==='confirmed' && r.is_current_confirmed || includeProposed && r.validation_state==='proposed'))throw new ApiError(502);
  for(const r of references)if(!provided.some(p=>p.revision_id===r.revision_id && JSON.stringify(p)===JSON.stringify(r)))throw new ApiError(502);
  if(!['dialogue','canonical','mixed','insufficient'].includes(a.support_basis)||
    a.insufficient_context!==(a.support_basis==='insufficient')||
    ['canonical','mixed'].includes(a.support_basis)&&!references.length||
    a.support_basis==='dialogue'&&references.length||
    ['dialogue','mixed'].includes(a.support_basis)&&!dialogue.some(m=>m.role==='user'&&m.content.trim()))throw new ApiError(502);
  return a;
}
