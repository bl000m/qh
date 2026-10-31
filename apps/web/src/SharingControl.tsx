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
import {OriginalDocumentPermission,SharedDocumentsPreview} from './SharingDocuments';
import {Icon} from './Ui';

interface InvitationRow{id:string;recipient_email:string;expires_at:string;revoked_at:string|null}
const reasonLabels:Record<string,string>={ineligible_state:'Informations rejetées ou retirées',endpoint_outside_scope:'Relations incomplètes',endpoint_not_disclosable:'Relations incomplètes',unsupported_content:'Informations vides ou trop longues'};
function knowledgeMatches(preview:SharingPreview|null,email:string,purpose:string,expiry:string){
 return !!preview&&preview.policy.recipient_email===email.trim()&&preview.policy.purpose===purpose
  &&preview.policy.knowledge_scope==='context'&&Date.parse(preview.policy.expires_at)===new Date(expiry).getTime();
}
function SharingPermission({title,description,included=false,checked=false,onChange}:{title:string;description:string;included?:boolean;checked?:boolean;onChange?:(checked:boolean)=>void}){
 return <label className="sharing-permission check"><input type="checkbox" checked={included||checked} disabled={included} onChange={e=>onChange?.(e.target.checked)}/><span><strong>{title}</strong>{included&&<span className="permission-badge">Toujours inclus</span>}<span className="permission-description">{description}</span></span></label>;
}
function Editor({api,scope,name,onClose}:{api:QhApi;scope:string;name:string;onClose:()=>void}){
 const [email,setEmail]=useState(''),[purpose,setPurpose]=useState('Consulter et interroger le contexte partagé');
 const [allowUpdates,setAllowUpdates]=useState(false);
 const [documents,setDocuments]=useState<import('../../../packages/shared/src/context-space').SourceDocument[]>([]),[originals,setOriginals]=useState<string[]>([]);
 const [documentStatus,setDocumentStatus]=useState('loading');
 function loadDocuments(){setDocumentStatus('loading');void api.sharing<import('../../../packages/shared/src/context-space').SourceDocument[]>(scope,'workspace/documents').then(rows=>{setDocuments(rows);setDocumentStatus('ready');}).catch(()=>setDocumentStatus('error'));}
 useEffect(()=>{loadDocuments();},[api,scope]);
 const [expiry,setExpiry]=useState(()=>{const d=new Date(Date.now()+3600000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,19);});
 const [previewRefresh,setPreviewRefresh]=useState(0);
 const [preparing,setPreparing]=useState(false);const generation=useRef(0);
 const [preview,setPreview]=useState<SharingPreview|null>(null),[link,setLink]=useState(''),[snapshot,setSnapshot]=useState('');
 const [question,setQuestion]=useState(''),[answer,setAnswer]=useState<RecipientAnswer|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[rows,setRows]=useState<InvitationRow[]>([]);const lock=useRef(false);
 const invitationLink=useRef<HTMLInputElement>(null);
 useEffect(()=>{
  if(!link||busy)return;
  const input=invitationLink.current,dialog=input?.closest('dialog');
  if(!input||!dialog)return;
  input.focus({preventScroll:true});
  dialog.scrollTo({top:dialog.scrollTop+input.getBoundingClientRect().top-dialog.getBoundingClientRect().top-dialog.clientHeight/2,behavior:'instant'});
 },[link,busy]);
 const refresh=()=>api.sharing<{items:InvitationRow[]}>(scope,'invitations').then(v=>setRows(v.items));
 useEffect(()=>{void refresh().catch(e=>setError(sharingError(e)));},[]);
 useEffect(()=>{
  const current=++generation.current;setPreview(previous=>knowledgeMatches(previous,email,purpose,expiry)?previous:null);setLink('');setSnapshot('');setAnswer(null);setError('');
  const expires=new Date(expiry).getTime();
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())||!purpose.trim()||!Number.isFinite(expires)||expires<=Date.now()){setPreparing(false);return;}
  setPreparing(true);
  const timer=setTimeout(()=>{
   const body:SharingInput={recipient_email:email.trim(),purpose,expires_at:new Date(expires).toISOString(),knowledge_scope:'context',allow_update_proposals:allowUpdates,documents:originals};
   void api.sharing<SharingPreview>(scope,'sharing/previews','POST',body)
    .then(value=>{if(current===generation.current){if(!knowledgeMatches(value,email,purpose,expiry))throw new ApiError(502);setPreview(value);}})
    .catch(e=>{if(current===generation.current)setError(sharingError(e));})
    .finally(()=>{if(current===generation.current)setPreparing(false);});
  },400);
  return()=>{clearTimeout(timer);generation.current++;};
 },[api,scope,email,purpose,expiry,allowUpdates,originals,previewRefresh]);
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
 const showKnowledge=knowledgeMatches(preview,email,purpose,expiry);
 const matches=showKnowledge&&preview
  &&(preview.policy.original_documents??[]).length===originals.length
  &&originals.every(id=>preview.policy.original_documents?.includes(id))
  &&(preview.policy.allow_update_proposals??false)===allowUpdates;
 const validEmail=/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
 const previewMessage=showKnowledge?(preview?.payload.notice??'Aucun résumé validé pour cette version. Toutes les informations détaillées restent interrogeables.')
  :preparing?'Préparation de l’aperçu autorisé…'
  :!validEmail?'Indiquez le destinataire pour préparer l’aperçu autorisé.'
  :error?'L’aperçu n’a pas pu être chargé. Réessayez.'
  :!purpose.trim()||!Number.isFinite(new Date(expiry).getTime())||new Date(expiry).getTime()<=Date.now()
   ?'Vérifiez la finalité et la date d’expiration pour préparer l’aperçu autorisé.'
   :'Préparation de l’aperçu autorisé…';
 const exclusions=[...new Set(preview?.report.exclusions.map(x=>reasonLabels[x.reason]??'Informations exclues par les règles de protection'))];
 return <Modal title="Partager ce contexte" onClose={onClose} className="sharing-dialog" closeOnBackdrop>
 <p className="sharing-intro">Partagez la compréhension de ce contexte et choisissez les fichiers originaux accessibles.</p>
 <form onSubmit={(event:FormEvent)=>{event.preventDefault();void approve();}}>
 <div className="sharing-columns"><div className="sharing-settings"><fieldset disabled={busy||!!link}>
 <label>Email du destinataire<input type="email" required maxLength={254} placeholder="votre@email.com" value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Expiration de l’accès<input type="datetime-local" step="1" required value={expiry} onChange={e=>setExpiry(e.target.value)}/></label>
 <h3>Droits accordés</h3>
 <div className="sharing-permissions">
 <SharingPermission title="Consulter et interroger le contexte" description="Le destinataire peut lire le résumé autorisé et poser des questions, sans modifier le contenu." included/>
 <SharingPermission title="Autoriser les propositions de mise à jour" description="Vous conservez le contrôle et la validation finale de toute modification." checked={allowUpdates} onChange={setAllowUpdates}/>
 </div>
 <p className="sharing-hint" role="note">La compréhension de ce Context Space sera accessible au destinataire. Les documents originaux restent privés sauf autorisation explicite.</p>
 <OriginalDocumentPermission documents={documents} selected={originals} onChange={setOriginals} status={documentStatus} onRetry={loadDocuments}/>

 </fieldset></div>
 <aside className="sharing-preview" aria-label="Aperçu du contexte partagé"><h3>Aperçu du contexte partagé</h3><p className="small muted">Voici ce que verra votre destinataire après vérification de son accès.</p>
 <div className="sharing-preview-card"><strong>{preview?.payload.name??name}</strong>
 <SharedRecap recap={showKnowledge?preview?.payload.recap:undefined}/>
 {(!showKnowledge||!preview?.payload.recap)&&<p className="muted" role={preparing&&!showKnowledge?'status':undefined}>{previewMessage}</p>}
 </div>
 <SharedDocumentsPreview documents={documents} selected={originals}/>
 <p className="sharing-original-warning"><Icon name="info"/>Un PDF original peut contenir des informations absentes de l’aperçu ou exclues du partage. Vérifiez chaque autorisation avant l’envoi.</p>
 </aside></div><div className="sharing-supplement">
 {error&&<div role="alert"><p className="notice error">{error}</p>{!matches&&<button type="button" className="secondary" disabled={busy||preparing} onClick={()=>setPreviewRefresh(n=>n+1)}>Réessayer</button>}</div>}
 <p className="sharing-hint">Créer l’invitation partage toute la compréhension de ce contexte, y compris les informations personnelles éventuellement présentes. Ce partage n’est pas une anonymisation.</p>
 <details className="sharing-advanced"><summary>Détails du partage</summary> <p className="sharing-hint">L’autorisation est enregistrée avec l’invitation. L’envoi de propositions reste indisponible dans cette démo : le parcours de réception et de validation des contributions externes n’est pas encore implémenté.</p>

 <label>Finalité du partage<textarea required maxLength={1024} value={purpose} disabled={busy||!!link} onChange={e=>setPurpose(e.target.value)}/></label>
 {preview&&<section aria-label="Prévisualisation du partage"><h3>Informations communicables</h3>
 {preview.payload.name&&<p>Nom partagé : {preview.payload.name}</p>}
 {!preview.payload.items.length&&<p>Aucune information communicable dans ce périmètre.</p>}
 {preview.payload.items.length>0&&!preview.payload.notice&&<details><summary>Consulter les informations communicables</summary>{preview.payload.items.map(item=><div key={item.reference}><p>{item.text}</p></div>)}</details>}
 {exclusions.length>0&&<div><h4>Non incluses</h4>{exclusions.map(text=><p key={text}>{text}</p>)}</div>}
 {preview.payload.items.length>0&&!preview.payload.notice&&!link&&<details><summary>Tester une question comme le destinataire</summary><p>Ce test lance une réponse à ta demande, uniquement sur les informations communicables.</p><label>Question de test<textarea value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)} disabled={busy}/></label><button type="button" disabled={busy||!question.trim()} onClick={()=>{void testQuestion();}}>Tester la question</button>{answer&&<div className="guest-answer">{answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={answer.answer}/>{answer.insufficient_context&&<p>Les informations communicables sont insuffisantes pour répondre complètement.</p>}</div>}</details>}
 </section>}
 <section><h3>Invitations</h3>{rows.map(row=><p key={row.id}>{row.recipient_email} · {row.revoked_at?'Révoquée':'Expire le '+new Date(row.expires_at).toLocaleString('fr-FR')} <button type="button" className="secondary" disabled={busy||!!row.revoked_at} onClick={()=>{void revoke(row.id);}}>Révoquer l’accès</button></p>)}</section>
 </details>
 {link&&<section aria-label="Invitation créée"><h3>Invitation prête</h3><p>Le destinataire devra vérifier sa boîte email.</p><label>Lien d’invitation<input ref={invitationLink} readOnly value={link} onFocus={e=>e.target.select()}/></label></section>}
 </div><footer className="sharing-footer"><span className="sharing-footer-note"><Icon name="lock"/>Accès nominatif · expiration et révocation conservées</span><button className="secondary" type="button" onClick={onClose}>Annuler</button>
 {!link&&<button disabled={busy||preparing||!matches||!preview?.payload.items.length}>{busy?'En cours…':preparing?'Préparation du partage…':'Créer l’invitation'}</button>}
 </footer></form></Modal>;
}
export default function SharingControl({api,scope,name,label='Partager ce contexte',primary=false}:{api:QhApi;scope:string;name:string;label?:string;primary?:boolean}){
 const [open,setOpen]=useState(false);if(!sharingEnabled)return null;
 return <div className="sharing-entry"><button className={primary?'sharing-primary':'secondary'} onClick={()=>setOpen(true)}>{label}</button>{open&&<Editor key={scope} api={api} scope={scope} name={name} onClose={()=>setOpen(false)}/>}</div>;
}
