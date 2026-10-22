import {useEffect,useRef,useState} from 'react';
import type {QhApi} from './api';
import {apiMessage} from './api';
import type {DialogueMessage} from './chat';
import type {ProviderSession,SessionCapabilities} from './provider-session';
import {Revision} from './Revision';
import {Modal} from './SpaceActions';
import ModelCatalogue from './ModelCatalogue';
export const offlineFixture=import.meta.env.MODE==='test'&&import.meta.env.VITE_QH_OFFLINE_TESTS==='1';
const defaultMode=offlineFixture?'mock':'mistral';
type Props={api:QhApi;scope:string;include:boolean;messages:DialogueMessage[];failure:number;contextChanged?:number;completed:number;request?:number;visible?:boolean;hasProposed?:boolean;onInclude?:(value:boolean)=>void;onCapabilities?:(value:SessionCapabilities|null)=>void;
 onChange:(mode:'mock'|'mistral',session:string|null,preserveDialogue?:boolean)=>void};
export default function ProviderChoice({api,scope,include,messages,failure,contextChanged=0,completed,request=0,visible=true,hasProposed=false,onInclude,onCapabilities,onChange}:Props){
 const [mode,setMode]=useState<'mock'|'mistral'>(defaultMode),[caps,setCaps]=useState<SessionCapabilities|null>(null),[session,setSession]=useState<ProviderSession|null>(null);
 const [consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[open,setOpen]=useState(false),[now,setNow]=useState(Date.now());
 const current=useRef<ProviderSession|null>(null),generation=useRef(0),prepared=useRef(''),attempted=useRef('');
 const dialogueKey=JSON.stringify(messages);
 function forget(){const old=current.current;current.current=null;setSession(null);setConsent(false);return old;}
 async function revoke(preserveDialogue=false){generation.current++;const old=forget();onChange('mistral',null,preserveDialogue);setBusy(false);if(old)try{await api.revokeSession(scope,old.session_id);setError('Autorisation retirée. Aucun nouvel envoi.');}catch{setError('Autorisation effacée dans cet onglet. Le serveur n’a pas confirmé son retrait ; elle reste limitée dans le temps.');}}
 useEffect(()=>{
  generation.current++;setCaps(null);onCapabilities?.(null);setSession(null);current.current=null;setConsent(false);setMode(defaultMode);setError('');attempted.current='';onChange(defaultMode,null,!!caps?.automatic);
  let mounted=true;api.chatCapabilities(scope).then(v=>{if(mounted){setCaps(v);onCapabilities?.(v);}}).catch(()=>{if(mounted)setError('Le modèle est indisponible pour ce contexte. Vous pouvez toujours ajouter un élément.');});
  const leave=()=>{const old=current.current;if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});};window.addEventListener('pagehide',leave);
  return()=>{mounted=false;generation.current++;window.removeEventListener('pagehide',leave);leave();};
 },[api,scope,onChange,onCapabilities]);
 useEffect(()=>{if(current.current)void revoke(true);},[include]);
 useEffect(()=>{if(request&&!caps?.automatic){attempted.current='';setError('');setOpen(true);}},[request]);
 useEffect(()=>{if(failure&&mode==='mistral'&&!caps?.automatic)void revoke(true).then(()=>setError('La discussion a été arrêtée. Donnez une nouvelle autorisation avant de réessayer.'));},[failure]);
 useEffect(()=>{if(!contextChanged||!current.current)return;generation.current++;const old=forget();setBusy(false);onChange('mistral',null,true);void api.revokeSession(scope,old!.session_id).catch(()=>{});setError('Le contexte a changé. Une nouvelle autorisation est nécessaire.');},[contextChanged]);
 useEffect(()=>{if(current.current?.state==='preview'&&prepared.current!==dialogueKey){void revoke();}},[dialogueKey]);
 useEffect(()=>{if(!session)return;const t=window.setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(t);},[session]);
 const remaining=session?Math.max(0,Math.ceil(session.expires_at-now/1000)):0;
 useEffect(()=>{if(session&&remaining===0){generation.current++;forget();onChange('mistral',null);setError('L’autorisation a expiré. Vous pouvez en donner une nouvelle.');}},[remaining,session,onChange]);
 async function preview(){
  const n=++generation.current;setBusy(true);setError('');setConsent(false);
  try{const v=await api.previewSession(scope,messages,include);if(n!==generation.current){void api.revokeSession(scope,v.session_id).catch(()=>{});return;}prepared.current=dialogueKey;current.current=v;setSession(v);setNow(Date.now());}
  catch(e){if(n===generation.current)setError(apiMessage(e));}finally{if(n===generation.current)setBusy(false);}
 }
 // One internal preview per explicit request/selection. It never invokes a provider.
 useEffect(()=>{const key=include+':'+dialogueKey;if(open&&caps?.enabled&&messages.at(-1)?.content.trim()&&!current.current&&!busy&&attempted.current!==key){attempted.current=key;void preview();}},[open,caps?.enabled,include,dialogueKey]);
 async function authorize(){if(!session||!consent)return;const n=generation.current;setBusy(true);setError('');try{const v=await api.consentSession(scope,session.session_id,session.snapshot_sha256,include);if(n!==generation.current){void api.revokeSession(scope,v.session_id).catch(()=>{});return;}current.current=v;setSession(v);setOpen(false);onChange('mistral',v.session_id);}catch{if(n===generation.current){forget();onChange('mistral',null);setError('Le contexte ou votre autorisation a changé. Rouvrez l’autorisation pour continuer.');}}finally{if(n===generation.current)setBusy(false);}}
 async function refresh(){if(!session)return;const n=generation.current;try{const [v,capabilities]=await Promise.all([api.sessionStatus(scope,session.session_id,include),api.chatCapabilities(scope)]);if(n!==generation.current)return;current.current=v;setSession(v);setCaps(capabilities);onCapabilities?.(capabilities);setNow(Date.now());}catch{if(n===generation.current){forget();onChange('mistral',null);setError('Autorisation indisponible.');}}}
 useEffect(()=>{if(completed&&current.current?.state==='active')void refresh();},[completed]);
 async function refreshCapabilities(){try{const v=await api.chatCapabilities(scope);setCaps(v);onCapabilities?.(v);}catch{setError('Le modèle est indisponible.');}}
 useEffect(()=>{if((completed||contextChanged||failure)&&caps?.automatic)void refreshCapabilities();},[completed,contextChanged,failure]);
 function close(){setOpen(false);if(current.current?.state==='preview')void revoke();}
 return <>
 <section hidden={!visible} id="space-panel-2" role="tabpanel" aria-labelledby="space-tab-2" className="space-tab-content model-panel"><ModelCatalogue caps={caps} active={mode==='mistral'} failed={!!error}/>
  {offlineFixture&&<div className="test-provider-choice"><label htmlFor="chat-provider">Mode de discussion</label><select id="chat-provider" value={mode} onChange={e=>{generation.current++;const old=forget();if(old)void api.revokeSession(scope,old.session_id).catch(()=>{});setBusy(false);setMode(e.target.value as 'mock'|'mistral');onChange(e.target.value as 'mock'|'mistral',null);}}><option value="mock">Démonstration mock — sans appel externe</option><option value="mistral">Mistral — consentement requis</option></select></div>}
  {caps?.automatic?<section className="automatic-ai-info" aria-label="Utilisation IA"><p>Mistral Small · mistral-small-2603. Envoyer transmet votre conversation et les éléments confirmés de ce Space uniquement. Les propositions nécessitent votre choix distinct. Aucune mémorisation automatique.</p><p>Plafond global : {caps.remaining_calls} requêtes et {caps.remaining_usd} USD restants, partagés entre tous vos Spaces. Aucun renouvellement par connexion ou session. Disponible jusqu’au {caps.provider_expires_at?new Date(caps.provider_expires_at*1000).toLocaleString('fr-FR'):'plafond atteint ou indisponibilité'}.</p>{caps.plafond_reached&&<p role="status">Plafond IA atteint. Aucune nouvelle requête ne sera facturée.</p>}<button type="button" className="secondary" onClick={()=>{void refreshCapabilities();}}>Actualiser la disponibilité</button></section>:<details className="administrative-disclosure"><summary>Autorisation et limites</summary>{offlineFixture&&hasProposed&&<label className="check"><input type="checkbox" checked={include} onChange={e=>onInclude?.(e.target.checked)}/>Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.</label>}{caps?.enabled&&<><p>Disponibilité jusqu’au {new Date(caps.provider_expires_at!*1000).toLocaleString('fr-FR')}. Au maximum {caps.max_calls} requêtes / {caps.max_usd} USD par session, pendant {caps.max_seconds/60} minutes.</p><p>Modèle : {caps.model}.</p><p>Aucun envoi automatique. Un changement des informations partagées nécessite une nouvelle autorisation.</p></>}{session&&<><p role="status">{session.state==='active'?'Autorisation active':'Autorisation à confirmer'} · {remaining} s restantes · {session.accounting.calls}/{session.max_calls} requêtes · {session.accounting.committed_usd} USD.</p><button type="button" className="secondary" onClick={()=>{void revoke();}}>Révoquer la session</button>{session.state==='active'&&<button type="button" className="secondary" onClick={()=>{void refresh();}}>Actualiser le budget</button>}</>}{error&&<p role="status">{error}</p>}</details>}
 </section>
 {open&&!caps?.automatic&&<Modal title="Autoriser cette discussion" onClose={close}><section aria-label="Consentement Mistral"><p>Votre question et les éléments affichés ci-dessous seront transmis à {caps?.model??'Mistral'}, uniquement pour cette discussion dans ce Space.</p>
 {hasProposed&&<label className="check"><input type="checkbox" checked={include} disabled={busy||session?.state==='active'} onChange={e=>onInclude?.(e.target.checked)}/>Utiliser aussi les éléments à vérifier. Ils ne sont pas encore confirmés.</label>}
 {!caps?.enabled?<p role="status">Le modèle n’est pas disponible pour ce contexte. Aucun envoi n’a lieu.</p>:<>
 {busy&&<p role="status">Préparation des informations à partager…</p>}
 {session&&<><p>{session.provided_revisions.length} éléments partagés{session.partial_coverage?' · sélection partielle':''}. Autorisation limitée à {caps.max_seconds/60} minutes, avec les mêmes limites de budget.</p><details open><summary>Informations partagées</summary>{session.provided_revisions.map(r=><Revision key={r.revision_id} row={r}/>)}<details><summary>Messages et empreinte de contrôle</summary><pre className="json-value">{JSON.stringify({snapshot_sha256:session.snapshot_sha256,messages:session.provider_messages},null,2)}</pre></details></details>
 <label className="check"><input type="checkbox" checked={consent} disabled={busy} onChange={e=>setConsent(e.target.checked)}/>J’autorise l’envoi à Mistral des informations affichées et de cette discussion temporaire, dans ces limites.</label><button type="button" disabled={!consent||busy||remaining===0} onClick={()=>{void authorize();}}>Autoriser cette session Mistral</button><p className="small muted">Après cette autorisation, choisissez Envoyer pour transmettre votre question. Aucune réponse ne sera mémorisée automatiquement.</p></>}
 {error&&<p role="alert">{error}</p>}</>}
 </section></Modal>}
 </>;
}
