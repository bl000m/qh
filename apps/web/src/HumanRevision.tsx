import {qualifiedAssignments} from './thematic';
import {Revision} from './Revision';
import {descriptorAssignment,recognizedCitations} from './understanding';
import type {CanonicalRevision,Json} from './understanding';

const labels:Record<string,string>={decision:'Décision déclarée',hypothesis:'Hypothèse',open_question:'Question ouverte',intention:'Intention déclarée',reversible_pause:'Pause réversible',stated_by:'Attribution déclarée'};
export function meaning(row:CanonicalRevision):string {
 if(row.structural_kind==='entity')return 'Entité';
 if(row.structural_kind==='relation')return 'Relation explicite';
 const values=row.type_version===2?qualifiedAssignments(row).filter(({assignment:d})=>d.dimension==='semantic_role'&&d.review_state!=='rejected'&&d.certainty==='asserted').map(({assignment:d})=>({value:d.value,certainty:d.certainty})):Array.isArray(row.content.descriptors)?row.content.descriptors.map(descriptorAssignment).filter(a=>a!==null&&a.certainty==='asserted'):[];
 return values.map(a=>labels[a!.value]).find(Boolean)||'Élément de compréhension';
}
export function validationLabel(row:CanonicalRevision){
 return row.validation_state==='proposed'?'Proposition non confirmée':row.validation_state==='rejected'?'Révision rejetée':row.is_current_confirmed?'Confirmée actuellement dans QH':'Confirmation historique';
}
const object=(v:Json|undefined):v is Record<string,Json>=>!!v&&typeof v==='object'&&!Array.isArray(v);
export function quotationSpeakers(row:CanonicalRevision):string[]{
 const speakers=new Set<string>();
 for(const citation of recognizedCitations(row)){
  const source=row.provenance.find(s=>s.source_revision_id===citation.source_revision_id);
  if(!citation.turn_id||!Array.isArray(source?.origin.turns))continue;
  const turns=source.origin.turns.filter(t=>object(t)&&t.turn_id===citation.turn_id&&typeof t.speaker==='string');
  if(turns.length===1&&object(turns[0])&&typeof turns[0].speaker==='string')speakers.add(turns[0].speaker);
 }
 return [...speakers];
}
export function EpistemicExplanation(){return <details className="epistemic-explanation"><summary>Comprendre les sources et la confirmation</summary><ol>
 <li><strong>Source traçable :</strong> un extrait permet de retrouver l’origine d’une information.</li>
 <li><strong>Interprétation :</strong> une extraction ou une réponse IA peut déformer ou omettre cette information.</li>
 <li><strong>Confirmation dans QH :</strong> l’utilisateur accepte un élément dans sa compréhension ; une hypothèse peut rester une hypothèse.</li>
 <li><strong>Vérité extérieure :</strong> ni une citation exacte ni une confirmation ne garantissent à elles seules que le contenu est vrai dans le monde.</li>
 </ol></details>;}
export function HumanRevision({row,onAnchor,related=[]}:{row:CanonicalRevision;onAnchor?:(id:string)=>void;related?:CanonicalRevision[]}){
 const quotes=recognizedCitations(row),speakers=quotationSpeakers(row);
 const dates=Object.entries(row.temporal).filter(([,value])=>value!==null);
 const dateNames:Record<string,string>={fact_from:'Fait — à partir du',fact_to:'Fait — jusqu’au',valid_from:'Applicabilité — à partir du',valid_to:'Applicabilité — jusqu’au'};
 const endpoint=(id:string)=>{const r=related.find(r=>r.revision_id===id);return r&&typeof r.content.text==='string'?r.content.text:'Élément ancré non inclus dans cette vue';};
 return <article className="human-revision" data-revision-id={row.revision_id} aria-label={meaning(row)+' : '+String(row.content.text??'contenu structuré').slice(0,100)}>
  <div className="human-revision-heading"><span className="badge">{meaning(row)}</span><span className={'state-'+row.validation_state}>{validationLabel(row)}</span></div>
  <p className="claim">{typeof row.content.text==='string'?row.content.text:'Contenu structuré disponible dans les détails.'}</p>
  <p className="small muted">{row.origin_kind==='ai'?'Interprétation issue d’une IA':row.origin_kind==='human'?'Contribution humaine':'Origine déclarée : '+row.origin_kind}. Révision {row.revision_no}{row.based_on_revision_id?' · une version précédente est conservée':''}.</p>
  {speakers.length>0&&<p>Prise de parole dans la source : <strong>{speakers.join(', ')}</strong>. Cela n’attribue pas automatiquement la décision à cette personne.</p>}
  {quotes.length>0?<section aria-label="Extraits d’origine"><h4>Dans la source</h4>{quotes.map((q,i)=><figure key={q.source_revision_id+':'+i}><blockquote>{q.quote}</blockquote><figcaption>Extrait original traçable, distinct de l’interprétation ci-dessus.</figcaption></figure>)}</section>:<p className="small muted">La provenance est conservée ; aucun extrait littéral reconnu n’est disponible dans cette vue.</p>}
  {row.relation&&<section aria-label="Relation lisible"><h4>Relation conservée</h4><p>{endpoint(row.relation.source_revision_id)} → <strong>{labels[row.relation.predicate]??row.relation.predicate}</strong> → {endpoint(row.relation.target_revision_id)}</p>
    {onAnchor&&<div className="actions"><button className="secondary" onClick={()=>onAnchor(row.relation!.source_revision_id)}>Voir la révision source</button><button className="secondary" onClick={()=>onAnchor(row.relation!.target_revision_id)}>Voir la révision cible</button></div>}</section>}
  {dates.length>0&&<dl className="metadata">{dates.map(([key,date])=><div key={key}><dt>{dateNames[key]}</dt><dd>{date}</dd></div>)}</dl>}
  <details className="technical-details"><summary>Détails techniques</summary><p>Identités exactes, descripteurs ouverts et certitude d’attribution, provenance, ancrages et historique canonique.</p><Revision row={row}/><details><summary>Enregistrement canonique complet (JSON)</summary><pre className="json-value">{JSON.stringify(row,null,2)}</pre></details></details>
 </article>;
}
