import {useEffect,useRef,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {EnrichmentReceipt} from './EnrichConversation';
import {Modal} from './SpaceActions';
import useDraft from './useDraft';

export default function ManualInformation({api,scope,disabled,onSaved,openRequest=0,hideAction=false}:{api:QhApi;scope:string;disabled:boolean;openRequest?:number;hideAction?:boolean;onSaved:(receipt:EnrichmentReceipt)=>void}){
 const [text,setText]=useDraft('element');
 const [open,setOpen]=useState(!!text),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [saved,setSaved]=useState<'added'|'source'|null>(null);
 useEffect(()=>{if(openRequest){setError('');setSaved(null);setOpen(true);}},[openRequest]);
 const attempt=useRef<{text:string;payload:Parameters<QhApi['enrich']>[1]}|null>(null);
 async function save(){
  if(busy||!text.trim())return;
  if(attempt.current?.text!==text)attempt.current={text,payload:{conversation_id:crypto.randomUUID(),operation_id:crypto.randomUUID(),persist_consent:true,turns:[{id:crypto.randomUUID(),role:'user',content:text,captured_at:new Date().toISOString()}]}};
  setBusy(true);setError('');
  try{const receipt=await api.enrich(scope,attempt.current.payload);setSaved(receipt.revision_ids.length?'added':'source');setOpen(false);setText('');attempt.current=null;onSaved(receipt);}
  catch(e){setError(apiMessage(e)+' Aucun nouvel essai automatique. Une nouvelle tentative de ce même texte conserve son identifiant.');}
  finally{setBusy(false);}
 }
 return <section className="manual-information" aria-label="Ajouter un élément sans IA">
  {!hideAction&&<button type="button" className="secondary" disabled={disabled||busy} onClick={()=>{setError('');setSaved(null);setOpen(true);}}>Ajouter un élément</button>}
  {saved&&<div role="status"><p>{saved==='added'?'Élément ajouté au contexte':'Texte conservé comme source ; aucun élément ajouté.'}</p></div>}
  {open&&<Modal title="Ajouter un élément" onClose={()=>{if(!busy)setOpen(false);}}><form onSubmit={e=>{e.preventDefault();void save();}}>
   <p>Une information, un objectif, une décision, une intention ou une question à conserver.</p>
   <label htmlFor="manual-information">Votre information</label><textarea id="manual-information" value={text} maxLength={4096} rows={5} disabled={busy} required onChange={e=>{setText(e.target.value);}}/>
   <p>Votre texte sera conservé tel quel, avec sa source. Vous pourrez le retrouver et le modifier dans Compréhension.</p>
   {error&&<p role="alert" className="notice error">{error}</p>}
   <div className="actions"><button disabled={busy||!text.trim()}>{busy?'Enregistrement…':'Ajouter au contexte'}</button><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button></div>
  </form></Modal>}
 </section>;
}
