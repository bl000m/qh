import {useRef,useState} from 'react';
import type {QhApi} from './api';
import Understanding from './Understanding';
import {Icon} from './Ui';

/** Native disclosure; lazy first load, retained when folded, reset by Space key. */
export default function UnderstandingExplorer({api,scope,onChanged}:{api:QhApi;scope:string;onChanged?:()=>void}) {
  const [visited,setVisited]=useState(false);
  const summary=useRef<HTMLElement>(null);
  const content=useRef<HTMLDivElement>(null);
  return <details className="understanding-explorer support-section" onToggle={event=>{
    if(event.currentTarget.open)setVisited(true);
    else if(content.current?.contains(document.activeElement))summary.current?.focus();
  }} onKeyDown={event=>{
    if(event.key==='Escape' && event.currentTarget.open){
      event.preventDefault();event.currentTarget.open=false;summary.current?.focus();
    }
  }}>
    <summary ref={summary}><Icon name="understanding"/><span>Compréhension<small>Explorer la compréhension</small></span></summary>
    <p className="muted">Consultez les éléments conservés, leurs sources et leur historique, sans formuler de recherche.</p>
    <div ref={content}>{visited && <Understanding api={api} scope={scope} onChanged={onChanged}/>}</div>
  </details>;
}
