import {useRef,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {EnrichmentReceipt} from './EnrichConversation';
import {Modal} from './SpaceActions';

export default function ManualInformation({api,scope,disabled,onSaved,onOpen}:{api:QhApi;scope:string;disabled:boolean;onSaved:()=>void;onOpen?:(id:string)=>void}){
 const [open,setOpen]=useState(false),[text,setText]=useState(''),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [saved,setSaved]=useState<EnrichmentReceipt|null>(null);
 const attempt=useRef<{text:string;payload:Parameters<QhApi['enrich']>[1]}|null>(null);
 async function save(){
  if(busy||!consent||!text.trim())return;
  if(attempt.current?.text!==text)attempt.current={text,payload:{conversation_id:crypto.randomUUID(),operation_id:crypto.randomUUID(),persist_consent:true,turns:[{id:crypto.randomUUID(),role:'user',content:text,captured_at:new Date().toISOString()}]}};
  setBusy(true);setError('');
  try{const value=await api.enrich(scope,attempt.current.payload);setSaved(value);setOpen(false);setText('');setConsent(false);attempt.current=null;onSaved();}
  catch(e){setError(apiMessage(e)+' Aucun nouvel essai automatique. Une nouvelle tentative de ce même texte conserve son identifiant.');}
  finally{setBusy(false);}
 }
 return <section className="manual-information" aria-label="Ajouter une information sans IA">
  <button type="button" className="secondary" disabled={disabled||busy} onClick={()=>{setError('');setOpen(true);}}>Ajouter une information</button>
  {saved&&<div role="status"><p>Votre information est conservée. Elle reste une proposition à vérifier ; rien n’est confirmé automatiquement.</p>{saved.revision_ids.map((id,i)=><button key={id} type="button" className="secondary" onClick={()=>onOpen?.(id)}>Examiner l’information {i+1}</button>)}</div>}
  {open&&<Modal title="Ajouter une information" onClose={()=>{if(!busy)setOpen(false);}}><form onSubmit={e=>{e.preventDefault();void save();}}>
   <p>Décrivez ce que vous souhaitez conserver dans ce contexte, même si la conversation est indisponible.</p>
   <label htmlFor="manual-information">Votre information</label><textarea id="manual-information" value={text} maxLength={4096} rows={5} disabled={busy} required onChange={e=>{setText(e.target.value);setConsent(false);}}/>
   <p>Le texte sera conservé tel quel, avec sa source. Aucune analyse par un modèle ni aucun envoi externe. Vous pourrez ensuite l’examiner, le corriger ou le refuser.</p>
   <label className="check"><input type="checkbox" checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/>Je souhaite conserver ce texte comme proposition non confirmée dans ce contexte.</label>
   {error&&<p role="alert" className="notice error">{error}</p>}
   <div className="actions"><button disabled={busy||!consent||!text.trim()}>{busy?'Enregistrement…':'Conserver cette information'}</button><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button></div>
  </form></Modal>}
 </section>;
}
