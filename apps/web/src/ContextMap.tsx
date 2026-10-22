import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {ApiError} from './api';
import type {QhApi,DimensionPresence} from './api';
import {DIMENSIONS} from './uum';
import {Orb,Icon} from './Ui';

type Connections={width:number;height:number;paths:string[]};
export default function ContextMap({api,scope,refreshKey,onExplore,onAdd,onDimension,showAdd=true}:{api:QhApi;scope:string;refreshKey:number;onExplore?:()=>void;onAdd:()=>void;onDimension?:(value:string)=>void;showAdd?:boolean}){
 const [view,setView]=useState<'current'|'proposed'>('proposed'),[data,setData]=useState<DimensionPresence|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0);
 const [connections,setConnections]=useState<Connections|null>(null);
 const visible=data?.context_id===scope&&data.view===view?data:null;
 const root=useRef<HTMLElement>(null),center=useRef<HTMLButtonElement>(null),orbit=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  let active=true;setData(null);setError(false);
  async function read(){
   const attempts=refreshKey>0?16:1;
   for(let attempt=0;attempt<attempts&&active;attempt++){
    try{const result=await api.dimensionPresence(scope,view);if(active)setData(result);return;}
    catch(reason){if(!active)return;if(!(reason instanceof ApiError)||reason.status!==503||attempt===attempts-1){setError(true);return;}await new Promise(resolve=>setTimeout(resolve,500));}
   }
  }
  void read();return()=>{active=false;};
 },[api,scope,view,refreshKey,retry]);
 useLayoutEffect(()=>{
  const board=orbit.current,hub=center.current;if(!board||!hub)return;
  let frame=0,active=true;
  function measure(){
   if(!active)return;
   if(getComputedStyle(board!).getPropertyValue('--map-radial').trim()!=='1'){setConnections(null);return;}
   const b=board!.getBoundingClientRect(),c=hub!.getBoundingClientRect();
   const paths=[...board!.querySelectorAll('.context-orbit-node')].map((node,i)=>{
    const n=node.getBoundingClientRect(),left=i%2===0;
    const x=(left?n.right:n.left)-b.left,y=n.top+n.height/2-b.top;
    const endX=c.left+c.width*(left ? 0.14 : 0.86)-b.left,endY=c.top+c.height/2-b.top+(Math.floor(i/2)-1)*c.height*.12;
    const middle=(x+endX)/2;
    return `M${x} ${y} C${middle} ${y} ${middle} ${endY} ${endX} ${endY}`;
   });
   const next={width:b.width,height:b.height,paths};
   setConnections(old=>JSON.stringify(old)===JSON.stringify(next)?old:next);
  }
  const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(measure);};
  const observer=new ResizeObserver(schedule);observer.observe(board);observer.observe(hub);
  board.querySelectorAll('.context-orbit-node').forEach(node=>observer.observe(node));
  document.addEventListener('fullscreenchange',schedule);void document.fonts.ready.then(schedule);schedule();
  return()=>{active=false;cancelAnimationFrame(frame);observer.disconnect();document.removeEventListener('fullscreenchange',schedule);};
 },[]);
 function leave(action:()=>void){root.current?.querySelector('details.map-navigation')?.removeAttribute('open');if(document.fullscreenElement===root.current)void document.exitFullscreen().then(action,action);else action();}
 return <section className="space-context-map" aria-label="Dimensions de compréhension" ref={root}>
  {error&&<p className="sr-only" role="alert">La compréhension est indisponible. Cela ne signifie pas que le Space est vide.</p>}
  <header className="map-heading"><div><h2>Carte de compréhension</h2><p>6 dimensions universelles · vos éléments restent vérifiables</p></div><div className="map-utility"><details className="map-navigation"><summary aria-label="Options de la carte"><Icon name="list"/></summary><div><button type="button" onClick={()=>leave(()=>onExplore?.())}>Voir les éléments</button><button type="button" onClick={()=>leave(()=>onDimension?.('unclassified:'+view))}>Non classés{visible?.unclassified?' · éléments disponibles':''}</button><p>{error?'La compréhension est indisponible. Cela ne signifie pas que le Space est vide.':'Les états des dimensions dépendent de la vue sélectionnée. Rien n’est confirmé automatiquement.'}</p></div></details><button type="button" className="secondary" aria-label="Agrandir la carte" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void root.current?.requestFullscreen?.().catch(()=>{});}}><Icon name="expand"/></button><button type="button" className="secondary" aria-label="Recentrer sur ce contexte" onClick={()=>center.current?.focus()}><Icon name="target"/></button></div></header>
  <div className="map-tools"><div className="map-views" role="group" aria-label="État de compréhension"><button type="button" aria-pressed={view==='proposed'} onClick={()=>setView('proposed')}>Propositions</button><button type="button" aria-pressed={view==='current'} onClick={()=>setView('current')}>Compréhension courante</button></div>{showAdd&&<button type="button" className="map-add" onClick={()=>leave(onAdd)}><Icon name="plus"/>Ajouter un élément</button>}</div>
  <div className="context-orbit" ref={orbit}>
   {connections&&<svg className="orbit-connections" viewBox={`0 0 ${connections.width} ${connections.height}`} aria-hidden="true">{connections.paths.map((d,i)=><path key={DIMENSIONS[i][0]} className={'orbit-line tone-'+i} d={d}/>)}</svg>}
   <button type="button" className="context-center" ref={center} aria-label="Explorer les éléments de ce contexte" onClick={()=>leave(()=>onExplore?.())}><Orb/><span className="map-orb-label" aria-hidden="true">QH</span></button>
   {DIMENSIONS.map(([id,label],i)=><button type="button" key={id} className={'context-orbit-node orbit-node-'+i+' tone-'+i} onClick={()=>leave(()=>onDimension?.(id+':'+view))}><span className="orbit-node-icon"><Icon name="understanding"/></span><span className="orbit-node-copy"><strong>{label}</strong><span className="orbit-node-state">{error?'Indisponible':!visible?'Chargement…':visible.dimensions[id]?(view==='proposed'?'Éléments proposés':'Éléments conservés'):'Aucun élément dans cette vue'}</span></span><span className="node-chevron" aria-hidden="true">›</span></button>)}
  </div>
  <footer className="map-footer"><div className="map-links"><button type="button" className="text-button" onClick={()=>leave(()=>onExplore?.())}>Voir les éléments</button><button type="button" className="text-button" onClick={()=>leave(()=>onDimension?.('unclassified:'+view))}>Non classés{visible?.unclassified?' · éléments disponibles':''}</button></div><p className="map-coverage">{view==='proposed'?'Propositions à vérifier, sans confirmation implicite.':'Compréhension courante confirmée.'} Les six dimensions restent visibles même si le Space est vide.</p><div className="map-error">{error&&<><p role="alert">La compréhension est indisponible. Cela ne signifie pas que le Space est vide.</p><button type="button" className="text-button" onClick={()=>setRetry(n=>n+1)}>Réessayer</button></>}</div></footer>
 </section>;
}
export function UsefulActions(){return <section className="useful-actions"><header><span className="card-icon"><Icon name="advice"/></span><h2>Actions utiles</h2></header><div>{([['share','Partager une projection'],['import','Importer une conversation'],['users','Partager ce Context Space']] as const).map(([icon,title])=><button type="button" disabled title="Fonction non encore disponible" className="secondary" key={title}><Icon name={icon}/><span>{title}</span><span aria-hidden="true">›</span></button>)}</div></section>;}
