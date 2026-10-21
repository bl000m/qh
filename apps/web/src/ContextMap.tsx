import {useRef} from 'react';
import type {QhApi} from './api';
import {usePage} from './Understanding';
import {thematicGroups} from './thematic';
import {Orb,Icon} from './Ui';

// Bounded graph-verified pages only; legacy descriptors never become themes.
export default function ContextMap({api,scope,refreshKey,onExplore,onAdd,onTheme}:{api:QhApi;scope:string;refreshKey:number;onExplore?:()=>void;onAdd:()=>void;onTheme?:(value:string)=>void}){
 const current=usePage(api,scope,{view:'current',limit:20,descriptor_dimension:'thematic',include_tentative:true},false,refreshKey,refreshKey>0?16:false);
 const pending=usePage(api,scope,{view:'proposed',limit:20,descriptor_dimension:'thematic',include_tentative:true,latest_pending:true},false,refreshKey,refreshKey>0?16:false);
 const error=current.error||pending.error,loading=current.loading||pending.loading;
 const groups=error||loading?[]:thematicGroups([...new Map([...current.rows,...pending.rows].map(r=>[r.revision_id,r])).values()]);
 const shown=groups.slice(0,6),partial=!!current.next||!!pending.next||groups.length>6;
 const root=useRef<HTMLElement>(null),center=useRef<HTMLButtonElement>(null);
 function leave(action:()=>void){if(document.fullscreenElement===root.current)void document.exitFullscreen().then(action,action);else action();}
 return <section className="space-context-map" aria-label="Carte thématique de ce contexte" ref={root}>
  <div className="map-tools"><button type="button" className="secondary" aria-label="Agrandir la carte" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void root.current?.requestFullscreen?.().catch(()=>{});}}><Icon name="expand"/></button><button type="button" className="secondary" aria-label="Ajouter un élément" title="Ajouter un élément depuis la carte" onClick={()=>leave(onAdd)}><Icon name="plus"/></button><button type="button" className="secondary" aria-label="Recentrer sur ce contexte" onClick={()=>{center.current?.focus();center.current?.scrollIntoView({block:'nearest',inline:'nearest'});}}><Icon name="target"/></button></div>
  <div className="context-orbit">
   {shown.length>0&&<svg className="orbit-connections" viewBox="0 0 880 370" preserveAspectRatio="none" aria-hidden="true">{shown.map((group,i)=><path className={'orbit-line tone-'+i} key={group.value} d={'M440 185 C'+(i%2?'555 185 470':'325 185 410')+' '+([65,65,185,185,305,305][i])+' '+(i%2?565:315)+' '+[65,65,185,185,305,305][i]}/>)}</svg>}
   {shown.map((group,i)=><button type="button" key={group.value} className={'context-orbit-node orbit-node-'+i+' tone-'+i} onClick={()=>leave(()=>onTheme?.(group.value))}><span className="orbit-node-icon"><Icon name="understanding"/></span><span className="orbit-node-copy"><strong>{group.value}</strong><span className="orbit-node-state">{group.assignments.some(d=>d.review_state==='proposed')?'Affectations à vérifier':'Affectations acceptées'}{group.assignments.some(d=>d.certainty==='tentative')?' · attribution incertaine':''}</span></span><span className="node-chevron" aria-hidden="true">›</span></button>)}
   <button type="button" className="context-center" ref={center} aria-label="Explorer les éléments de ce contexte" onClick={()=>leave(()=>onExplore?.())}><Orb/></button>
   {loading&&<p className="orbit-feedback" role="status">Chargement des thèmes…</p>}
   {error&&<div className="orbit-feedback"><p role="alert">Les thèmes sont indisponibles. Ce résultat ne signifie pas que le Space est vide.</p><button type="button" className="text-button" onClick={()=>{current.retry();pending.retry();}}>Réessayer</button></div>}
   {!loading&&!error&&shown.length===0&&<div className="orbit-feedback"><p>Aucun regroupement thématique vérifié n’est disponible dans cette vue.</p><button type="button" className="text-button" onClick={()=>leave(()=>onExplore?.())}>Voir les éléments</button></div>}
  </div>{shown.length>0&&<p className="map-coverage">Thèmes des éléments de cette page.{partial?' Vue partielle ; d’autres éléments restent accessibles dans Éléments.':' Courant et dernières propositions affichés.'}</p>}
 </section>;
}
export function UsefulActions(){return <section className="useful-actions"><header><span className="card-icon"><Icon name="advice"/></span><h2>Actions utiles</h2></header><div>{([['share','Partager une projection'],['import','Importer une conversation'],['users','Partager ce Context Space']] as const).map(([icon,title])=><button type="button" disabled title="Fonction non encore disponible" className="secondary" key={title}><Icon name={icon}/><span>{title}</span><span aria-hidden="true">›</span></button>)}</div></section>;}
