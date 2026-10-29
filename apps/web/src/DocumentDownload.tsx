import {useState} from 'react';
import type {SourceDocument} from '../../../packages/shared/src/context-space';
import type {QhApi} from './api';
import {guestRequest} from './sharing';

/** UI availability only. Backend independently resolves and authorizes each document. */
export function isOriginalRequest(text:string):boolean{
 const value=text.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 if(/\b(telecharg\w*|download\w*|scaric\w*)\b/.test(value))return true;
 const explicit=/\b(pdf|original|originale)\b/.test(value);
 if(!explicit&&/\b(resume|summary|riassunto|competences|skills|informations|informazioni|contenu)\b/.test(value))return false;
 return /\b(pdf|original|originale|fichier|file|document|documento|cv|curriculum)\b/.test(value)
  &&/\b(recuper\w*|retrieve\w*|renvo\w*|rimand\w*|restitui\w*|invi\w*|envoi\w*|donne\w*|donn\w*|dammi|darmi|mostr\w*|vedere|voir|consulter|get|give|show|send|open)\b/.test(value);
}

export default function DocumentDownload({document,api,scope}:{document:SourceDocument;api?:QhApi;scope?:string}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 async function download(){setBusy(true);setError('');
  try{
   if(api&&scope)await api.downloadDocument(scope,document.source_revision_id,document.filename);
   else {
    // Recheck the guest session and exact permission before even offering navigation.
    const current=await guestRequest('/documents') as SourceDocument[];
    if(!current.some(d=>d.source_revision_id===document.source_revision_id))throw Error('denied');
    const link=window.document.createElement('a');link.href='/api/guest/documents/'+document.source_revision_id;link.download=document.filename;link.click();
   }
  }catch{setError('Document indisponible ou accès refusé.');}finally{setBusy(false);}
 }
 return <span><button type="button" className="secondary" disabled={busy} onClick={()=>{void download();}}>Télécharger l’original</button>{error&&<span role="alert">{error}</span>}</span>;
}
