import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestInvitationCreated,SharingInput,SharingPreview,RecipientAnswer} from '@qh/shared';
import type {QhApi} from './api';
import {ApiError} from './api';
import {Modal} from './SpaceActions';
import {sharingEnabled,sharingError,recipientAnswer} from './sharing';
import SharedRecap from './SharedRecap';
import AnswerMarkdown from './AnswerMarkdown';
import './sharing.css';

interface InvitationRow{id:string;recipient_email:string;expires_at:string;revoked_at:string|null}
const reasonLabels:Record<string,string>={owner_restriction:'Informations retirées à ta demande',recognised_high_risk:'Informations sensibles repérées',recognised_high_risk_citation:'Citations sensibles',endpoint_outside_scope:'Relations hors du périmètre autorisé',endpoint_not_disclosable:'Relations avec des informations exclues',unsupported_content:'Informations non communicables'};
const maskLabels:Record<string,string>={email:'Adresses email masquées',url:'Liens masqués',number:'Coordonnées ou numéros masqués',identifier:'Identifiants masqués'};
function Editor({api,scope,name,onClose}:{api:QhApi;scope:string;name:string;onClose:()=>void}){
 const [email,setEmail]=useState(''),[purpose,setPurpose]=useState('Consulter et interroger le contexte partagé');
 const [allowUpdates,setAllowUpdates]=useState(false);
 const [documents,setDocuments]=useState<import('../../../packages/shared/src/context-space').SourceDocument[]>([]),[originals,setOriginals]=useState<string[]>([]);
 useEffect(()=>{void api.sharing<import('../../../packages/shared/src/context-space').SourceDocument[]>(scope,'workspace/documents').then(setDocuments).catch(()=>{});},[api,scope]);
 const [expiry,setExpiry]=useState(()=>{const d=new Date(Date.now()+3600000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,19);});
 const [excluded,setExcluded]=useState<NonNullable<SharingInput['excluded']>>([]);
 const [previewRefresh,setPreviewRefresh]=useState(0);
 const [preparing,setPreparing]=useState(false);const generation=useRef(0);
 const [preview,setPreview]=useState<SharingPreview|null>(null),[link,setLink]=useState(''),[snapshot,setSnapshot]=useState('');
 const [question,setQuestion]=useState(''),[answer,setAnswer]=useState<RecipientAnswer|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[rows,setRows]=useState<InvitationRow[]>([]);const lock=useRef(false);
 const refresh=()=>api.sharing<{items:InvitationRow[]}>(scope,'invitations').then(v=>setRows(v.items));
 useEffect(()=>{void refresh().catch(e=>setError(sharingError(e)));},[]);
 useEffect(()=>{
  const current=++generation.current;setPreview(null);setLink('');setSnapshot('');setAnswer(null);setError('');
  const expires=new Date(expiry).getTime();
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||!purpose.trim()||!Number.isFinite(expires)||expires<=Date.now()){setPreparing(false);return;}
  setPreparing(true);
  const timer=setTimeout(()=>{
   const body:SharingInput={recipient_email:email,purpose,expires_at:new Date(expires).toISOString(),excluded,allow_update_proposals:allowUpdates,original_documents:originals};
   void api.sharing<SharingPreview>(scope,'sharing/previews','POST',body)
    .then(value=>{if(current===generation.current)setPreview(value);})
    .catch(e=>{if(current===generation.current)setError(sharingError(e));})
    .finally(()=>{if(current===generation.current)setPreparing(false);});
  },400);
  return()=>{clearTimeout(timer);generation.current++;};
 },[api,scope,email,purpose,expiry,excluded,allowUpdates,originals,previewRefresh]);
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
  &&JSON.stringify(preview.policy.original_documents??[])===JSON.stringify(originals)
  &&(preview.policy.allow_update_proposals??false)===allowUpdates
  &&Date.parse(preview.policy.expires_at)===new Date(expiry).getTime()
  &&!excluded.some(k=>preview.report.anchors?.some(a=>a.item_id===k.item_id&&a.revision_id===k.revision_id));
 const exclusions=[...new Set(preview?.report.exclusions.map(x=>reasonLabels[x.reason]??'Informations exclues par les règles de protection'))];
 const masks=[...new Set(preview?.report.masks.flatMap(x=>x.rules.map(r=>maskLabels[r]??'Informations masquées')))];
 return <Modal title="Partager ce contexte" onClose={onClose} className="sharing-dialog" closeOnBackdrop>
 <p className="sharing-intro">Invitez une personne à accéder aux informations autorisées de ce contexte partagé.</p>
 <form onSubmit={(event:FormEvent)=>{event.preventDefault();void approve();}}>
 <div className="sharing-columns"><div className="sharing-settings"><fieldset disabled={busy||!!link}>
 <label>Email du destinataire<input type="email" required maxLength={254} placeholder="votre@email.com" value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Expiration de l’accès<input type="datetime-local" step="1" required value={expiry} onChange={e=>setExpiry(e.target.value)}/></label>
 <h3>Droits accordés</h3>
 <div className="sharing-permission included"><span className="permission-tick" aria-hidden="true">✓</span><div><strong>Consulter et interroger le contexte</strong><span className="permission-badge">Toujours inclus</span><p>Le destinataire peut lire le résumé autorisé et poser des questions, sans modifier le contenu.</p></div></div>
 <label className="sharing-permission check"><input type="checkbox" checked={allowUpdates} onChange={e=>setAllowUpdates(e.target.checked)}/><span><strong>Autoriser les propositions de mise à jour</strong><span className="permission-description">Vous conservez le contrôle et la validation finale de toute modification.</span></span></label>
 <p className="sharing-hint">L’autorisation est enregistrée avec l’invitation. L’envoi de propositions reste indisponible dans cette démo : le parcours de réception et de validation des contributions externes n’est pas encore implémenté.</p>
 </fieldset></div>
 <aside className="sharing-preview" aria-label="Aperçu du contexte partagé"><h3>Aperçu du contexte partagé</h3><p className="small muted">Présentation générale des informations autorisées, sans les sources ni la structure interne.</p>
 <div className="sharing-preview-card"><strong>{preview?.payload.name??name}</strong>
 <SharedRecap recap={matches?preview?.payload.recap:undefined}/>
 {(!matches||!preview?.payload.recap)&&<p className="muted">{preparing?'Préparation de l’aperçu autorisé…':matches?'Aucun résumé communicable pour ce partage. Les questions porteront sur les informations autorisées.':'Indiquez le destinataire pour préparer l’aperçu autorisé.'}</p>}
 <p className="small muted">Contenu filtré selon les règles de confidentialité</p></div>
 <div className="sharing-chat-art" aria-hidden="true"><span>•••</span><p>Un contexte à explorer,<br/>un partage maîtrisé.</p></div>
 </aside></div><div className="sharing-supplement">
 {error&&<div role="alert"><p className="notice error">{error}</p>{!preview&&<button type="button" className="secondary" disabled={busy||preparing} onClick={()=>setPreviewRefresh(n=>n+1)}>Réessayer</button>}</div>}
 <p className="sharing-hint">Créer l’invitation approuve la divulgation des informations communicables. Vérifiez les exclusions, masquages et risques dans Confidentialité avancée ; le masquage ne garantit pas l’anonymat.</p>
 <details className="sharing-advanced"><summary>Confidentialité avancée</summary>
 <section><h3>Documents originaux</h3><p>Privés par défaut. Un original peut contenir des informations exclues ou masquées dans le partage. L’autorisation porte sur chaque document, expire avec l’invitation et se révoque avec l’accès. Ces documents ne sont pas envoyés à l’IA du destinataire.</p>{documents.map(doc=><label key={doc.source_revision_id}><input type="checkbox" disabled={busy||!!link} checked={originals.includes(doc.source_revision_id)} onChange={e=>setOriginals(ids=>e.target.checked?[...ids,doc.source_revision_id]:ids.filter(id=>id!==doc.source_revision_id))}/>Autoriser le téléchargement de {doc.filename}</label>)}</section>
 <label>Finalité du partage<textarea required maxLength={1024} value={purpose} disabled={busy||!!link} onChange={e=>setPurpose(e.target.value)}/></label>
 {preview&&<section aria-label="Prévisualisation du partage"><h3>Informations communicables</h3>
 {preview.payload.name&&<p>Nom partagé : {preview.payload.name}</p>}
 {!preview.payload.items.length&&<p>Aucune information communicable dans ce périmètre.</p>}
 {preview.payload.items.length>0&&<details><summary>Consulter les informations communicables</summary>{preview.payload.items.map(item=><div key={item.reference}><p>{item.text}</p>{!link&&<button type="button" className="secondary" disabled={busy||!preview.report.anchors?.some(a=>a.reference===item.reference)} onClick={()=>{void exclude(item.reference);}}>Exclure cette information</button>}</div>)}</details>}
 {(exclusions.length>0||masks.length>0)&&<div><h4>Protection appliquée</h4>{[...exclusions,...masks].map(text=><p key={text}>{text}</p>)}</div>}
 {excluded.length>0&&!link&&<button type="button" className="secondary" disabled={busy} onClick={()=>{setExcluded([]);}}>Annuler les exclusions supplémentaires</button>}
 {preview.payload.items.length>0&&!link&&<details><summary>Tester une question comme le destinataire</summary><p>Ce test lance une réponse à ta demande, uniquement sur les informations communicables.</p><label>Question de test<textarea value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)} disabled={busy}/></label><button type="button" disabled={busy||!question.trim()} onClick={()=>{void testQuestion();}}>Tester la question</button>{answer&&<div className="guest-answer">{answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={answer.answer}/>{answer.insufficient_context&&<p>Les informations communicables sont insuffisantes pour répondre complètement.</p>}</div>}</details>}
 <p>Le masquage automatique ne garantit pas à lui seul la confidentialité : vérifie ces textes pour ce destinataire, y compris les informations indirectement identifiantes.</p>
 </section>}
 <section><h3>Invitations</h3>{rows.map(row=><p key={row.id}>{row.recipient_email} · {row.revoked_at?'Révoquée':'Expire le '+new Date(row.expires_at).toLocaleString('fr-FR')} <button type="button" className="secondary" disabled={busy||!!row.revoked_at} onClick={()=>{void revoke(row.id);}}>Révoquer l’accès</button></p>)}</section>
 </details>
 {link&&<section aria-label="Invitation créée"><h3>Invitation prête</h3><p>Le destinataire devra vérifier sa boîte email.</p><label>Lien d’invitation<input readOnly value={link} onFocus={e=>e.target.select()}/></label></section>}
 </div><footer className="sharing-footer"><button className="secondary" type="button" onClick={onClose}>Annuler</button>
 {!link&&<button disabled={busy||preparing||!matches||!preview?.payload.items.length}>{busy?'En cours…':preparing?'Préparation du partage…':'Créer l’invitation'}</button>}
 </footer></form></Modal>;
}
export default function SharingControl({api,scope,name,label='Partager ce contexte',primary=false}:{api:QhApi;scope:string;name:string;label?:string;primary?:boolean}){
 const [open,setOpen]=useState(false);if(!sharingEnabled)return null;
 return <div className="sharing-entry"><button className={primary?'sharing-primary':'secondary'} onClick={()=>setOpen(true)}>{label}</button>{open&&<Editor key={scope} api={api} scope={scope} name={name} onClose={()=>setOpen(false)}/>}</div>;
}
