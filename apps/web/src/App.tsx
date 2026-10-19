import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { apiMessage, QhApi, validName } from './api';
import type { ContextSpace } from './api';
import type { BrowserSession } from './auth';
import Chat from './Chat';
import EnvironmentDomains,{useOrganization,SpaceMemberships,OrganizationEditor,CarouselArrows} from './EnvironmentDomains';
import UnderstandingExplorer from './UnderstandingExplorer';
import { navigate, usePath, domainPath, spacePath, parseRoute } from './navigation';
import Link from './NavLink';
import qhLogo from './brand/qh-logo.png';
import qhBubble from './brand/qh-bubble.png';
import {spaceTitle} from './presentation';

function DecorativeBubble() {
  return <img className="qh-bubble" src={qhBubble} width={400} height={300} alt="" aria-hidden="true" decoding="async"/>;
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
function Spaces({ api, recent, onCreated, domain = null, collection = false }: { api: QhApi; recent: ContextSpace | null; onCreated: (space: ContextSpace) => void; domain?: string|null; collection?: boolean }) {
  const organization=useOrganization(api);
  const home=!domain&&!collection;
  const activeDomain=organization.value?.domains.find(d=>d.id===domain);
  const heading=home?'Mon environnement':activeDomain?.name??(domain==='unclassified'?'Non classés':'Tous les Context Spaces');
  const title=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{if(home||organization.value)title.current?.focus();},[home,activeDomain?.id,domain]);
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
    if(domain&&domain!=='unclassified'&&!activeDomain){setLoading(false);setItems([]);return;}
    setLoading(true); setError('');setNext(null);
    api.resumeSpaces(sort,domain).then(page => { if (active) { setItems(page.items); setNext(page.next_after_id); } })
      .catch(reason => { if (active) setError(apiMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, refresh,sort,domain,organization.value?.version,activeDomain?.id]);
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
  if(domain&&domain!=='unclassified'&&!organization.value)return <section><Link to="/">Mon environnement</Link>{organization.error?<><Notice error>{organization.error}</Notice><button onClick={organization.reload}>Réessayer</button></>:<Notice>Chargement du domaine…</Notice>}</section>;
  if(domain&&domain!=='unclassified'&&organization.value&&!activeDomain)return <section><Link to="/">Mon environnement</Link><Notice error>Ce domaine est introuvable ou inaccessible.</Notice></section>;
  return <section className={home?'environment-home':'domain-page'} aria-labelledby="environment-title">
    {!home&&<nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">{heading}</span></nav>}
    <div className={home?'environment-topline':'domain-heading'}>{!home&&domain!=='unclassified'&&<DecorativeBubble/>}<h1 id="environment-title" ref={title} tabIndex={-1}>{heading}</h1>{home&&<Link to="/settings" label="Paramètres de mon environnement">Paramètres</Link>}</div>
    {home&&<EnvironmentDomains state={organization}/>}
    <div className="section-heading"><h2 id="spaces-title">{home?'Reprendre mes Context Spaces':'Context Spaces'}</h2><div className="actions">{home&&<Link to="/spaces">Tous les Spaces</Link>}<button className="secondary" onClick={() => { setPrimaryDomain(activeDomain?.id??'');setForm(true); setSuccess(''); }} disabled={form}>Créer un Context Space</button></div></div>
    {form && <form className="create-panel" onSubmit={event => { void create(event); }}>
      <label htmlFor="space-name">Nom du Context Space</label>
      <p id="name-help" className="muted">Un nom qui vous aide à retrouver ce contexte. 256 caractères maximum.</p>
      <input id="space-name" autoFocus value={name} onChange={event => setName(event.target.value)} aria-describedby="name-help" required disabled={creating} />
      <label htmlFor="space-primary-domain">Domaine principal</label><select id="space-primary-domain" required value={primaryDomain} disabled={creating||!organization.value} onChange={e=>setPrimaryDomain(e.target.value)}><option value="">Choisir un domaine</option>{organization.value?.domains.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select><p className="small muted">Vous pourrez ensuite associer ce Space à d’autres domaines.</p>
      {createError && <Notice error>{createError}</Notice>}
      <div className="actions"><button type="submit" disabled={creating||!primaryDomain}>{creating ? 'Création…' : 'Créer'}</button>
        <button className="secondary" type="button" disabled={creating} onClick={() => setForm(false)}>Annuler</button></div>
    </form>}
    {success && <Notice>{success} {recent&&<Link to={spacePath(recent.id,activeDomain?.id)}>Ouvrir ce Space</Link>}</Notice>}
    {!form&&createError&&<Notice error>{createError}</Notice>}
    {error && <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>}
    {loading && <Notice>Chargement des Context Spaces…</Notice>}
    {!loading && !error && items.length===0 && <div className="empty compact-empty"><h3>{activeDomain?'Ce domaine est encore vide.':domain==='unclassified'?'Tous vos Spaces sont organisés.':'Votre premier contexte commence ici.'}</h3>{domain!=='unclassified'&&<button onClick={()=>{setPrimaryDomain(activeDomain?.id??'');setForm(true);}}>Créer mon premier Context Space</button>}</div>}
    {home&&<div className="resume-controls"><label>Ordre des Spaces<select value={sort} onChange={e=>{setItems([]);setSort(e.target.value as 'recent'|'used');}}><option value="recent">Récemment ouverts</option><option value="used">Les plus utilisés</option></select></label><CarouselArrows target={spacesCarousel} name="Spaces"/></div>}
    <ul ref={spacesCarousel} className={home?"space-grid horizontal-carousel":"space-grid"} aria-label={home?"Carrousel Reprendre mes Context Spaces":"Context Spaces de cette vue"}>{items.map(item => <li key={item.id} className="space-card">
      <Link to={spacePath(item.id,activeDomain?.id)} label={item.name} title={item.name}>
        <h3><span aria-hidden="true">{spaceTitle(item.name)}</span><span className="sr-only">{item.name}</span></h3>
        <div className="space-capsule"><DecorativeBubble/><span className="capsule-action">Ouvrir ce contexte <span aria-hidden="true">↗</span></span></div>
      </Link>
      {!home&&<div className="space-card-caption"><SpaceMemberships space={item} state={organization}/><details><summary>Métadonnées du Space</summary><p>{item.name}</p><Metadata space={item} /></details></div>}

    </li>)}</ul>
    {next && <button className="secondary" disabled={loading} onClick={() => { void more(); }}>Afficher plus</button>}
  </section>;
}
function Detail({ id, api, origin }: { id: string; api: QhApi; origin?:string }) {
  const organization=useOrganization(api);
  const from=organization.value?.domains.find(d=>d.id===origin&&organization.value?.memberships[id]?.includes(d.id));
  const [understandingVersion,setUnderstandingVersion]=useState(0);
  const openEvent=useRef(crypto.randomUUID());
  const [openingError,setOpeningError]=useState('');
  const [space, setSpace] = useState<ContextSpace | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (space) title.current?.focus(); }, [space]);
  useEffect(() => {
    let active = true; setSpace(null); setError('');
    api.get(id).then(value => { if (active) {setSpace(value);void api.opened(id,openEvent.current).catch(()=>{if(active)setOpeningError('Cette ouverture n’a pas pu être enregistrée dans votre activité.');});} })
      .catch(reason => { if (active) setError(apiMessage(reason)); });
    return () => { active = false; };
  }, [id, api, refresh]);
  return <section><nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span>{space&&from&&<><Link to={domainPath(from.id)}>{from.name}</Link><span aria-hidden="true"> / </span></>}<span aria-current="page">{space?.name ?? 'Context Space'}</span></nav>
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
  const route=parseRoute(path);
  return <>
    {route.kind==='home'||route.kind==='domain'||route.kind==='collection'?<Spaces key={path} api={api} recent={recent} onCreated={setRecent} domain={route.kind==='domain'?route.id:route.kind==='collection'?route.domain:null} collection={route.kind==='collection'}/>:route.kind==='space'?<Detail key={route.id} id={route.id} origin={route.origin} api={api}/>:route.kind==='settings'?<Settings api={api}/>:<><Notice error>Cette page est introuvable.</Notice><Link to="/">Mon environnement</Link></>}

    <details className="identity small muted"><summary>Informations du compte QH</summary><p>Identité QH : {identity}</p></details>
  </>;
}
function Settings({api}:{api:QhApi}){
 const state=useOrganization(api);const heading=useRef<HTMLHeadingElement>(null);useEffect(()=>{heading.current?.focus();},[]);
 return <section><nav className="breadcrumbs" aria-label="Fil d’Ariane"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">Paramètres</span></nav><h1 tabIndex={-1} ref={heading}>Mon profil & mes préférences</h1><OrganizationEditor state={state}/><div className="secondary-navigation"><Link to="/spaces">Tous les domaines</Link><Link to="/spaces/unclassified">Non classés</Link></div><details><summary>Préférences personnelles</summary><p>Le profil de compréhension personnel et les préférences partagées ne sont pas encore disponibles.</p></details></section>;
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
