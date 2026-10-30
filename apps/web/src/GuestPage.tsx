import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestSessionView,GuestCodeReceipt,RecipientAnswer,RecipientMessage,RecipientQuestion} from '@qh/shared';
import {guestRequest,recipientAnswer,sessionView,sharingError,guestChatError} from './sharing';
import AnswerMarkdown from './AnswerMarkdown';
import qhLogo from './brand/qh-logo.png';
import SharedRecap from './SharedRecap';
import {isOriginalRequest} from './DocumentDownload';
import {DocumentFileCard} from './DocumentCards';
import './sharing.css';
import {GuestDocuments} from './SharingDocuments';
import {Icon} from './Ui';

interface Turn {question:string;answer?:RecipientAnswer;failed?:string}

function recentHistory(turns:Turn[]):RecipientMessage[]{
 const history:RecipientMessage[]=[];let size=0;
 for(const turn of turns.slice().reverse()){
  if(!turn.answer)continue;
  const pair:RecipientMessage[]=[{role:'user',content:turn.question},{role:'assistant',content:turn.answer.answer.slice(0,6000)}];
  const length=pair.reduce((sum,m)=>sum+m.content.length,0);
  if(history.length+2>12||size+length>16000)break;
  history.unshift(...pair);size+=length;
 }
 return history;
}

