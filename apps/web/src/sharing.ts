import {ApiError,isUuid} from './transport';
import type {GuestSessionView,SharedPayload,GuestAnswer,GuestProviderStatus} from '@qh/shared';
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
 if(!v||!isUuid(v.snapshot_id)||v.verification!=='mailbox_control'||!Array.isArray(v.rights)||!v.rights.length||
   v.rights.some(r=>r!=='READ'&&r!=='ASK_AI')||!Number.isFinite(Date.parse(v.expires_at)))throw new ApiError(502);
 return v;
}
export function sharedPayload(value:unknown):SharedPayload{
 const v=value as SharedPayload;
 if(!v||v.format!=='qh.disclosure/1'||!Array.isArray(v.items)||!v.items.length||v.items.length>100||v.items.some(i=>
   !i||typeof i.reference!=='string'||typeof i.text!=='string'||i.text.length>16000||
   !['proposed','confirmed'].includes(i.validation_state)||!Array.isArray(i.sources)))throw new ApiError(502);
 if(v.recap&&(typeof v.recap.title!=='string'||!v.recap.title.trim()||v.recap.title.length>120||typeof v.recap.text!=='string'||!v.recap.text.trim()||v.recap.text.length>1500||v.recap.text.trim().split(/\s+/).length>100))throw new ApiError(502);
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
