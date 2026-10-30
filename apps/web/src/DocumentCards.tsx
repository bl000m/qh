import type {SourceDocument,ContextIntake} from '../../../packages/shared/src/context-space';
import type {QhApi} from './api';
import DocumentDownload from './DocumentDownload';
import logo from './brand/qh-logo.png';
import './documents.css';

export const documentName=(doc:SourceDocument)=>doc.display_name||doc.filename;
export const readableDocumentName=(name:string)=>name.replace(/\.pdf$/i,'').replace(/[_-]+/g,' ').replace(/\s+/g,' ').trim()||'Document';
export function documentSize(bytes?:number){
 if(bytes===undefined)return 'PDF';
 const unit=bytes>=1_000_000?'Mo':'Ko',value=bytes/(unit==='Mo'?1_000_000:1000);
 return 'PDF · '+new Intl.NumberFormat('fr-FR',{maximumFractionDigits:1}).format(value)+' '+unit;
}
export function documentDate(value?:string){
 if(!value||!Number.isFinite(Date.parse(value)))return '';
 const date=new Date(value),today=new Date();
 return new Intl.DateTimeFormat('fr-FR',date.toDateString()===today.toDateString()?{hour:'2-digit',minute:'2-digit'}:{day:'numeric',month:'short',year:'numeric'}).format(date);
}
export function PdfMark(){return <span className="document-pdf-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M22 6c-6-4-4 11 0 18 3 5 10 6 11 3 1-5-15-4-23 1-9 6-5 11 0 5 6-7 16-25 12-27Z"/></svg></span>;}
export function DocumentFileCard({document,api,scope,upload=false,compact=false}:{document:SourceDocument;api?:QhApi;scope?:string;upload?:boolean;compact?:boolean}){
 return <div className={'document-file-card'+(compact?' compact':'')+(upload?' uploaded':'')}>
  <PdfMark/><div className="document-file-info"><strong title={upload||compact?documentName(document):document.filename}>{upload||compact?documentName(document):document.filename}</strong>
  <span>{upload?'Nom du fichier original : '+document.filename:documentSize(document.size_bytes)+(compact&&documentDate(document.created_at)?' · '+documentDate(document.created_at):'')}</span></div>
  {!upload&&<DocumentDownload api={api} scope={scope} document={document} label="Télécharger" iconOnly={compact}/>}
 </div>;
}
export default function DocumentChatMessage({item,documents,api,scope}:{item:ContextIntake;documents:SourceDocument[];api:QhApi;scope:string}){
 const uploaded=item.source_revision_id?documents.find(d=>d.source_revision_id===item.source_revision_id)??{source_revision_id:item.source_revision_id,filename:item.name!,display_name:item.display_name,size_bytes:item.size_bytes,created_at:item.created_at}:null;
 return <div className="document-chat-layout"><span className="document-qh-avatar"><img src={logo} alt="QH"/></span><div className="document-chat-content">
  <div className="document-chat-bubble"><p>{uploaded?'Document ajouté au contexte':item.text}</p>
  {uploaded?<DocumentFileCard document={uploaded} upload/>:item.documents?.map(doc=><DocumentFileCard key={doc.source_revision_id} document={documents.find(d=>d.source_revision_id===doc.source_revision_id)??doc} api={api} scope={scope}/>)}
  {uploaded&&<p className="document-available">Disponible dans Documents.</p>}</div>
  {item.created_at&&<time className="document-chat-time" dateTime={item.created_at}>{documentDate(item.created_at)}</time>}
 </div></div>;
}
