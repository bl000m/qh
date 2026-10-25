import type {SharedPayload} from '@qh/shared';
export default function SharedItems({payload}:{payload:SharedPayload}){
 return <ul className="shared-items">{payload.items.map(item=><li key={item.reference}><article>
   <span className="item-state">{item.validation_state==='proposed'?'Proposé, non confirmé':'Élément confirmé'}</span>
   <p>{item.text}</p><small>{item.reference} · Provenance autorisée : {item.sources.join(', ')||'aucune citation affichée'}</small>
   {item.citations?.map((citation,i)=><blockquote key={i}>{citation.quote}<small>{citation.source}{citation.redacted?' · Citation masquée':''}</small></blockquote>)}
 </article></li>)}</ul>;
}
