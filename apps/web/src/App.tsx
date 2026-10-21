import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import type { FormEvent, ReactNode } from 'react';
import {createPortal} from 'react-dom';
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
import SpaceTabs from './SpaceTabs';
import type {SpaceTab} from './SpaceTabs';
import ContextSettings from './ContextSettings';
import SourcesPanel from './SourcesPanel';
import type {ChatAnswer} from './chat';
import {drafts} from './drafts';
import SessionExpired from './SessionExpired';

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
function Detail({id,api,origin,breadcrumbHost,ownerId}:{id:string;api:QhApi;origin?:string;breadcrumbHost:HTMLElement|null;ownerId:string}){
 const [space,setSpace]=useState<ContextSpace|null>(null),[error,setError]=useState(''),[refresh,setRefresh]=useState(0);
 const [tab,setTab]=useState<SpaceTab>('Discussion'),[addRequest,setAddRequest]=useState(0),[renameRequest,setRenameRequest]=useState(0),[draftRequest,setDraftRequest]=useState<{id:number;text:string}>();
 const [contentVersion,setContentVersion]=useState(0);
 const [answers,setAnswers]=useState<ChatAnswer[]>([]),[sourceIndex,setSourceIndex]=useState<number|null>(null),[understandingVersion,setUnderstandingVersion]=useState(0),[enrichedRevision,setEnrichedRevision]=useState<{id:string;open:number}|null>(null);
 const organization=useOrganization(api,space!==null),openEvent=useRef(crypto.randomUUID());
 const from=organization.value?.domains.find(d=>d.id===(origin??organization.value?.primary_domains[id])&&organization.value?.memberships[id]?.includes(d.id));
 const title=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{if(space)title.current?.focus();},[space]);
 useEffect(()=>{let active=true;setSpace(null);setError('');api.get(id).then(value=>{if(active){drafts.enter(ownerId,id);setSpace(value);void api.opened(id,openEvent.current).catch(()=>{});}}).catch(e=>{if(active)setError(apiMessage(e));});return()=>{active=false;};},[id,api,refresh,ownerId]);
 const answersChanged=useCallback((next:ChatAnswer[])=>setAnswers(next),[]);
 const openProposal=useCallback((revision:string)=>{setEnrichedRevision(previous=>({id:revision,open:(previous?.open??0)+1}));setTab('Éléments');},[]);
 function starter(text:string){setTab('Discussion');setDraftRequest(previous=>({id:(previous?.id??0)+1,text}));}
 const breadcrumb=<nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span>{space&&from&&<><Link to={domainPath(from.id)}>{from.name}</Link><span aria-hidden="true"> / </span></>}<span aria-current="page">{space?.name??'Context Space'}</span></nav>;
 return <section className="context-page">{breadcrumbHost?createPortal(breadcrumb,breadcrumbHost):breadcrumb}
 {error?<><Notice error>{error}</Notice><button onClick={()=>setRefresh(v=>v+1)}>Réessayer</button></>:!space?<Notice>Chargement du Context Space…</Notice>:<article className="detail definitive-space">
 <header className="space-heading"><Orb/><div className="space-title"><div className="space-name-line"><h1 ref={title} tabIndex={-1}>{space.name}</h1><button type="button" className="edit-space-shortcut" aria-label="Modifier le Space" title="Modifier le Space" disabled={!organization.value||organization.busy} onClick={()=>{setTab('Paramètres');setRenameRequest(n=>n+1);}}><Icon name="edit"/></button></div>{organization.value?.space_descriptions?.[space.id]&&<p className="space-description">{organization.value.space_descriptions[space.id]}</p>}<div className="space-domain-anchor"><span className="domain-anchor-label"><Icon name="folder"/>Domaines</span><div className="space-domain-pills">{organization.value?.domains.filter(d=>organization.value?.memberships[space.id]?.includes(d.id)).map((d,i)=><Link key={d.id} to={domainPath(d.id)} label={'Domaine : '+d.name} className={'domain-pill domain-tone-'+i%4}>{d.name}</Link>)}{organization.value&&!organization.value.memberships[space.id]?.length&&<span className="domain-unclassified">Non classé</span>}</div><SpaceActions space={space} state={organization} label="Gérer"/></div></div></header>
 <SpaceTabs value={tab} onChange={setTab}/>
 <Chat ownerId={ownerId} onExploreContext={()=>setTab('Éléments')} key={'chat:'+space.id+':'+understandingVersion} api={api} scope={space.id} tab={tab} addRequest={addRequest} draftRequest={draftRequest} onAnswersChange={answersChanged} onOpenProposal={openProposal} refreshKey={contentVersion} onContextSaved={()=>setContentVersion(v=>v+1)}/>
 <section hidden={tab!=='Éléments'} role="tabpanel" id="space-panel-1" aria-labelledby="space-tab-1" className="space-tab-content elements-panel"><div className="section-heading"><h2>Éléments</h2><button type="button" className="secondary" onClick={()=>setAddRequest(n=>n+1)}><Icon name="sources"/>Ajouter un élément</button></div>
 <details className="element-section"><summary><span className="card-icon"><Icon name="sources"/></span><span><strong>Sources</strong><small>Éléments cités dans les réponses</small></span></summary><div className="element-content">{answers.length?answers.map((answer,i)=><button key={i} className="secondary" type="button" onClick={()=>setSourceIndex(i)}>Sources de la réponse {i+1} · {answer.references.length} éléments cités</button>):<p>Les sources citées apparaîtront ici après une réponse. Les sources conservées sont aussi accessibles depuis chaque élément de compréhension.</p>}</div></details>
 <UnderstandingExplorer refreshKey={contentVersion} spaceName={space.name} onAdd={()=>setAddRequest(n=>n+1)} standalone key={'understanding:'+space.id+':'+(enrichedRevision?.open??'')} initialRevision={enrichedRevision?.id} api={api} scope={space.id} onChanged={()=>setUnderstandingVersion(n=>n+1)}/>
 <details className="element-section"><summary><span className="card-icon"><Icon name="info"/></span><span><strong>Détails du contexte</strong><small>Métadonnées du Space</small></span></summary><div className="element-content"><Metadata space={space}/></div></details></section>
 <section hidden={tab!=='Conseils'} role="tabpanel" id="space-panel-3" aria-labelledby="space-tab-3" className="space-tab-content advice-panel"><h2>Conseils</h2><div className="advice-grid">{[['Faire le point','Préparer un point sur la situation actuelle.','sources','Peux-tu m’aider à faire le point sur ce contexte à partir des éléments disponibles ?'],['Clarifier les priorités','Mettre mes objectifs en perspective.','advice','Peux-tu m’aider à clarifier mes priorités et les questions qui restent ouvertes dans ce contexte ?'],['Préparer la prochaine discussion','Choisir les questions utiles à poser.','discussion','Quelles questions pourrions-nous aborder lors de notre prochaine discussion sur ce contexte ?']].map(([name,description,icon,text])=><button type="button" className="advice-card" key={name} onClick={()=>starter(text)}><span className="card-icon"><Icon name={icon as 'sources'|'advice'|'discussion'}/></span><span><strong>{name}</strong><small>{description}</small></span><span className="advice-chevron" aria-hidden="true">›</span></button>)}</div><p className="advice-note muted">Choisissez un point de départ, puis adaptez votre question avant de l’envoyer.</p></section>
 <section hidden={tab!=='Paramètres'} role="tabpanel" id="space-panel-4" aria-labelledby="space-tab-4" className="space-tab-content context-settings"><ContextSettings visible={tab==='Paramètres'} renameRequest={renameRequest} space={space} api={api} state={organization} onChanged={setSpace}/></section>
 {sourceIndex!==null&&answers[sourceIndex]&&<SourcesPanel answer={answers[sourceIndex]} index={sourceIndex} onClose={()=>setSourceIndex(null)}/>}
 </article>}</section>;
}
function Environment({api,logout,breadcrumbHost}:{api:QhApi;logout:()=>void;breadcrumbHost:HTMLElement|null}) {
  const path = usePath();
  const [recent, setRecent] = useState<ContextSpace | null>(null);
  const [identity, setIdentity] = useState('');
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true; setError('');
    api.me().then(id => { if (active) {drafts.verifyOwner(id);setIdentity(id);} }).catch(reason => { if (active) setError(apiMessage(reason)); });
    return () => { active = false; };
  }, [api, refresh]);
  useEffect(()=>{if(identity&&parseRoute(path).kind!=='space')drafts.logout();},[identity,path]);
  if (error) return <><Notice error>{error}</Notice><button className="secondary" onClick={() => setRefresh(v => v + 1)}>Réessayer</button></>;
  if (!identity) return <Notice>Vérification de votre identité QH…</Notice>;
  const route=parseRoute(path);
  return <>
    {route.kind==='home'||route.kind==='domain'||route.kind==='collection'?<Spaces key={path} api={api} recent={recent} onCreated={setRecent} domain={route.kind==='domain'?route.id:route.kind==='collection'?route.domain:null} collection={route.kind==='collection'}/>:route.kind==='space'?<Detail key={route.id} id={route.id} origin={route.origin} api={api} breadcrumbHost={breadcrumbHost} ownerId={identity}/>:route.kind==='settings'?<Settings api={api} identity={identity} logout={logout}/>:<><Notice error>Cette page est introuvable.</Notice><Link to="/">Mon environnement</Link></>}


  </>;
}
function Settings({api,identity,logout}:{api:QhApi;identity:string;logout:()=>void}){
 const state=useOrganization(api),heading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{heading.current?.focus();},[]);
 return <section className="global-settings"><nav aria-label="Fil d’Ariane" className="breadcrumbs"><Link to="/">Mon environnement</Link><span aria-hidden="true"> / </span><span aria-current="page">Paramètres</span></nav><h1 tabIndex={-1} ref={heading}>Paramètres</h1><div className="settings-stack">
 <section className="product-card"><span className="card-icon"><Icon name="user"/></span><div><h2>Profil</h2><p className="muted">Votre environnement personnel QH.</p><dl className="setting-rows"><div><dt>Accès</dt><dd>Compte personnel</dd></div></dl></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="sources"/></span><div><h2>Mes domaines</h2><p className="muted">Organisez vos espaces par domaine.</p><OrganizationEditor state={state}/></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="settings"/></span><div><h2>Préférences</h2><p className="muted">Présentation actuelle de votre environnement.</p><dl className="setting-rows"><div><dt>Langue de l’interface</dt><dd>Français</dd></div><div><dt>Apparence</dt><dd>Clair</dd></div></dl></div></section>
 <section className="product-card"><span className="card-icon"><Icon name="info"/></span><div><h2>Compte QH</h2><p className="muted">Gérez votre connexion.</p><details><summary>Informations du compte</summary><p>Identité QH : <span className="account-identifier">{identity}</span></p></details><button type="button" className="text-button" onClick={logout}><Icon name="logout"/>Se déconnecter</button></div></section>
 </div></section>;
}
export default function App({ session }: { session: BrowserSession }) {
  const state = useSyncExternalStore(session.subscribe, session.snapshot);
  const path=usePath(),spacePage=parseRoute(path).kind==='space';
  const [breadcrumbHost,setBreadcrumbHost]=useState<HTMLDivElement|null>(null);
  const retained=state==='authenticated'||state==='expired'&&!!session.preserveDrafts;
  const api = useMemo(() => new QhApi(session.readyToken??session.accessToken, session.expire), [session]);
  useEffect(() => { void session.initialize(); }, [session]);
  const logout=useCallback(()=>{drafts.logout();let credential:string|null=null;try{credential=session.accessToken();}catch{/* Expired credentials cannot revoke. */}api.revokeSessionsBeforeLogout(credential);void session.logout();},[api,session]);
  return <div className={'app-shell'+(retained?' signed-in':'')}><a className="skip-link" href="#main-content" onClick={event=>{event.preventDefault();document.getElementById('main-content')?.focus();}}>Aller au contenu</a><header className="topbar"><a href="/" aria-label="QH — accueil" onClick={event => { event.preventDefault(); navigate('/'); }} className={'brand'+(spacePage?' space-brand':'')}>{spacePage?<><Orb/><strong>QH</strong></>:<><img src={qhLogo} width={876} height={768} alt="QH"/><span>Votre contexte, sous votre contrôle.</span></>}</a><div className="header-breadcrumbs" ref={setBreadcrumbHost}/>
    {state === 'authenticated' && <nav className="account-navigation" aria-label="Compte QH"><Link to="/settings" label="Paramètres de mon environnement"><Icon name="settings"/>Paramètres</Link><button aria-label="Se déconnecter" title="Se déconnecter" className="secondary logout-button" onClick={logout}><Icon name="logout"/></button></nav>}</header>
    <main id="main-content" tabIndex={-1}>
      {state === 'authenticated'||state==='expired'&&session.preserveDrafts ? <><Environment api={api} logout={logout} breadcrumbHost={breadcrumbHost}/>{state==='expired'&&<SessionExpired session={session}/>}</> : <section className="signin">
        {state === 'starting' ? <Notice>Connexion en cours…</Notice> : <>
          {state === 'expired' && <Notice error>Votre session a expiré. Reconnectez-vous pour continuer.</Notice>}
          {state === 'error' && <Notice error>La connexion n’a pas abouti. Veuillez recommencer.</Notice>}
          {state === 'signed-out' && <Notice>Vous êtes déconnecté de QH.</Notice>}
          <div className="welcome-heading"><DecorativeBubble/><div><h1>Bienvenue dans votre environnement QH</h1><p>Connectez-vous pour accéder à vos Context Spaces.</p></div></div>
          <button onClick={() => { void session.login(); }}>Se connecter</button></>}
      </section>}
    </main><footer>QH — Environnement souverain de contexte</footer></div>;
}
