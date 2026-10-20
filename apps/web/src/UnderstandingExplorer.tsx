import {useRef,useState} from 'react';
import type {QhApi} from './api';
import UnderstandingWorkspace from './UnderstandingWorkspace';
import {Icon} from './Ui';

/** Entry from Éléments; closing the workspace restores the same card and tab. */
export default function UnderstandingExplorer({api,scope,onChanged,initialRevision,standalone=false,spaceName='Ce contexte',refreshKey=0,onAdd}:{api:QhApi;scope:string;onChanged?:()=>void;initialRevision?:string;standalone?:boolean;spaceName?:string;refreshKey?:number;onAdd?:()=>void}) {
 const [open,setOpen]=useState(!!initialRevision),[visited,setVisited]=useState(!!initialRevision);const entry=useRef<HTMLDetailsElement>(null),summary=useRef<HTMLElement>(null);
 function close(){setOpen(false);if(entry.current)entry.current.open=false;requestAnimationFrame(()=>summary.current?.focus({preventScroll:true}));}
 return <details ref={entry} open={open} className={'understanding-explorer '+(standalone?'element-section':'support-section')} onToggle={e=>{if(e.currentTarget.open){setVisited(true);setOpen(true);}}}><summary ref={summary}><span className="card-icon"><Icon name="understanding"/></span><span><strong>Compréhension</strong><small>Vos informations, les interprétations et leurs sources</small></span></summary>{visited&&<UnderstandingWorkspace open={open} api={api} scope={scope} spaceName={spaceName} initialRevision={initialRevision} refreshKey={refreshKey} onClose={close} onChanged={onChanged} onAdd={onAdd}/>}</details>;
}
