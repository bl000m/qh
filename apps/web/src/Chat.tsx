import EnrichConversation from './EnrichConversation';
import ManualInformation from './ManualInformation';
import type {SelectedConversationTurn} from './EnrichConversation';
import {useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import {apiMessage,ApiError} from './api';
import type {QhApi} from './api';
import SourcesPanel from './SourcesPanel';
import ProviderChoice,{offlineFixture} from './ProviderChoice';
import type {ChatAnswer,DialogueMessage} from './chat';

export default function Chat({api,scope,onAnswersChange,onOpenProposal}:{api:QhApi;scope:string;onAnswersChange?:(answers:ChatAnswer[])=>void;onOpenProposal?:(id:string)=>void}) {
  const [available,setAvailable]=useState<{current:boolean;proposed:boolean;historical:boolean}|null>(null);
  const [includeProposed,setIncludeProposed]=useState(false);
  const [messages,setMessages]=useState<DialogueMessage[]>([]);
  const [conversationId,setConversationId]=useState(()=>crypto.randomUUID());
  const [sourceTurns,setSourceTurns]=useState<SelectedConversationTurn[]>([]);
  const [answers,setAnswers]=useState<ChatAnswer[]>([]);
  useEffect(()=>{onAnswersChange?.(answers);},[answers,onAnswersChange]);
  const [question,setQuestion]=useState('');
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
  useEffect(()=>{
    const n=++generation.current;
    setAvailable(null);setError('');
      Promise.all([api.browse(scope,{view:'current',limit:1}),api.browse(scope,{view:'proposed',limit:1})])
        .then(async([current,proposed])=>{
          const hasCurrent=current.items.length>0,hasProposed=proposed.items.length>0;
          // A lack of active support does not establish an empty Space. Reuse the
          // authorized, graph-verified history view; never infer absence on error.
          const historical=!hasCurrent&&!hasProposed ? (await api.browse(scope,{view:'history',limit:1})).items.length>0 : false;
          if(n===generation.current)setAvailable({current:hasCurrent,proposed:hasProposed,historical});
        })
        .catch(e=>{if(n===generation.current){setError(apiMessage(e));setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());}});
    return()=>{generation.current++;};
  },[api,scope]);
  function reset(){setSourceIndex(null);follow.current=true;generation.current++;setMessages([]);setAnswers([]);setSourceTurns([]);setConversationId(crypto.randomUUID());setQuestion('');setError('');setLoading(false);}
  async function submit(event:FormEvent){
    event.preventDefault();if(loading || !question.trim() || messages.length>=8 || !available || providerMode==='mistral'&&!providerSession)return;
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
  const proposalsExcluded=!!available&&!available.current&&available.proposed&&!includeProposed;
  const noActive=!!available&&!available.current&&!available.proposed;
  const proposalHelp='Des éléments sont disponibles, mais ils ne sont pas confirmés. Pour en discuter, cochez « Inclure explicitement les propositions non confirmées ».';
  return <section className="context-chat" aria-labelledby="chat-title">
    <h2 id="chat-title">Discuter avec ce contexte</h2>
      {!available && !error && <p role="status">Vérification du contexte disponible…</p>}
      {available && <>
        {!available.current && available.proposed && <div className="notice chat-availability"><p>Compréhension disponible : propositions non confirmées uniquement.</p>{proposalsExcluded && <p id="chat-availability-help">{proposalHelp}</p>}</div>}
        {noActive && <div className="chat-empty" role="note"><h3>{available.historical ? 'Une histoire à explorer, aucun élément actif pour discuter.' : 'Ce Space attend sa première compréhension.'}</h3>
          <p>{available.historical ? 'Des révisions sont conservées dans l’historique. Elles restent consultables dans Explorer la compréhension, mais ne sont pas transmises à la chat.' : 'Aucune révision de compréhension n’est disponible dans ce Space. Il n’y a pas encore d’éléments sur lesquels appuyer une réponse.'}</p>
          <p className="small muted">Ajoutez votre première information ci-dessous, sans appel à un fournisseur. Elle restera proposée jusqu’à votre examen explicite.</p></div>}
        <label className="chat-opt-in"><input type="checkbox" checked={includeProposed} disabled={loading} onChange={e=>{reset();setIncludeProposed(e.target.checked);}}/> Inclure explicitement les propositions non confirmées</label>
      </>}
      <div className="conversation-scroll" ref={viewport} role="log" aria-label="Conversation temporaire" aria-live="polite" aria-relevant="additions" aria-busy={loading} tabIndex={0} onScroll={()=>{const n=viewport.current;if(n&&!moving.current){follow.current=n.scrollHeight-n.clientHeight-n.scrollTop<48;if(follow.current)setUnread(false);}}}>
      {answers.map((answer,i)=><article ref={i===answers.length-1&&!loading?latest:undefined} className="chat-turn" key={i} aria-label={'Échange '+(i+1)}>
        <div className="chat-question-message"><h3>Votre question</h3><p className="chat-text">{messages[i*2]?.content}</p></div>
        <div className="chat-answer-message">
        <h3>{answer.model==='qh-mock-extractive/1' ? 'Extraits de démonstration — sans compréhension de la question' : 'Réponse de l’IA'}</h3><p className="small muted">Modèle : {answer.model}</p>
        {(answer.references.some(row=>row.validation_state==='proposed')||answer.provided_revisions.length>0&&answer.provided_revisions.every(row=>row.validation_state==='proposed'))&&<p role="note" className="epistemic-line">Cette réponse s’appuie sur des éléments non encore confirmés dans QH.{answer.provided_revisions.every(row=>row.validation_state==='proposed')?' Tout le contexte fourni est proposé ; aucune révision confirmée courante n’a été transmise.':''}</p>}
        <p className="chat-text">{answer.answer}</p>
        {answer.insufficient_context && <p className="notice">{proposalsExcluded ? proposalHelp : noActive ? (available?.historical ? 'L’historique est conservé, mais aucun élément actif n’est disponible pour cette discussion.' : 'Ce Space ne contient pas encore de révisions de compréhension pour étayer cette réponse.') : 'Les informations autorisées fournies ne suffisent pas à étayer une réponse à cette question. Cela ne signifie pas que l’information n’existe pas ailleurs dans le Space.'}</p>}
        {answer.partial_coverage && <p className="notice">Couverture partielle : limites de pages ou de taille atteintes. Les éléments absents de cette réponse peuvent exister dans le Space.</p>}
        <div className="answer-source-link"><span>{answer.references.length} éléments cités{answer.references.some(r=>r.validation_state==='proposed')?' · Compréhension non confirmée':''}</span><button type="button" className="secondary" onClick={()=>setSourceIndex(i)}>Voir les sources<span className="sr-only"> de la réponse {i+1}</span></button></div>
        </div>
      </article>)}
      {error && <p role="alert" className="notice error">{error}</p>}
      {loading && <div ref={latest as React.RefObject<HTMLDivElement>} className="chat-pending"><div className="chat-question-message"><h3>Votre question</h3><p className="chat-text">{question}</p></div><p role="status">Préparation de la réponse…</p></div>}
      </div>
      {unread&&<button type="button" className="new-response" onClick={()=>{follow.current=true;showLatest();}}>Voir la nouvelle réponse ↓</button>}
      <p className="generation-status" role="status">{loading?'Réponse en cours…':answers.length?'Réponse disponible. La discussion reste temporaire.':''}</p>
      <ManualInformation api={api} scope={scope} disabled={loading} onOpen={onOpenProposal} onSaved={()=>{setAvailable(previous=>previous?{...previous,proposed:true,historical:false}:previous);setContextChanged(n=>n+1);}}/>
      <form className="chat-composer" onSubmit={e=>{void submit(e);}}>
        <label htmlFor="chat-question">Votre question sur ce contexte</label>
        <textarea id="chat-question" ref={questionField} value={question} maxLength={4096} onChange={e=>setQuestion(e.target.value)} aria-describedby={proposalsExcluded ? 'chat-availability-help' : undefined} disabled={loading || !available || messages.length>=8} rows={4} placeholder="Que souhaitez-vous savoir ?"/>
      {available&&<ProviderChoice api={api} scope={scope} include={includeProposed} messages={[...messages,{role:'user',content:question}]} failure={providerFailure} contextChanged={contextChanged} completed={answers.length} onChange={providerChanged}/>}
        <div className="actions"><button disabled={loading || !available || !question.trim() || messages.length>=8 || providerMode==='mistral'&&!providerSession}>Envoyer la question</button>
          <button type="button" className="secondary" disabled={loading} onClick={()=>{reset();if(providerMode==='mistral')setProviderFailure(v=>v+1);}}>Nouvelle discussion</button></div>
        {messages.length>=8 && <p>Limite de quatre questions atteinte. Commencez une nouvelle discussion dans ce même Space.</p>}
      </form>
      <EnrichConversation key={conversationId} api={api} scope={scope} conversationId={conversationId} turns={sourceTurns} disabled={loading} onOpen={onOpenProposal} onSaved={receipt=>{if(receipt.revision_ids.length){setAvailable(previous=>previous?{...previous,proposed:true,historical:false}:previous);setContextChanged(n=>n+1);}}}/>
      {sourceIndex!==null&&answers[sourceIndex]&&<SourcesPanel answer={answers[sourceIndex]} index={sourceIndex} onClose={()=>setSourceIndex(null)}/>}
      <details className="chat-help"><summary>Fonctionnement et limites</summary>
      <p>Échanges temporaires, distincts de la compréhension conservée. La réponse seule n’ajoute ni ne confirme rien. « Enrichir ce contexte » permet une conservation séparée, explicite et non confirmée.</p>
      <p>La discussion utilise une sélection bornée, sans classement sémantique. Mistral exige une activation administrative et une autorisation explicite des données affichées. Sans fournisseur disponible, vous pouvez conserver une information sans IA.</p>
      <p>Les révisions historiques et refusées sont exclues. Changer le choix des propositions efface la discussion temporaire.</p>
      <p className="small muted">La discussion reste uniquement en mémoire dans cet onglet. Fermer, changer de Space ou se déconnecter l’efface. Seuls les messages explicitement sélectionnés via « Enrichir ce contexte » peuvent être conservés comme source et propositions.</p>
      </details>
  </section>;
}
