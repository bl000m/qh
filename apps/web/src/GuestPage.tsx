import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestSessionView,GuestCodeReceipt,RecipientAnswer} from '@qh/shared';
import {guestRequest,recipientAnswer,sessionView,sharingError} from './sharing';
import AnswerMarkdown from './AnswerMarkdown';
import qhLogo from './brand/qh-logo.png';

export default function GuestPage(){
 const [invitation]=useState(()=>new URLSearchParams(location.hash.slice(1)).get('invite')??'');
 const [email,setEmail]=useState(''),[code,setCode]=useState(''),[receipt,setReceipt]=useState<GuestCodeReceipt|null>(null);
 const [session,setSession]=useState<GuestSessionView|null>(null),[answer,setAnswer]=useState<RecipientAnswer|null>(null);
 const [question,setQuestion]=useState(''),[error,setError]=useState(''),[enabled,setEnabled]=useState(false);
 const [busy,setBusy]=useState(false),[ready,setReady]=useState(false);const epoch=useRef(0),lock=useRef(false);
 function clear(){epoch.current++;setSession(null);setAnswer(null);setEnabled(false);setCode('');}
 async function accept(value:unknown){const next=sessionView(value);setSession(next);setCode('');
  if(next.can_ask){const status=await guestRequest('/provider') as {enabled:boolean};setEnabled(status.enabled===true);}}
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
 async function requestCode(event:FormEvent){event.preventDefault();if(lock.current)return;lock.current=true;setBusy(true);setError('');
  try{setReceipt(await guestRequest('/code',{invitation_token:invitation,email}) as GuestCodeReceipt);setCode('');}
  catch(e){setError(sharingError(e));}finally{lock.current=false;setBusy(false);}}
 async function verify(event:FormEvent){event.preventDefault();if(!receipt||lock.current)return;lock.current=true;setBusy(true);setError('');
  try{await accept(await guestRequest('/verify',{invitation_token:invitation,challenge_id:receipt.challenge_id,code}));setReceipt(null);}
  catch{clear();setError('Vérification impossible. Vérifiez le code et la boîte invitée.');}finally{lock.current=false;setBusy(false);}}
 async function ask(event:FormEvent){event.preventDefault();if(!session||lock.current)return;lock.current=true;setBusy(true);setAnswer(null);setError('');const ticket=epoch.current;
  try{const value=recipientAnswer(await guestRequest('/ask',{question}));if(ticket===epoch.current)setAnswer(value);}
  catch(e){setError(sharingError(e));}finally{lock.current=false;setBusy(false);}}
 async function logout(){clear();setError('Accès fermé.');await guestRequest('/logout',{}).catch(()=>{});}
 return <div className="app-shell guest-shell"><header className="topbar"><a href="/" className="brand"><img src={qhLogo} width={100} alt="QH"/></a><span>Contexte partagé</span></header>
 <main id="main-content" className="guest-content"><h1>{session?.name??'Ouvrir un contexte partagé'}</h1>
 {!ready&&<p role="status">Vérification de l’accès…</p>}{error&&<p role="alert" className="notice error">{error}</p>}
 {ready&&!session&&!receipt&&invitation&&<form onSubmit={e=>{void requestCode(e);}}><label>Votre email<input type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} disabled={busy}/></label><button disabled={busy}>Recevoir mon code</button></form>}
 {!session&&receipt&&<form onSubmit={e=>{void verify(e);}}><p>{receipt.message}</p><label>Code reçu par email<input required inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={code} onChange={e=>setCode(e.target.value)} disabled={busy}/></label><button disabled={busy||code.length!==8}>Vérifier le code</button><button type="button" className="secondary" disabled={busy} onClick={()=>{setReceipt(null);setCode('');}}>Modifier l’email</button></form>}
 {session&&<><div className="actions"><p className="small muted">Accès jusqu’au {new Date(session.expires_at).toLocaleString('fr-FR')}</p><button className="secondary" onClick={()=>{void logout();}}>Fermer mon accès</button></div>
 <p>Posez vos questions sur les informations autorisées. Les sources et la structure interne restent privées.</p>
 {session.can_ask?<form onSubmit={e=>{void ask(e);}}><label>Votre question<textarea required maxLength={2000} value={question} disabled={busy} onChange={e=>setQuestion(e.target.value)}/></label><button disabled={busy||!question.trim()||!enabled}>{busy?'Réponse en cours…':'Envoyer'}</button>{!enabled&&<p>Les réponses sont temporairement indisponibles.</p>}</form>:<p>Demandez une nouvelle invitation pour pouvoir poser des questions.</p>}
 {answer&&<div role="status" className="guest-answer">{answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={answer.answer}/>{answer.insufficient_context&&<p>Les informations autorisées ne suffisent pas à répondre complètement.</p>}</div>}
 </>}
 </main></div>;
}
