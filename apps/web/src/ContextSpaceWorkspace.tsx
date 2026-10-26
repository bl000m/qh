import {useCallback,useEffect,useRef,useState} from 'react';
import type {QhApi} from './api';
import {ApiError,apiMessage} from './api';
import type {ContextIntake,WorkspaceState} from '../../../packages/shared/src/context-space';
import type {CanonicalRevision} from './understanding';
import {recognizedCitations} from './understanding';
import {DIMENSIONS,primaryAssignment} from './uum';
import type {DialogueMessage} from './chat';
import type {SessionCapabilities} from './provider-session';
import AnswerMarkdown from './AnswerMarkdown';
import WorkspaceAnswerSources from './WorkspaceAnswerSources';
import AIDiagnostics from './AIDiagnostics';
import useDraft from './useDraft';

type State=WorkspaceState & {understanding:CanonicalRevision[]};
const labels={empty:'Aucun contexte mémorisé',pending:'Nouveaux apports en attente',running:'Mémorisation en cours',current:'Compréhension à jour',failed:'Échec de mémorisation'};
function intake(kind:ContextIntake['kind'],text:string|null,name:string|null=null):ContextIntake {
 return {id:crypto.randomUUID(),kind,role:'user',text,name,context:null};
}
function dialogue(items:ContextIntake[]):DialogueMessage[] {
 const messages:DialogueMessage[]=[];
 for(const item of items.filter(i=>i.kind==='message')){
  const content=item.text!;
  if(messages.at(-1)?.role===item.role)messages[messages.length-1].content+='\n\n'+content;
  else if(messages.length||item.role==='user')messages.push({role:item.role,content});
 }
 return messages;
}
function failure(error:unknown){return error instanceof ApiError&&error.status===402?'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.':error instanceof ApiError&&error.status===422?'L’analyse ou ses citations ne permettent pas une compréhension valide. Les apports restent disponibles.':error instanceof ApiError&&error.status===503?'Le résultat n’est pas confirmé. Actualisez l’état avant de réessayer ; les apports déjà enregistrés sont conservés.':apiMessage(error);}

