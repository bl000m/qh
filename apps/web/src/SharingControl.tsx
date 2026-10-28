import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestInvitationCreated,SharingInput,SharingPreview,RecipientAnswer} from '@qh/shared';
import type {QhApi} from './api';
import {ApiError} from './api';
import {Modal} from './SpaceActions';
import {sharingEnabled,sharingError,recipientAnswer} from './sharing';
import SharedRecap from './SharedRecap';
import AnswerMarkdown from './AnswerMarkdown';

interface InvitationRow{id:string;recipient_email:string;expires_at:string;revoked_at:string|null}
const reasonLabels:Record<string,string>={owner_restriction:'Informations retirées à ta demande',recognised_high_risk:'Informations sensibles repérées',recognised_high_risk_citation:'Citations sensibles',endpoint_outside_scope:'Relations hors du périmètre autorisé',endpoint_not_disclosable:'Relations avec des informations exclues',unsupported_content:'Informations non communicables'};
const maskLabels:Record<string,string>={email:'Adresses email masquées',url:'Liens masqués',number:'Coordonnées ou numéros masqués',identifier:'Identifiants masqués'};
function Editor({api,scope,name,onClose}:{api:QhApi;scope:string;name:string;onClose:()=>void}){
 const [email,setEmail]=useState(''),[purpose,setPurpose]=useState('');
 const [expiry,setExpiry]=useState(()=>{const d=new Date(Date.now()+3600000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,19);});
 const [excluded,setExcluded]=useState<NonNullable<SharingInput['excluded']>>([]);
 const [summary,setSummary]=useState<SharingPreview['payload']['recap']|null>();
 const [previewRefresh,setPreviewRefresh]=useState(0);
 const [preparing,setPreparing]=useState(false);const generation=useRef(0);
 const [preview,setPreview]=useState<SharingPreview|null>(null),[link,setLink]=useState(''),[snapshot,setSnapshot]=useState('');
 const [question,setQuestion]=useState(''),[answer,setAnswer]=useState<RecipientAnswer|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[rows,setRows]=useState<InvitationRow[]>([]);const lock=useRef(false);
 const refresh=()=>api.sharing<{items:InvitationRow[]}>(scope,'invitations').then(v=>setRows(v.items));
 useEffect(()=>{void refresh().catch(e=>setError(sharingError(e)));let active=true;
  void api.workspace(scope).then(s=>{if(active)setSummary(s.recap?{title:s.recap.title,text:s.recap.text}:null);}).catch(()=>{if(active)setSummary(null);});
  return()=>{active=false;};},[]);
 useEffect(()=>{
  const current=++generation.current;setPreview(null);setLink('');setSnapshot('');setAnswer(null);setError('');
  const expires=new Date(expiry).getTime();
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||!purpose.trim()||!Number.isFinite(expires)||expires<=Date.now()){setPreparing(false);return;}
  setPreparing(true);
  const timer=setTimeout(()=>{
   const body:SharingInput={recipient_email:email,purpose,expires_at:new Date(expires).toISOString(),excluded};
   void api.sharing<SharingPreview>(scope,'sharing/previews','POST',body)
    .then(value=>{if(current===generation.current)setPreview(value);})
    .catch(e=>{if(current===generation.current)setError(sharingError(e));})
    .finally(()=>{if(current===generation.current)setPreparing(false);});
  },400);
  return()=>{clearTimeout(timer);generation.current++;};
 },[api,scope,email,purpose,expiry,excluded,previewRefresh]);
 function exclude(reference:string){const key=preview?.report.anchors?.find(a=>a.reference===reference);if(!key)return;
  setExcluded(previous=>[...previous,{item_id:key.item_id,revision_id:key.revision_id}]);}
 function fail(error:unknown){setError(sharingError(error));if(error instanceof ApiError&&error.status===409){setPreview(null);setSnapshot('');}}
 async function testQuestion(){if(!preview||preparing||lock.current||!question.trim())return;const current=generation.current;lock.current=true;setBusy(true);setError('');setAnswer(null);
  try{const value=recipientAnswer(await api.sharing(scope,'sharing/previews/'+preview.id+'/ask','POST',{question}));if(current===generation.current)setAnswer(value);}
  catch(e){if(current===generation.current)fail(e);}finally{lock.current=false;setBusy(false);}}
 async function approve(){if(!preview||!matches||preparing||lock.current)return;lock.current=true;setBusy(true);setError('');
  try{let id=snapshot;if(!id){const result=await api.sharing<{snapshot_id:string}>(scope,'sharing/previews/'+preview.id+'/approve','POST',{fingerprint:preview.fingerprint,exceptions:preview.report.risks});id=result.snapshot_id;setSnapshot(id);}
   const invite=await api.sharing<GuestInvitationCreated>(scope,'snapshots/'+id+'/invitations','POST',{});
   setLink(location.origin+'/guest#invite='+encodeURIComponent(invite.invitation_token));await refresh();}
  catch(e){fail(e);}finally{lock.current=false;setBusy(false);}}
 async function revoke(id:string){if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await api.sharing(scope,'invitations/'+id+'/revoke','POST',{});await refresh();setLink('');}
  catch(e){setError(sharingError(e));}finally{lock.current=false;setBusy(false);}}
 const matches=preview&&preview.policy.recipient_email===email&&preview.policy.purpose===purpose
  &&Date.parse(preview.policy.expires_at)===new Date(expiry).getTime()
  &&!excluded.some(k=>preview.report.anchors?.some(a=>a.item_id===k.item_id&&a.revision_id===k.revision_id));
 const exclusions=[...new Set(preview?.report.exclusions.map(x=>reasonLabels[x.reason]??'Informations exclues par les règles de protection'))];
 const masks=[...new Set(preview?.report.masks.flatMap(x=>x.rules.map(r=>maskLabels[r]??'Informations masquées')))];
 return <Modal title="Partager ce contexte" onClose={onClose} className="sharing-dialog"><p>{name}</p>
 <p>Le destinataire pourra poser des questions sur ce contexte, dans les limites de l’accès autorisé. Les sources et la structure interne restent privées.</p>
 <form onSubmit={(event:FormEvent)=>{event.preventDefault();void approve();}}><fieldset disabled={busy||!!link}><legend>Ton partage</legend>
 <label>Email du destinataire<input type="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Finalité du partage<textarea required maxLength={1024} value={purpose} onChange={e=>setPurpose(e.target.value)}/></label>
 <label>Expiration<input type="datetime-local" step="1" required value={expiry} onChange={e=>setExpiry(e.target.value)}/></label>
 </fieldset><section aria-label="Résumé du contexte"><SharedRecap recap={summary??undefined}/>{!summary&&<p>{summary===undefined?"Chargement du résumé…":"Résumé enregistré indisponible."}</p>}</section>
 <p>Les exclusions et masquages protègent les informations sensibles, sans garantie absolue. Créer l’invitation autorise la divulgation des informations communicables, consultables dans Confidentialité avancée.</p>
 {!link&&<button disabled={busy||preparing||!matches||!preview?.payload.items.length}>{busy?'En cours…':preparing?'Préparation du partage…':'Créer l’invitation'}</button>}
 </form>
 {error&&<div role="alert"><p className="notice error">{error}</p>{!preview&&<button type="button" className="secondary" disabled={busy||preparing} onClick={()=>setPreviewRefresh(n=>n+1)}>Réessayer</button>}</div>}
 <details><summary>Confidentialité avancée</summary>
 {preview&&<section aria-label="Prévisualisation du partage"><h3>Informations communicables</h3>
 {preview.payload.name&&<p>Nom partagé : {preview.payload.name}</p>}
 {!preview.payload.items.length&&<p>Aucune information communicable dans ce périmètre.</p>}
 {preview.payload.items.length>0&&<details><summary>Consulter les informations communicables</summary>{preview.payload.items.map(item=><div key={item.reference}><p>{item.text}</p>{!link&&<button type="button" className="secondary" disabled={busy||!preview.report.anchors?.some(a=>a.reference===item.reference)} onClick={()=>{void exclude(item.reference);}}>Exclure cette information</button>}</div>)}</details>}
 {(exclusions.length>0||masks.length>0)&&<div><h4>Protection appliquée</h4>{[...exclusions,...masks].map(text=><p key={text}>{text}</p>)}</div>}
 {excluded.length>0&&!link&&<button type="button" className="secondary" disabled={busy} onClick={()=>{setExcluded([]);}}>Annuler les exclusions supplémentaires</button>}
 {preview.payload.items.length>0&&!link&&<details><summary>Tester une question comme le destinataire</summary><p>Ce test lance une réponse à ta demande, uniquement sur les informations communicables.</p><label>Question de test<textarea value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)} disabled={busy}/></label><button type="button" disabled={busy||!question.trim()} onClick={()=>{void testQuestion();}}>Tester la question</button>{answer&&<div className="guest-answer">{answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={answer.answer}/>{answer.insufficient_context&&<p>Les informations communicables sont insuffisantes pour répondre complètement.</p>}</div>}</details>}
 <p>Le masquage automatique ne garantit pas à lui seul la confidentialité : vérifie ces textes pour ce destinataire, y compris les informations indirectement identifiantes.</p>
 </section>}
 <section><h3>Invitations</h3>{rows.map(row=><p key={row.id}>{row.recipient_email} · {row.revoked_at?'Révoquée':'Expire le '+new Date(row.expires_at).toLocaleString('fr-FR')} <button className="secondary" disabled={busy||!!row.revoked_at} onClick={()=>{void revoke(row.id);}}>Révoquer l’accès</button></p>)}</section>
 </details>
 {link&&<section aria-label="Invitation créée"><h3>Invitation prête</h3><p>Le destinataire devra vérifier sa boîte email.</p><label>Lien d’invitation<input readOnly value={link} onFocus={e=>e.target.select()}/></label></section>}
 </Modal>;
}
export default function SharingControl({api,scope,name,label='Partager ce contexte',primary=false}:{api:QhApi;scope:string;name:string;label?:string;primary?:boolean}){
 const [open,setOpen]=useState(false);if(!sharingEnabled)return null;
 return <div className="sharing-entry"><button className={primary?'sharing-primary':'secondary'} onClick={()=>setOpen(true)}>{label}</button>{open&&<Editor key={scope} api={api} scope={scope} name={name} onClose={()=>setOpen(false)}/>}</div>;
}
