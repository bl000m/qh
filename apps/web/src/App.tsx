import ContextSpaceWorkspace from './ContextSpaceWorkspace';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import {createPortal} from 'react-dom';
import { apiMessage, QhApi, validName } from './api';
import type { ContextSpace } from './api';
import type { BrowserSession } from './auth';
import EnvironmentDomains,{useOrganization,SpaceMemberships,OrganizationEditor,CarouselArrows} from './EnvironmentDomains';
import { navigate, usePath, domainPath, spacePath, parseRoute } from './navigation';
import Link from './NavLink';
import qhLogo from './brand/qh-logo.png';
import {Orb,Icon} from './Ui';
import ContextSettings from './ContextSettings';
import {drafts} from './drafts';
import SessionExpired from './SessionExpired';
import SharingControl from './SharingControl';
import {Modal} from './SpaceActions';
import Loading from './Loading';
import PublicPages, {isPublicPath} from './PublicPages';
import EnvironmentHome from './EnvironmentHome';
import SessionLoading, {SessionFailure} from './SessionLoading';
import {useApplicationSession} from './application-session';
import type {Organization} from './environment';

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
function Spaces({ api, domain = null, collection = false,breadcrumbHost,initialOrganization }: { api: QhApi; domain?: string|null; collection?: boolean;breadcrumbHost:HTMLElement|null;initialOrganization?:Organization }) {
  const organization=useOrganization(api,true,initialOrganization);
  const home=!domain&&!collection;
  const activeDomain=organization.value?.domains.find(d=>d.id===domain);
  const heading=home?'Mon environnement':activeDomain?.name??(domain==='unclassified'?'Non classés':domain?'Domaine':'Tous les Context Spaces');
  const title=useRef<HTMLHeadingElement>(null),domainMenu=useRef<HTMLDetailsElement>(null);
  const breadcrumb=!home?<nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">{heading}</span></nav>:null;
  const breadcrumbs=breadcrumb&&breadcrumbHost?createPortal(breadcrumb,breadcrumbHost):breadcrumb;
  useEffect(()=>{if(home||organization.value)title.current?.focus();},[home,activeDomain?.id,domain,home&&!!organization.value]);
  const [sort,setSort]=useState<'recent'|'used'>('recent');
  const [primaryDomain,setPrimaryDomain]=useState('');
  const spacesCarousel=useRef<HTMLUListElement>(null);
  const [items, setItems] = useState<ContextSpace[]>([]);
  const selection=JSON.stringify([domain,sort]);
  const currentSelection=useRef(selection);
  currentSelection.current=selection;
  const [loadedSelection,setLoadedSelection]=useState('');
  const visibleItems=loadedSelection===selection?items:[];
  const [next, setNext] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const collectionLoading=loading||loadedSelection!==selection;
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [form, setForm] = useState(false);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');
  const organizationVersion=useRef<number>();
  useEffect(()=>{
    const version=organization.value?.version;
    if(version===undefined)return;
    if(organizationVersion.current!==undefined&&organizationVersion.current!==version)setRefresh(n=>n+1);
    organizationVersion.current=version;
  },[organization.value?.version]);
  useEffect(() => {
    if(home)return;
    let active = true;
    setLoading(true); setError('');setNext(null);
    api.resumeSpaces(sort,domain).then(page => { if (active) { setItems(page.items); setLoadedSelection(selection); setNext(page.next_after_id); } })
      .catch(reason => { if (active) {setItems([]);setLoadedSelection(selection);setError(apiMessage(reason));} })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, refresh,sort,domain,selection,home]);
  useEffect(()=>{setForm(false);setCreateError('');setName('');},[domain,collection]);
  if(home&&!organization.value)return organization.error?<><Notice error>{organization.error}</Notice><button className="secondary" onClick={organization.reload}>Réessayer</button></>:<Loading label="Chargement de ton organisation…"/>;
  if(home)return <EnvironmentHome state={organization} headingRef={title}/>;
  async function more() {
    if (!next || loading) return;
    setLoading(true); setError('');
    try {
      const page = await api.resumeSpaces(sort,domain,next);
      if(currentSelection.current!==selection)return;
      setItems(previous => [...previous, ...page.items.filter(item => !previous.some(p => p.id === item.id))]);
      setNext(page.next_after_id);
    } catch (reason) { if(currentSelection.current===selection)setError(apiMessage(reason)); } finally { if(currentSelection.current===selection)setLoading(false); }
  }
  async function create(event: FormEvent) {
    event.preventDefault(); if (creating) return;
    setCreateError('');
    if (!validName(name)) { setCreateError('Saisis un nom de 1 à 256 caractères, non vide.'); return; }
    setCreating(true);
    try {
      const created = await api.createOrganized(name,primaryDomain);
      navigate(spacePath(created.id,primaryDomain));
    } catch (reason) { setCreateError(apiMessage(reason)); } finally { setCreating(false); }
  }
  if(domain&&domain!=='unclassified'&&!organization.value)return <section className="domain-page">{breadcrumbs}<div className="domain-heading"><h1>Domaine</h1></div>{organization.error?<><Notice error>{organization.error}</Notice><button onClick={organization.reload}>Réessayer</button></>:<Loading label="Chargement du domaine…"/>}</section>;
  if(domain&&domain!=='unclassified'&&organization.value&&!activeDomain)return <section><Link to="/">Mon environnement</Link><Notice error>Ce domaine est introuvable ou inaccessible.</Notice></section>;
  return <section className={home?'environment-home':'domain-page'} aria-labelledby="environment-title">
    {breadcrumbs}
    <div className={home?'environment-topline':'domain-heading'}>{!home&&domain!=='unclassified'&&<Orb tone={(organization.value?.domains.findIndex(d=>d.id===domain)??0)*34}/>}<h1 id="environment-title" ref={title} tabIndex={-1}>{heading}</h1></div>
    {activeDomain?.description&&<p>{activeDomain.description}</p>}
    {home&&<EnvironmentDomains state={organization}/>}
    <section className={home?"resume-shelf":"space-collection"} aria-labelledby="spaces-title"><div className="section-heading spaces-section-heading"><h2 id="spaces-title">{home?'Mes Context Spaces':'Context Spaces'}</h2><div className="actions">{(home||visibleItems.length>0)&&<label className="sort-control"><span className="sr-only">Ordre des Spaces</span><select value={sort} onChange={e=>setSort(e.target.value as 'recent'|'used')}><option value="recent">Récemment ouverts</option><option value="used">Les plus utilisés</option></select></label>}{home&&<Link to="/spaces">Tous les Spaces <span aria-hidden="true">›</span></Link>}{(home||visibleItems.length>0||form)&&<button onClick={() => { setPrimaryDomain(activeDomain?.id??'');setForm(true); }} disabled={form}>Créer un Context Space</button>}</div></div>
    {form && <Modal title="Créer un Context Space" className="create-space-dialog" onClose={()=>{if(!creating)setForm(false);}}><form onSubmit={event => { void create(event); }}>
      <label htmlFor="space-name">Nom du Context Space</label>
      <p id="name-help" className="muted">Un nom qui t’aide à retrouver ce contexte. 256 caractères maximum.</p>
      <input id="space-name" autoFocus value={name} maxLength={256} onChange={event => setName(event.target.value)} aria-describedby="name-help" required disabled={creating} />
      {activeDomain?<p className="small muted">Domaine : {activeDomain.name}</p>:<><label htmlFor="space-primary-domain">Domaine principal</label><select id="space-primary-domain" required value={primaryDomain} disabled={creating||!organization.value} onChange={e=>setPrimaryDomain(e.target.value)}><option value="">Choisir un domaine</option>{organization.value?.domains.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></>}
      {createError && <Notice error>{createError}</Notice>}
      <div className="actions"><button type="submit" disabled={creating||!primaryDomain}>{creating ? 'Création…' : 'Créer et ouvrir'}</button>
        <button className="secondary" type="button" disabled={creating} onClick={() => setForm(false)}>Annuler</button></div>
    </form></Modal>}
    {!form&&createError&&<Notice error>{createError}</Notice>}
    {error && <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>}
    {collectionLoading && <Loading label="Chargement des Context Spaces…"/>}
    {!collectionLoading && !error && visibleItems.length===0 && <div className="empty compact-empty"><h3>{activeDomain?'Ce domaine est encore vide.':domain==='unclassified'?'Tous tes Spaces sont organisés.':'Ton premier contexte commence ici.'}</h3>{domain!=='unclassified'&&<button onClick={()=>{setPrimaryDomain(activeDomain?.id??'');setForm(true);}}>Créer mon premier Context Space</button>}</div>}
    {home&&<CarouselArrows target={spacesCarousel} name="Spaces"/>}
    <ul ref={spacesCarousel} className={home?"space-grid horizontal-carousel":"space-grid"} aria-label={home?"Carrousel Mes Context Spaces":"Context Spaces de cette vue"}>{visibleItems.map(item => <li key={item.id} className="space-card">
      <Link to={spacePath(item.id,activeDomain?.id)} label={item.name} title={item.name} onIntent={()=>api.prefetchWorkspace(item.id)}>
        <Orb tone={visibleItems.indexOf(item)*42+105}/><h3>{item.name}</h3>{!home&&<span className="open-space">Ouvrir <span aria-hidden="true">›</span></span>}

      </Link>
      {collection&&<div className="space-card-caption"><SpaceMemberships space={item} state={organization}/><details><summary>Métadonnées du Space</summary><p>{item.name}</p><Metadata space={item} /></details></div>}

    </li>)}</ul>
    {loadedSelection===selection && next && <button className="secondary" disabled={loading} onClick={() => { void more(); }}>Afficher plus</button>}</section>
  </section>;
}
function Detail({id,api,origin,breadcrumbHost,ownerId}:{id:string;api:QhApi;origin?:string;breadcrumbHost:HTMLElement|null;ownerId:string}){
 const [space,setSpace]=useState<ContextSpace|null>(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
 const [renameRequest,setRenameRequest]=useState(0);
 const [workspaceLoaded,setWorkspaceLoaded]=useState(false);
 const heading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{if(space)heading.current?.focus();},[space]);
 const organization=useOrganization(api,workspaceLoaded),openEvent=useRef(crypto.randomUUID());
 const from=organization.value?.domains.find(d=>d.id===(origin??organization.value?.primary_domains[id])&&organization.value?.memberships[id]?.includes(d.id));
 useEffect(()=>{
  let active=true;setSpace(null);setError('');setWorkspaceLoaded(false);
  // Start independent content I/O immediately; fresh metadata still authorizes
  // entry before any prefetched content is rendered.
  const completed=()=>{if(active)setWorkspaceLoaded(true);};
  void api.workspace(id).then(completed,completed);
  api.get(id).then(value=>{if(active){drafts.enter(ownerId,id);setSpace(value);void api.opened(id,openEvent.current).catch(()=>{});}}).catch(e=>{if(active)setError(apiMessage(e));});
  return()=>{active=false;};
 },[id,api,refresh,ownerId]);
 const breadcrumb=<nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span>{space&&from&&<><Link to={domainPath(from.id)}>{from.name}</Link><span aria-hidden="true"> / </span></>}<span aria-current="page">{space?.name??'Context Space'}</span></nav>;
 return <section className="context-page">{breadcrumbHost?createPortal(breadcrumb,breadcrumbHost):breadcrumb}
 {error?<><Notice error>{error}</Notice><button onClick={()=>setRefresh(v=>v+1)}>Réessayer</button></>:!space?<article className="detail definitive-space"><section className="context-space-v02"><header className="context-space-tools"><h1>Context Space</h1><div className="actions"><button className="secondary" disabled>Compréhension</button><button className="secondary" disabled>Partager</button><button className="secondary" disabled>Paramètres</button></div></header><div className="context-space-workspace"><section className="workspace-discussion" aria-busy="true"><div className="workspace-log"><Loading label="Chargement du Context Space…"/></div><div className="workspace-composer"><label className="sr-only" htmlFor="context-loading-message">Ton message</label><textarea id="context-loading-message" rows={3} disabled placeholder="Ajoute une information ou pose une question…"/><div className="workspace-composer-actions"><button disabled>Envoyer</button></div></div></section></div></section></article>:<article className="detail definitive-space">
 <ContextSpaceWorkspace key={space.id} api={api} scope={space.id} name={space.name} settingsRequest={renameRequest}
 heading={<div className="space-title"><div className="space-name-line"><h1 ref={heading} tabIndex={-1}>{space.name}</h1><button type="button" className="edit-space-shortcut" aria-label="Renommer le Space" disabled={!organization.value||organization.busy} onClick={()=>setRenameRequest(n=>n+1)}><Icon name="edit"/></button></div></div>}
 sharingContent={<SharingControl key={space.id} api={api} scope={space.id} name={space.name} label="Partager" primary/>}
 settingsContent={<ContextSettings visible parentDomainId={from?.id} renameRequest={renameRequest} space={space} api={api} state={organization} onChanged={setSpace}/>}/>

 </article>}</section>;
}
function Environment({api,logout,breadcrumbHost,identity,initialOrganization}:{api:QhApi;logout:()=>void;breadcrumbHost:HTMLElement|null;identity:string;initialOrganization?:Organization}) {
  const path = usePath();
  const seed = useRef(initialOrganization);
  useEffect(()=>{seed.current=undefined;},[]);
  useEffect(()=>{if(identity&&parseRoute(path).kind!=='space')drafts.logout();},[identity,path]);
  const route=parseRoute(path);
  return <>
    {route.kind==='home'||route.kind==='domain'||route.kind==='collection'?<Spaces api={api} breadcrumbHost={breadcrumbHost} initialOrganization={seed.current} domain={route.kind==='domain'?route.id:route.kind==='collection'?route.domain:null} collection={route.kind==='collection'}/>:route.kind==='space'?<Detail key={route.id} id={route.id} origin={route.origin} api={api} breadcrumbHost={breadcrumbHost} ownerId={identity}/>:route.kind==='settings'?<Settings api={api} identity={identity} logout={logout}/>:<><Notice error>Cette page est introuvable.</Notice><Link to="/">Mon environnement</Link></>}


  </>;
}
function Settings({api,identity,logout}:{api:QhApi;identity:string;logout:()=>void}){
 const state=useOrganization(api),heading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{heading.current?.focus();},[]);
 return <section className="global-settings"><nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">Paramètres</span></nav><h1 tabIndex={-1} ref={heading}>Paramètres</h1><div className="settings-stack">
 <section className="product-card"><span className="card-icon"><Icon name="user"/></span><div><h2>Profil</h2><p className="muted">Ton environnement personnel QH.</p><dl className="setting-rows"><div><dt>Accès</dt><dd>Compte personnel</dd></div></dl></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="sources"/></span><div><h2>Mes domaines</h2><p className="muted">Organise tes espaces par domaine.</p><OrganizationEditor state={state}/></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="settings"/></span><div><h2>Préférences</h2><p className="muted">Présentation actuelle de ton environnement.</p><dl className="setting-rows"><div><dt>Langue de l’interface</dt><dd>Français</dd></div><div><dt>Apparence</dt><dd>Clair</dd></div></dl></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="info"/></span><div><h2>Compte QH</h2><p className="muted">Gère ta connexion.</p><details><summary>Informations du compte</summary><p>Identité QH : <span className="account-identifier">{identity}</span></p></details><button type="button" className="text-button" onClick={logout}><Icon name="logout"/>Se déconnecter</button></div></section>
 </div></section>;
}
export default function App({ session }: { session: BrowserSession }) {
  const path = usePath();
  const [breadcrumbHost,setBreadcrumbHost]=useState<HTMLDivElement|null>(null);
  const api = useMemo(() => new QhApi(session.readyToken??session.accessToken, session.expire), [session]);
  const view=useApplicationSession(session,api),state=view.state;
  const retained=view.phase==='authenticated';
  const logout=useCallback(()=>{drafts.logout();let credential:string|null=null;try{credential=session.accessToken();}catch{/* Expired credentials cannot revoke. */}api.revokeSessionsBeforeLogout(credential);void session.logout();},[api,session]);
  if(view.phase==='initializing')return <SessionLoading/>;
  if(view.phase==='error')return <SessionFailure expired={state==='expired'} message={view.error} retry={view.error?view.retry:()=>{void session.login();}}/>;
  if(isPublicPath(path)||view.phase==='unauthenticated')return <PublicPages path={path} session={session} state={state}/>;
  return <div className={'app-shell'+(retained?' signed-in':'')}><a className="skip-link" href="#main-content" onClick={event=>{event.preventDefault();document.getElementById('main-content')?.focus();}}>Aller au contenu</a><header className="topbar"><a href="/" aria-label="QH — accueil" onClick={event => { event.preventDefault(); navigate('/'); }} className="brand"><img src={qhLogo} width={876} height={768} alt="QH"/><span>Ton contexte, sous ton contrôle.</span></a><div className="header-breadcrumbs" ref={setBreadcrumbHost}/>
    {state === 'authenticated' && <nav className="account-navigation" aria-label="Compte QH"><Link to="/settings" label="Paramètres de mon environnement"><Icon name="settings"/>Paramètres</Link><button aria-label="Se déconnecter" title="Se déconnecter" className="secondary logout-button" onClick={logout}><Icon name="logout"/></button></nav>}</header>
    <main id="main-content" tabIndex={-1}>
      <Environment api={api} logout={logout} breadcrumbHost={breadcrumbHost} identity={view.bootstrap!.identity} initialOrganization={view.bootstrap!.organization}/>{state==='expired'&&<SessionExpired session={session}/>}
    </main><footer>QH — Environnement souverain de contexte</footer></div>;
}
