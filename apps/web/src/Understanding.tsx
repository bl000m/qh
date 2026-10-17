import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, apiMessage } from './api';
import type { QhApi } from './api';
import { descriptorValues, recognizedCitations } from './understanding';
import type { CanonicalRevision, Json, RevisionQuery, RevisionView } from './understanding';

const views: { value: RevisionView; label: string }[] = [
  {value:'current',label:'Confirmé'}, {value:'proposed',label:'Propositions'}, {value:'history',label:'Historique'}
];
function JsonValue({ value }: { value: Json }) { return <pre className="json-value">{JSON.stringify(value,null,2)}</pre>; }
function Revision({ row }: { row: CanonicalRevision }) {
  const assignments = Array.isArray(row.content.descriptors) ? row.content.descriptors : [];
  const citations = recognizedCitations(row);
  return <article className="revision" aria-label={'Révision ' + row.revision_id}>
    <div className="revision-heading"><span className="badge">{row.structural_kind}</span><strong className={'state-' + row.validation_state}>{row.validation_state}</strong><span>Révision {row.revision_no}</span></div>
    {typeof row.content.text === 'string' ? <p className="claim">{row.content.text}</p> : <JsonValue value={row.content} />}
    <p className="muted">Révision confirmée courante : <strong>{row.is_current_confirmed ? 'oui' : 'non'}</strong> · Origine de l’élément : {row.origin_kind}</p>
    <h4>Descripteurs</h4>
    {assignments.length ? <ul className="assignments">{assignments.map((a,i) => typeof a === 'object' && a !== null && !Array.isArray(a) && typeof a.value === 'string' ?
      <li key={i}><code>{a.value}</code> <span>· attribution : {String(a.certainty ?? 'non renseignée')}</span></li> : <li key={i}><JsonValue value={a} /></li>)}</ul> : <p className="muted">Aucun descripteur déclaré.</p>}
    <p className="small muted">La certitude d’attribution d’un descripteur ne confirme ni le contenu ni sa véracité.</p>
    {row.relation && <section aria-label="Relation"><h4>Relation</h4><p>Prédicat : <code>{row.relation.predicate}</code></p><dl className="metadata">
      <div><dt>Élément source</dt><dd>{row.relation.source_item_id}</dd></div><div><dt>Révision source</dt><dd>{row.relation.source_revision_id}</dd></div>
      <div><dt>Élément cible</dt><dd>{row.relation.target_item_id}</dd></div><div><dt>Révision cible</dt><dd>{row.relation.target_revision_id}</dd></div>
    </dl></section>}
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
export default function Understanding({ api, scope }: { api: QhApi; scope: string }) {
  const [view, setView] = useState<RevisionView>('current');
  const [selector, setSelector] = useState<'text' | 'descriptors'>('text');
  const [input, setInput] = useState('');
  const [tentative, setTentative] = useState(false);
  const [limit, setLimit] = useState(20);
  const [selection, setSelection] = useState<Omit<RevisionQuery,'view'|'context_ids'|'after_revision_id'> | null>(null);
  const [resultFor, setResultFor] = useState<{view: RevisionView; selection: typeof selection} | null>(null);
  const matches = resultFor?.view === view && resultFor.selection === selection;
  const [items, setItems] = useState<CanonicalRevision[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [invalid, setInvalid] = useState('');
  const [refresh, setRefresh] = useState(0);
  const generation = useRef(0);
  async function load(query: RevisionQuery, append: boolean, version: number) {
    setLoading(true); setError('');
    if (!append) { setItems([]); setNext(null); }
    try {
      const page = await api.query(query);
      if (version !== generation.current) return;
      setItems(previous => append ? [...previous,...page.items.filter(r => !previous.some(p => p.revision_id === r.revision_id))] : page.items);
      setNext(page.next_after_revision_id); setResultFor({view:query.view,selection});
    } catch (reason) {
      if (version !== generation.current) return;
      // Discard prior pages too: a failed freshness check must never look reliable.
      setItems([]); setNext(null);
      setError(reason instanceof ApiError && reason.status === 503 ?
        'Compréhension indisponible : le graphe peut être en attente, désynchronisé ou inaccessible. Ce résultat ne signifie pas que le Space est vide.' : apiMessage(reason));
    } finally { if (version === generation.current) setLoading(false); }
  }
  useEffect(() => {
    const version = ++generation.current;
    if (selection) void load({...selection, context_ids:[scope], view},false,version);
    return () => { generation.current++; };
  }, [scope, api, view, selection, refresh]); // The submitted selection is immutable across pages/views.
  function submit(event: FormEvent) {
    event.preventDefault(); setInvalid('');
    const values = descriptorValues(input);
    if (selector === 'text' && (!input.trim() || [...input].length > 4096) ||
        selector === 'descriptors' && (values.length === 0 || values.length > 100)) {
      setInvalid(selector === 'text' ? 'Saisissez un texte non vide (4096 caractères maximum).' : 'Saisissez de 1 à 100 descripteurs, un par ligne.'); return;
    }
    setSelection(selector === 'text' ? {text:input,limit} : {descriptors:values,include_tentative:tentative,limit});
  }
  return <section className="understanding" aria-labelledby="understanding-title"><h2 id="understanding-title">Compréhension du contexte</h2>
    <p className="muted">Consultez les révisions conservées. Une proposition IA reste une proposition, même si son descripteur porte « asserted ».</p>
    <div className="view-tabs" role="group" aria-label="Vue des révisions">{views.map(v => <button key={v.value} type="button" className="secondary" aria-pressed={view === v.value} onClick={() => setView(v.value)}>{v.label}</button>)}</div>
    <form onSubmit={submit} className="query-panel"><fieldset><legend>Rechercher par</legend>
      <label><input type="radio" name="selector" checked={selector === 'text'} onChange={() => {setSelector('text'); setInput(''); setTentative(false);}} /> Texte</label>
      <label><input type="radio" name="selector" checked={selector === 'descriptors'} onChange={() => {setSelector('descriptors'); setInput('');}} /> Descripteurs</label>
    </fieldset><label htmlFor="query-input">{selector === 'text' ? 'Texte à rechercher' : 'Descripteurs exacts, un par ligne'}</label>
      <textarea id="query-input" rows={3} value={input} onChange={event => setInput(event.target.value)} aria-describedby="query-help" />
      <p id="query-help" className="small muted">{selector === 'text' ? 'Recherche de sous-chaîne, sans classement sémantique.' : 'Correspondance avec au moins un descripteur. Casse et espaces sont significatifs ; aucun vocabulaire imposé.'}</p>
      <label className="check"><input type="checkbox" checked={tentative} disabled={selector !== 'descriptors'} onChange={event => setTentative(event.target.checked)} /> Inclure les attributions tentative</label>
      <label className="page-size">Résultats par page <select value={limit} onChange={event => setLimit(Number(event.target.value))}><option value={5}>5</option><option value={20}>20</option><option value={50}>50</option></select></label>
      {invalid && <p role="alert" className="notice error">{invalid}</p>}<button type="submit">Rechercher</button>
    </form>
    {!selection && <p className="notice" role="status">Choisissez une vue et un sélecteur pour consulter la compréhension. L’API ne fournit pas de liste complète sans recherche.</p>}
    {loading && <p className="notice" role="status">Chargement des révisions…</p>}
    {error && <><p role="alert" className="notice error">{error}</p><button className="secondary" onClick={() => setRefresh(n => n + 1)}>Réessayer la recherche</button></>}
    {selection && matches && !loading && !error && items.length === 0 && <p className="notice" role="status">{view === 'current' ? 'Aucune révision confirmée courante ne correspond à cette recherche.' : 'Aucune révision ne correspond à cette recherche.'}</p>}
    <div aria-live="polite" aria-busy={loading}>{matches && !loading && items.map(row => <Revision key={row.revision_id} row={row} />)}</div>
    {next && matches && !error && <button className="secondary" disabled={loading} onClick={() => { if(selection) void load({...selection,context_ids:[scope],view,after_revision_id:next},true,generation.current); }}>Afficher les révisions suivantes</button>}
  </section>;
}
