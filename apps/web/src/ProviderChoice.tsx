import {useEffect,useRef,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {DialogueMessage} from './chat';
import type {ProviderSession,SessionCapabilities} from './provider-session';
import {Revision} from './Revision';

export const offlineFixture=import.meta.env.MODE==='test'&&import.meta.env.VITE_QH_OFFLINE_TESTS==='1';
const defaultMode=offlineFixture?'mock':'mistral';
type Props={api:QhApi;scope:string;include:boolean;messages:DialogueMessage[];failure:number;contextChanged?:number;completed:number;
 onChange:(mode:'mock'|'mistral',session:string|null,preserveDialogue?:boolean)=>void};
export default function ProviderChoice({api,scope,include,messages,failure,contextChanged=0,completed,onChange}:Props){
 const [mode,setMode]=useState<'mock'|'mistral'>(defaultMode);
 const [caps,setCaps]=useState<SessionCapabilities|null>(null);
 const [session,setSession]=useState<ProviderSession|null>(null);
 const [consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [expanded,setExpanded]=useState(false);
 const manage=useRef<HTMLButtonElement>(null);
 const [now,setNow]=useState(Date.now());
 const current=useRef<ProviderSession|null>(null),generation=useRef(0),prepared=useRef('');
 function forget(){const old=current.current;current.current=null;setSession(null);setConsent(false);return old;}
 async function revoke(){
  generation.current++;const old=forget();onChange('mistral',null);setBusy(false);
  if(old)try{await api.revokeSession(scope,old.session_id);setError('Session révoquée. Aucun nouvel envoi autorisé.');}
  catch{setError('État local effacé. Révocation serveur non confirmée : la session reste bornée par sa courte expiration.');}
 }
 useEffect(()=>{
  generation.current++;setCaps(null);setSession(null);current.current=null;setConsent(false);setMode(defaultMode);setError('');onChange(defaultMode,null);
  let mounted=true;
  api.chatCapabilities(scope).then(v=>{if(mounted)setCaps(v);}).catch(()=>{if(mounted)setError('Le fournisseur est indisponible. Vous pouvez toujours ajouter une information sans IA.');});
  const leave=()=>{const old=current.current;if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});};
  window.addEventListener('pagehide',leave);
  return()=>{mounted=false;generation.current++;window.removeEventListener('pagehide',leave);leave();};
 },[api,scope,include,onChange]);
 useEffect(()=>{if(failure&&mode==='mistral'){void revoke().then(()=>setError('Session arrêtée après erreur ou nouvelle discussion. Aucun nouvel essai automatique ; un nouveau consentement est requis.'));}},[failure]); // Generation failure terminates, never retries.
 useEffect(()=>{if(!contextChanged||!current.current)return;generation.current++;const old=forget();setBusy(false);onChange('mistral',null,true);void api.revokeSession(scope,old!.session_id).catch(()=>{});setError('Compréhension enrichie : nouveau contexte, nouvel aperçu et consentement requis.');},[contextChanged]);
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
   current.current=v;setSession(v);setExpanded(false);onChange('mistral',v.session_id);
  }catch{if(n===generation.current){forget();onChange('mistral',null);setError('Consentement refusé ou contexte modifié. Préparez un nouvel aperçu.');}}
  finally{if(n===generation.current)setBusy(false);}
 }
 async function refresh(){if(!session)return;const n=generation.current;try{const v=await api.sessionStatus(scope,session.session_id,include);if(n!==generation.current)return;current.current=v;setSession(v);setCaps(await api.chatCapabilities(scope));if(v.state!=='active'||v.accounting.blocked||v.accounting.calls>=v.max_calls||Number(v.accounting.committed_usd)>=Number(v.max_usd)){onChange('mistral',null,v.state==='active'&&!v.accounting.blocked);setError('Session arrêtée : plafond atteint ou budget indisponible. Le consentement ne réinitialise pas les plafonds de la session de travail.');}}
  catch{if(n===generation.current)await revoke();}}
 useEffect(()=>{if(completed&&current.current?.state==='active')void refresh();},[completed]);
 const active=session?.state==='active';
 useEffect(()=>{if(active)manage.current?.focus({preventScroll:true});},[active]);
 return <div className={'provider-choice'+(active?' provider-is-active':'')}>
  {active&&session&&<div className="provider-active-line"><p role="status">Mistral · Session active · {session.model} · {session.max_calls-session.accounting.calls} requêtes restantes · {session.accounting.committed_usd}/{session.max_usd} USD engagés · {remaining} s restantes</p><button ref={manage} type="button" className="secondary" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}>Budget et autorisation</button></div>}
  <div hidden={active&&!expanded}>
  {offlineFixture&&<><label htmlFor="chat-provider">Mode de discussion</label>
  <select id="chat-provider" value={mode} onChange={e=>{
   const next=e.target.value as 'mock'|'mistral';generation.current++;const old=forget();if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});
   setBusy(false);setMode(next);setError('');onChange(next,null);
  }}><option value="mock">Démonstration mock — sans appel externe</option><option value="mistral">Mistral — consentement requis</option></select></>}
  {mode==='mistral'&&<section aria-label="Consentement Mistral" className="provider-consent">
   {!caps?.enabled?<p role="status">{caps?'Mistral n’est pas activé sur ce serveur. Aucune donnée n’est envoyée.':error?'Fournisseur indisponible. Aucun envoi autorisé.':'Vérification de la disponibilité du fournisseur. Aucun envoi autorisé.'}</p>:<>
    <p>Disponibilité jusqu’au {new Date(caps.provider_expires_at!*1000).toLocaleString('fr-FR')}. Budget global restant : {caps.remaining_calls} requêtes / {caps.remaining_usd} USD.</p>
    <p>Modèle : {caps.model}. Un seul Space : celui que vous consultez.</p>
    <p>Plafond par session : {caps.max_calls} requêtes, {caps.max_usd} USD. Réservation et limites globales appliquées par le serveur. Aucun retry ni fallback automatique.</p>
    <p className="small">Autorisation bornée à {caps.max_seconds/60} minutes. {caps.max_seconds===1800?'Le renouvellement de la connexion conserve cette autorisation pour le même contenu et la même session de travail.':'La durée restante de la connexion peut réduire cette limite.'} Les plafonds administratifs restent appliqués.</p>
    {!session&&<button type="button" disabled={busy||!messages.at(-1)?.content.trim()} onClick={()=>{void preview();}}>Examiner les données avant envoi</button>}
    {session&&<>
     <p role="status">Session {session.state==='active'?'autorisée':'à autoriser'} · {remaining} s restantes · {session.accounting.calls}/{session.max_calls} requêtes · coût engagé/réservé {session.accounting.committed_usd} USD.</p>
     <p>Visibilité : {session.include_proposed?'informations confirmées actuelles et propositions explicitement incluses':'informations confirmées actuelles uniquement'}. {session.partial_coverage?'Couverture partielle.':''}</p>
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
    <p className="small">La révocation bloque les nouveaux envois ; les données déjà transmises ne peuvent pas être rappelées. Changer de Space, de propositions ou de mode efface la discussion. La réponse de chat seule n’ajoute rien à la compréhension canonique.</p>
   </>}
  </section>}
  </div>
  {error&&<p role="alert">{error}</p>}
 </div>;
}
