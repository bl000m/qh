import {useEffect,useRef,useState} from 'react';
import {ApiError,apiMessage} from './api';
import type {QhApi} from './api';
import {Modal} from './SpaceActions';

export interface SelectedConversationTurn {id:string;role:'user'|'assistant';content:string;captured_at:string}
export interface EnrichmentReceipt {context_id:string;source_revision_id:string;revision_ids:string[];replayed:boolean;provider_mode:'offline-literal/1'|'semantic-simulated/2'|'uum-offline-literal/3'|'uum-simulated/3'}

export default function EnrichConversation({api,scope,conversationId,turns,disabled,onOpen,onSaved}:{api:QhApi;scope:string;conversationId:string;turns:SelectedConversationTurn[];disabled:boolean;onOpen?:(id:string)=>void;onSaved?:(receipt:EnrichmentReceipt)=>void}){
 const [open,setOpen]=useState(false),[selected,setSelected]=useState<string[]>([]),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [semanticAvailable,setSemanticAvailable]=useState(false),[semantic,setSemantic]=useState(false);
 useEffect(()=>{let active=true;if(open&&typeof api.enrichmentCapabilities==='function')api.enrichmentCapabilities(scope).then(c=>{if(active)setSemanticAvailable(c.semantic);}).catch(()=>{if(active){setSemanticAvailable(false);setSemantic(false);}});return()=>{active=false;};},[api,scope,open]);
 const [savedTurns,setSavedTurns]=useState<string[]>([]);
 const [receipt,setReceipt]=useState<EnrichmentReceipt|null>(null);
 const attempts=useRef(new Map<string,string>());
 function prepare(){setSemantic(false);setSelected(turns.filter(t=>t.role==='user'&&!savedTurns.includes(t.id)).map(t=>t.id));setConsent(false);setError('');setOpen(true);}
 async function submit(){
  const chosen=turns.filter(t=>selected.includes(t.id));if(!consent||!chosen.length||busy)return;
  const key=JSON.stringify({chosen,semantic});const operation=attempts.current.get(key)??crypto.randomUUID();attempts.current.set(key,operation);setBusy(true);setError('');
  try{const result=await api.enrich(scope,{conversation_id:conversationId,operation_id:operation,turns:chosen,persist_consent:true,...(semantic?{extraction_mode:'semantic' as const}:{})});setReceipt(result);setSavedTurns(previous=>[...new Set([...previous,...chosen.map(t=>t.id)])]);setOpen(false);onSaved?.(result);}
  catch(e){setError(e instanceof ApiError&&e.status===409?'Cette sélection entre en conflit avec un enregistrement précédent. Rien n’a été remplacé.':e instanceof ApiError&&e.status===503?'Enrichissement indisponible. Aucun nouvel essai automatique. Une nouvelle tentative explicite de la même sélection réutilise son identifiant pour éviter les doublons.':e instanceof ApiError&&e.status===422?'La sélection ou les citations ne permettent pas une publication valide. Aucune source ni proposition n’a été ajoutée.':apiMessage(e));}
  finally{setBusy(false);}
 }
 return <section className="conversation-enrichment" aria-label="Enrichissement explicite du contexte">
  {turns.length>0&&<button type="button" className="memory-card" disabled={disabled} onClick={prepare}><strong>Mémoriser cette conversation</strong><span>Choisir les messages utiles à conserver dans ce contexte.</span><span aria-hidden="true">›</span></button>}
  {receipt&&<div role="status" className="notice"><p>{receipt.revision_ids.length?receipt.revision_ids.length+(receipt.revision_ids.length===1?' nouvelle proposition à vérifier.':' nouvelles propositions à vérifier.')+' Rien n’est confirmé. Les nouvelles propositions peuvent prendre un instant à devenir consultables.':'Messages sélectionnés conservés comme source ; aucun nouvel élément à vérifier.'}{receipt.replayed?' Enregistrement déjà conservé, sans doublon.':''}</p>
   {receipt.revision_ids.map((id,i)=><button key={id} className="secondary" type="button" onClick={()=>onOpen?.(id)}>Examiner la proposition {i+1}</button>)}</div>}
  {open&&<Modal title="Mémoriser cette conversation" onClose={()=>{if(!busy)setOpen(false);}}>
   <p>Choisissez les passages utiles à retrouver dans ce contexte. Rien ne sera confirmé automatiquement.</p>
   <p className="notice">Seuls les messages que vous sélectionnez seront conservés. {semantic?'La source exacte sera conservée et QH proposera des interprétations sémantiques à vérifier, avec un fournisseur simulé hors réseau.':'Vos mots seront repris tels quels, sans analyse par une IA.'} Les réponses de l’assistant restent des réponses à vérifier.</p>
   <form onSubmit={e=>{e.preventDefault();void submit();}}><fieldset disabled={busy}><legend>Messages à conserver</legend>{turns.map((t,i)=><label className="enrichment-turn" key={t.id}><input type="checkbox" checked={selected.includes(t.id)} onChange={e=>{setSelected(p=>e.target.checked?[...p,t.id]:p.filter(id=>id!==t.id));setConsent(false);}}/><span><strong>{i+1} · {t.role==='user'?'Votre message déclaré':'Réponse de l’assistant non vérifiée'}</strong>{savedTurns.includes(t.id)&&<small>Déjà conservé dans une source sélectionnée. Une autre sélection explicite peut produire une autre proposition ; aucune fusion sémantique automatique.</small>}<span className="chat-text">{t.content}</span></span></label>)}
   {semanticAvailable&&<label className="check"><input type="checkbox" checked={semantic} onChange={e=>{setSemantic(e.target.checked);setConsent(false);}}/>Proposer aussi une compréhension sémantique (simulation hors réseau)</label>}
   <label className="check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>J’autorise la conservation des messages sélectionnés comme source et la création de propositions non confirmées dans ce Space.</label></fieldset>
   <p className="small muted">Aucun envoi à un fournisseur externe. Ce consentement ne confirme aucun élément. Vous pourrez examiner, corriger ou refuser les propositions avec les contrôles existants.</p>
   {error&&<p role="alert" className="notice error">{error}</p>}
   <div className="actions"><button disabled={busy||!consent||!selected.length}>{busy?'Préparation des propositions…':'Conserver et proposer'}</button><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button></div></form>
  </Modal>}
 </section>;
}
