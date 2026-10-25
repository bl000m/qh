import {useEffect,useRef,useState} from 'react';
import type {ContextSpace,QhApi} from './api';
import {apiMessage,validName} from './api';
import type {useOrganization} from './EnvironmentDomains';
import {Modal} from './SpaceActions';
import {Icon} from './Ui';

export default function SpaceEditor({space,api,state,onChanged,triggerLabel='Modifier',openRequest=0}:{space:ContextSpace;api:QhApi;state:ReturnType<typeof useOrganization>;onChanged:(space:ContextSpace)=>void;triggerLabel?:string;openRequest?:number}){
 const [open,setOpen]=useState(false),[name,setName]=useState(space.name),[description,setDescription]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const initial=useRef(state.value),handled=useRef(0);
 function prepare(){initial.current=state.value;setName(space.name);setDescription(state.value?.space_descriptions?.[space.id]??'');setError('');setOpen(true);}
 useEffect(()=>{if(openRequest>handled.current&&state.value){handled.current=openRequest;prepare();}},[openRequest,state.value]);
 async function save(){
  if(busy||!initial.current)return;setBusy(true);setError('');
  try{
   // Independent existing endpoints: acknowledge a successful rename even if the
   // organization CAS subsequently conflicts; never claim an atomic combined save.
   if(name!==space.name)onChanged(await api.rename(space.id,name));
   const metadata=initial.current;
   await state.save({...metadata,space_descriptions:{...metadata.space_descriptions,[space.id]:description}});
   setOpen(false);
  }catch(e){setError(apiMessage(e)+' Le nom et la description sont enregistrés séparément. Rechargez avant de réessayer en cas de conflit.');}
  finally{setBusy(false);}
 }
 return <><button type="button" className={'secondary '+(triggerLabel==='Renommer'?'rename-context-button':'')} aria-label={triggerLabel==='Renommer'?'Renommer le Space':'Modifier le Space'} title={triggerLabel==='Renommer'?'Renommer le Space':'Modifier le Space'} disabled={!state.value||state.busy} onClick={prepare}><Icon name="edit"/>{triggerLabel}</button>
 {open&&<Modal title="Modifier le Space" onClose={()=>{if(!busy)setOpen(false);}}><form onSubmit={e=>{e.preventDefault();void save();}}><p>Ces repères personnels ne changent ni la compréhension ni les droits du Space.</p><label htmlFor="edit-space-name">Nom du Space</label><input id="edit-space-name" value={name} maxLength={256} required disabled={busy} onChange={e=>setName(e.target.value)}/><label htmlFor="edit-space-description">Description du Space</label><textarea id="edit-space-description" value={description} maxLength={500} disabled={busy} onChange={e=>setDescription(e.target.value)}/>{error&&<p role="alert">{error}</p>}<div className="actions"><button disabled={busy||!validName(name)}>Enregistrer le Space</button><button type="button" className="secondary" disabled={busy} onClick={()=>setOpen(false)}>Annuler</button></div></form></Modal>}</>;
}
