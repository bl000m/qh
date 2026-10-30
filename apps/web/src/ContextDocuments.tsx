import {useEffect,useRef,useState} from 'react';
import type {SourceDocument} from '../../../packages/shared/src/context-space';
import type {QhApi} from './api';
import {DocumentFileCard,documentName} from './DocumentCards';
import {Modal} from './SpaceActions';

export function NameDocumentDialog({file,value,onChange,onClose,onContinue,busy,error}:{file:File;value:string;onChange:(value:string)=>void;onClose:()=>void;onContinue:()=>void;busy:boolean;error:string}){
 return <Modal title="Nommer le document" className="document-name-dialog" onClose={()=>{if(!busy)onClose();}}>
  <form onSubmit={event=>{event.preventDefault();if(value.trim()&&!busy)onContinue();}}>
   <div className="document-name-body"><p>Attribuez un nom simple pour retrouver facilement ce fichier.<br/>Si le nom du fichier est déjà clair, il sera repris automatiquement.</p>
   <label className="sr-only" htmlFor="document-display-name">Nom du document</label><input id="document-display-name" autoFocus value={value} onChange={event=>onChange(event.target.value)} maxLength={256} required disabled={busy}/>
   <p className="document-detected-name">Nom du fichier détecté : {file.name}</p>{error&&<p role="alert">{error}</p>}</div>
   <footer><button type="button" className="secondary" disabled={busy} onClick={onClose}>Annuler</button><button type="submit" disabled={busy||!value.trim()}>{busy?'Import en cours…':'Continuer'}</button></footer>
  </form>
 </Modal>;
}
const normalized=(text:string)=>text.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[_-]/g,' ');
export default function ContextDocuments({documents,api,scope,onClose,error,onRetry}:{documents:SourceDocument[];api:QhApi;scope:string;onClose:()=>void;error:string;onRetry:()=>void}){
 const [query,setQuery]=useState(''),[canLeft,setCanLeft]=useState(false),[canRight,setCanRight]=useState(false);
 const track=useRef<HTMLDivElement>(null);
 const found=documents.filter(doc=>normalized(documentName(doc)+' '+doc.filename).includes(normalized(query).trim()));
 function measure(){const n=track.current;if(n){setCanLeft(n.scrollLeft>2);setCanRight(n.scrollLeft+n.clientWidth<n.scrollWidth-2);}}
 useEffect(()=>{measure();const observer=new ResizeObserver(measure);if(track.current)observer.observe(track.current);return()=>observer.disconnect();},[documents,query]);
 function scroll(direction:number){track.current?.scrollBy({left:direction*(track.current.clientWidth*.85),behavior:'smooth'});}
 return <section className="context-documents-panel" aria-label="Documents du contexte" id="context-documents-panel">
  <span className="documents-panel-handle" aria-hidden="true"/><header><div><h2>Documents du contexte</h2><p>Documents originaux conservés dans ce Space.</p></div><button type="button" className="documents-close" aria-label="Fermer les documents" onClick={onClose}>×</button></header>
  <div className="documents-search-row"><label className="documents-search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/></svg><input type="search" placeholder="Rechercher un document" aria-label="Rechercher un document" value={query} onChange={event=>setQuery(event.target.value)}/></label>
  <span className="documents-sort">Du plus récent au plus ancien</span><div className="documents-arrows"><button type="button" aria-label="Documents précédents" disabled={!canLeft} onClick={()=>scroll(-1)}>‹</button><button type="button" aria-label="Documents suivants" disabled={!canRight} onClick={()=>scroll(1)}>›</button></div></div>
  {error?<p className="documents-empty" role="alert">{error} <button type="button" onClick={onRetry}>Réessayer</button></p>:<div className="documents-track" ref={track} onScroll={measure} tabIndex={0} aria-label="Liste des documents">
   {found.map(doc=><DocumentFileCard key={doc.source_revision_id} document={doc} compact api={api} scope={scope}/>)}
   {!found.length&&<p className="documents-empty">{query?'Aucun document ne correspond à cette recherche.':'Aucun document ajouté pour le moment.'}</p>}
  </div>}
 </section>;
}
