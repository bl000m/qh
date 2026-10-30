import {useState} from 'react';
import type {ContextSpace,QhApi} from './api';
import {ApiError} from './api';
import {Modal} from './SpaceActions';
import {navigate} from './navigation';
import {drafts} from './drafts';

export default function DeleteSpace({space,api}:{space:ContextSpace;api:QhApi}){
 const [open,setOpen]=useState(false),[name,setName]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function remove(){
  if(busy||name!==space.name)return;
  setBusy(true);setError('');
  try{await api.deleteSpace(space.id,{name});drafts.clear();navigate('/');}
  catch(e){setError(e instanceof ApiError&&e.status===409?'Le nom doit correspondre exactement au nom actuel du Space.':
   'La suppression est indisponible ou incomplète. Les accès peuvent déjà être révoqués. Réessaie pour vérifier et terminer la suppression.');}
  finally{setBusy(false);}
 }
 return <><button type="button" className="secondary" onClick={()=>{setOpen(true);setName('');setError('');}}>Supprimer ce Context Space</button>
 {open&&<Modal title="Supprimer ce Context Space" onClose={()=>{if(!busy)setOpen(false);}}>
  <p>Cette action supprime définitivement ce Space, sa compréhension, ses sources, ses PDF et ses partages. Les accès des destinataires seront révoqués.</p>
  <p>Pour confirmer, saisis le nom exact : <strong>{space.name}</strong></p>
  <form onSubmit={e=>{e.preventDefault();void remove();}}><label>Nom du Space à supprimer<input autoComplete="off" value={name} disabled={busy} onChange={e=>setName(e.target.value)}/></label>
  {error&&<p role="alert">{error}</p>}{busy&&<p role="status">Suppression et vérification en cours…</p>}
  <div className="actions"><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button><button disabled={busy||name!==space.name}>{busy?'Suppression…':'Supprimer définitivement'}</button></div></form>
 </Modal>}</>;
}
