import {ApiError,isUuid} from './transport';
import type {GuestSessionView,SharedPayload,GuestAnswer,GuestProviderStatus,RecipientAnswer} from '@qh/shared';
export const sharingEnabled=import.meta.env.VITE_QH_SHARING==='1';

export async function guestRequest(path:string,body?:unknown):Promise<unknown>{
 let response:Response;
 try{response=await fetch('/api/guest'+path,{method:body?'POST':'GET',credentials:'same-origin',cache:'no-store',redirect:'error',
   headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});}catch{throw new ApiError(503);}
 if(!response.ok)throw new ApiError(response.status);
 if(response.status===204)return null;
 return response.json();
}
export function sessionView(value:unknown):GuestSessionView{
 const v=value as GuestSessionView;
 if(!v||typeof v.name!=='string'||!v.name.trim()||typeof v.can_ask!=='boolean'||v.verification!=='mailbox_control'||!Number.isFinite(Date.parse(v.expires_at)))throw new ApiError(502);
 if(v.recap&&!validRecap(v.recap))throw new ApiError(502);
 if(!validDocumentCount(v.semantic_document_count))throw new ApiError(502);
 if(v.document_recaps&&(!Array.isArray(v.document_recaps)||v.document_recaps.length>100||v.document_recaps.some(c=>!validRecap(c))))throw new ApiError(502);
 return v;
}
function validRecap(recap:NonNullable<GuestSessionView['recap']>):boolean{
 return typeof recap.title==='string'&&!!recap.title.trim()&&recap.title.length<=120
  &&typeof recap.text==='string'&&!!recap.text.trim()&&recap.text.length<=1500&&recap.text.trim().split(/\s+/).length<=100;
}
function validDocumentCount(count:number|undefined):boolean{
 return count===undefined||Number.isInteger(count)&&count>=0&&count<=100;
}
export function sharedPayload(value:unknown):SharedPayload{
 const v=value as SharedPayload;
 if(!v||v.format!=='qh.disclosure/1'||!Array.isArray(v.items)||v.items.length>100||v.items.some(i=>
   !i||typeof i.reference!=='string'||typeof i.text!=='string'||i.text.length>16000||
   !['proposed','confirmed'].includes(i.validation_state)||!Array.isArray(i.sources)))throw new ApiError(502);
 if(v.recap&&!validRecap(v.recap))throw new ApiError(502);
 if(!validDocumentCount(v.semantic_document_count))throw new ApiError(502);
 if(v.document_recaps&&(!Array.isArray(v.document_recaps)||v.document_recaps.length>100||v.document_recaps.some(c=>!validRecap(c))))throw new ApiError(502);
 return v;
}
export function recipientAnswer(value:unknown):RecipientAnswer{
 const v=value as RecipientAnswer;
 if(!v||typeof v.answer!=='string'||!v.answer.trim()||typeof v.insufficient_context!=='boolean'||typeof v.simulated!=='boolean')throw new ApiError(502);
 if(v.documents&&(!Array.isArray(v.documents)||v.documents.some(d=>!isUuid(d.source_revision_id)||typeof d.filename!=='string'||!d.filename||d.filename.length>256)))throw new ApiError(502);
 return v;
}
export function guestAnswer(value:unknown):GuestAnswer{
 const v=value as GuestAnswer;
 if(!v||typeof v.simulated!=='boolean'||!v.simulated&&v.model!=='mistral-small-2603'||typeof v.answer!=='string'||v.answer.length>1_000_000||typeof v.insufficient_context!=='boolean'||
   !Array.isArray(v.reference_aliases)||v.reference_aliases.some(r=>typeof r!=='string'))throw new ApiError(502);
 return v;
}
export function providerStatus(value:unknown):GuestProviderStatus{
 const v=value as GuestProviderStatus;if(!v||!['offline','mistral-small-2603'].includes(v.model)||typeof v.enabled!=='boolean'||typeof v.simulated!=='boolean'||v.remaining_usd!=null&&!/^\d+(\.\d+)?$/.test(v.remaining_usd))throw new ApiError(502);return v;
}
export function sharingError(e:unknown){
 if(e instanceof ApiError&&e.status===402)return 'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.';
 return e instanceof ApiError&&e.status===409?'La prévisualisation a changé ou expiré. Préparez-la à nouveau.':
   e instanceof ApiError&&e.status===429?'Trop de tentatives. Patientez une minute.':'Accès indisponible ou non autorisé. Aucun contenu supplémentaire n’a été divulgué.';
}

/** Safe failure categories only: never render provider bodies or private diagnostics. */
export function guestChatError(error:unknown):string{
 if(!(error instanceof ApiError))return 'La réponse n’a pas pu être obtenue.';
 if([402,429].includes(error.status))return sharingError(error);
 if([401,403].includes(error.status))return 'Cet accès n’est plus valide. Rouvrez votre invitation.';
 if([400,413,422].includes(error.status))return 'La question ou l’historique n’a pas pu être accepté. Rouvrez la discussion si nécessaire.';
 if(error.status===503)return 'Le service de réponse est indisponible ou n’a pas pu valider la réponse.';
 if(error.status===502)return 'La réponse reçue n’a pas pu être lue.';
 return 'La réponse n’a pas pu être obtenue.';
}
