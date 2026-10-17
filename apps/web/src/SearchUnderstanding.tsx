import { Revision } from './Revision';
import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, apiMessage } from './api';
import type { QhApi } from './api';
import { descriptorValues } from './understanding';
import type { CanonicalRevision, RevisionQuery, RevisionView } from './understanding';

const views: { value: RevisionView; label: string }[] = [
  {value:'current',label:'Confirmé'}, {value:'proposed',label:'Propositions'}, {value:'history',label:'Historique'}
];
export default function SearchUnderstanding({ api, scope }: { api: QhApi; scope: string }) {
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
    {!selection && <p className="notice" role="status">Choisissez une vue et un sélecteur pour consulter la compréhension. Cette recherche complète la navigation du contexte.</p>}
    {loading && <p className="notice" role="status">Chargement des révisions…</p>}
    {error && <><p role="alert" className="notice error">{error}</p><button className="secondary" onClick={() => setRefresh(n => n + 1)}>Réessayer la recherche</button></>}
    {selection && matches && !loading && !error && items.length === 0 && <p className="notice" role="status">{view === 'current' ? 'Aucune révision confirmée courante ne correspond à cette recherche.' : 'Aucune révision ne correspond à cette recherche.'}</p>}
    <div aria-live="polite" aria-busy={loading}>{matches && !loading && items.map(row => <Revision key={row.revision_id} row={row} />)}</div>
    {next && matches && !error && <button className="secondary" disabled={loading} onClick={() => { if(selection) void load({...selection,context_ids:[scope],view,after_revision_id:next},true,generation.current); }}>Afficher les révisions suivantes</button>}
  </section>;
}
