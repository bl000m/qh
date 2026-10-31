import {useState} from 'react';
import type {SourceDocument} from '../../../packages/shared/src/context-space';
import {documentName,documentMatches,PdfMark} from './DocumentCards';
import DocumentDownload from './DocumentDownload';
import {Icon} from './Ui';

export function OriginalDocumentPermission({documents,selected,onChange,status,onRetry}:{documents:SourceDocument[];selected:string[];onChange:(ids:string[])=>void;status:string;onRetry:()=>void}){
 const [enabled,setEnabled]=useState(false),[mode,setMode]=useState<'choose'|'all'>('choose'),[search,setSearch]=useState('');
 function toggle(){setEnabled(!enabled);setMode('choose');onChange([]);}
 return <section className={'sharing-originals'+(enabled?' enabled':'')} aria-label="Documents originaux">
  <div className="sharing-originals-heading"><Icon name="sources"/><strong>Documents originaux</strong><button type="button" role="switch" aria-label="Autoriser l’accès aux documents originaux" aria-checked={enabled} disabled={status==='loading'||status==='error'} className="originals-toggle" onClick={toggle}><span/></button></div>
  <p>Autoriser aussi la consultation et le téléchargement de fichiers originaux, séparément du contexte partagé.</p>
  {status==='loading'?<p role="status">Chargement des documents…</p>:status==='error'?<p role="alert">Documents indisponibles. <button type="button" onClick={onRetry}>Réessayer</button></p>:!documents.length?<p className="originals-empty">Aucun document original dans ce contexte.</p>:enabled&&<>
   <div className="originals-modes" aria-label="Sélection des documents"><button type="button" aria-pressed={mode==='choose'} onClick={()=>setMode('choose')}>Choisir les documents</button><button type="button" aria-pressed={mode==='all'} onClick={()=>{setMode('all');onChange(documents.map(doc=>doc.source_revision_id));}}>Tous les documents actuels</button></div>
   {documents.length>5&&<input type="search" aria-label="Rechercher les documents à partager" placeholder="Rechercher un document" value={search} onChange={e=>setSearch(e.target.value)}/>}
   <div className="originals-selection">{documents.filter(doc=>documentMatches(doc,search)).map(doc=><label className="originals-choice" key={doc.source_revision_id}>
    <input type="checkbox" checked={selected.includes(doc.source_revision_id)} onChange={e=>{setMode('choose');onChange(e.target.checked?[...selected,doc.source_revision_id]:selected.filter(id=>id!==doc.source_revision_id));}}/>
    <span className="originals-file-icon"><Icon name="sources"/></span><span><strong>{documentName(doc)}</strong><small>{doc.filename}</small></span>
   </label>)}</div><p className="originals-future"><Icon name="lock"/>Les documents ajoutés après cette invitation resteront privés.</p>
  </>}
 </section>;
}

export function SharedDocumentsPreview({documents,selected}:{documents:SourceDocument[];selected:string[]}){
 const visible=documents.filter(doc=>selected.includes(doc.source_revision_id));
 return <section className="shared-documents-preview" aria-label="Documents accessibles"><header><h4>Documents accessibles</h4><span>{visible.length?visible.length+' sur '+documents.length:'Aucun'}</span></header>
  <div>{visible.length?visible.map(doc=><p key={doc.source_revision_id}><Icon name="sources"/>{documentName(doc)}</p>):<p className="muted">Aucun fichier original n’est partagé. Le destinataire peut interroger le contexte, mais pas télécharger les sources.</p>}</div>
 </section>;
}

export function GuestDocuments({documents}:{documents:SourceDocument[]}){
 const [search,setSearch]=useState('');
 return <section className="guest-documents" aria-label="Documents autorisés"><header><h2>Documents autorisés</h2><span>{documents.length}</span></header><p>Partagés par le propriétaire de ce contexte</p>
  <input type="search" aria-label="Rechercher un document autorisé" placeholder="Rechercher un document" value={search} onChange={e=>setSearch(e.target.value)}/>
  <div className="guest-document-list">{documents.filter(doc=>documentMatches(doc,search)).map(doc=><div className="guest-document-row" key={doc.source_revision_id}><PdfMark/><div><strong title={documentName(doc)}>{documentName(doc)}</strong><small title={doc.filename}>{doc.filename}</small></div><DocumentDownload document={doc} iconOnly/></div>)}</div>
  {search&&!documents.some(doc=>documentMatches(doc,search))&&<p>Aucun document ne correspond à cette recherche.</p>}
  <p className="guest-documents-notice"><Icon name="info"/>Accès limité aux documents sélectionnés. Consultation et téléchargement autorisés.</p>
 </section>;
}