export default function ContextSpaceWorkspace({api,scope}:{api:QhApi;scope:string}) {
 const [state,setState]=useState<State|null>(null),[caps,setCaps]=useState<SessionCapabilities|null>(null);
 const [open,setOpen]=useState(false),[expanded,setExpanded]=useState(false),[settings,setSettings]=useState(false);
 const [error,setError]=useState(''),[busy,setBusy]=useState<'send'|'memory'|'file'|null>(null);
 const [draft,setDraft]=useDraft('message');
 const [notice,setNotice]=useState('');
 const panel=useRef<HTMLElement>(null);
 const appendAttempt=useRef<ContextIntake|null>(null),lock=useRef(false);
 const documentInput=useRef<HTMLInputElement>(null),contextInput=useRef<HTMLInputElement>(null),log=useRef<HTMLDivElement>(null);
 const reload=useCallback(async()=>{const value=await api.workspace(scope);setState(value);return value;},[api,scope]);
 useEffect(()=>{let active=true;setState(null);setError('');api.workspace(scope).then(s=>{if(active)setState(s);}).catch(e=>{if(active)setError(failure(e));});api.chatCapabilities(scope).then(c=>{if(active)setCaps(c);}).catch(()=>{});return()=>{active=false;};},[api,scope]);
 useEffect(()=>{if(open)panel.current?.focus();},[open]);
 useEffect(()=>{log.current?.scrollTo({top:log.current.scrollHeight});},[state?.intake.length,busy]);
 function accept(next:WorkspaceState){setState(previous=>({...next,understanding:previous?.understanding??[]}));}
 async function saveDraft(){
  if(!draft.trim())return state;
  if(!appendAttempt.current||appendAttempt.current.text!==draft)appendAttempt.current=intake('message',draft);
  const next=await api.addIntake(scope,appendAttempt.current);accept(next);appendAttempt.current=null;setDraft('');
  return {...next,understanding:state?.understanding??[]};
 }
 async function send(){
  if(lock.current||!draft.trim()||!state)return;
  lock.current=true;setBusy('send');setError('');setNotice('');
  try{
   const next=await saveDraft();
   if(!next)return;
   const answer=await api.workspaceChat(scope,dialogue(next.intake));
   await reload();
   if(answer.insufficient_context||answer.partial_coverage)setNotice('Les informations disponibles ne permettent pas une réponse complète.');
  }catch(e){setError(failure(e));}finally{lock.current=false;setBusy(null);}
 }
 async function memorize(){
  if(lock.current||!state)return;
  lock.current=true;setBusy('memory');setError('');setNotice('');
  try{
   await saveDraft();
   const saved=await api.consolidate(scope);accept(saved);setState(previous=>previous?{...previous,understanding:[]}:previous);setOpen(true);
   // Projection is asynchronous. These reads never generate or retry paid work.
   let synchronized=false;
   for(let attempt=0;attempt<16;attempt++){
    try{await reload();synchronized=true;break;}
    catch(e){if(!(e instanceof ApiError)||e.status!==503)throw e;await new Promise(resolve=>setTimeout(resolve,500));}
   }
   if(!synchronized)setNotice('Version enregistrée. La compréhension sera disponible après synchronisation. Actualisez son état.');
   else setNotice('Compréhension enregistrée.');
  }catch(e){setError(failure(e));}finally{lock.current=false;setBusy(null);}
 }
 async function addFile(file:File|undefined,context:boolean){
  if(!file||lock.current)return;
  if(file.size>500000){setError('Ce fichier dépasse la limite de 500 Ko.');return;}
  if(!context&&!/\.(txt|md|markdown)$/i.test(file.name)){setError('L’extraction PDF n’est pas encore disponible. Utilisez un fichier TXT ou Markdown ; aucun document n’a été ajouté.');return;}
  lock.current=true;setBusy('file');setError('');setNotice('');
  try{
   const text=await file.text();
   const input=intake(context?'context':'document',context?null:text,file.name);
   if(context)input.context=JSON.parse(text);
   accept(await api.addIntake(scope,input));
   setNotice(context?'Contexte importé, en attente de mémorisation.':'Document ajouté, en attente de mémorisation.');
  }catch(e){setError(e instanceof SyntaxError?'Le fichier ne contient pas un contexte JSON valide.':failure(e));}finally{lock.current=false;setBusy(null);}
 }
 async function download(){
  setError('');
  try{
   const data=await api.exportContext(scope),url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
   const anchor=document.createElement('a');anchor.href=url;anchor.download='qh-context-v'+data.version+'.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError(failure(e));}
 }
 useEffect(()=>{
  if(state?.state!=='running')return;
  const timer=setTimeout(()=>{void reload().catch(e=>setError(failure(e)));},1500);
  return()=>clearTimeout(timer);
 },[state,reload]);
 const disabled=!!busy||state?.state==='running';
 const consumed=new Set(state?.current?.intake_ids??[]);
 return <section className="context-space-v02" aria-label="Context Space">
  <div className="context-space-tools"><strong>Discussion</strong><div className="actions">
   <button type="button" className="secondary" aria-expanded={open} aria-controls="context-understanding" onClick={()=>setOpen(v=>!v)}>Compréhension</button>
   <label className="compact-model"><span className="sr-only">Modèle</span><select value="mistral-small-2603" onChange={()=>{}}><option value="mistral-small-2603">Mistral Small{caps?.enabled?'':' · indisponible'}</option></select></label>
   <button type="button" className="secondary" aria-expanded={settings} onClick={()=>setSettings(v=>!v)}>Données envoyées</button>
  </div></div>
  {settings&&<div className="workspace-disclosure"><p>Envoyer transmet cette discussion et la compréhension consolidée à Mistral Small. Mémoriser transmet les apports de ce Space, y compris les documents et contextes importés. Les interprétations restent non confirmées par un humain. {caps?.automatic&&<>Budget commun restant : {caps.remaining_usd} USD.</>}</p>{caps?.automatic&&<AIDiagnostics api={api} scope={scope}/>}</div>}
  <div className={'context-space-workspace'+(open?' with-understanding':'')+(expanded&&open?' understanding-expanded':'')}>
   <section className="workspace-discussion" aria-label="Discussion">
    <div className="workspace-log" ref={log} role="log" aria-label="Discussion du Context Space" aria-live="polite" aria-busy={!!busy} tabIndex={0}>
     {!state&&!error&&<p role="status">Chargement du contexte…</p>}
     {state&&!state.intake.length&&<div className="workspace-welcome"><h2>Qu’aimeriez-vous garder en contexte ?</h2><p>Écrivez vos informations ou ajoutez un document. Discutez, puis choisissez Mémoriser pour construire votre compréhension.</p></div>}
     {state?.intake.map(item=><article key={item.id} className={'workspace-message '+(item.role==='assistant'?'assistant':'user')}>
      {item.kind==='message'?<><span className="sr-only">{item.role==='assistant'?'QH':'Vous'}</span>{item.role==='assistant'?<><AnswerMarkdown text={item.text!}/>{item.attribution&&<WorkspaceAnswerSources api={api} scope={scope} attribution={item.attribution}/>}</>:<p>{item.text}</p>}</>:<p>{item.kind==='context'?'Contexte importé':'Document'} : {item.name}</p>}
      {item.role!=='assistant'&&!consumed.has(item.id)&&<span className="small muted">En attente de mémorisation</span>}
     </article>)}
     {busy==='send'&&<p role="status">Préparation de la réponse…</p>}
    </div>
    <div className="workspace-feedback">{error&&<p role="alert" className="notice error">{error}</p>}{notice&&<p role="status">{notice}</p>}{error&&<button type="button" className="secondary" disabled={!!busy} onClick={()=>{void reload().then(()=>setError('')).catch(e=>setError(failure(e)));}}>Actualiser l’état</button>}</div>
    <form className="workspace-composer" onSubmit={event=>{event.preventDefault();void send();}}>
     <label className="sr-only" htmlFor="context-message">Votre message</label><textarea id="context-message" rows={3} value={draft} onChange={event=>setDraft(event.target.value)} disabled={disabled||!state} placeholder="Ajoutez une information ou posez une question…"/>
     <div className="workspace-composer-actions"><div className="actions"><button type="button" className="secondary" disabled={disabled||!state} onClick={()=>documentInput.current?.click()}>Joindre un document</button><button type="button" className="secondary" disabled={disabled||!state} onClick={()=>contextInput.current?.click()}>Importer un contexte</button></div><div className="actions"><button type="submit" className="secondary" disabled={disabled||!state||!draft.trim()||!caps?.enabled}>Envoyer</button><button type="button" disabled={disabled||!state||(!state.pending_count&&!draft.trim())||!caps?.enabled} onClick={()=>{void memorize();}}>{busy==='memory'?'Mémorisation…':'Mémoriser'}</button></div></div>
     <p className="small muted">Envoyer utilise la compréhension consolidée de ce Space, y compris ses interprétations non confirmées.</p>
     <p className="small muted" role="status">{busy==='memory'?'Mémorisation en cours':state?labels[state.state]:'État indisponible'}{state&&state.pending_count>0?` · ${state.pending_count} apports en attente`:''}</p>
     <input ref={documentInput} type="file" accept=".txt,.md,.markdown,.pdf" hidden onChange={event=>{void addFile(event.target.files?.[0],false);event.target.value='';}}/>
     <input ref={contextInput} type="file" accept=".json,application/json" hidden onChange={event=>{void addFile(event.target.files?.[0],true);event.target.value='';}}/>
    </form>
   </section>
   {open&&<aside id="context-understanding" ref={panel} tabIndex={-1} className="context-understanding" aria-label="Compréhension">
    <header><h2>Compréhension</h2><div className="actions"><button type="button" className="secondary" aria-pressed={expanded} onClick={()=>setExpanded(v=>!v)}>{expanded?'Réduire':'Agrandir'}</button><button type="button" className="secondary" onClick={()=>setOpen(false)}>Fermer</button></div></header>
    {state?.current?<><p className="small muted">Version {state.current.version} · {new Date(state.current.created_at).toLocaleString('fr-FR')}</p><button type="button" className="secondary" onClick={()=>{void download();}}>Exporter</button><p className="small muted">Pour corriger cette compréhension, ajoutez un message puis mémorisez.</p></>:<p>Aucun contexte mémorisé.</p>}
    {[...DIMENSIONS,['unclassified','Autres informations'] as const].map(([id,label])=>{
     const rows=state?.understanding.filter(item=>(primaryAssignment(item)?.value??'unclassified')===id)??[];
     return rows.length>0&&<section key={id}><h3>{label}</h3>{rows.map(item=><div className="understanding-statement" key={item.revision_id}><p>{String(item.content.text??'')}</p><details><summary>Provenance</summary><p className="small">Interprétation de QH · non confirmée par un humain</p>{recognizedCitations(item).map((citation,index)=><blockquote key={index}>{citation.quote}</blockquote>)}</details></div>)}</section>;
    })}
   </aside>}
  </div>
 </section>;
}
