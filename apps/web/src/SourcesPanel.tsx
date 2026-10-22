import AnswerSupport from './AnswerSupport';
import {useEffect,useId,useRef} from 'react';
import type {ChatAnswer} from './chat';
import {HumanRevision,EpistemicExplanation} from './HumanRevision';
export default function SourcesPanel({answer,index,onClose}:{answer:ChatAnswer;index:number;onClose:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null),title=useId();
 useEffect(()=>{const node=dialog.current;const opener=document.activeElement as HTMLElement|null;node?.showModal();return()=>{node?.close();if(opener?.isConnected)opener.focus({preventScroll:true});};},[]);
 const ids=new Set(answer.references.map(r=>r.item_id));
 const relations=answer.provided_revisions.filter(r=>r.relation&&(ids.has(r.relation.source_item_id)||ids.has(r.relation.target_item_id))&&!answer.references.some(a=>a.revision_id===r.revision_id));
 return <dialog className="sources-panel" ref={dialog} aria-labelledby={title} onCancel={event=>{event.preventDefault();onClose();}}>
  <header className="sources-panel-header"><div><p className="eyebrow">Réponse {index+1}</p><h2 id={title}>Sources & compréhension</h2></div><button type="button" className="secondary" onClick={onClose} autoFocus>Fermer les sources</button></header>
  <p>{answer.references.length} éléments cités par {answer.model}. Une référence exacte indique ce qui a été cité, pas une validation indépendante du sens.</p>
  <AnswerSupport answer={answer}/><p>Les références sont contrôlées par QH ; la déclaration d’appui ne prouve pas le sens ni la vérité de la réponse.</p>
  <EpistemicExplanation/>
  <section aria-label="Éléments cités dans cette réponse"><h3>Ce que cette réponse cite</h3>{!answer.references.length&&<p>Aucun élément cité. Le contexte peut être insuffisant.</p>}{answer.references.map(r=><HumanRevision key={r.revision_id} row={r} related={answer.provided_revisions}/>)}</section>
  {relations.length>0&&<details><summary>Relations transmises associées ({relations.length})</summary><p>Ces relations étaient disponibles ; le modèle ne les a pas nécessairement citées.</p>{relations.map(r=><HumanRevision key={r.revision_id} row={r} related={answer.provided_revisions}/>)}</details>}
  <details><summary>Contexte fourni et limites ({answer.provided_revisions.length} révisions)</summary><p>Les éléments fournis ne sont pas tous cités. {answer.partial_coverage?'Couverture partielle : d’autres informations peuvent exister.':'Sélection bornée, sans classement de pertinence sémantique.'}</p>{answer.provided_revisions.map(r=><HumanRevision key={r.revision_id} row={r} related={answer.provided_revisions}/>)}<details><summary>Détails techniques de l’envoi</summary><p>Borne d’entrée : {answer.input_bound} unités estimées, pas un relevé de tokens API. Contexte : {answer.context_bytes} octets.</p></details></details>
 </dialog>;
}
