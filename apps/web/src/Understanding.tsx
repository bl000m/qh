import { useEffect, useRef, useState } from 'react';
import { ApiError, apiMessage } from './api';
import type { QhApi } from './api';
import { Revision } from './Revision';
import SearchUnderstanding from './SearchUnderstanding';
import { descriptorAssignment } from './understanding';
import type { BrowseQuery, CanonicalRevision, RevisionView } from './understanding';

const viewNames: Record<RevisionView,string> = {current:'Compréhension confirmée courante',proposed:'Propositions à examiner',history:'Historique complet'};
function status(row:CanonicalRevision) {
  return row.is_current_confirmed ? 'Confirmé courant' : row.validation_state === 'proposed' ? 'Proposé · non confirmé' :
    row.validation_state === 'rejected' ? 'Historique · refusé' : 'Historique · confirmé';
}
function text(row:CanonicalRevision) {return typeof row.content.text==='string' ? row.content.text : 'Élément structuré — ouvrir le contenu';}
function assignments(row:CanonicalRevision) {return (Array.isArray(row.content.descriptors) ? row.content.descriptors : []).flatMap(a=>{const v=descriptorAssignment(a);return v ? [v] : [];});}
function usePage(api:QhApi,scope:string,query:BrowseQuery|null) {
  const [refresh,setRefresh]=useState(0);
  const key=scope+JSON.stringify(query)+refresh;
  const version=useRef(0);
  const [result,setResult]=useState<{key:string;rows:CanonicalRevision[];next:string|null;loading:boolean;error:string}|null>(null);
  const matches=result?.key===key;
  async function load(after?:string,expected=version.current) {
    if (!query) return;
    setResult(previous=>({key,rows:after && previous?.key===key ? previous.rows : [],next:null,loading:true,error:''}));
    try {
      const page=await api.browse(scope,{...query,...(after ? {after_revision_id:after} : {})});
      if(expected!==version.current)return;
      setResult(previous=>({key,rows:after && previous?.key===key ? [...previous.rows,...page.items.filter(r=>!previous.rows.some(p=>p.revision_id===r.revision_id))] : page.items,next:page.next_after_revision_id,loading:false,error:''}));
    } catch(error) {
      if(expected!==version.current)return;
      setResult({key,rows:[],next:null,loading:false,error:error instanceof ApiError && error.status===503 ?
        'Compréhension indisponible : le graphe peut être en attente, désynchronisé ou inaccessible. Ce résultat ne signifie pas que le Space est vide.' : apiMessage(error)});
    }
  }
  useEffect(()=>{const n=++version.current;if(query)void load(undefined,n);else setResult(null);return()=>{version.current++;};},[key,api]);
  return {rows:matches ? result.rows : [],next:matches ? result.next : null,
    loading:!!query && (!matches || result.loading),error:matches ? result.error : '',
    more:()=>{if(matches && result.next && !result.loading)void load(result.next);},retry:()=>setRefresh(n=>n+1)};
}
function Feedback({page}:{page:ReturnType<typeof usePage>}) {
  return <>{page.loading && <p role="status" className="notice">Chargement de la compréhension…</p>}{page.error && <div><p role="alert" className="notice error">{page.error}</p><button className="secondary" onClick={page.retry}>Réessayer la navigation</button></div>}</>;
}
function Cards({rows,onOpen}:{rows:CanonicalRevision[];onOpen:(row:CanonicalRevision)=>void}) {
  return <ul className="understanding-cards">{rows.map(row=><li key={row.revision_id}><button className="understanding-card" onClick={()=>onOpen(row)}>
    <span className={'state-'+row.validation_state}>{status(row)}</span><span className="card-text">{text(row)}</span>
    <span className="small muted">{row.structural_kind} · révision {row.revision_no}{assignments(row).map(a=>' · '+a.value+' ('+a.certainty+')').join('')}</span>
  </button></li>)}</ul>;
}
export default function Understanding({api,scope}:{api:QhApi;scope:string}) {
  const [mode,setMode]=useState<'overview'|'explore'|'detail'>('overview');
  const [filter,setFilter]=useState<BrowseQuery>({view:'current',limit:20});
  const [selected,setSelected]=useState<string|null>(null);
  const overview=mode==='overview';
  const current=usePage(api,scope,overview ? {view:'current',limit:5} : null);
  const proposed=usePage(api,scope,overview ? {view:'proposed',limit:5} : null);
  const history=usePage(api,scope,overview ? {view:'history',limit:1} : null);
  const explored=usePage(api,scope,mode==='explore' ? filter : null);
  const detail=usePage(api,scope,mode==='detail' && selected ? {view:'history',limit:1,revision_id:selected} : null);
  const row=detail.rows[0];
  const revisions=usePage(api,scope,row ? {view:'history',limit:20,item_id:row.item_id} : null);
  const related=usePage(api,scope,row ? {view:'history',limit:20,related_item_id:row.item_id} : null);
  const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{if(mode!=='overview')heading.current?.focus();},[mode,selected]);
  function explore(query:BrowseQuery) {setFilter(query);setMode('explore');setSelected(null);}
  function open(r:CanonicalRevision) {setSelected(r.revision_id);setMode('detail');}
  const groups=[...new Set(explored.rows.flatMap(r=>assignments(r).map(a=>a.value)))].sort();
  // No group or count is inferred from unloaded pages or from natural-language text.
  const overviewFailed=current.error||proposed.error||history.error;
  const overviewLoading=current.loading||proposed.loading||history.loading;
  return <section className="understanding browse-understanding" aria-labelledby="browse-title">
    <h2 id="browse-title" ref={heading} tabIndex={-1}>Compréhension du contexte</h2>
    <p className="muted">Explorez ce que le contexte conserve. Les propositions restent distinctes de la compréhension confirmée.</p>
    <nav className="actions" aria-label="Navigation de la compréhension"><button className="secondary" onClick={()=>{setMode('overview');setSelected(null);}}>Vue d’ensemble</button>
      <button className="secondary" onClick={()=>explore({view:'current',limit:20})}>Parcourir les éléments</button></nav>
    {overview && <section aria-label="Vue d’ensemble"><h3>Aperçu structuré</h3><p className="small muted">Extraits littéraux des éléments conservés, sans interprétation ni synthèse validée. Ordre technique stable, sans classement d’importance.</p>
      {overviewLoading ? <p role="status" className="notice">Chargement de l’aperçu…</p> : overviewFailed ? <><p role="alert" className="notice error">{overviewFailed}</p><button onClick={()=>{current.retry();proposed.retry();history.retry();}}>Réessayer l’aperçu</button></> : <>
        {!history.rows.length && <p role="status" className="empty">Ce Context Space ne contient pas encore d’éléments de compréhension.</p>}
        {([{page:current,view:'current'},{page:proposed,view:'proposed'}] as const).map(({page,view})=><section key={view} aria-label={viewNames[view]}><h4>{viewNames[view]}</h4>
          {page.rows.length ? <><p className="small muted">{page.rows.length} extraits affichés{page.next ? ' · aperçu partiel, d’autres éléments sont disponibles' : ' pour cette vue'}.</p><Cards rows={page.rows} onOpen={open}/></> : <p>{view==='current' ? 'Aucune révision confirmée courante.' : 'Aucune proposition en attente dans cette vue.'}</p>}
          <button className="secondary" onClick={()=>explore({view,limit:20})}>Explorer : {viewNames[view]}</button></section>)}
        {!!history.rows.length && <button className="secondary" onClick={()=>explore({view:'history',limit:20})}>Consulter l’historique complet</button>}
      </>}
    </section>}
    {mode==='explore' && <section aria-label="Explorer les éléments"><h3>{viewNames[filter.view]}</h3><div className="actions">{(Object.keys(viewNames) as RevisionView[]).map(view=><button key={view} className="secondary" aria-pressed={filter.view===view} onClick={()=>explore({...filter,view})}>{viewNames[view]}</button>)}</div>
      <div className="actions exploration-filters"><button className="secondary" onClick={()=>explore({view:filter.view,limit:filter.limit})}>Tous les éléments</button>
        <button className="secondary" onClick={()=>explore({view:filter.view,limit:filter.limit,kind:'entity'})}>Entités canoniques</button>
        <button className="secondary" onClick={()=>explore({view:filter.view,limit:filter.limit,kind:'relation'})}>Relations explicites</button>
        <button className="secondary" onClick={()=>explore({view:filter.view,limit:filter.limit,unclassified:true})}>Sans descripteur reconnu</button></div>
      <label>Éléments par page <select value={filter.limit} onChange={e=>explore({...filter,limit:Number(e.target.value)})}><option value={5}>5</option><option value={20}>20</option><option value={50}>50</option></select></label>
      {filter.descriptor!==undefined && <p>Descripteur exact : <strong>{filter.descriptor}</strong> · tentative inclus : {filter.include_tentative ? 'oui' : 'non'}</p>}
      <Feedback page={explored}/>
      {!explored.loading && !explored.error && <><section aria-label="Descripteurs de la page"><h4>Descripteurs dans les pages affichées</h4><p className="small muted">Regroupements locaux aux éléments chargés ; ni liste globale ni comptes du Space. Les pages suivantes peuvent révéler d’autres significations.</p><div className="actions">{groups.map(value=><button className="secondary" key={value} onClick={()=>explore({view:filter.view,limit:filter.limit,descriptor:value,include_tentative:true})}>{value}</button>)}</div><p className="small muted">Ces liens incluent les attributions asserted et tentative ; leur certitude reste affichée sur chaque élément.</p></section>
        {!explored.rows.length && <p role="status">Aucun élément dans cette vue avec ces filtres. Consultez aussi les propositions et l’historique.</p>}
        <Cards rows={explored.rows} onOpen={open}/></>}
      {explored.next && <button disabled={explored.loading} onClick={explored.more}>Afficher les éléments suivants</button>}
    </section>}
    {mode==='detail' && <section aria-label="Détail de l’élément"><Feedback page={detail}/>{!detail.loading && !detail.error && !row && <p>Cette révision n’est pas disponible dans ce Space.</p>}
      {row && !detail.loading && !detail.error && <><Revision row={row} onAnchor={id=>setSelected(id)}/>
        <details><summary>Révisions de cet élément</summary><section aria-label="Révisions de cet élément"><Feedback page={revisions}/>{!revisions.error && !revisions.loading && <Cards rows={revisions.rows} onOpen={open}/>}{revisions.next && <button onClick={revisions.more}>Autres révisions</button>}</section></details>
        <details><summary>Relations conservées avec cet élément</summary><p className="small muted">Relations explicites de l’historique, avec leur propre état et leurs ancrages exacts.</p><Feedback page={related}/>{!related.loading && !related.error && <>{!related.rows.length && <p>Aucune relation explicite dans cette page.</p>}<Cards rows={related.rows} onOpen={open}/></>}{related.next && <button onClick={related.more}>Autres relations</button>}</details>
      </>}
    </section>}
    <details className="secondary-search"><summary>Rechercher dans ce contexte</summary><section aria-label="Recherche complémentaire"><SearchUnderstanding api={api} scope={scope}/></section></details>
  </section>;
}
