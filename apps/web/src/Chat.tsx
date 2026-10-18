import {useEffect,useRef,useState} from 'react';
import type {FormEvent} from 'react';
import {apiMessage,ApiError} from './api';
import type {QhApi} from './api';
import {Revision} from './Revision';
import type {ChatAnswer,DialogueMessage} from './chat';

export default function Chat({api,scope}:{api:QhApi;scope:string}) {
  const [available,setAvailable]=useState<{current:boolean;proposed:boolean}|null>(null);
  const [includeProposed,setIncludeProposed]=useState(false);
  const [messages,setMessages]=useState<DialogueMessage[]>([]);
  const [answers,setAnswers]=useState<ChatAnswer[]>([]);
  const [question,setQuestion]=useState('');
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const generation=useRef(0);
  const questionField=useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{
    const n=++generation.current;
    setAvailable(null);setError('');
      Promise.all([api.browse(scope,{view:'current',limit:1}),api.browse(scope,{view:'proposed',limit:1})])
        .then(([current,proposed])=>{if(n===generation.current)setAvailable({current:current.items.length>0,proposed:proposed.items.length>0});})
        .catch(e=>{if(n===generation.current){setError(apiMessage(e));setMessages([]);setAnswers([]);}});
    return()=>{generation.current++;};
  },[api,scope]);
  function reset(){generation.current++;setMessages([]);setAnswers([]);setQuestion('');setError('');setLoading(false);}
  async function submit(event:FormEvent){
    event.preventDefault();if(loading || !question.trim() || messages.length>=8 || !available)return;
    const n=generation.current;
    const next:DialogueMessage[]=[...messages,{role:'user',content:question}];
    setLoading(true);setError('');
    try{
      const answer=await api.chat(scope,next,includeProposed);
      if(n!==generation.current)return;
      // No conversation is persisted or promoted to canonical understanding.
      setMessages([...next,{role:'assistant',content:answer.answer}]);
      setAnswers(previous=>[...previous,answer]);setQuestion('');
    }catch(e){if(n!==generation.current)return;setMessages([]);setAnswers([]);
      setError(e instanceof ApiError && e.status===422 ? 'La discussion dépasse les limites autorisées. Commencez une nouvelle discussion avec une question plus courte.' : e instanceof ApiError && e.status===503 ? 'Discussion indisponible : contexte non fiable ou fournisseur indisponible. Aucun nouvel essai automatique.' : apiMessage(e));
    }finally{if(n===generation.current)setLoading(false);}
  }
  return <section className="context-chat" aria-labelledby="chat-title">
    <h2 id="chat-title">Discuter avec ce contexte</h2>
      {!available && !error && <p role="status">Vérification du contexte disponible…</p>}
      {available && <>
        {!available.current && <p className="notice chat-availability">{available.proposed ? 'Compréhension disponible : propositions non confirmées uniquement.' : 'Aucune compréhension utilisable n’est disponible ; le Space peut être vide ou ne contenir que de l’historique.'}</p>}
        <label className="chat-opt-in"><input type="checkbox" checked={includeProposed} disabled={loading} onChange={e=>{reset();setIncludeProposed(e.target.checked);}}/> Inclure explicitement les propositions non confirmées</label>
      </>}
      {answers.map((answer,i)=><article className="chat-turn" key={i} aria-label={'Échange '+(i+1)}>
        <div className="chat-question-message"><h3>Votre question</h3><p className="chat-text">{messages[i*2]?.content}</p></div>
        <div className="chat-answer-message">
        <h3>{answer.model==='qh-mock-extractive/1' ? 'Extraits de démonstration — sans compréhension de la question' : 'Réponse de l’IA'}</h3><p className="small muted">Modèle : {answer.model}</p>
        {answer.references.some(row=>row.validation_state==='proposed') && <p role="note" className="notice">Cette réponse cite des propositions non confirmées. Elle ne constitue pas une validation de la compréhension.</p>}
        {answer.provided_revisions.length>0 && answer.provided_revisions.every(row=>row.validation_state==='proposed') && <p role="note" className="notice">Tout le contexte fourni est proposé et non confirmé. Aucune révision confirmée courante n’a été transmise.</p>}
        <p className="chat-text">{answer.answer}</p>
        {answer.insufficient_context && <p className="notice">Le contexte disponible ne suffit pas à établir une réponse étayée.</p>}
        {answer.partial_coverage && <p className="notice">Couverture partielle : limites de pages ou de taille atteintes. Les éléments absents de cette réponse peuvent exister dans le Space.</p>}
        <details><summary>Sources utilisées ({answer.references.length} références déclarées)</summary>
          <p>Les identités ci-dessous sont vérifiées dans le contexte transmis. Leur pertinence sémantique est déclarée par le modèle, pas validée indépendamment.</p>
          {answer.references.map(row=><Revision key={row.revision_id} row={row}/>)}
          {!answer.references.length && <p>Aucune référence déclarée.</p>}
        </details>
        <details><summary>Contexte fourni et limites ({answer.provided_revisions.length} révisions)</summary>
          <p>Éléments transmis, qui ne sont pas tous nécessairement utilisés. Borne d’entrée : {answer.input_bound} unités estimées (octets UTF-8 + marge), pas un relevé de tokens API. Contexte : {answer.context_bytes} octets.</p>
          {answer.provided_revisions.map(row=><Revision key={row.revision_id} row={row}/>)}
        </details>
        </div>
      </article>)}
      {error && <p role="alert" className="notice error">{error}</p>}
      {loading && <div className="chat-pending"><div className="chat-question-message"><h3>Votre question</h3><p className="chat-text">{question}</p></div><p role="status">Préparation de la réponse…</p></div>}
      <form className="chat-composer" onSubmit={e=>{void submit(e);}}>
        <label htmlFor="chat-question">Votre question sur ce contexte</label>
        <textarea id="chat-question" ref={questionField} value={question} maxLength={4096} onChange={e=>setQuestion(e.target.value)} disabled={loading || !available || messages.length>=8} rows={3} placeholder="Que souhaitez-vous savoir ?"/>
        <div className="actions"><button disabled={loading || !available || !question.trim() || messages.length>=8}>Envoyer la question</button>
          <button type="button" className="secondary" disabled={loading} onClick={reset}>Nouvelle discussion</button></div>
        {messages.length>=8 && <p>Limite de quatre questions atteinte. Commencez une nouvelle discussion dans ce même Space.</p>}
      </form>
      <details className="chat-help"><summary>Fonctionnement et limites</summary>
      <p>Échanges temporaires, distincts de la compréhension conservée. Rien n’est ajouté ni confirmé dans le Context Space.</p>
      <p>La discussion utilise une sélection bornée, sans classement sémantique. Le mode mock restitue des extraits ; Mistral n’est pas activé par la présence d’une clé.</p>
      <p>Les révisions historiques et refusées sont exclues. Changer le choix des propositions efface la discussion temporaire.</p>
      <p className="small muted">La discussion reste uniquement en mémoire dans cet onglet. Fermer, changer de Space ou se déconnecter l’efface. Aucune écriture Understanding.</p>
      </details>
  </section>;
}
