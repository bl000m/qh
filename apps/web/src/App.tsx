import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
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
import {Orb,Icon} from './Ui';
import SpaceActions from './SpaceActions';
import SpaceEditor from './SpaceEditor';
import SourcesPanel from './SourcesPanel';
import type {ChatAnswer} from './chat';

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
    // Initial metadata hydration must not reset a page the owner already paginated.
    if(!organization.value&&!organization.error){setLoading(true);return;}
    if(domain&&domain!=='unclassified'&&!activeDomain){setLoading(false);setItems([]);return;}
    setLoading(true); setError('');setNext(null);
    api.resumeSpaces(sort,domain).then(page => { if (active) { setItems(page.items); setNext(page.next_after_id); } })
      .catch(reason => { if (active) setError(apiMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, refresh,sort,domain,organization.value?.version,organization.error,activeDomain?.id]);
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
    <div className={home?'environment-topline':'domain-heading'}>{!home&&domain!=='unclassified'&&<Orb tone={(organization.value?.domains.findIndex(d=>d.id===domain)??0)*34}/>}<h1 id="environment-title" ref={title} tabIndex={-1}>{heading}</h1></div>
    {activeDomain?.description&&<p>{activeDomain.description}</p>}
    {home&&<EnvironmentDomains state={organization}/>}
    <section className={home?"resume-shelf":"space-collection"} aria-labelledby="spaces-title"><div className="section-heading spaces-section-heading"><h2 id="spaces-title">{home?'Reprendre mes Context Spaces':'Context Spaces'}</h2><div className="actions">{(home||items.length>0)&&<label className="sort-control"><span className="sr-only">Ordre des Spaces</span><select value={sort} onChange={e=>setSort(e.target.value as 'recent'|'used')}><option value="recent">Récemment ouverts</option><option value="used">Les plus utilisés</option></select></label>}{home&&<Link to="/spaces">Tous les Spaces <span aria-hidden="true">›</span></Link>}{(home||items.length>0||form)&&<button onClick={() => { setPrimaryDomain(activeDomain?.id??'');setForm(true); setSuccess(''); }} disabled={form}>Créer un Context Space</button>}</div></div>
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
    {home&&<CarouselArrows target={spacesCarousel} name="Spaces"/>}
    <ul ref={spacesCarousel} className={home?"space-grid horizontal-carousel":"space-grid"} aria-label={home?"Carrousel Reprendre mes Context Spaces":"Context Spaces de cette vue"}>{items.map(item => <li key={item.id} className="space-card">
      <Link to={spacePath(item.id,activeDomain?.id)} label={item.name} title={item.name}>
        <Orb tone={items.indexOf(item)*42+105}/><h3>{item.name}</h3>{!home&&<span className="open-space">Ouvrir <span aria-hidden="true">›</span></span>}

      </Link>
      {collection&&<div className="space-card-caption"><SpaceMemberships space={item} state={organization}/><details><summary>Métadonnées du Space</summary><p>{item.name}</p><Metadata space={item} /></details></div>}

    </li>)}</ul>
    {next && <button className="secondary" disabled={loading} onClick={() => { void more(); }}>Afficher plus</button>}</section>
  </section>;
}
function Detail({ id, api, origin }: { id: string; api: QhApi; origin?:string }) {
  const [space,setSpace]=useState<ContextSpace|null>(null);
  const organization=useOrganization(api,space!==null);
  const [answers,setAnswers]=useState<ChatAnswer[]>([]),[sourceIndex,setSourceIndex]=useState<number|null>(null),[supportOpen,setSupportOpen]=useState(false);
  const supportTitle=useRef<HTMLHeadingElement>(null),supportToggle=useRef<HTMLButtonElement>(null);
  const answersChanged=useCallback((next:ChatAnswer[])=>{setAnswers(next);if(!next.length)setSourceIndex(null);},[]);
  useEffect(()=>{if(supportOpen)supportTitle.current?.focus();},[supportOpen]);
  const from=organization.value?.domains.find(d=>d.id===origin&&organization.value?.memberships[id]?.includes(d.id));
  const [understandingVersion,setUnderstandingVersion]=useState(0);
  const [enrichedRevision,setEnrichedRevision]=useState<{id:string;open:number}|null>(null);
  const openEvent=useRef(crypto.randomUUID());
  const [openingError,setOpeningError]=useState('');
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
      space ? <article className={'detail'+(supportOpen?' support-open':'')}><header className="space-heading"><Orb tone={110}/><div className="space-title"><h1 ref={title} tabIndex={-1}>{space.name}</h1>{organization.value?.space_descriptions?.[space.id]&&<p>{organization.value.space_descriptions[space.id]}</p>}</div><SpaceActions space={space} state={organization}><SpaceEditor space={space} api={api} state={organization} onChanged={setSpace}/></SpaceActions></header>{openingError&&<p role="status">{openingError}</p>}

      <div className="space-workspace"><Chat key={'chat:'+space.id+':'+understandingVersion} api={api} scope={space.id} onAnswersChange={answersChanged} onOpenProposal={id=>{setEnrichedRevision(previous=>({id,open:(previous?.open??0)+1}));setSupportOpen(true);}}/><button ref={supportToggle} className="secondary support-toggle" aria-expanded={supportOpen} onClick={()=>{setSupportOpen(v=>!v);if(supportOpen)requestAnimationFrame(()=>supportToggle.current?.focus());}}><Icon name="understanding"/>{supportOpen?'Revenir à la discussion':'Sources & compréhension'}</button><aside className="support-panel" aria-labelledby="support-title"><header><Icon name="understanding"/><div><h2 id="support-title" ref={supportTitle} tabIndex={-1}>Sources & compréhension</h2><p>Sources utilisées et état de la compréhension.</p></div></header>
      <details className="support-sources support-section"><summary><Icon name="sources"/><span>Sources<small>Éléments cités dans les réponses</small></span></summary>{answers.length?answers.map((answer,i)=><button key={i} type="button" className="secondary" onClick={()=>setSourceIndex(i)}>Sources de la réponse {i+1} · {answer.references.length} éléments cités</button>):<p>Les sources d’une réponse apparaîtront ici après votre question.</p>}</details>
      <UnderstandingExplorer key={'understanding:'+space.id+':'+(enrichedRevision?.open??'')} initialRevision={enrichedRevision?.id} api={api} scope={space.id} onChanged={()=>setUnderstandingVersion(n=>n+1)} />
      <details className="space-metadata support-section"><summary><Icon name="info"/><span>Détails du contexte<small>Métadonnées du Space</small></span></summary><Metadata space={space}/></details>
      </aside></div>{sourceIndex!==null&&answers[sourceIndex]&&<SourcesPanel answer={answers[sourceIndex]} index={sourceIndex} onClose={()=>setSourceIndex(null)}/>}</article> :
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
function Reconnect({session}:{session:BrowserSession}){
 const dialog=useRef<HTMLDialogElement>(null);const [copied,setCopied]=useState('');
 useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close();},[]);
 return <dialog ref={dialog} className="space-action-dialog" onCancel={e=>e.preventDefault()} aria-labelledby="reconnect-title"><h2 id="reconnect-title">Reconnectez-vous pour continuer</h2><p>La session a expiré. Vos brouillons restent dans cet onglet. La reconnexion quitte cette page : copiez les textes que vous souhaitez conserver avant de continuer.</p><button type="button" onClick={()=>{const text=[...document.querySelectorAll<HTMLTextAreaElement>('textarea')].map(n=>n.value).filter(Boolean).join('\n\n');void navigator.clipboard.writeText(text).then(()=>setCopied('Brouillons copiés.'),()=>setCopied('Copie indisponible. Sélectionnez et copiez votre texte avant de vous reconnecter.'));}}>Copier mes brouillons</button><p role="status">{copied}</p><button onClick={()=>{void session.login();}}>Se reconnecter</button><button className="secondary" onClick={()=>{void session.logout();}}>Se déconnecter et effacer les brouillons</button></dialog>;
}
export default function App({ session }: { session: BrowserSession }) {
  const state = useSyncExternalStore(session.subscribe, session.snapshot);
  const api = useMemo(() => new QhApi(session.readyToken??session.accessToken, session.expire), [session]);
  useEffect(() => { void session.initialize(); }, [session]);
  return <div className={'app-shell'+(state==='authenticated'?' signed-in':'')}><a className="skip-link" href="#main-content" onClick={event=>{event.preventDefault();document.getElementById('main-content')?.focus();}}>Aller au contenu</a><header className="topbar"><a href="/" aria-label="QH — accueil" onClick={event => { event.preventDefault(); navigate('/'); }} className="brand"><img src={qhLogo} width={876} height={768} alt="QH"/><span>Votre contexte, sous votre contrôle.</span></a>
    {state === 'authenticated' && <nav className="account-navigation" aria-label="Compte QH"><Link to="/settings" label="Paramètres de mon environnement"><Icon name="settings"/>Paramètres</Link><button aria-label="Se déconnecter" title="Se déconnecter" className="secondary logout-button" onClick={() => { let credential:string|null=null;try{credential=session.accessToken();}catch{/* Expired credentials cannot revoke a grant. */}api.revokeSessionsBeforeLogout(credential); void session.logout(); }}><Icon name="logout"/></button></nav>}</header>
    <main id="main-content" tabIndex={-1}>
      {state === 'authenticated'||state==='expired'&&session.preserveDrafts ? <><Environment api={api}/>{state==='expired'&&<Reconnect session={session}/>}</> : <section className="signin">
        {state === 'starting' ? <Notice>Connexion en cours…</Notice> : <>
          {state === 'expired' && <Notice error>Votre session a expiré. Reconnectez-vous pour continuer.</Notice>}
          {state === 'error' && <Notice error>La connexion n’a pas abouti. Veuillez recommencer.</Notice>}
          {state === 'signed-out' && <Notice>Vous êtes déconnecté de QH.</Notice>}
          <div className="welcome-heading"><DecorativeBubble/><div><h1>Bienvenue dans votre environnement QH</h1><p>Connectez-vous pour accéder à vos Context Spaces.</p></div></div>
          <button onClick={() => { void session.login(); }}>Se connecter</button></>}
      </section>}
    </main><footer>QH — Environnement souverain de contexte</footer></div>;
}
