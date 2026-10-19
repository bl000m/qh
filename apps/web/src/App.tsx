import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import type { FormEvent, MouseEvent, ReactNode } from 'react';
import { apiMessage, QhApi, validName } from './api';
import type { ContextSpace } from './api';
import type { BrowserSession } from './auth';
import Chat from './Chat';
import EnvironmentDomains,{useOrganization,SpaceMemberships} from './EnvironmentDomains';
import UnderstandingExplorer from './UnderstandingExplorer';
import { navigate, usePath } from './navigation';
import qhLogo from './brand/qh-logo.png';
import qhBubble from './brand/qh-bubble.png';
import {spaceTitle} from './presentation';

function DecorativeBubble() {
  return <img className="qh-bubble" src={qhBubble} width={400} height={300} alt="" aria-hidden="true" decoding="async"/>;
}

function Link({ to, children, label, title }: { to: string; children: ReactNode; label?: string; title?: string }) {
  function follow(event: MouseEvent<HTMLAnchorElement>) {
    if (event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault(); navigate(to);
    }
  }
  return <a href={to} onClick={follow} aria-label={label} title={title}>{children}</a>;
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
  const organization=useOrganization(api);
  const [domain,setDomain]=useState<string|null>(null);
  const [sort,setSort]=useState<'recent'|'used'>('recent');
  const [primaryDomain,setPrimaryDomain]=useState('');
  const spacesCarousel=useRef<HTMLUListElement>(null);
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
    api.resumeSpaces(sort,domain).then(page => { if (active) { setItems(page.items); setNext(page.next_after_id); } })
      .catch(reason => { if (active) setError(apiMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, refresh,sort,domain,organization.value?.version]);
  async function more() {
    if (!next || loading) return;
    setLoading(true); setError('');
    try {
      const page = await api.resumeSpaces(sort,domain,next);
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
      const created = await api.createOrganized(name,primaryDomain);
      onCreated(created);
      organization.reload();
      setSuccess('Context Space créé : ' + created.name); setName(''); setForm(false);
      setRefresh(value => value + 1);
    } catch (reason) { setCreateError(apiMessage(reason)); } finally { setCreating(false); }
  }
  return <section aria-labelledby="spaces-title">
    <div className="page-heading environment-heading"><div><p className="eyebrow">QH · Environnement personnel</p><h1>Mon environnement</h1><p className="muted">Retrouvez vos Context Spaces et choisissez celui avec lequel discuter.</p></div><DecorativeBubble/></div>
    <EnvironmentDomains state={organization} selected={domain} onSelect={setDomain} onCreate={()=>{setPrimaryDomain(domain&&domain!=='unclassified'?domain:'');setForm(true);}}/>
    <div className="section-heading"><div><h2 id="spaces-title">Reprendre mes Context Spaces</h2><p className="muted">Vos espaces de compréhension, sous votre contrôle.</p></div>
      <button onClick={() => { setPrimaryDomain(domain&&domain!=='unclassified'?domain:'');setForm(true); setSuccess(''); }} disabled={form}>Créer un Context Space</button></div>
    {form && <form className="create-panel" onSubmit={event => { void create(event); }}>
      <label htmlFor="space-name">Nom du Context Space</label>
      <p id="name-help" className="muted">Un nom qui vous aide à retrouver ce contexte. 256 caractères maximum.</p>
      <input id="space-name" autoFocus value={name} onChange={event => setName(event.target.value)} aria-describedby="name-help" required disabled={creating} />
      <label htmlFor="space-primary-domain">Domaine principal</label><select id="space-primary-domain" required value={primaryDomain} disabled={creating||!organization.value} onChange={e=>setPrimaryDomain(e.target.value)}><option value="">Choisir un domaine</option>{organization.value?.domains.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select><p className="small muted">Vous pourrez ensuite associer ce Space à d’autres domaines.</p>
      {createError && <Notice error>{createError}</Notice>}
      <div className="actions"><button type="submit" disabled={creating||!primaryDomain}>{creating ? 'Création…' : 'Créer'}</button>
        <button className="secondary" type="button" disabled={creating} onClick={() => setForm(false)}>Annuler</button></div>
    </form>}
    {success && <Notice>{success}</Notice>}
    {!form&&createError&&<Notice error>{createError}</Notice>}
    {error && <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>}
    {loading && <Notice>Chargement des Context Spaces…</Notice>}
    {!loading && !error && items.length === 0 && !recent && <div className="empty"><h3>Votre premier contexte commence ici.</h3><p>Vous n’avez pas encore de Context Space. Créez-en un pour commencer.</p></div>}
    <div className="resume-controls"><label>Ordre des Spaces<select value={sort} onChange={e=>setSort(e.target.value as 'recent'|'used')}><option value="recent">Récemment ouverts</option><option value="used">Les plus utilisés</option></select></label><p className="small muted">Basé sur vos ouvertures enregistrées depuis UX V2 ; aucune activité antérieure n’est inventée.</p><div className="carousel-controls" role="group" aria-label="Navigation des Spaces"><button className="secondary" onClick={()=>spacesCarousel.current?.scrollBy({left:-320,behavior:'smooth'})}>Spaces précédents</button><button className="secondary" onClick={()=>spacesCarousel.current?.scrollBy({left:320,behavior:'smooth'})}>Spaces suivants</button></div></div>
    {domain&&!loading&&!items.length&&<div className="empty"><h3>{domain==='unclassified'?'Tous vos Spaces sont organisés.':'Ce domaine attend vos premiers contextes.'}</h3><p>Créez un Space ou affichez tous les domaines pour associer un Space existant.</p></div>}
    <ul ref={spacesCarousel} className="space-grid horizontal-carousel" aria-label="Carrousel Reprendre mes Context Spaces">{items.map(item => <li key={item.id} className="space-card">
      <Link to={'/context-spaces/' + item.id} label={item.name} title={item.name}>
        <h3><span aria-hidden="true">{spaceTitle(item.name)}</span><span className="sr-only">{item.name}</span></h3>
        <div className="space-capsule"><DecorativeBubble/><span className="capsule-action">Ouvrir ce contexte <span aria-hidden="true">↗</span></span></div>
      </Link>
      <div className="space-card-caption"><SpaceMemberships space={item} state={organization}/>{recent?.id === item.id && <p className="muted">Créé récemment</p>}<p className="space-lifecycle">{item.status === 'active' ? 'Space actif' : item.status}</p><p className="small muted">{organization.value?.usage[item.id]?<>{organization.value.usage[item.id].open_count} ouvertures · <time dateTime={organization.value.usage[item.id].last_opened_at}>{new Date(organization.value.usage[item.id].last_opened_at).toLocaleString('fr-FR')}</time></>:'Aucune ouverture enregistrée'}</p><details><summary>Métadonnées du Space</summary><p>{item.name}</p><Metadata space={item} /></details></div>
    </li>)}</ul>
    {next && <button className="secondary" disabled={loading} onClick={() => { void more(); }}>Afficher plus</button>}
  </section>;
}
function Detail({ id, api }: { id: string; api: QhApi }) {
  const [understandingVersion,setUnderstandingVersion]=useState(0);
  const openEvent=useRef(crypto.randomUUID());
  const [openingError,setOpeningError]=useState('');
  useEffect(()=>{void api.get(id).then(()=>api.opened(id,openEvent.current)).catch(()=>setOpeningError('Cette ouverture n’a pas pu être enregistrée dans votre activité.'));},[api,id]);
  const [space, setSpace] = useState<ContextSpace | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (space) title.current?.focus(); }, [space]);
  useEffect(() => {
    let active = true; setSpace(null); setError('');
    api.get(id).then(value => { if (active) setSpace(value); })
      .catch(reason => { if (active) setError(apiMessage(reason)); });
    return () => { active = false; };
  }, [id, api, refresh]);
  return <section><nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">{space?.name ?? 'Context Space'}</span></nav>
    {error ? <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></> :
      space ? <article className="detail"><p className="eyebrow">Context Space</p><h1 ref={title} tabIndex={-1}>{space.name}</h1>{openingError&&<p role="status">{openingError}</p>}<Chat key={'chat:'+space.id+':'+understandingVersion} api={api} scope={space.id} /><UnderstandingExplorer key={'understanding:'+space.id} api={api} scope={space.id} onChanged={()=>setUnderstandingVersion(n=>n+1)} /><details className="space-metadata"><summary>Métadonnées du Space</summary><Metadata space={space} /></details></article> :
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
  return <>
    {path === '/' ? <Spaces api={api} recent={recent} onCreated={setRecent} /> : match ? <Detail key={match[1]} id={match[1]} api={api} /> :
      <><Notice error>Cette page est introuvable.</Notice><Link to="/">Mes Context Spaces</Link></>}
    <details className="identity small muted"><summary>Informations du compte QH</summary><p>Identité QH : {identity}</p></details>
  </>;
}
export default function App({ session }: { session: BrowserSession }) {
  const state = useSyncExternalStore(session.subscribe, session.snapshot);
  const api = useMemo(() => new QhApi(session.accessToken, session.expire), [session]);
  useEffect(() => { void session.initialize(); }, [session]);
  return <div className="app-shell"><a className="skip-link" href="#main-content" onClick={event=>{event.preventDefault();document.getElementById('main-content')?.focus();}}>Aller au contenu</a><header className="topbar"><a href="/" aria-label="QH — accueil" onClick={event => { event.preventDefault(); navigate('/'); }} className="brand"><img src={qhLogo} width={876} height={768} alt="QH"/><span>Votre contexte, sous votre contrôle.</span></a>
    {state === 'authenticated' && <button className="secondary" onClick={() => { api.revokeSessionsBeforeLogout(); void session.logout(); }}>Se déconnecter</button>}</header>
    <main id="main-content" tabIndex={-1}>
      {state === 'authenticated' ? <Environment api={api} /> : <section className="signin">
        {state === 'starting' ? <Notice>Connexion en cours…</Notice> : <>
          {state === 'expired' && <Notice error>Votre session a expiré. Reconnectez-vous pour continuer.</Notice>}
          {state === 'error' && <Notice error>La connexion n’a pas abouti. Veuillez recommencer.</Notice>}
          {state === 'signed-out' && <Notice>Vous êtes déconnecté de QH.</Notice>}
          <div className="welcome-heading"><DecorativeBubble/><div><h1>Bienvenue dans votre environnement QH</h1><p>Connectez-vous pour accéder à vos Context Spaces.</p></div></div>
          <button onClick={() => { void session.login(); }}>Se connecter</button></>}
      </section>}
    </main><footer>QH — Environnement souverain de contexte</footer></div>;
}
