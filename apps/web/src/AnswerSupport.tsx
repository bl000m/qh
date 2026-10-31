import type {ChatAnswer} from './chat';
const labels={general:'Connaissances générales du modèle',dialogue:'Conversation envoyée',canonical:'Éléments cités du Space',mixed:'Conversation et éléments cités du Space',insufficient:'Appui non établi'};
export default function AnswerSupport({answer}:{answer:ChatAnswer}){
 return <div className="answer-support" data-support-basis={answer.support_basis}>
  <p>Appui déclaré : <strong>{labels[answer.support_basis]}</strong>.</p>
  {answer.insufficient_context&&<p className="muted" data-insufficient-context="true">Les éléments disponibles ne suffisent pas à répondre complètement à cette question.</p>}
  {['dialogue','mixed'].includes(answer.support_basis)&&<p role="note">Les informations de cette conversation ne sont pas des connaissances confirmées enregistrées dans QH. Aucune mémorisation automatique.</p>}
 </div>;
}
