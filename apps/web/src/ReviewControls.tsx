import {useEffect,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {CanonicalRevision} from './understanding';
export interface ReviewStatus {revision_id:string;latest_revision_id:string;current_revision_id:string|null;pending:boolean;successor_revision_id:string|null}
export default function ReviewControls({api,scope,row,onChanged,onOpen,compact=false,personal=false}:{api:QhApi;scope:string;row:CanonicalRevision;onChanged:(id:string)=>void;onOpen:(id:string)=>void;compact?:boolean;personal?:boolean}){
 const [status,setStatus]=useState<ReviewStatus|null>(null),[error,setError]=useState(''),[action,setAction]=useState<'confirm'|'reject'|'correct'|null>(null),[text,setText]=useState(String(row.content.text??'')),[busy,setBusy]=useState(false),[reload,setReload]=useState(0);
 useEffect(()=>{let active=true;setStatus(null);api.reviewStatus(scope,row.revision_id).then(s=>{if(active)setStatus(s);}).catch(e=>{if(active)setError(apiMessage(e));});return()=>{active=false;};},[api,scope,row.revision_id,reload]);
 const pending=!!status?.pending&&status.latest_revision_id===row.revision_id;
 const correct=pending||status?.current_revision_id===row.revision_id;
 async function submit(){if(!status||!action)return;setBusy(true);setError('');try{
  const receipt=await api.review(scope,row.revision_id,{operation_id:crypto.randomUUID(),action,expected_latest_revision_id:status.latest_revision_id,expected_current_revision_id:status.current_revision_id,text:action==='correct'?text:null});onChanged(receipt.revision_id);
 }catch(e){setError(apiMessage(e)+' Aucun nouvel essai automatique. Rechargez la révision avant de décider à nouveau.');setAction(null);setStatus(null);}finally{setBusy(false);}}
 return <section className="human-review" aria-label="Révision par le propriétaire">{!compact&&<><h3>Votre décision dans QH</h3><p>Confirmer accepte cet élément dans votre compréhension ; cela ne prouve pas sa vérité extérieure. Rien n’est confirmé automatiquement.</p></>}
 {!status&&!error&&<p role="status">Vérification de l’état de révision…</p>}
 {error&&<div role="alert"><p>{error}</p><button type="button" onClick={()=>{setError('');setReload(n=>n+1);}}>Recharger l’état de révision</button></div>}
 {status?.successor_revision_id&&<p>Une révision ultérieure est conservée. <button className="secondary" onClick={()=>onOpen(status.successor_revision_id!)}>Voir l’évolution conservée</button></p>}
 {status&&!pending&&!correct&&<p>Cette version historique n’est plus une proposition à examiner. Consultez son évolution avant toute décision.</p>}
 {status&&!action&&<div className="actions">{pending&&!personal&&<><button className="secondary" onClick={()=>setAction('confirm')}>{compact?'Confirmer':'Examiner une confirmation'}</button><button className="secondary" onClick={()=>setAction('reject')}>{compact?'Refuser':'Examiner un refus'}</button></>}{correct&&<button className="secondary" onClick={()=>setAction('correct')}>{compact?(personal?'Modifier':'Corriger'):'Proposer une correction'}</button>}</div>}
 {action&&<form onSubmit={e=>{e.preventDefault();void submit();}}><p>{action==='confirm'?'Vous confirmez explicitement le contenu affiché. Une nouvelle révision confirmée deviendra courante.':action==='reject'?'Vous refusez cette proposition. La compréhension précédemment confirmée sera conservée.':'Votre texte deviendra une nouvelle proposition humaine non confirmée. Les sources et les ancrages resteront identiques.'}</p>
 {action==='correct'&&<label>Texte corrigé<textarea required maxLength={16000} value={text} disabled={busy} onChange={e=>setText(e.target.value)}/></label>}
 <div className="actions"><button disabled={busy||action==='correct'&&!text.trim()}>{busy?'Enregistrement…':action==='confirm'?'Confirmer explicitement cet élément':action==='reject'?'Refuser explicitement cette proposition':(compact?'Enregistrer la correction':'Enregistrer la correction comme proposition')}</button><button className="secondary" type="button" disabled={busy} onClick={()=>setAction(null)}>Annuler la décision</button></div></form>}
 </section>;
}
