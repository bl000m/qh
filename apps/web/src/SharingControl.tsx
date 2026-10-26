import {useEffect,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestInvitationCreated,GuestRight,SharingPolicy,SharingPreview,GuestProviderStatus} from '@qh/shared';
import type {QhApi} from './api';
import {Modal} from './SpaceActions';
import {sharingEnabled,sharingError,sharedPayload} from './sharing';
import SharedItems from './SharedItems';

interface InvitationRow{id:string;snapshot_id:string;recipient_email:string;expires_at:string;revoked_at:string|null}
function Editor({api,scope,name,onClose}:{api:QhApi;scope:string;name:string;onClose:()=>void}){
 const [email,setEmail]=useState(''),[purpose,setPurpose]=useState(''),[read,setRead]=useState(true),[ask,setAsk]=useState(false);
 const [providers,setProviders]=useState<GuestProviderStatus[]>([{model:'offline',enabled:true,simulated:true}]),[provider,setProvider]=useState<'offline'|'mistral-small-2603'>('offline');
 const [providersReady,setProvidersReady]=useState(false);
 const [expiry,setExpiry]=useState(()=>{const d=new Date(Date.now()+3600000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);});
 const [proposed,setProposed]=useState(false),[quotes,setQuotes]=useState(false),[risk,setRisk]=useState(false);
 const [preview,setPreview]=useState<SharingPreview|null>(null),[link,setLink]=useState(''),[snapshot,setSnapshot]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[rows,setRows]=useState<InvitationRow[]>([]),[more,setMore]=useState(false);
 const refresh=()=>api.sharing<{items:InvitationRow[];has_more:boolean}>(scope,'invitations').then(v=>{setRows(v.items);setMore(v.has_more);});
 useEffect(()=>{void refresh().catch(e=>setError(sharingError(e)));void api.sharing<{providers:GuestProviderStatus[]}>(scope,'sharing/providers').then(v=>{setProviders(v.providers);setProvidersReady(true);if(v.providers.some(p=>p.model==='mistral-small-2603'&&p.enabled))setProvider('mistral-small-2603');}).catch(e=>setError(sharingError(e)));},[]);
 useEffect(()=>{setPreview(null);setRisk(false);setLink('');setSnapshot('');},[email,purpose,read,ask,expiry,proposed,quotes,provider]);
 async function prepare(event:FormEvent){event.preventDefault();setError('');setPreview(null);setRisk(false);setBusy(true);
   try{const rights:GuestRight[]=[...(read?['READ' as const]:[]),...(ask?['ASK_AI' as const]:[])];
     const policy:SharingPolicy={recipient_email:email,purpose,rights,expires_at:new Date(expiry).toISOString(),
       include_proposed:proposed,include_quotes:quotes,provider:ask?provider:null};
     const v=await api.sharing<SharingPreview>(scope,'sharing/previews','POST',policy);sharedPayloadOrEmpty(v);setPreview(v);
   }catch(e){setError(sharingError(e));}finally{setBusy(false);}}
 async function approve(){if(!preview)return;setBusy(true);setError('');try{
   let id=snapshot;if(!id){const result=await api.sharing<{snapshot_id:string}>(scope,'sharing/previews/'+preview.id+'/approve','POST',
       {fingerprint:preview.fingerprint,exceptions:risk?preview.report.risks:[]});id=result.snapshot_id;setSnapshot(id);}
   const invite=await api.sharing<GuestInvitationCreated>(scope,'snapshots/'+id+'/invitations','POST',{});
   setLink(location.origin+'/guest#invite='+encodeURIComponent(invite.invitation_token));await refresh();
 }catch(e){setError(sharingError(e));}finally{setBusy(false);}}
 async function revoke(id:string){setBusy(true);setError('');try{await api.sharing(scope,'invitations/'+id+'/revoke','POST',{});await refresh();setLink('');}
   catch(e){setError(sharingError(e));}finally{setBusy(false);}}
 return <Modal title="Partager ce Context Space" onClose={onClose} className="sharing-dialog"><p>{name}</p>
 <p>Partagez un accès protégé à ce contexte. Le lien seul ne permet aucune consultation.</p>
 <form onSubmit={e=>{void prepare(e);}}><fieldset disabled={busy||!!link}><legend>Destinataire et autorisations</legend>
 <label>Email du destinataire<input type="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Finalité<textarea required maxLength={1024} value={purpose} onChange={e=>setPurpose(e.target.value)}/></label>
 <label className="check"><input type="checkbox" checked={read} onChange={e=>setRead(e.target.checked)}/>Consulter le snapshot (READ)</label>
 <label className="check"><input type="checkbox" checked={ask} onChange={e=>setAsk(e.target.checked)}/>Poser des questions (ASK_AI)</label>
 {ask&&<><label>Provider autorisé<select aria-label="Provider autorisé" value={provider} onChange={e=>setProvider(e.target.value as 'offline'|'mistral-small-2603')}>{providers.map(p=><option key={p.model} value={p.model} disabled={!p.enabled}>{p.model==='offline'?'Simulation locale — sans coût':'Mistral Small — réel'}</option>)}</select></label><p className="notice">{provider==='offline'?'Simulation locale. Aucun appel IA réel ni facturation.':'Mistral Small reçoit uniquement le snapshot approuvé et la question du destinataire vérifié. Plafond développement commun : 10 € au total, historique inclus.'}{provider==='mistral-small-2603'&&<span> Disponible : {providers.find(p=>p.model===provider)?.remaining_usd??'—'} USD. Chaque question réserve son coût maximal avant envoi.</span>}</p></>}
 <label>Expiration<input type="datetime-local" step="1" required value={expiry} onChange={e=>setExpiry(e.target.value)}/></label>
 <label className="check"><input type="checkbox" checked={proposed} onChange={e=>setProposed(e.target.checked)}/>Inclure les Propositions, sans les confirmer</label>
 {proposed&&<p className="notice">Les propositions restent non confirmées et seront signalées au destinataire.</p>}
 <label className="check"><input type="checkbox" checked={quotes} onChange={e=>setQuotes(e.target.checked)}/>Inclure les citations minimisées autorisées</label>
 </fieldset><button disabled={busy||!read&&!ask||!!link||ask&&!providersReady}>{busy?'Préparation…':'Préparer le partage'}</button></form>
 {error&&<p role="alert" className="notice error">{error}</p>}
 {preview&&<section aria-label="Prévisualisation de la divulgation"><h3>Ce qui sera partagé</h3><p>{preview.report.message}</p>
 <p>{preview.payload.items.length} élément{preview.payload.items.length===1?'':'s'} inclus · {preview.report.exclusions.length} exclus · {preview.report.masks.length} éléments masqués.</p>
 {preview.payload.items.length>0&&<SharedItems payload={preview.payload}/>}
 <details><summary>Exclusions et masquages</summary><ul>{preview.report.exclusions.map((x,i)=><li key={i}>Exclusion : {x.reason}</li>)}{preview.report.masks.map(m=><li key={m.reference}>{m.reference} : {m.rules.join(', ')} masqué.</li>)}</ul></details>
 {preview.report.risks.length>0&&<fieldset disabled={busy||!!link}><legend>Risque résiduel à examiner</legend><p>{preview.report.warning}</p>
 <label className="check"><input type="checkbox" checked={risk} onChange={e=>setRisk(e.target.checked)}/>J’ai examiné ces textes minimisés pour {preview.policy.recipient_email}, y compris les identifiants indirects et leurs combinaisons, et j’autorise ce risque résiduel pour cette finalité.</label></fieldset>}
 <p>Cette approbation autorise la divulgation. Elle ne confirme pas la véracité des éléments.</p>
 {!link&&<button disabled={busy||!preview.payload.items.length||preview.report.risks.length>0&&!risk} onClick={()=>{void approve();}}>Approuver la divulgation et créer l’invitation</button>}
 </section>}
 {link&&<section aria-label="Invitation créée"><h3>Invitation prête</h3><p>Le destinataire devra vérifier sa boîte email. Copiez ce lien maintenant.</p><label>Lien d’invitation<input readOnly value={link} onFocus={e=>e.target.select()}/></label></section>}
 <section><h3>Invitations</h3>{more&&<p>Les 100 invitations les plus récentes sont affichées.</p>}<ul className="invitation-list">{rows.map(row=><li key={row.id}><span>{row.recipient_email} · {row.revoked_at?'Révoquée':'Expire le '+new Date(row.expires_at).toLocaleString('fr-FR')}</span><button className="secondary" disabled={busy||!!row.revoked_at} onClick={()=>{void revoke(row.id);}}>Révoquer l’accès</button></li>)}</ul></section>
 </Modal>;
}
function sharedPayloadOrEmpty(v:SharingPreview){if(!v||typeof v.id!=='string'||typeof v.fingerprint!=='string'||!v.report||!Array.isArray(v.payload?.items))throw Error();if(v.payload.items.length)sharedPayload(v.payload);}
export default function SharingControl({api,scope,name}:{api:QhApi;scope:string;name:string}){
 const [open,setOpen]=useState(false);if(!sharingEnabled)return null;
 return <div className="sharing-entry"><button className="secondary" onClick={()=>setOpen(true)}>Partager ce Context Space</button>{open&&<Editor key={scope} api={api} scope={scope} name={name} onClose={()=>setOpen(false)}/>}</div>;
}
