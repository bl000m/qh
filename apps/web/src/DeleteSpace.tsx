import {useState} from 'react';
import type {ContextSpace,QhApi} from './api';
import {ApiError} from './api';
import {Modal} from './SpaceActions';
import {navigate,domainPath} from './navigation';
import {Icon} from './Ui';
import {drafts} from './drafts';

export default function DeleteSpace({space,api,parentDomainId,disabled=false}:{space:ContextSpace;api:QhApi;parentDomainId?:string;disabled?:boolean}){
 const [open,setOpen]=useState(false),[name,setName]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function remove(){
  if(busy||name!==space.name)return;
  setBusy(true);setError('');
  try{await api.deleteSpace(space.id,{name});drafts.clear();navigate(parentDomainId?domainPath(parentDomainId):'/');}
  catch(e){setError(e instanceof ApiError&&e.status===409?'Le nom doit correspondre exactement au nom actuel du Space.':
   'La suppression est indisponible ou incomplète. Les accès peuvent déjà être révoqués. Réessaie pour vérifier et terminer la suppression.');}
  finally{setBusy(false);}
 }
 return <><div className="delete-space-action"><button type="button" className="delete-space-trigger" disabled={disabled} onClick={()=>{setOpen(true);setName('');setError('');}}><Icon name="trash"/>Supprimer ce Context Space</button></div>
 {open&&<Modal title="Supprimer ce Context Space" className="delete-space-dialog" closeOnBackdrop onClose={()=>{if(!busy)setOpen(false);}}>
  <span className="delete-space-icon"><Icon name="trash"/></span>
  <p className="delete-space-warning">Cette action supprime définitivement ce Space, sa compréhension, ses sources, ses PDF et ses partages. Les accès des destinataires seront révoqués.</p>
  <form onSubmit={e=>{e.preventDefault();void remove();}}><label>Pour confirmer, saisissez le nom exact :<strong>{space.name}</strong><input aria-label="Nom du Space à supprimer" placeholder={space.name} autoComplete="off" value={name} disabled={busy} onChange={e=>setName(e.target.value)}/></label>
  {error&&<p role="alert">{error}</p>}{busy&&<p role="status">Suppression et vérification en cours…</p>}
  <div className="actions"><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button><button className="danger" disabled={busy||name!==space.name}>{busy?'Suppression…':'Supprimer définitivement'}</button></div></form>
 </Modal>}</>;
}