export default function GuestPage(){
 const [invitation]=useState(()=>new URLSearchParams(location.hash.slice(1)).get('invite')??'');
 const [email,setEmail]=useState(''),[code,setCode]=useState(''),[receipt,setReceipt]=useState<GuestCodeReceipt|null>(null);
 const [session,setSession]=useState<GuestSessionView|null>(null),[turns,setTurns]=useState<Turn[]>([]);
 const [documents,setDocuments]=useState<import('../../../packages/shared/src/context-space').SourceDocument[]>([]);
 useEffect(()=>{let active=true;setDocuments([]);if(session)void guestRequest('/documents').then(v=>{if(active)setDocuments(v as import('../../../packages/shared/src/context-space').SourceDocument[]);}).catch(()=>{});return()=>{active=false;};},[session?.expires_at]);
 const [question,setQuestion]=useState(''),[error,setError]=useState(''),[enabled,setEnabled]=useState(false);
 const [resendAfter,setResendAfter]=useState(0);
 const resendDeadline=useRef(0);
 const codeInput=useRef<HTMLInputElement>(null);
 const [busy,setBusy]=useState(false),[ready,setReady]=useState(false);const epoch=useRef(0),lock=useRef(false),bottom=useRef<HTMLDivElement>(null);
 function clear(){epoch.current++;setSession(null);setDocuments([]);setTurns([]);setQuestion('');setEnabled(false);setCode('');}
 async function accept(value:unknown){const next=sessionView(value);setSession(next);setCode('');
  setEnabled(false);if(next.can_ask){try{const status=await guestRequest('/provider') as {enabled:boolean};setEnabled(status.enabled===true);}catch{setEnabled(false);}}}
 useEffect(()=>{let active=true;if(invitation)history.replaceState(null,'','/guest');
  if(invitation){setReady(true);return()=>{active=false;};}
  void guestRequest('/session').then(v=>{if(active)return accept(v);}).catch(()=>{if(active)setError('Rouvrez votre invitation pour vérifier votre boîte email.');}).finally(()=>{if(active)setReady(true);});
  return()=>{active=false;epoch.current++;};},[]);
 useEffect(()=>{if(!session)return;let active=true;
  const timer=setInterval(()=>{void guestRequest('/session').then(value=>{
   if(!active)return;const next=sessionView(value);
   if(next.name!==session.name||next.expires_at!==session.expires_at){clear();setError('Cet accès a changé. Rouvrez votre invitation.');return;}
   if(next.can_ask)void guestRequest('/provider').then(v=>{if(active)setEnabled((v as {enabled:boolean}).enabled===true);}).catch(()=>{if(active)setEnabled(false);});
  }).catch(()=>{if(active){clear();setError('Cet accès a expiré ou a été révoqué.');}});},3000);
  return()=>{active=false;clearInterval(timer);};},[session?.expires_at]);
 useEffect(()=>{if(receipt)codeInput.current?.focus();},[receipt]);
 useEffect(()=>{if(resendAfter<=0)return;const timer=setTimeout(()=>setResendAfter(Math.max(0,Math.ceil((resendDeadline.current-Date.now())/1000))),1000);return()=>clearTimeout(timer);},[resendAfter]);
 async function requestCode(event?:FormEvent){event?.preventDefault();if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{setReceipt(await guestRequest('/code',{invitation_token:invitation,email}) as GuestCodeReceipt);setCode('');resendDeadline.current=Date.now()+60000;setResendAfter(60);}
  catch(e){setError(sharingError(e));}finally{lock.current=false;setBusy(false);}}
 async function verify(event:FormEvent){event.preventDefault();if(!receipt||lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await accept(await guestRequest('/verify',{invitation_token:invitation,challenge_id:receipt.challenge_id,code}));setReceipt(null);}
  catch{clear();setError('Vérification impossible. Vérifiez le code et la boîte invitée.');}finally{lock.current=false;setBusy(false);}}
 useEffect(()=>{const log=bottom.current?.parentElement;if(log)log.scrollTop=log.scrollHeight;},[turns,busy]);
 async function askQuestion(text:string,retry?:number){
  if(!session||(!enabled&&!isOriginalRequest(text))||!text.trim()||lock.current)return;
  lock.current=true;setBusy(true);setError('');const ticket=epoch.current;
  const index=retry??turns.length;
  const body:RecipientQuestion={question:text,history:recentHistory(turns.slice(0,index))};
  setTurns(previous=>retry===undefined?[...previous,{question:text}]:previous.map((turn,i)=>i===index?{question:text}:turn));
  if(retry===undefined)setQuestion('');
  try{const answer=recipientAnswer(await guestRequest('/ask',body));
   if(ticket===epoch.current)setTurns(previous=>previous.map((turn,i)=>i===index?{...turn,answer}:turn));}
  catch(e){if(ticket===epoch.current)setTurns(previous=>previous.map((turn,i)=>i===index?{...turn,failed:guestChatError(e)}:turn));}
  finally{lock.current=false;setBusy(false);}
 }
 function ask(event:FormEvent){event.preventDefault();void askQuestion(question);}
 async function logout(){clear();setError('Accès fermé.');await guestRequest('/logout',{}).catch(()=>{});}
 return <div className={'app-shell guest-shell'+(session?' guest-chat-shell':' guest-access-shell')}>
 <header className="topbar"><a href="/" className="brand"><img src={qhLogo} width={100} alt="QH"/></a>
 {session&&<span className="guest-breadcrumb">Contexte partagé <span aria-hidden="true">/</span> {session.name}</span>}
 <span className="guest-header-label">Contexte partagé</span>{session&&<button className="secondary" onClick={()=>{void logout();}}>Fermer mon accès</button>}</header>
 <main id="main-content" className="guest-content">
 {!session?<div className="guest-access-layout"><section className="guest-access-intro"><h1>Ouvrir un contexte partagé</h1><p>Accédez aux informations autorisées de ce contexte partagé en toute sécurité.</p>
 <div className="guest-access-art" aria-hidden="true"><div><span className="guest-red-orb"/><i/><i/></div><div><span className="guest-person">●</span><i/><i/></div></div></section>
 <section className="guest-access-card" aria-labelledby="guest-access-title"><span className="guest-chat-symbol" aria-hidden="true">•••</span><h2 id="guest-access-title">Accès sécurisé à un contexte partagé</h2>
 <p className="muted">Entrez votre email pour recevoir un code d’accès. Vous pourrez ensuite consulter les informations autorisées de ce contexte partagé.</p>
 {!ready&&<p role="status">Vérification de l’accès…</p>}{error&&<p role="alert" className="notice error">{error}</p>}
 {ready&&invitation&&<form onSubmit={e=>{void (receipt?verify(e):requestCode(e));}}>
 <label>Votre email<input type="email" required autoComplete="email" placeholder="votre@email.com" value={email} onChange={e=>setEmail(e.target.value)} disabled={busy} readOnly={!!receipt}/></label>
 {receipt&&<div className="guest-code-panel"><div className="guest-code-heading"><label htmlFor="guest-code">Insérez ici le code reçu par mail</label><button type="button" className="guest-text-button" disabled={busy} onClick={()=>{setReceipt(null);setCode('');setError('');}}>Modifier l’email</button></div>
 <p className="small muted" role="status">{receipt.message}</p>
 <input ref={codeInput} id="guest-code" className="guest-code-input" aria-describedby="guest-code-help" required pattern="[0-9]{8}" inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={code} onChange={e=>setCode(e.target.value.replace(/[^0-9]/g,''))} disabled={busy}/>
 <p id="guest-code-help" className="small muted">Code de sécurité à 8 chiffres.</p><button type="button" className="guest-text-button" disabled={busy||resendAfter>0} onClick={()=>{void requestCode();}}>Renvoyer le code{resendAfter>0?` (${resendAfter}s)`:''}</button></div>}
 <button disabled={busy||!!receipt&&code.length!==8}>{busy?'Vérification en cours…':receipt?'Accéder au contexte':'Recevoir mon code'}</button></form>}
 <p className="guest-access-privacy">Vous ne verrez que les informations spécifiquement autorisées par le propriétaire de ce contexte. Les sources et la structure interne restent privées.</p></section></div>
 :<><aside className="guest-context"><h1><span className="guest-context-icon"><Icon name="sources"/></span>{session.name}</h1><details open><summary>Résumé du contexte</summary><SharedRecap recap={session.recap??undefined}/>{!session.recap&&<p className="muted">Aucun résumé communicable pour cet accès.</p>}</details>
 {documents.length>0&&<GuestDocuments documents={documents}/>}
 <p className="guest-expiry">Accès jusqu’au {new Date(session.expires_at).toLocaleString('fr-FR')}</p></aside>
 <section className="guest-conversation" aria-label="Conversation">
 {error&&<p role="alert" className="notice error">{error}</p>}
 <div className="guest-messages" role="log" aria-label="Messages" aria-live="polite" aria-busy={busy}>
 {!turns.length&&<div className="guest-conversation-empty"><span className="guest-chat-symbol" aria-hidden="true">•••</span><h2>Explorez ce contexte</h2><p>Posez votre première question sur les informations partagées.</p></div>}
 {turns.map((turn,index)=><div className="guest-turn" key={index}>
  <div className="guest-question"><span className="small muted">Vous</span><p>{turn.question}</p></div>
  {turn.answer&&<div className="guest-answer"><span className="small muted">QH</span>{turn.answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={turn.answer.answer}/>{turn.answer.documents?.map(doc=><DocumentFileCard key={doc.source_revision_id} document={doc}/>)}</div>}
  {turn.failed&&<div role="alert" className="notice error">{turn.failed} <button className="secondary" disabled={busy||!enabled} onClick={()=>{void askQuestion(turn.question,index);}}>Réessayer</button></div>}
 </div>)}
 {busy&&<p role="status">Réponse en cours…</p>}<div ref={bottom}/>
 </div>
 {<form className="guest-composer" onSubmit={ask}><label className="sr-only" htmlFor="guest-question">Votre question</label><textarea id="guest-question" placeholder="Posez votre question sur ce contexte…" required maxLength={2000} value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();if(!busy)void askQuestion(question);}}}/>
 <div className="guest-composer-actions"><button type="button" className="secondary" disabled aria-describedby="guest-proposals-help">Proposer une mise à jour</button><button disabled={busy||!question.trim()||(!enabled&&!isOriginalRequest(question))}>Envoyer</button></div>
 <p id="guest-proposals-help" className="small muted">Les contributions externes sont indisponibles dans cette démo : leur réception et leur validation par le propriétaire ne sont pas encore implémentées.</p>
 {!enabled&&<p>Les réponses sont temporairement indisponibles.</p>}</form>}
 </section></>}
 </main></div>;
}
