import {useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {AnswerAttribution} from '../../../packages/shared/src/context-space';
import type {CanonicalRevision} from './understanding';
import {recognizedCitations} from './understanding';
const labels={general:'Connaissances générales',dialogue:'Conversation',canonical:'Informations de ce Space',mixed:'Informations de ce Space et conseils généraux',insufficient:'Informations disponibles'};

export default function WorkspaceAnswerSources({api,scope,attribution}:{api:QhApi;scope:string;attribution:AnswerAttribution}){
 const [rows,setRows]=useState<CanonicalRevision[]|null>(null),[error,setError]=useState('');
 async function load(){
  setError('');setRows(null);
  try{
   const pages=await Promise.all(attribution.reference_ids.map(revision_id=>api.browse(scope,{view:'history',revision_id,limit:1})));
   if(pages.some((p,i)=>p.items.length!==1||p.items[0].revision_id!==attribution.reference_ids[i]))throw new Error('Source indisponible');
   setRows(pages.flatMap(p=>p.items));
  }catch(e){setError(apiMessage(e));}
 }
 if(!attribution.reference_ids.length&&!attribution.insufficient_context&&!attribution.partial_coverage)return null;
 return <div className="workspace-answer-support">
  {attribution.insufficient_context&&<p className="small muted">Les informations disponibles ne suffisent pas à répondre complètement.</p>}
  {attribution.partial_coverage&&<p className="small muted">Seule une partie de la compréhension a été utilisée.</p>}
  {attribution.reference_ids.length>0&&<details onToggle={event=>{if(event.currentTarget.open)void load();else setRows(null);}}><summary>Sources du contexte</summary>
   <p className="small">{labels[attribution.support_basis]}.</p>
   {!attribution.reference_ids.length?<p className="small muted">Aucun élément de compréhension cité.</p>:error?<p role="alert">{error}</p>:rows===null?<p role="status">Vérification des sources…</p>:rows.map(row=><section key={row.revision_id}><p>{String(row.content.text??'')}</p>{recognizedCitations(row).map((citation,index)=><blockquote key={index}>{citation.quote}</blockquote>)}</section>)}
  </details>}
 </div>;
}
