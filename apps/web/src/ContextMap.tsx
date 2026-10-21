import {useRef} from 'react';
import {Orb,Icon} from './Ui';

// Legacy descriptors do not identify thematic assignments. Fail closed until the
// approved Understanding Engine exposes a verifiable thematic read contract.
export default function ContextMap({onExplore,onAdd}:{onExplore?:()=>void;onAdd:()=>void}){
 const root=useRef<HTMLElement>(null),center=useRef<HTMLButtonElement>(null);
 function leave(action:()=>void){if(document.fullscreenElement===root.current)void document.exitFullscreen().then(action,action);else action();}
 return <section className="space-context-map" aria-label="Carte thématique de ce contexte" ref={root}>
  <div className="map-tools"><button type="button" className="secondary" aria-label="Agrandir la carte" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void root.current?.requestFullscreen?.().catch(()=>{});}}><Icon name="expand"/></button><button type="button" className="secondary" aria-label="Ajouter un élément" title="Ajouter un élément depuis la carte" onClick={()=>leave(onAdd)}><Icon name="plus"/></button><button type="button" className="secondary" aria-label="Recentrer sur ce contexte" onClick={()=>{center.current?.focus();center.current?.scrollIntoView({block:'nearest',inline:'nearest'});}}><Icon name="target"/></button></div>
  <div className="context-orbit">
   <button type="button" className="context-center" ref={center} aria-label="Explorer les éléments de ce contexte" onClick={()=>leave(()=>onExplore?.())}><Orb/></button>
   <div className="orbit-feedback"><p>Aucun regroupement thématique vérifié n’est disponible dans cette vue.</p><button type="button" className="text-button" onClick={()=>leave(()=>onExplore?.())}>Voir les éléments</button></div>
  </div>
 </section>;
}
export function UsefulActions(){return <section className="useful-actions"><header><span className="card-icon"><Icon name="advice"/></span><h2>Actions utiles</h2></header><div>{([['share','Partager une projection'],['import','Importer une conversation'],['users','Partager ce Context Space']] as const).map(([icon,title])=><button type="button" disabled title="Fonction non encore disponible" className="secondary" key={title}><Icon name={icon}/><span>{title}</span><span aria-hidden="true">›</span></button>)}</div></section>;}
