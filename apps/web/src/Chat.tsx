import EnrichConversation from './EnrichConversation';
import ManualInformation from './ManualInformation';
import useDraft from './useDraft';
import type {SelectedConversationTurn} from './EnrichConversation';
import {useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import {ApiError,apiMessage} from './api';
import type {QhApi} from './api';
import SourcesPanel from './SourcesPanel';
import {Orb,Icon} from './Ui';
import ContextMap,{UsefulActions} from './ContextMap';
import type {SpaceTab} from './SpaceTabs';
import type {SessionCapabilities} from './provider-session';
import ProviderChoice,{offlineFixture} from './ProviderChoice';
import type {ChatAnswer,DialogueMessage} from './chat';

export default function Chat({api,scope,onAnswersChange,onOpenProposal,tab='Discussion',addRequest=0,draftRequest,onContextSaved,refreshKey=0,onExploreContext,onTheme}:{api:QhApi;scope:string;onAnswersChange?:(answers:ChatAnswer[])=>void;onOpenProposal?:(id:string)=>void;tab?:SpaceTab;addRequest?:number;draftRequest?:{id:number;text:string};onContextSaved?:()=>void;refreshKey?:number;onExploreContext?:()=>void;onTheme?:(value:string)=>void}) {
  const [available,setAvailable]=useState<{current:boolean;proposed:boolean;historical:boolean}|null>(null);
  const [includeProposed,setIncludeProposed]=useState(false);
  const [messages,setMessages]=useState<DialogueMessage[]>([]);
  const [conversationId,setConversationId]=useState(()=>crypto.randomUUID());
  const [sourceTurns,setSourceTurns]=useState<SelectedConversationTurn[]>([]);
  const [answers,setAnswers]=useState<ChatAnswer[]>([]);
  useEffect(()=>{onAnswersChange?.(answers);},[answers,onAnswersChange]);
  const [question,setQuestion]=useDraft('message');
  const [manualOpen,setManualOpen]=useState(0);
  const [authorizationRequest,setAuthorizationRequest]=useState(0);
  const [capabilities,setCapabilities]=useState<SessionCapabilities|null>(null);
  const capabilitiesChanged=useCallback((value:SessionCapabilities|null)=>setCapabilities(value),[]);
  useEffect(()=>{if(addRequest)setManualOpen(n=>n+1);},[addRequest]);
  const [loading,setLoading]=useState(false);
  const [providerMode,setProviderMode]=useState<'mock'|'mistral'>(offlineFixture?'mock':'mistral');
  const [providerSession,setProviderSession]=useState<string|null>(null);
  const [providerFailure,setProviderFailure]=useState(0);
  const [contextChanged,setContextChanged]=useState(0);
  const [sourceIndex,setSourceIndex]=useState<number|null>(null);
  const [unread,setUnread]=useState(false);
  const viewport=useRef<HTMLDivElement>(null),latest=useRef<HTMLElement|null>(null);
  const follow=useRef(true),moving=useRef(false);
  function showLatest(){const node=viewport.current;if(!node)return;moving.current=true;const item=latest.current;node.scrollTop=item?item.getBoundingClientRect().top-node.getBoundingClientRect().top+node.scrollTop:node.scrollHeight;setUnread(false);requestAnimationFrame(()=>{moving.current=false;});}
  useLayoutEffect(()=>{if(follow.current)showLatest();else if(answers.length||loading)setUnread(true);},[answers.length,loading]);
  const providerChanged=useCallback((mode:'mock'|'mistral',id:string|null,preserveDialogue=false)=>{
    setProviderMode(mode);setProviderSession(id);
    if(id===null&&!preserveDialogue){setSourceIndex(null);follow.current=true;generation.current++;setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());setLoading(false);setError('');}
  },[]);
  const [error,setError]=useState('');
  const generation=useRef(0);
  const questionField=useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{if(draftRequest){setQuestion(draftRequest.text);requestAnimationFrame(()=>questionField.current?.focus());}},[draftRequest]);
  useEffect(()=>{
    const n=++generation.current;
    setAvailable(null);setError('');
      async function read(view:'current'|'proposed'|'history'){
        const attempts=refreshKey>0?16:1;
        for(let attempt=0;attempt<attempts;attempt++){
          if(n!==generation.current)return null;
          try{return await api.browse(scope,{view,limit:1});}
          catch(error){if(!(error instanceof ApiError)||error.status!==503||attempt===attempts-1)throw error;await new Promise(resolve=>setTimeout(resolve,500));}
        }
        return null;
      }
      Promise.all([read('current'),read('proposed')])
        .then(async([current,proposed])=>{
          if(!current||!proposed||n!==generation.current)return;
          const hasCurrent=current.items.length>0,hasProposed=proposed.items.length>0;
          // A lack of active support does not establish an empty Space. Reuse the
          // authorized, graph-verified history view; never infer absence on error.
          const historical=!hasCurrent&&!hasProposed ? ((await read('history'))?.items.length??0)>0 : false;
          if(n===generation.current)setAvailable({current:hasCurrent,proposed:hasProposed,historical});
        })
        .catch(e=>{if(n===generation.current){setError(apiMessage(e));setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());}});
    return()=>{generation.current++;};
  },[api,scope,refreshKey]);
  function reset(){setSourceIndex(null);follow.current=true;generation.current++;setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());setQuestion('');setError('');setLoading(false);}
  async function submit(event:FormEvent){
    event.preventDefault();if(loading || !question.trim() || messages.length>=8 || !available)return;
    if(providerMode==='mistral'&&!providerSession){if(capabilities?.enabled)setAuthorizationRequest(n=>n+1);else setError('Le modèle n’est pas disponible pour ce contexte. Vous pouvez toujours ajouter un élément.');return;}
    const n=generation.current;
    const next:DialogueMessage[]=[...messages,{role:'user',content:question}];
    const userTurn:SelectedConversationTurn={id:crypto.randomUUID(),role:'user',content:question,captured_at:new Date().toISOString()};
    setLoading(true);setError('');
    try{
      const answer=providerMode==='mistral' ? await api.sessionChat(scope,providerSession!,next,includeProposed) : await api.chat(scope,next,includeProposed);
      if(n!==generation.current)return;
      // Answering never persists; separate explicit enrichment consent is required.
      setMessages([...next,{role:'assistant',content:answer.answer}]);
      setSourceTurns(previous=>[...previous,userTurn,{id:crypto.randomUUID(),role:'assistant',content:answer.answer,captured_at:new Date().toISOString()}]);
      setAnswers(previous=>[...previous,answer]);setQuestion('');
    }catch(e){if(n!==generation.current)return;setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());
      if(providerMode==='mistral'){setProviderFailure(v=>v+1);setProviderSession(null);}
      setError(e instanceof ApiError && e.status===422 ? 'La discussion dépasse les limites autorisées. Commencez une nouvelle discussion avec une question plus courte.' : e instanceof ApiError && e.status===503 ? 'Discussion indisponible : contexte non fiable ou fournisseur indisponible. Aucun nouvel essai automatique.' : apiMessage(e));
    }finally{if(n===generation.current)setLoading(false);}
  }
  const empty=!!available&&!available.current&&!available.proposed&&!available.historical;
  const assistant=useRef<HTMLElement>(null);
  function starter(text:string){setQuestion(text);requestAnimationFrame(()=>questionField.current?.focus());}
  return <>
  <section hidden={tab!=='Discussion'} id="space-panel-0" role="tabpanel" aria-labelledby="space-tab-0" className={'context-chat product-discussion space-discussion-grid '+(empty?'space-empty-layout':'space-populated-layout')}>
    <h2 id="chat-title" className="sr-only">Discussion</h2>
    {!available&&!error&&<p role="status">Chargement…</p>}
    <aside className="space-context-column">{available&&(empty?<section className="space-add-card"><span className="card-icon"><Icon name="sources"/></span><h2>J’ajoute un élément</h2><p>J’ajoute une information utile<br/>à ce contexte.</p><button type="button" onClick={()=>setManualOpen(n=>n+1)}><Icon name="plus"/>Ajouter un élément</button></section>:<><ContextMap api={api} scope={scope} refreshKey={refreshKey} onTheme={onTheme} onExplore={onExploreContext} onAdd={()=>setManualOpen(n=>n+1)}/><UsefulActions/></>)}</aside>
    <section className="assistant-card" ref={assistant}><header><span className="card-icon"><Icon name="discussion"/></span><h2>Je discute avec l’assistant</h2>{!empty&&<button type="button" className="secondary assistant-expand" aria-label="Agrandir la discussion" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void assistant.current?.requestFullscreen?.().catch(()=>{});}}><Icon name="expand"/></button>}</header>{answers.length===0&&!loading&&<p className="assistant-intro">Je pose une question pour mieux comprendre, organiser et décider.</p>}
    <div className="conversation-scroll" ref={viewport} role="log" aria-label="Conversation temporaire" aria-live="polite" aria-relevant="additions" aria-busy={loading} tabIndex={0} onScroll={()=>{const n=viewport.current;if(n&&!moving.current){follow.current=n.scrollHeight-n.clientHeight-n.scrollTop<48;if(follow.current)setUnread(false);}}}>
      {answers.map((answer,i)=><article ref={i===answers.length-1&&!loading?latest:undefined} className="chat-turn" key={i} aria-label={'Échange '+(i+1)}><div className="chat-question-message"><h3 className="sr-only">Votre question</h3><p className="chat-text">{messages[i*2]?.content}</p></div><div className="chat-answer-message"><span className="answer-brand"><Orb/></span><h3 className="sr-only">{answer.model==='qh-mock-extractive/1'?'Extraits de démonstration — sans compréhension de la question':'Réponse de l’IA'}</h3><p className="chat-text">{answer.answer}</p>{answer.insufficient_context&&<p className="muted">Les éléments disponibles ne suffisent pas à répondre à cette question.</p>}<div className="answer-source-link"><button type="button" className="text-button" onClick={()=>setSourceIndex(i)}>Sources de la réponse {i+1}</button>{(answer.references.some(r=>r.validation_state==='proposed')||answer.provided_revisions.length>0&&answer.provided_revisions.every(r=>r.validation_state==='proposed'))&&<span role="note" className="small muted">Éléments à vérifier</span>}</div><details className="answer-details"><summary>Détails de cette réponse</summary><p>Modèle : {answer.model}</p>{answer.provided_revisions.length>0&&answer.provided_revisions.every(r=>r.validation_state==='proposed')&&<p>Tout le contexte fourni est proposé ; aucune révision confirmée courante n’a été transmise.</p>}<p>Les sources permettent de retrouver les informations utilisées ; elles ne confirment pas automatiquement la réponse.</p>{answer.partial_coverage&&<p>Seule une partie des éléments a été utilisée.</p>}</details></div></article>)}
      {loading&&<div ref={latest as React.RefObject<HTMLDivElement>} className="chat-pending"><div className="chat-question-message"><p className="chat-text">{question}</p></div><p role="status">Préparation de la réponse…</p></div>}
    </div>
    {error&&<p role="alert" className="chat-error">{error}</p>}
    {unread&&<button type="button" className="new-response" onClick={()=>{follow.current=true;showLatest();}}>Voir la nouvelle réponse ↓</button>}
    <EnrichConversation key={conversationId} api={api} scope={scope} conversationId={conversationId} turns={sourceTurns} disabled={loading} onOpen={onOpenProposal} onSaved={receipt=>{onContextSaved?.();if(receipt.revision_ids.length){setAvailable(previous=>previous?{...previous,proposed:true,historical:false}:previous);setContextChanged(n=>n+1);}}}/>
    <div className="chat-starters" aria-label="Points de départ de ma discussion">{(empty?['M’aide à y voir plus clair','Organise ces informations','Quels sont les points importants ?']:['Aide-moi à clarifier mes priorités','Prépare la prochaine discussion','Résume ce qui est important']).map((text,i)=><button type="button" className="secondary" key={text} onClick={()=>starter(text)}><Icon name={i===0?'advice':i===1?'list':'target'}/><span>{text}</span></button>)}</div>
    <form className="chat-composer product-composer" onSubmit={e=>{void submit(e);}}><label className="sr-only" htmlFor="chat-question">Votre question sur ce contexte</label><textarea id="chat-question" ref={questionField} value={question} maxLength={4096} onChange={e=>setQuestion(e.target.value)} disabled={loading||!available||messages.length>=8} rows={1} placeholder="J’écris mon message…"/><button aria-label="Envoyer la question" title="Envoyer" disabled={loading||!available||!question.trim()||messages.length>=8}><Icon name="send"/></button><div className="composer-media">{(['clip','image'] as const).map((icon,i)=><button key={icon} type="button" disabled aria-label={['Joindre un fichier — indisponible','Joindre une image — indisponible','Ajouter une source — indisponible'][i]}><Icon name={icon}/></button>)}</div><details className="composer-options"><summary aria-label="Options de la discussion"><Icon name="book"/></summary><div>{answers.length>0&&<button type="button" className="secondary" onClick={()=>setManualOpen(n=>n+1)}>Ajouter un élément</button>}<button type="button" className="secondary" disabled={loading} onClick={e=>{e.currentTarget.closest('details')?.removeAttribute('open');reset();if(providerMode==='mistral')setProviderFailure(v=>v+1);}}>Nouvelle discussion</button><p className="small muted">Les brouillons et la discussion restent dans cet onglet. Seuls les messages que vous choisissez de mémoriser sont conservés.</p></div></details></form>
    {messages.length>=8&&<p role="status">Commencez une nouvelle discussion pour continuer.</p>}
    </section>
  </section>
  <ManualInformation api={api} scope={scope} disabled={loading} openRequest={manualOpen} hideAction onSaved={receipt=>{onContextSaved?.();if(receipt.revision_ids.length)setAvailable(previous=>previous?{...previous,proposed:true,historical:false}:previous);setContextChanged(n=>n+1);}}/>
  <ProviderChoice api={api} scope={scope} include={includeProposed} messages={[...messages,{role:'user',content:question}]} failure={providerFailure} contextChanged={contextChanged} completed={answers.length} request={authorizationRequest} visible={tab==='Modèles'} hasProposed={available?.proposed} onInclude={setIncludeProposed} onCapabilities={capabilitiesChanged} onChange={providerChanged}/>
  {sourceIndex!==null&&answers[sourceIndex]&&<SourcesPanel answer={answers[sourceIndex]} index={sourceIndex} onClose={()=>setSourceIndex(null)}/>}
  </>;
}
