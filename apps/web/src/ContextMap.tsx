import {useEffect,useRef,useState} from 'react';
import {ApiError} from './api';
import type {QhApi} from './api';
import {DIMENSIONS} from './uum';
import type {DimensionPresence} from './api';
import {Orb,Icon} from './Ui';

export default function ContextMap({api,scope,refreshKey,onExplore,onAdd,onDimension,showAdd=true}:{api:QhApi;scope:string;refreshKey:number;onExplore?:()=>void;onAdd:()=>void;onDimension?:(value:string)=>void;showAdd?:boolean}){
 const [view,setView]=useState<'current'|'proposed'>('proposed'),[data,setData]=useState<DimensionPresence|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0);
 const visible=data?.context_id===scope&&data.view===view?data:null;
 const root=useRef<HTMLElement>(null),center=useRef<HTMLButtonElement>(null);
 useEffect(()=>{
  let active=true;setData(null);setError(false);
  async function read(){
   const attempts=refreshKey>0?16:1;
   for(let attempt=0;attempt<attempts&&active;attempt++){
    try{const result=await api.dimensionPresence(scope,view);if(active)setData(result);return;}
    catch(error){if(!active)return;if(!(error instanceof ApiError)||error.status!==503||attempt===attempts-1){setError(true);return;}await new Promise(resolve=>setTimeout(resolve,500));}
   }
  }
  void read();return()=>{active=false;};
 },[api,scope,view,refreshKey,retry]);
 function leave(action:()=>void){if(document.fullscreenElement===root.current)void document.exitFullscreen().then(action,action);else action();}
 return <section className="space-context-map" aria-label="Dimensions de compréhension" ref={root}>
  <div className="map-tools"><div className="map-views" role="group" aria-label="État de compréhension"><button type="button" aria-pressed={view==='proposed'} onClick={()=>setView('proposed')}>Propositions</button><button type="button" aria-pressed={view==='current'} onClick={()=>setView('current')}>Compréhension courante</button></div><button type="button" className="secondary" aria-label="Agrandir la carte" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void root.current?.requestFullscreen?.().catch(()=>{});}}><Icon name="expand"/></button>{showAdd&&<button type="button" className="secondary" aria-label="Ajouter un élément" onClick={()=>leave(onAdd)}><Icon name="plus"/></button>}<button type="button" className="secondary" aria-label="Recentrer sur ce contexte" onClick={()=>{center.current?.focus();}}><Icon name="target"/></button></div>
  <div className="context-orbit">
   <button type="button" className="context-center" ref={center} aria-label="Explorer les éléments de ce contexte" onClick={()=>leave(()=>onExplore?.())}><Orb/></button>
   {DIMENSIONS.map(([id,label],i)=><button type="button" key={id} className={'context-orbit-node orbit-node-'+i+' tone-'+i} onClick={()=>leave(()=>onDimension?.(id+':'+view))}><span className="orbit-node-icon"><Icon name="understanding"/></span><span className="orbit-node-copy"><strong>{label}</strong><span className="orbit-node-state">{error?'Indisponible':!visible?'Chargement…':visible.dimensions[id]?(view==='proposed'?'Éléments proposés':'Éléments conservés'):'Aucun élément dans cette vue'}</span></span><span className="node-chevron" aria-hidden="true">›</span></button>)}
  </div>
  {error&&<div><p role="alert">La compréhension est indisponible. Cela ne signifie pas que le Space est vide.</p><button type="button" className="text-button" onClick={()=>setRetry(n=>n+1)}>Réessayer</button></div>}
  <button type="button" className="text-button" onClick={()=>leave(()=>onExplore?.())}>Voir les éléments</button>
  <p className="map-coverage">Six dimensions universelles · {view==='proposed'?'dernières propositions, sans confirmation implicite':'révisions courantes confirmées'}.</p>
  <button type="button" className="text-button" onClick={()=>leave(()=>onDimension?.('unclassified:'+view))}>Non classés{visible?.unclassified?' · éléments disponibles':''}</button>
 </section>;
}
export function UsefulActions(){return <section className="useful-actions"><header><span className="card-icon"><Icon name="advice"/></span><h2>Actions utiles</h2></header><div>{([['share','Partager une projection'],['import','Importer une conversation'],['users','Partager ce Context Space']] as const).map(([icon,title])=><button type="button" disabled title="Fonction non encore disponible" className="secondary" key={title}><Icon name={icon}/><span>{title}</span><span aria-hidden="true">›</span></button>)}</div></section>;}
