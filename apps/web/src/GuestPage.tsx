import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestSessionView,GuestCodeReceipt,RecipientAnswer,RecipientMessage,RecipientQuestion} from '@qh/shared';
import {guestRequest,recipientAnswer,sessionView,sharingError,guestChatError} from './sharing';
import AnswerMarkdown from './AnswerMarkdown';
import qhLogo from './brand/qh-logo.png';

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
 const [question,setQuestion]=useState(''),[error,setError]=useState(''),[enabled,setEnabled]=useState(false);
 const [busy,setBusy]=useState(false),[ready,setReady]=useState(false);const epoch=useRef(0),lock=useRef(false),bottom=useRef<HTMLDivElement>(null);
 function clear(){epoch.current++;setSession(null);setTurns([]);setQuestion('');setEnabled(false);setCode('');}
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
 useEffect(()=>{const log=bottom.current?.parentElement;if(log)log.scrollTop=log.scrollHeight;},[turns,busy]);
 async function askQuestion(text:string,retry?:number){
  if(!session||!enabled||!text.trim()||lock.current)return;
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
 return <div className="app-shell guest-shell"><header className="topbar"><a href="/" className="brand"><img src={qhLogo} width={100} alt="QH"/></a><span>Contexte partagé</span></header>
 <main id="main-content" className="guest-content"><h1>{session?.name??'Ouvrir un contexte partagé'}</h1>
 {!ready&&<p role="status">Vérification de l’accès…</p>}{error&&<p role="alert" className="notice error">{error}</p>}
 {ready&&!session&&!receipt&&invitation&&<form onSubmit={e=>{void requestCode(e);}}><label>Votre email<input type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} disabled={busy}/></label><button disabled={busy}>Recevoir mon code</button></form>}
 {!session&&receipt&&<form onSubmit={e=>{void verify(e);}}><p>{receipt.message}</p><label>Code reçu par email<input required inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={code} onChange={e=>setCode(e.target.value)} disabled={busy}/></label><button disabled={busy||code.length!==8}>Vérifier le code</button><button type="button" className="secondary" disabled={busy} onClick={()=>{setReceipt(null);setCode('');}}>Modifier l’email</button></form>}
 {session&&<><div className="actions"><p className="small muted">Accès jusqu’au {new Date(session.expires_at).toLocaleString('fr-FR')}</p><button className="secondary" onClick={()=>{void logout();}}>Fermer mon accès</button></div>
 <p>Posez vos questions sur les informations autorisées. Les sources et la structure interne restent privées.</p>
 <section className="guest-conversation" aria-label="Conversation">
 <div className="guest-messages" role="log" aria-label="Messages" aria-live="polite" aria-busy={busy}>
 {turns.map((turn,index)=><div className="guest-turn" key={index}>
  <div className="guest-question"><span className="small muted">Vous</span><p>{turn.question}</p></div>
  {turn.answer&&<div className="guest-answer"><span className="small muted">QH</span>{turn.answer.simulated&&<p>Démonstration locale, sans réponse IA réelle.</p>}<AnswerMarkdown text={turn.answer.answer}/></div>}
  {turn.failed&&<div role="alert" className="notice error">{turn.failed} <button className="secondary" disabled={busy||!enabled} onClick={()=>{void askQuestion(turn.question,index);}}>Réessayer</button></div>}
 </div>)}
 {busy&&<p role="status">Réponse en cours…</p>}<div ref={bottom}/>
 </div>
 {session.can_ask?<form className="guest-composer" onSubmit={ask}><label htmlFor="guest-question">Votre question</label><textarea id="guest-question" required maxLength={2000} value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();if(!busy)void askQuestion(question);}}}/><button disabled={busy||!question.trim()||!enabled}>Envoyer</button>{!enabled&&<p>Les réponses sont temporairement indisponibles.</p>}</form>:<p>Demandez une nouvelle invitation pour pouvoir poser des questions.</p>}
 </section>
 </>}
 </main></div>;
}
