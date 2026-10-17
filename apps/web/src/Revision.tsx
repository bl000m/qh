import { descriptorAssignment, recognizedCitations } from './understanding';
import type { CanonicalRevision, Json } from './understanding';

function JsonValue({ value }: { value: Json }) { return <pre className="json-value">{JSON.stringify(value,null,2)}</pre>; }
export function Revision({ row, onAnchor }: { row: CanonicalRevision; onAnchor?: (id: string) => void }) {
  const assignments = Array.isArray(row.content.descriptors) ? row.content.descriptors : [];
  const citations = recognizedCitations(row);
  return <article className="revision" aria-label={'Révision ' + row.revision_id}>
    <div className="revision-heading"><span className="badge">{row.structural_kind}</span><strong className={'state-' + row.validation_state}>{row.validation_state}</strong><span>Révision {row.revision_no}</span></div>
    {typeof row.content.text === 'string' ? <p className="claim">{row.content.text}</p> : <JsonValue value={row.content} />}
    <p className="muted">Révision confirmée courante : <strong>{row.is_current_confirmed ? 'oui' : 'non'}</strong> · Origine de l’élément : {row.origin_kind}</p>
    <h4>Descripteurs</h4>
    {assignments.length ? <ul className="assignments">{assignments.map((a,i) => {
      const assignment = descriptorAssignment(a);
      return assignment ? <li key={i}><code>{assignment.value}</code> <span>· attribution : {assignment.certainty}</span></li> : <li key={i}><JsonValue value={a} /></li>;
    })}</ul> : <p className="muted">Aucun descripteur déclaré.</p>}
    <p className="small muted">La certitude d’attribution d’un descripteur ne confirme ni le contenu ni sa véracité.</p>
    {row.relation && <section aria-label="Relation"><h4>Relation</h4><p>Prédicat : <code>{row.relation.predicate}</code></p><dl className="metadata">
      <div><dt>Élément source</dt><dd>{row.relation.source_item_id}</dd></div><div><dt>Révision source</dt><dd>{row.relation.source_revision_id}</dd></div>
      <div><dt>Élément cible</dt><dd>{row.relation.target_item_id}</dd></div><div><dt>Révision cible</dt><dd>{row.relation.target_revision_id}</dd></div>
    </dl>{onAnchor && <div className="actions"><button className="secondary" onClick={() => onAnchor(row.relation!.source_revision_id)}>Voir la révision source</button><button className="secondary" onClick={() => onAnchor(row.relation!.target_revision_id)}>Voir la révision cible</button></div>}</section>}
    <details><summary>Temporalité</summary><dl className="metadata">{([
      ['fact_from','Fait — début'],['fact_to','Fait — fin'],['valid_from','Applicabilité — début'],['valid_to','Applicabilité — fin']
    ] as const).map(([key,label]) => <div key={key}><dt>{label}</dt><dd>{row.temporal[key] ?? 'Non renseigné'}</dd></div>)}</dl>
      <p className="small muted">Les bornes inconnues restent inconnues. Aucun intervalle n’est déduit de la date de création.</p></details>
    <section aria-label="Provenance"><h4>Sources et provenance</h4>
      {row.provenance.length === 0 && <p>Aucune référence de source disponible.</p>}
      {row.provenance.map(source => <div className="source" key={source.source_revision_id}><dl className="metadata">
        <div><dt>Source</dt><dd>{source.source_id}</dd></div><div><dt>Révision de source {source.revision_no}</dt><dd>{source.source_revision_id}</dd></div>
      </dl><details><summary>Origine et locator</summary><JsonValue value={source.origin} /></details>
        {citations.filter(c => c.source_revision_id === source.source_revision_id).map((citation,i) => <figure key={i}>
          <blockquote>{citation.quote}</blockquote><figcaption>Citation littérale QH-8 · positions Unicode [{citation.start}, {citation.end}){citation.turn_id ? ' · tour ' + citation.turn_id : ''}</figcaption>
        </figure>)}
      </div>)}
      <p className="small muted">Un ancrage littéral exact ne prouve pas le soutien sémantique. Le texte intégral de la source n’est pas fourni par cette API.</p>
      {citations.length === 0 && <p className="small muted">Aucune citation QH-8 reconnaissable disponible ; les autres propriétés restent consultables ci-dessous.</p>}
    </section>
    <details><summary>Identité et détails canoniques</summary><dl className="metadata">
      <div><dt>Élément</dt><dd>{row.item_id}</dd></div><div><dt>Révision</dt><dd>{row.revision_id}</dd></div>
      <div><dt>Type enregistré</dt><dd>{row.type_id}/{row.type_version}</dd></div><div><dt>Pointer courant</dt><dd>{row.current_revision_id ?? 'Aucun'}</dd></div>
      <div><dt>Révision précédente</dt><dd>{row.based_on_revision_id ?? 'Aucune'}</dd></div>
      <div><dt>Créée le</dt><dd>{row.created_at}</dd></div><div><dt>Validée par / le</dt><dd>{row.validated_by ?? 'Non renseigné'} / {row.validated_at ?? 'Non renseigné'}</dd></div>
    </dl><h4>Contenu canonique intégral</h4><JsonValue value={row.content} /></details>
  </article>;
}
