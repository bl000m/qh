import {useEffect,useRef,useState} from 'react';
import {ApiError,apiMessage} from './api';
import type {QhApi} from './api';
import {Modal} from './SpaceActions';
import {Icon} from './Ui';
export interface SelectedConversationTurn {id:string;role:'user'|'assistant';content:string;captured_at:string}
export interface EnrichmentReceipt {context_id:string;source_revision_id:string;revision_ids:string[];replayed:boolean;provider_mode:'offline-literal/1'|'semantic-simulated/2'|'uum-offline-literal/3'|'uum-simulated/3'|'uum-mistral/3'}
export default function EnrichConversation({api,scope,conversationId,turns,disabled,onOpen,onSaved}:{api:QhApi;scope:string;conversationId:string;turns:SelectedConversationTurn[];disabled:boolean;onOpen?:(id:string)=>void;onSaved?:(receipt:EnrichmentReceipt)=>void}){
 const [open,setOpen]=useState(false),[snapshot,setSnapshot]=useState<SelectedConversationTurn[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [caps,setCaps]=useState<{semantic:boolean;external_disclosure:boolean}|null>(null),[receipt,setReceipt]=useState<EnrichmentReceipt|null>(null);
 const attempts=useRef(new Map<string,string>());
 useEffect(()=>{let active=true;if(open){setCaps(null);api.enrichmentCapabilities(scope).then(c=>{if(active)setCaps(c);}).catch(()=>{if(active)setCaps({semantic:false,external_disclosure:false});});}return()=>{active=false;};},[api,scope,open]);
 function prepare(){setSnapshot(turns.map(t=>({...t})));setReceipt(null);setError('');setOpen(true);}
 async function submit(){
  if(busy||!snapshot.length||!caps?.semantic)return;
  const key=JSON.stringify(snapshot),operation=attempts.current.get(key)??crypto.randomUUID();attempts.current.set(key,operation);setBusy(true);setError('');
  try{
   const payload={conversation_id:conversationId,operation_id:operation,turns:snapshot,persist_consent:true,extraction_mode:'semantic' as const};
   const result=await (caps.external_disclosure?api.proposeWithAI(scope,payload):api.enrich(scope,payload));
   if(!result)throw new Error('No receipt');setReceipt(result);onSaved?.(result);
  }catch(e){setError(e instanceof ApiError&&e.status===402?'Plafond IA atteint. Aucune nouvelle requête ne sera facturée. Aucune source ni proposition ajoutée.':e instanceof ApiError&&e.status===422?'La réponse ou ses citations ne permettent pas une publication valide. Aucune source ni proposition ajoutée.':e instanceof ApiError&&e.status===409?'Cette opération est en conflit. Aucun contenu existant n’a été remplacé.':e instanceof ApiError&&e.status===503?'Le résultat de l’enregistrement n’est pas confirmé. Aucun nouvel essai automatique. Une nouvelle tentative explicite réutilisera la même opération pour retrouver un éventuel enregistrement sans doublon.':apiMessage(e));}
  finally{setBusy(false);}
 }
 const steps=[['sources','Comprendre','Identifier les informations importantes (objectifs, décisions, questions…).'],['network','Proposer','Créer une proposition de compréhension dans votre Space.'],['folder','Enregistrer','Conserver vos messages comme source, sans rien confirmer.']] as const;
 return <section className="conversation-enrichment" aria-label="Mémorisation de la conversation">
  <button type="button" className="memory-card" disabled={disabled||!turns.length} onClick={prepare}><Icon name="sparkles"/><span><strong>Mémoriser cette conversation</strong><small>Cette conversation sera ajoutée à votre Space QH.</small></span></button>
  {open&&<Modal title="Mémoriser cette conversation" className="memory-modal" onClose={()=>{if(!busy)setOpen(false);}}>
   <div className="memory-lead"><Icon name="sparkles"/><h3>{receipt?'Votre proposition est prête':busy?'Nous analysons cette conversation':'Nous allons analyser cette conversation'}</h3><p>{busy?'QH prépare une compréhension à vérifier.':'QH va comprendre, proposer et conserver — sans rien confirmer.'}</p></div>
   <div className="memory-steps">{steps.map(([icon,title,text])=><section key={title}><span className="memory-step-icon"><Icon name={icon}/></span><h4>{title}</h4><p>{text}</p></section>)}</div>
   {!receipt&&<p className="memory-disclosure">Continuer autorise l’analyse de toute cette conversation par {caps?.external_disclosure?'Mistral Small':'le fournisseur sémantique de cet environnement'} et sa conservation comme source dans ce Space, avec des propositions non confirmées. Les rôles sont conservés ; les réponses de l’assistant restent non vérifiées.</p>}
   {!caps&&!receipt&&<p role="status">Vérification de la disponibilité…</p>}
   {caps&&!caps.semantic&&!receipt&&<p role="status">L’extraction sémantique est indisponible. Aucune source ni proposition n’a été ajoutée.</p>}
   {busy&&<p role="status">Analyse et préparation des propositions…</p>}
   {error&&<p role="alert" className="notice error">{error}</p>}
   {receipt&&<p role="status">{receipt.revision_ids.length?'Source et propositions enregistrées. Rien n’est confirmé.':'Conversation conservée comme source ; aucune proposition produite.'}{receipt.replayed?' Enregistrement retrouvé sans doublon.':''}</p>}
   <footer className="memory-actions">{receipt?<button type="button" onClick={()=>{setOpen(false);if(receipt.revision_ids[0])onOpen?.(receipt.revision_ids[0]);}}>{receipt.revision_ids.length?'Voir la proposition':'Fermer'} <span aria-hidden="true">→</span></button>:<button type="button" disabled={busy||!caps?.semantic} onClick={()=>{void submit();}}>{busy?'Analyse en cours…':'Continuer'} <span aria-hidden="true">→</span></button>}</footer>
  </Modal>}
 </section>;
}
