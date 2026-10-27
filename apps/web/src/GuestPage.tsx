import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import type {GuestSessionView,SharedPayload,GuestCodeReceipt,GuestAnswer,GuestProviderStatus} from '@qh/shared';
import {guestRequest,guestAnswer,sessionView,sharedPayload,sharingError,providerStatus} from './sharing';
import {ApiError} from './transport';
import SharedRecap from './SharedRecap';
import qhLogo from './brand/qh-logo.png';

export default function GuestPage(){
 const [invitation]=useState(()=>new URLSearchParams(location.hash.slice(1)).get('invite')??'');
 const [email,setEmail]=useState(''),[code,setCode]=useState(''),[receipt,setReceipt]=useState<GuestCodeReceipt|null>(null);
 const [session,setSession]=useState<GuestSessionView|null>(null),[payload,setPayload]=useState<SharedPayload|null>(null);
 const [answer,setAnswer]=useState<GuestAnswer|null>(null),[question,setQuestion]=useState(''),[error,setError]=useState('');
 const [provider,setProvider]=useState<GuestProviderStatus|null>(null);
 const [busy,setBusy]=useState(false),[ready,setReady]=useState(false);const epoch=useRef(0);
 function clear(){epoch.current++;setSession(null);setPayload(null);setAnswer(null);setProvider(null);setCode('');}
 async function accept(value:unknown){const v=sessionView(value);const ticket=epoch.current;
   const p=v.rights.includes('READ')?sharedPayload(await guestRequest('/snapshots/'+v.snapshot_id)):null;
   const status=v.rights.includes('ASK_AI')?providerStatus(await guestRequest('/provider')):null;
   if(ticket===epoch.current){setSession(v);setPayload(p);setProvider(status);setCode('');}}
 useEffect(()=>{let active=true;if(invitation)history.replaceState(null,'','/guest');
   if(invitation){setReady(true);return()=>{active=false;};}
   void guestRequest('/session').then(v=>{if(active)return accept(v);}).catch(()=>{if(active)setError('Rouvrez votre invitation pour vérifier votre boîte email.');}).finally(()=>{if(active)setReady(true);});
   return()=>{active=false;epoch.current++;};},[]);
 useEffect(()=>{if(!session)return;let active=true;
   const timer=setInterval(()=>{void guestRequest('/session').then(v=>{if(active&&sessionView(v).snapshot_id!==session.snapshot_id){clear();setError('Cet accès a changé. Rouvrez votre invitation.');}else if(active&&session.rights.includes('ASK_AI')){const ticket=epoch.current;void guestRequest('/provider').then(s=>{if(active&&ticket===epoch.current)setProvider(providerStatus(s));}).catch(()=>{});}}).catch(()=>{if(active){clear();setError('Cet accès a expiré ou a été révoqué.');}});},3000);
   return()=>{active=false;clearInterval(timer);};},[session?.snapshot_id]);
 async function requestCode(event:FormEvent){event.preventDefault();setBusy(true);setError('');try{setReceipt(await guestRequest('/code',{invitation_token:invitation,email}) as GuestCodeReceipt);setCode('');}
   catch(e){setError(sharingError(e));}finally{setBusy(false);}}
 async function verify(event:FormEvent){event.preventDefault();if(!receipt)return;setBusy(true);setError('');try{
   await accept(await guestRequest('/verify',{invitation_token:invitation,challenge_id:receipt.challenge_id,code}));setReceipt(null);
 }catch{clear();setError('Vérification impossible. Vérifiez le code et la boîte invitée, ou demandez une nouvelle invitation.');}finally{setBusy(false);}}
 async function ask(event:FormEvent){event.preventDefault();if(!session)return;setBusy(true);setAnswer(null);setError('');const ticket=epoch.current;
   try{const v=guestAnswer(await guestRequest('/snapshots/'+session.snapshot_id+'/ask',{question}));if(ticket===epoch.current){setAnswer(v);if(v.budget)setProvider(v.budget);}}
   catch(e){if(e instanceof ApiError&&e.status===401)clear();setError(sharingError(e));if(session?.rights.includes('ASK_AI'))void guestRequest('/provider').then(s=>{if(ticket===epoch.current)setProvider(providerStatus(s));}).catch(()=>{});}finally{setBusy(false);}}
 async function logout(){clear();setError('Accès fermé.');await guestRequest('/logout',{}).catch(()=>{});}
 return <div className="app-shell guest-shell"><header className="topbar"><a href="/" className="brand"><img src={qhLogo} width={100} alt="QH"/></a><span>Contexte partagé</span></header>
 <main id="main-content" className="guest-content"><h1>Consulter un contexte partagé</h1><p>Un code vérifie le contrôle de la boîte email invitée, pas l’identité civile. Aucun compte QH requis.</p>
 {!ready&&<p role="status">Vérification de l’accès…</p>}{error&&<p role="alert" className="notice error">{error}</p>}
 {ready&&!session&&invitation&&!receipt&&<form onSubmit={e=>{void requestCode(e);}}><label>Votre email<input type="email" required autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)} disabled={busy}/></label><button disabled={busy}>Recevoir mon code</button></form>}
 {!session&&receipt&&<form onSubmit={e=>{void verify(e);}}><p>{receipt.message}</p><label>Code reçu par email<input required inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={code} onChange={e=>setCode(e.target.value)} disabled={busy}/></label><button disabled={busy||code.length!==8}>Vérifier le code</button><button type="button" className="secondary" disabled={busy} onClick={()=>{setReceipt(null);setCode('');}}>Modifier l’email</button><small>Après un envoi, attendez une minute avant d’en demander un autre. Trois envois maximum par invitation.</small></form>}
 {session&&<><div className="actions"><p>Boîte email vérifiée · Accès temporaire jusqu’au {new Date(session.expires_at).toLocaleString('fr-FR')}</p><button className="secondary" onClick={()=>{void logout();}}>Fermer mon accès</button></div>
 <section aria-label="Compréhension"><h2>Compréhension</h2>
 {payload?<><SharedRecap recap={payload.recap}/>{!payload.recap&&<p>Aucun récapitulatif n’a été approuvé pour cette projection. Les informations autorisées restent disponibles ci-dessous.</p>}
 <details><summary>Informations autorisées</summary>{payload.items.map(item=><div key={item.reference}><p>{item.text}</p>{item.validation_state==='proposed'&&<small>Proposition non confirmée</small>}</div>)}</details></>:<p>La consultation directe n’est pas autorisée par cette invitation.</p>}
 <p className="small muted">Cette projection reste figée au périmètre approuvé.</p></section>
 {session.rights.includes('ASK_AI')&&<section aria-label="Question sur le snapshot"><h2>Poser une question</h2><p className="notice">{provider?.simulated?'Simulation locale uniquement — aucun appel IA réel ni facturation.':provider?.model==='mistral-small-2603'?(provider.enabled?'Mistral Small · mistral-small-2603 · réponses réelles.':'Mistral Small · indisponible. Aucun appel automatique.'): 'Vérification du provider…'} Seul le snapshot autorisé et votre question sont transmis.{provider?.remaining_usd!=null&&<span> Budget développement commun restant : {provider.remaining_usd} USD · plafond global autorisé 10 €, historique inclus. Réservation automatique avant chaque appel.</span>}{provider?.plafond_reached&&<span> Plafond IA atteint. Aucune nouvelle requête ne sera facturée.</span>}</p>
 <form onSubmit={e=>{void ask(e);}}><label>Votre question sur le snapshot<textarea required maxLength={2000} value={question} disabled={busy} onChange={e=>setQuestion(e.target.value)}/></label><button disabled={busy||!question.trim()||!provider?.enabled}>Interroger le snapshot</button></form>
 {answer&&<div role="status" className="guest-answer"><strong>{answer.simulated?'Simulation locale':'Réponse de Mistral Small'}</strong><p>{answer.answer}</p>{answer.insufficient_context&&<p>Informations incomplètes : cette réponse peut nécessiter des précisions.</p>}<small>Références du snapshot : {answer.reference_aliases.join(', ')||'aucune'}. {answer.simulated?'Cette simulation ne juge pas le sens de votre question.':'Les références ne certifient pas la vérité de la réponse.'} Les propositions restent à vérifier. {answer.accounting&&<>Coût comptabilisé : {answer.accounting.cost_usd} USD · tentative {answer.accounting.attempt}.</>}</small></div>}</section>}
 </>}
 </main></div>;
}
