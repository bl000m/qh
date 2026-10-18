import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import type { FormEvent, MouseEvent, ReactNode } from 'react';
import { apiMessage, QhApi, validName } from './api';
import type { ContextSpace } from './api';
import type { BrowserSession } from './auth';
import Understanding from './Understanding';
import Chat from './Chat';
import { navigate, usePath } from './navigation';

function Link({ to, children }: { to: string; children: ReactNode }) {
  function follow(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault(); navigate(to);
    }
  }
  return <a href={to} onClick={follow}>{children}</a>;
}
function Notice({ error, children }: { error?: boolean; children: ReactNode }) {
  return <p className={error ? 'notice error' : 'notice'} role={error ? 'alert' : 'status'}>{children}</p>;
}
function Metadata({ space }: { space: ContextSpace }) {
  return <dl className="metadata">
    <div><dt>Identifiant</dt><dd>{space.id}</dd></div>
    <div><dt>Statut</dt><dd>{space.status === 'active' ? 'Actif' : space.status}</dd></div>
    <div><dt>Création</dt><dd><time dateTime={space.created_at}>{new Date(space.created_at).toLocaleString('fr-FR')}</time></dd></div>
    <div><dt>Dernière modification</dt><dd><time dateTime={space.updated_at}>{new Date(space.updated_at).toLocaleString('fr-FR')}</time></dd></div>
  </dl>;
}
function Spaces({ api, recent, onCreated }: { api: QhApi; recent: ContextSpace | null; onCreated: (space: ContextSpace) => void }) {
  const [items, setItems] = useState<ContextSpace[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [form, setForm] = useState(false);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const [success, setSuccess] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api.list().then(page => { if (active) { setItems(page.items); setNext(page.next_after_id); } })
      .catch(reason => { if (active) setError(apiMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, refresh]);
  async function more() {
    if (!next || loading) return;
    setLoading(true); setError('');
    try {
      const page = await api.list(next);
      setItems(previous => [...previous, ...page.items.filter(item => !previous.some(p => p.id === item.id))]);
      setNext(page.next_after_id);
    } catch (reason) { setError(apiMessage(reason)); } finally { setLoading(false); }
  }
  async function create(event: FormEvent) {
    event.preventDefault(); if (creating) return;
    setCreateError(''); setSuccess('');
    if (!validName(name)) { setCreateError('Saisissez un nom de 1 à 256 caractères, non vide.'); return; }
    setCreating(true);
    try {
      const created = await api.create(name);
      onCreated(created);
      setSuccess('Context Space créé : ' + created.name); setName(''); setForm(false);
      setRefresh(value => value + 1);
    } catch (reason) { setCreateError(apiMessage(reason)); } finally { setCreating(false); }
  }
  return <section aria-labelledby="spaces-title">
    <div className="section-heading"><div><p className="eyebrow">Votre espace personnel</p><h2 id="spaces-title">Mes Context Spaces</h2></div>
      <button onClick={() => { setForm(true); setSuccess(''); }} disabled={form}>Créer un Context Space</button></div>
    {form && <form className="create-panel" onSubmit={event => { void create(event); }}>
      <label htmlFor="space-name">Nom du Context Space</label>
      <p id="name-help" className="muted">Un nom qui vous aide à retrouver ce contexte. 256 caractères maximum.</p>
      <input id="space-name" autoFocus value={name} onChange={event => setName(event.target.value)} aria-describedby="name-help" required disabled={creating} />
      {createError && <Notice error>{createError}</Notice>}
      <div className="actions"><button type="submit" disabled={creating}>{creating ? 'Création…' : 'Créer'}</button>
        <button className="secondary" type="button" disabled={creating} onClick={() => setForm(false)}>Annuler</button></div>
    </form>}
    {success && <Notice>{success}</Notice>}
    {error && <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>}
    {loading && <Notice>Chargement des Context Spaces…</Notice>}
    {!loading && !error && items.length === 0 && !recent && <div className="empty"><h3>Votre premier contexte commence ici.</h3><p>Vous n’avez pas encore de Context Space. Créez-en un pour commencer.</p></div>}
    <ul className="space-grid">{(recent ? [recent, ...items.filter(item => item.id !== recent.id)] : items).map(item => <li key={item.id} className="space-card"><p className="eyebrow">Context Space</p>{recent?.id === item.id && <p className="muted">Créé récemment</p>}<h3><Link to={'/context-spaces/' + item.id}>{item.name}</Link></h3><Metadata space={item} /></li>)}</ul>
    {next && <button className="secondary" disabled={loading} onClick={() => { void more(); }}>Afficher plus</button>}
  </section>;
}
function Detail({ id, api }: { id: string; api: QhApi }) {
  const [space, setSpace] = useState<ContextSpace | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true; setSpace(null); setError('');
    api.get(id).then(value => { if (active) setSpace(value); })
      .catch(reason => { if (active) setError(apiMessage(reason)); });
    return () => { active = false; };
  }, [id, api, refresh]);
  return <section><Link to="/">← Mes Context Spaces</Link>
    {error ? <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></> :
      space ? <article className="detail"><p className="eyebrow">Context Space</p><h2>{space.name}</h2><details><summary>Métadonnées du Space</summary><Metadata space={space} /></details><Understanding key={'understanding:'+space.id} api={api} scope={space.id} /><Chat key={'chat:'+space.id} api={api} scope={space.id} /></article> :
        <Notice>Chargement du Context Space…</Notice>}
  </section>;
}
function Environment({ api }: { api: QhApi }) {
  const path = usePath();
  const [recent, setRecent] = useState<ContextSpace | null>(null);
  const [identity, setIdentity] = useState('');
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true; setError('');
    api.me().then(id => { if (active) setIdentity(id); }).catch(reason => { if (active) setError(apiMessage(reason)); });
    return () => { active = false; };
  }, [api, refresh]);
  if (error) return <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>;
  if (!identity) return <Notice>Vérification de votre identité QH…</Notice>;
  const match = /^\/context-spaces\/([^/]+)$/.exec(path);
  return <><p className="identity muted">Identité QH : {identity}</p>
    {path === '/' ? <Spaces api={api} recent={recent} onCreated={setRecent} /> : match ? <Detail key={match[1]} id={match[1]} api={api} /> :
      <><Notice error>Cette page est introuvable.</Notice><Link to="/">Mes Context Spaces</Link></>}
  </>;
}
export default function App({ session }: { session: BrowserSession }) {
  const state = useSyncExternalStore(session.subscribe, session.snapshot);
  const api = useMemo(() => new QhApi(session.accessToken, session.expire), [session]);
  useEffect(() => { void session.initialize(); }, [session]);
  return <div className="app-shell"><header className="topbar"><a href="/" aria-label="QH — accueil" onClick={event => { event.preventDefault(); navigate('/'); }} className="brand">QH<span>Votre contexte, sous votre contrôle.</span></a>
    {state === 'authenticated' && <button className="secondary" onClick={() => { void session.logout(); }}>Se déconnecter</button>}</header>
    <main id="main-content"><div className="page-heading"><p className="eyebrow">QH · Environnement personnel</p><h1>Mon environnement</h1><p className="muted">Un lieu pour construire et retrouver vos contextes.</p></div>
      {state === 'authenticated' ? <Environment api={api} /> : <section className="signin">
        {state === 'starting' ? <Notice>Connexion en cours…</Notice> : <>
          {state === 'expired' && <Notice error>Votre session a expiré. Reconnectez-vous pour continuer.</Notice>}
          {state === 'error' && <Notice error>La connexion n’a pas abouti. Veuillez recommencer.</Notice>}
          {state === 'signed-out' && <Notice>Vous êtes déconnecté de QH.</Notice>}
          <h2>Bienvenue dans votre environnement QH</h2><p>Connectez-vous pour accéder à vos Context Spaces.</p>
          <button onClick={() => { void session.login(); }}>Se connecter</button></>}
      </section>}
    </main><footer>QH — Environnement souverain de contexte</footer></div>;
}
