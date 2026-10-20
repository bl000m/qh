import {useRef} from 'react';
import {Icon} from './Ui';
export const spaceTabs=['Discussion','Éléments','Modèle','Conseils','Paramètres'] as const;
export type SpaceTab=typeof spaceTabs[number];
export default function SpaceTabs({value,onChange}:{value:SpaceTab;onChange:(tab:SpaceTab)=>void}){
 const refs=useRef<(HTMLButtonElement|null)[]>([]);
 const icons=['discussion','sources','model','advice','settings'] as const;
 return <div role="tablist" aria-label="Context Space" className="space-tabs">{spaceTabs.map((tab,i)=><button key={tab} ref={n=>{refs.current[i]=n;}} type="button" role="tab" id={'space-tab-'+i} aria-selected={value===tab} aria-controls={'space-panel-'+i} tabIndex={value===tab?0:-1} onClick={()=>onChange(tab)} onKeyDown={e=>{const next=e.key==='ArrowRight'?(i+1)%5:e.key==='ArrowLeft'?(i+4)%5:e.key==='Home'?0:e.key==='End'?4:null;if(next!==null){e.preventDefault();onChange(spaceTabs[next]);refs.current[next]?.focus();}}}><Icon name={icons[i]}/>{tab}</button>)}</div>;
}
