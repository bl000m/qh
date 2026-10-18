import {useEffect,useRef,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {DialogueMessage} from './chat';
import type {ProviderSession,SessionCapabilities} from './provider-session';
import {Revision} from './Revision';

type Props={api:QhApi;scope:string;include:boolean;messages:DialogueMessage[];failure:number;completed:number;
 onChange:(mode:'mock'|'mistral',session:string|null)=>void};
export default function ProviderChoice({api,scope,include,messages,failure,completed,onChange}:Props){
 const [mode,setMode]=useState<'mock'|'mistral'>('mock');
 const [caps,setCaps]=useState<SessionCapabilities|null>(null);
 const [session,setSession]=useState<ProviderSession|null>(null);
 const [consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [now,setNow]=useState(Date.now());
 const current=useRef<ProviderSession|null>(null),generation=useRef(0),prepared=useRef('');
 function forget(){const old=current.current;current.current=null;setSession(null);setConsent(false);return old;}
 async function revoke(){
  generation.current++;const old=forget();onChange('mistral',null);setBusy(false);
  if(old)try{await api.revokeSession(scope,old.session_id);setError('Session révoquée. Aucun nouvel envoi autorisé.');}
  catch{setError('État local effacé. Révocation serveur non confirmée : la session reste bornée par sa courte expiration.');}
 }
 useEffect(()=>{
  generation.current++;setCaps(null);setSession(null);current.current=null;setConsent(false);setMode('mock');setError('');onChange('mock',null);
  let mounted=true;
  api.chatCapabilities(scope).then(v=>{if(mounted)setCaps(v);}).catch(()=>{if(mounted)setError('Mode Mistral indisponible. Le mock reste utilisable.');});
  const leave=()=>{const old=current.current;if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});};
  window.addEventListener('pagehide',leave);
  return()=>{mounted=false;generation.current++;window.removeEventListener('pagehide',leave);leave();};
 },[api,scope,include,onChange]);
 useEffect(()=>{if(failure&&mode==='mistral'){void revoke().then(()=>setError('Session arrêtée après erreur ou nouvelle discussion. Aucun nouvel essai automatique ; un nouveau consentement est requis.'));}},[failure]); // Generation failure terminates, never retries.
 const dialogueKey=JSON.stringify(messages);
 useEffect(()=>{if(current.current?.state==='preview'&&prepared.current!==dialogueKey){void revoke();setError('Question modifiée : préparez un nouvel aperçu avant de consentir.');}},[dialogueKey]);
 useEffect(()=>{if(!session)return;const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[session]);
 const remaining=session?Math.max(0,Math.ceil(session.expires_at-now/1000)):0;
 useEffect(()=>{if(session&&remaining===0){generation.current++;forget();onChange('mistral',null);setError('Session expirée. Reconnectez-vous si nécessaire puis donnez un nouveau consentement.');}},[remaining,session,onChange]);
 async function preview(){
  const n=++generation.current;setBusy(true);setError('');setConsent(false);
  try{const v=await api.previewSession(scope,messages,include);
   if(n!==generation.current){void api.revokeSession(scope,v.session_id).catch(()=>{});return;}
   prepared.current=dialogueKey;current.current=v;setSession(v);setNow(Date.now());
  }catch(e){if(n===generation.current)setError(apiMessage(e));}finally{if(n===generation.current)setBusy(false);}
 }
 async function authorize(){
  if(!session||!consent)return;const n=generation.current;setBusy(true);setError('');
  try{const v=await api.consentSession(scope,session.session_id,session.snapshot_sha256,include);
   if(n!==generation.current){void api.revokeSession(scope,v.session_id).catch(()=>{});return;}
   current.current=v;setSession(v);onChange('mistral',v.session_id);
  }catch{if(n===generation.current){forget();onChange('mistral',null);setError('Consentement refusé ou contexte modifié. Préparez un nouvel aperçu.');}}
  finally{if(n===generation.current)setBusy(false);}
 }
 async function refresh(){if(!session)return;const n=generation.current;try{const v=await api.sessionStatus(scope,session.session_id,include);if(n!==generation.current)return;current.current=v;setSession(v);if(v.state!=='active'||v.accounting.blocked||v.accounting.calls>=v.max_calls||Number(v.accounting.committed_usd)>=Number(v.max_usd)){onChange('mistral',null);setError('Session arrêtée : plafond atteint ou budget indisponible. Un nouveau consentement est requis.');}}
  catch{if(n===generation.current)await revoke();}}
 useEffect(()=>{if(completed&&current.current?.state==='active')void refresh();},[completed]);
 return <div className="provider-choice">
  <label htmlFor="chat-provider">Mode de discussion</label>
  <select id="chat-provider" value={mode} onChange={e=>{
   const next=e.target.value as 'mock'|'mistral';generation.current++;const old=forget();if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});
   setBusy(false);setMode(next);setError('');onChange(next,null);
  }}><option value="mock">Démonstration mock — sans appel externe</option><option value="mistral">Mistral — consentement requis</option></select>
  {mode==='mistral'&&<section aria-label="Consentement Mistral" className="provider-consent">
   {!caps?.enabled?<p role="status">Mistral n’est pas activé sur ce serveur. Aucune donnée n’est envoyée.</p>:<>
    <p>Modèle : {caps.model}. Un seul Space : celui que vous consultez.</p>
    <p>Plafond par session : {caps.max_calls} requêtes, {caps.max_usd} USD. Réservation et limites globales appliquées par le serveur. Aucun retry ni fallback automatique.</p>
    <p className="small">Maximum 5 minutes, sans dépasser le temps restant de votre connexion (token de 300 secondes). Une reconnexion exige un nouveau consentement. Aucun renouvellement automatique.</p>
    {!session&&<button type="button" disabled={busy||!messages.at(-1)?.content.trim()} onClick={()=>{void preview();}}>Examiner les données avant envoi</button>}
    {session&&<>
     <p role="status">Session {session.state==='active'?'autorisée':'à autoriser'} · {remaining} s restantes · {session.accounting.calls}/{session.max_calls} requêtes · coût engagé/réservé {session.accounting.committed_usd} USD.</p>
     <p>Visibilité : {session.include_proposed?'confirmed-current et propositions explicitement incluses':'confirmed-current uniquement'}. {session.partial_coverage?'Couverture partielle.':''}</p>
     {session.provided_revisions.every(r=>r.validation_state==='proposed')&&<p role="note" className="notice">Tout le contexte fourni est proposé et non confirmé.</p>}
     <details><summary>Données exactes et provenance avant envoi ({session.provided_revisions.length} révisions)</summary>
      {session.provided_revisions.map(r=><Revision key={r.revision_id} row={r}/>)}
      <details><summary>Messages destinés au fournisseur et empreinte</summary><pre className="json-value">{JSON.stringify({snapshot_sha256:session.snapshot_sha256,messages:session.provider_messages},null,2)}</pre></details>
     </details>
     {session.state==='preview'&&<>
      <label className="chat-opt-in"><input type="checkbox" checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/> J’autorise l’envoi à Mistral du contexte affiché, de ma question et de cette discussion temporaire, pour ce modèle, ce Space et ces limites.</label>
      <button type="button" disabled={!consent||busy||remaining===0} onClick={()=>{void authorize();}}>Autoriser cette session Mistral</button>
     </>}
     <button type="button" className="secondary" onClick={()=>{void revoke();}}>Révoquer la session</button>
     {session.state==='active'&&<button type="button" className="secondary" onClick={()=>{void refresh();}}>Actualiser le budget</button>}
    </>}
    <p className="small">La révocation bloque les nouveaux envois ; les données déjà transmises ne peuvent pas être rappelées. Changer de Space, de propositions ou de mode efface la discussion. Rien n’est ajouté à la compréhension canonique.</p>
   </>}
  </section>}
  {error&&<p role="alert">{error}</p>}
 </div>;
}
