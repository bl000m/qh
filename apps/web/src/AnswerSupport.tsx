import type {ChatAnswer} from './chat';
const labels={dialogue:'Conversation envoyée',canonical:'Éléments cités du Space',mixed:'Conversation et éléments cités du Space',insufficient:'Appui insuffisant'};
export default function AnswerSupport({answer}:{answer:ChatAnswer}){
 return <div className="answer-support" data-support-basis={answer.support_basis}>
  <p>Appui déclaré : <strong>{labels[answer.support_basis]}</strong>.</p>
  {['dialogue','mixed'].includes(answer.support_basis)&&<p role="note">Les informations de cette conversation ne sont pas des connaissances confirmées enregistrées dans QH. Aucune mémorisation automatique.</p>}
 </div>;
}
