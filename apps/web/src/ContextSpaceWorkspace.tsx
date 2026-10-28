import {useCallback,useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {Modal} from './SpaceActions';
import type {QhApi} from './api';
import {ApiError,apiMessage} from './api';
import type {ContextIntake,WorkspaceState} from '../../../packages/shared/src/context-space';
import type {CanonicalRevision} from './understanding';
import {recognizedCitations} from './understanding';
import type {SessionCapabilities} from './provider-session';
import AnswerMarkdown from './AnswerMarkdown';
import WorkspaceAnswerSources from './WorkspaceAnswerSources';
import AIDiagnostics from './AIDiagnostics';
import useDraft from './useDraft';
import Loading from './Loading';

type State=WorkspaceState & {understanding:CanonicalRevision[]};
function intake(kind:ContextIntake['kind'],text:string|null,name:string|null=null):ContextIntake {
 return {id:crypto.randomUUID(),kind,role:'user',text,name,context:null};
}
function failure(error:unknown){return error instanceof ApiError&&error.status===402?'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.':error instanceof ApiError&&error.status===422?'L’analyse ou ses citations ne permettent pas une compréhension valide. Les apports restent disponibles.':error instanceof ApiError&&error.status===503?'Le résultat n’est pas confirmé. Actualise l’état avant de réessayer ; les apports déjà enregistrés sont conservés.':apiMessage(error);}

export default function ContextSpaceWorkspace({api,scope,heading,settingsContent,sharingContent,settingsRequest=0,name}:{api:QhApi;name?:string;scope:string;heading?:ReactNode;settingsContent?:ReactNode;sharingContent?:ReactNode;settingsRequest?:number}) {
 const [state,setState]=useState<State|null>(null),[caps,setCaps]=useState<SessionCapabilities|null>(null);
 const [loadStatus,setLoadStatus]=useState<'loading'|'empty'|'ready'|'error'>('loading');
 const initialRead=useRef<{api:QhApi;scope:string;promise:Promise<State>}|null>(null);
 const [open,setOpen]=useState(false),[settings,setSettings]=useState(false);
 const [sourcesVisited,setSourcesVisited]=useState(false);
 const [sourceError,setSourceError]=useState(''),[loadingSources,setLoadingSources]=useState(false);
 const latestVersion=useRef(0);
 const [narrow,setNarrow]=useState(()=>window.matchMedia('(max-width:850px)').matches);
 const [error,setError]=useState(''),[busy,setBusy]=useState<'send'|'memory'|'regenerate'|'file'|null>(null);
 const [draft,setDraft]=useDraft('message');
 const [notice,setNotice]=useState('');
 const [questionStates,setQuestionStates]=useState<Record<string,'sending'|'uncertain'|'failed'>>({});
 const [sendingQuestion,setSendingQuestion]=useState<string|null>(null);
 const sendOperations=useRef<Record<string,string>>({}),regenerationAttempt=useRef<string|null>(null);
 const [availabilityError,setAvailabilityError]=useState(''),[checkingAvailability,setCheckingAvailability]=useState(false);
 const availabilityGeneration=useRef(0);
 const availabilityRead=useRef<{api:QhApi;scope:string;promise:Promise<SessionCapabilities>}|null>(null);
 const panel=useRef<HTMLElement>(null);
 const appendAttempt=useRef<ContextIntake|null>(null),lock=useRef(false);
 const documentInput=useRef<HTMLInputElement>(null),contextInput=useRef<HTMLInputElement>(null),log=useRef<HTMLDivElement>(null);
 const reload=useCallback(async(expectedVersion?:string)=>{const value=await api.workspace(scope,true);if(expectedVersion&&value.current?.id!==expectedVersion||(value.current?.version??0)<latestVersion.current)throw new ApiError(503);latestVersion.current=value.current?.version??0;setState(value);setLoadStatus(value.current?'ready':'empty');return value;},[api,scope]);
 useEffect(()=>{
  let active=true;
  setState(null);latestVersion.current=0;setLoadStatus('loading');setError('');setQuestionStates({});sendOperations.current={};regenerationAttempt.current=null;
  // Reuse only an in-flight mount read (including React StrictMode's replay).
  if(initialRead.current?.api!==api||initialRead.current.scope!==scope)initialRead.current={api,scope,promise:api.workspace(scope)};
  const request=initialRead.current;
  request.promise.then(value=>{if(active){latestVersion.current=value.current?.version??0;setState(value);setLoadStatus(value.current?'ready':'empty');}})
   .catch(e=>{if(active){setLoadStatus('error');setError(failure(e));}})
   .finally(()=>{if(initialRead.current===request)initialRead.current=null;});
  return()=>{active=false;};
 },[api,scope]);
 const refreshAvailability=useCallback(async()=>{
  const generation=++availabilityGeneration.current;
  setCheckingAvailability(true);setAvailabilityError('');
  if(availabilityRead.current?.api!==api||availabilityRead.current.scope!==scope)availabilityRead.current={api,scope,promise:api.chatCapabilities(scope)};
  const request=availabilityRead.current;
  try{const value=await request.promise;if(generation===availabilityGeneration.current)setCaps(value);}
  catch(e){if(generation===availabilityGeneration.current){setCaps(null);setAvailabilityError(apiMessage(e));}}
  finally{if(availabilityRead.current===request)availabilityRead.current=null;if(generation===availabilityGeneration.current)setCheckingAvailability(false);}
 },[api,scope]);
 useEffect(()=>{
  void refreshAvailability();
  const refresh=()=>{if(document.visibilityState==='visible')void refreshAvailability();};
  window.addEventListener('focus',refresh);document.addEventListener('visibilitychange',refresh);
  return()=>{availabilityGeneration.current++;window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',refresh);};
 },[refreshAvailability]);
 useEffect(()=>{if(open)panel.current?.focus();},[open,narrow]);
 useEffect(()=>{if(settingsRequest)setSettings(true);},[settingsRequest]);
 useEffect(()=>{const media=window.matchMedia('(max-width:850px)');const update=()=>setNarrow(media.matches);media.addEventListener('change',update);return()=>media.removeEventListener('change',update);},[]);
 useEffect(()=>{log.current?.scrollTo({top:log.current.scrollHeight});},[state?.intake.length,busy]);
 function accept(next:WorkspaceState){latestVersion.current=next.current?.version??0;setState(previous=>({...next,understanding:next.current?.id===previous?.current?.id?previous?.understanding??[]:[],recap:next.recap??(next.current?.id===previous?.current?.id?previous?.recap:null)}));setLoadStatus(next.current?'ready':'empty');}
 async function showSources(){
  const version=latestVersion.current;
  setSourcesVisited(true);setSourceError('');
  if(state?.understanding.length)return;
  setLoadingSources(true);
  try{await reload(state?.current?.id);}catch{if(latestVersion.current===version)setSourceError('Les sources détaillées n’ont pas pu être chargées. La compréhension enregistrée reste disponible.');}
  finally{if(latestVersion.current===version)setLoadingSources(false);}
 }
 async function saveDraft(){
  if(!draft.trim())return state;
  if(!appendAttempt.current||appendAttempt.current.text!==draft)appendAttempt.current=intake('message',draft);
  const next=await api.addIntake(scope,appendAttempt.current);accept(next);appendAttempt.current=null;setDraft('');
  return {...next,understanding:state?.understanding??[]};
 }
 async function synchronize(){
  const next=await reload();
  setQuestionStates(previous=>Object.fromEntries(Object.keys(previous).map(id=>[id,next.chat_attempts?.find(a=>a.question_id===id)?.state==='running'?'uncertain':'failed'])));
  if(next.state==='failed')regenerationAttempt.current=null;
  return next;
 }
 async function send(question?:string){
  if(lock.current||!state||(!question&&!draft.trim()))return;
  lock.current=true;setBusy('send');setSendingQuestion(question??null);setError('');setNotice('');
  let target=question;
  try{
   const next=question?state:await saveDraft();
   target=question??next?.intake.filter(i=>i.kind==='message'&&i.role==='user').at(-1)?.id;
   if(!target)return;
   setSendingQuestion(target);
   const failed=next?.chat_attempts?.find(a=>a.question_id===target)?.state==='failed';
   const operation=failed||!sendOperations.current[target]?crypto.randomUUID():sendOperations.current[target];
   sendOperations.current[target]=operation;
   setQuestionStates(previous=>({...previous,[target!]:'sending'}));
   await api.workspaceChat(scope,target,operation);
   await reload();
  }catch(e){
   if(target){
    setQuestionStates(previous=>({...previous,[target!]:'uncertain'}));
    try{await synchronize();}catch{/* A read failure leaves the question awaiting synchronization. */}
   }else setError('Le message n’a pas pu être enregistré. Tu peux réessayer.');
  }finally{lock.current=false;setBusy(null);setSendingQuestion(null);void refreshAvailability();}
 }
 async function memorize(regenerate=false){
  if(lock.current||!state)return;
  lock.current=true;setBusy(regenerate?'regenerate':'memory');setError('');setNotice('');
  setOpen(true);
  try{
   if(!regenerate)await saveDraft();
   if(regenerate&&!regenerationAttempt.current)regenerationAttempt.current=crypto.randomUUID();
   const saved=regenerate?await api.regenerate(scope,regenerationAttempt.current!):await api.consolidate(scope);
   regenerationAttempt.current=null;accept(saved);setOpen(true);setSourcesVisited(false);setSourceError('');setLoadingSources(false);
   if(!saved.recap){
    try{await reload(saved.current?.id);}catch{setLoadStatus('error');setNotice('Version enregistrée. Le récapitulatif n’a pas pu être chargé. Actualise l’état pour le consulter.');return;}
   }
   setNotice('Compréhension mise à jour');
  }catch(e){setError(failure(e));if(regenerate){try{await synchronize();}catch{/* Keep operation identity while publication is uncertain. */}}}finally{lock.current=false;setBusy(null);void refreshAvailability();}
 }
 async function addFile(file:File|undefined,context:boolean){
  if(!file||lock.current)return;
  if(file.size>500000){setError('Ce fichier dépasse la limite de 500 Ko.');return;}
  if(!context&&!/\.(txt|md|markdown)$/i.test(file.name)){setError('L’extraction PDF n’est pas encore disponible. Utilise un fichier TXT ou Markdown ; aucun document n’a été ajouté.');return;}
  lock.current=true;setBusy('file');setError('');setNotice('');
  try{
   const text=await file.text();
   const input=intake(context?'context':'document',context?null:text,file.name);
   if(context)input.context=JSON.parse(text);
   accept(await api.addIntake(scope,input));
   setNotice(context?'Contexte importé. Clique sur Mémoriser pour l’intégrer.':'Document ajouté. Clique sur Mémoriser pour l’intégrer.');
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
 const availabilityMessage=availabilityError?'La disponibilité de l’IA n’a pas pu être vérifiée.':caps?.accounting_blocked?'L’IA est suspendue après une erreur du fournisseur. Tes messages sont conservés.':caps?.plafond_reached?'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.':caps&&!caps.enabled?'L’IA est indisponible pour ce contexte.':checkingAvailability&&!caps?'Vérification de la disponibilité de l’IA…':'';


 const items=state?.intake??[];
 const paired=new Map(items.filter(i=>i.reply_to).map(i=>[i.reply_to!,i]));
 const displayed=items.filter(i=>!i.reply_to).flatMap(i=>paired.has(i.id)?[i,paired.get(i.id)!]:[i]);
 function questionStatus(item:ContextIntake){
  if(item.kind!=='message'||item.role!=='user'||paired.has(item.id))return null;
  const index=items.indexOf(item);
  if(items.slice(index+1).some(i=>i.role==='assistant'&&!i.reply_to))return null;
  return questionStates[item.id]??(state?.chat_attempts?.find(a=>a.question_id===item.id)?.state==='running'?'uncertain':'failed');
 }
 const summary=state?.recap;
 const sources=state?.understanding.filter(row=>!summary||summary.support_revision_ids.includes(row.revision_id))??[];
 const recap=<>
  {busy==='memory'||busy==='regenerate'?<div className="memory-progress"><Loading label="Mémorisation en cours"/><p>Compréhension en cours de préparation et d’enregistrement…</p></div>:loadStatus==='loading'?<Loading label="Chargement de la compréhension…"/>:loadStatus==='error'?<p role="alert" className="small muted">La compréhension n’a pas pu être chargée. Actualise l’état pour réessayer.</p>:<>
  {state?.current?<>
   <p className="small muted">Version {state.current.version} · {new Date(state.current.created_at).toLocaleString('fr-FR')}</p>
   <h3>{summary?.title??name??'Ce contexte'}</h3>
   {summary?summary.text.split(/\n\s*\n/).map((text,index)=><p className="context-recap" key={index}>{text}</p>):<p>Un aperçu synthétique sera préparé lors de la prochaine mémorisation. Les informations détaillées restent conservées.</p>}
   {state.current.has_recap===false&&<p className="small muted">Mémoriser actualisera le récapitulatif, sans ajouter de message.</p>}
   <div className="actions"><button type="button" className="secondary" onClick={()=>{void download();}}>Exporter</button><button type="button" className="secondary" disabled={disabled||!caps?.enabled} onClick={()=>{void memorize(true);}}>Régénérer</button></div>
   <details className="recap-sources" onToggle={event=>{if(event.currentTarget.open&&!sourcesVisited)void showSources();}}><summary>Consulter les sources</summary>{loadingSources&&<Loading label="Chargement des sources…"/>}{sourceError&&<><p role="alert">{sourceError}</p><button type="button" className="secondary" disabled={loadingSources} onClick={()=>{void showSources();}}>Réessayer les sources</button></>}{sourcesVisited&&sources.map(row=><section key={row.revision_id}><p>{String(row.content.text??'')}</p>{recognizedCitations(row).map((citation,index)=><blockquote key={index}>{citation.quote}</blockquote>)}</section>)}</details>
   <p className="small muted">Pour corriger cette compréhension, ajoute un message puis mémorise.</p>
  </>:<p>Ce contexte n’a pas encore été mémorisé. Ajoute des informations puis clique sur Mémoriser.</p>}
  </>}
 </>;

 return <section className="context-space-v02" aria-label="Context Space">
  <header className="context-space-tools">{heading??<strong>Discussion</strong>}<div className="actions">
   <label className="compact-model"><span className="sr-only">Modèle</span><select value="mistral-small-2603" onChange={()=>{}}><option value="mistral-small-2603">Mistral Small{caps?.enabled?'':' · indisponible'}</option></select></label>
   <button type="button" className="secondary" aria-expanded={open} onClick={()=>setOpen(v=>!v)}>Compréhension</button>
   {sharingContent}
   <button type="button" className="secondary" onClick={()=>setSettings(true)}>Paramètres</button>
  </div></header>
  {settings&&<Modal title="Paramètres du Space" className="workspace-settings-dialog" onClose={()=>setSettings(false)}>
   {settingsContent}
   <details><summary>Données envoyées</summary><p>Envoyer transmet cette conversation et la compréhension de ce Space à Mistral Small. Mémoriser analyse les apports de ce Space, y compris les documents et contextes importés. {caps?.automatic&&<>Budget commun restant : {caps.remaining_usd} USD.</>}</p></details>
   {caps?.automatic&&<details><summary>Diagnostics IA (développement)</summary><AIDiagnostics api={api} scope={scope}/></details>}
  </Modal>}
  <div className={'context-space-workspace'+(open&&!narrow?' with-understanding':'')}>
   <section className="workspace-discussion" aria-label="Discussion">
    <div className="workspace-log" ref={log} role="log" aria-label="Discussion du Context Space" aria-live="polite" aria-busy={!!busy} tabIndex={0}>
     {!state&&!error&&<Loading label="Chargement du contexte…"/>}
     {state&&!state.intake.length&&<div className="workspace-welcome"><h2>Commence à discuter.</h2><p>QH peut ensuite en retenir l’essentiel dans ce Space.</p></div>}
     {displayed.map(item=><article key={item.id} className={'workspace-message '+(item.role==='assistant'?'assistant':'user')}>
      {item.kind==='message'?<><span className="sr-only">{item.role==='assistant'?'QH':'Toi'}</span>{item.role==='assistant'?<><AnswerMarkdown text={item.text!}/>{item.attribution&&<WorkspaceAnswerSources api={api} scope={scope} attribution={item.attribution}/>}</>:<p>{item.text}</p>}</>:<p>{item.kind==='context'?'Contexte importé':'Document'} : {item.name}</p>}
      {questionStatus(item)&&questionStatus(item)!=='sending'&&<div className="message-feedback">
       <p role="alert">{questionStatus(item)==='uncertain'?'La réponse est en attente de synchronisation.':'La réponse n’a pas pu être obtenue. Ta question est conservée.'}</p>
       {questionStatus(item)==='uncertain'?<button type="button" className="secondary" disabled={!!busy} onClick={()=>{void synchronize().catch(()=>{});}}>Actualiser l’état</button>:questionStatus(item)==='failed'&&<button type="button" className="secondary" disabled={disabled||!caps?.enabled} onClick={()=>{void send(item.id);}}>Réessayer</button>}
      </div>}
     </article>)}
     {busy==='send'&&!error&&(!sendingQuestion||!paired.has(sendingQuestion)&&questionStates[sendingQuestion]==='sending')&&<div className="workspace-message assistant workspace-answer-pending" role="status">Préparation de la réponse…</div>}
    </div>
    <div className="workspace-feedback">{(busy==='memory'||busy==='regenerate')&&<p role="status">Mémorisation en cours : analyse et enregistrement de tes apports…</p>}{availabilityMessage&&<div className="workspace-availability"><p role="status">{availabilityMessage}</p>{!checkingAvailability&&<button type="button" className="secondary" onClick={()=>{void refreshAvailability();}}>Actualiser la disponibilité</button>}</div>}{error&&<p role="alert" className="notice error">{error}</p>}{notice&&<p role="status">{notice}</p>}{error&&<button type="button" className="secondary" disabled={!!busy} onClick={()=>{void synchronize().then(()=>setError('')).catch(e=>setError(failure(e)));}}>Actualiser l’état</button>}</div>
    <form className="workspace-composer" onSubmit={event=>{event.preventDefault();void send();}}>
     <label className="sr-only" htmlFor="context-message">Ton message</label><textarea id="context-message" rows={3} value={draft} onChange={event=>setDraft(event.target.value)} disabled={disabled||!state} placeholder="Ajoute une information ou pose une question…"/>
     <div className="workspace-composer-actions"><div className="actions"><button type="button" className="secondary" disabled={disabled||!state} onClick={()=>documentInput.current?.click()}>Joindre un document</button><button type="button" className="secondary" disabled={disabled||!state} onClick={()=>contextInput.current?.click()}>Importer un contexte</button></div><div className="actions"><button type="submit" className="workspace-send" disabled={disabled||!state||!draft.trim()||!caps?.enabled}>Envoyer</button><button type="button" className="secondary workspace-memory" title="Consolider les informations de ce Space" disabled={disabled||!state||(!state.pending_count&&!draft.trim()&&(!state.current||!!state.recap&&state.current.has_recap!==false))||!caps?.enabled} onClick={()=>{void memorize();}}>{busy==='memory'?'Mémorisation…':'Mémoriser'}</button>{!!state?.pending_count&&<span className="workspace-unsaved small muted">Modifications non mémorisées</span>}</div></div>
     <input ref={documentInput} type="file" accept=".txt,.md,.markdown,.pdf" hidden onChange={event=>{void addFile(event.target.files?.[0],false);event.target.value='';}}/>
     <input ref={contextInput} type="file" accept=".json,application/json" hidden onChange={event=>{void addFile(event.target.files?.[0],true);event.target.value='';}}/>
    </form>
   </section>
   {open&&(narrow?<Modal title="Compréhension" className="workspace-understanding-overlay" onClose={()=>setOpen(false)}>{recap}</Modal>:<aside id="context-understanding" ref={panel} tabIndex={-1} className="context-understanding" aria-label="Compréhension"><header><h2>Compréhension</h2><button type="button" className="secondary" onClick={()=>setOpen(false)}>Fermer</button></header>{recap}</aside>)}
  </div>
 </section>;
}
