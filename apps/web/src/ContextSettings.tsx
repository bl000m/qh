import {useEffect,useRef,useState} from 'react';
import type {ContextSpace,QhApi} from './api';
import {apiMessage} from './api';
import type {useOrganization} from './EnvironmentDomains';
import {Icon} from './Ui';
import SpaceEditor from './SpaceEditor';
import SpaceActions from './SpaceActions';
export default function ContextSettings({space,api,state,onChanged,renameRequest=0,visible=true}:{space:ContextSpace;api:QhApi;state:ReturnType<typeof useOrganization>;onChanged:(space:ContextSpace)=>void;renameRequest?:number;visible?:boolean}){
 const [description,setDescription]=useState(''),[error,setError]=useState(''),[success,setSuccess]=useState(''),[busy,setBusy]=useState(false),[dirty,setDirty]=useState(false);
 const initial=useRef(state.value);
 useEffect(()=>{if(!visible)setSuccess('');},[visible]);
 useEffect(()=>{if(!dirty&&state.value){initial.current=state.value;setDescription(state.value.space_descriptions?.[space.id]??'');}},[space.id,state.value,dirty]);
 async function save(){if(busy||!initial.current)return;setBusy(true);setError('');setSuccess('');try{await state.save({...initial.current,space_descriptions:{...initial.current.space_descriptions,[space.id]:description}});setDirty(false);setSuccess('Description enregistrée.');}catch(e){setError(apiMessage(e)+' Recharge avant de réessayer en cas de conflit.');}finally{setBusy(false);}}
 const primary=state.value?.domains.find(d=>d.id===state.value?.primary_domains[space.id]);
 return <><h2>Paramètres du contexte</h2><form className="product-card" onSubmit={e=>{e.preventDefault();void save();}}><span className="card-icon"><Icon name="sources"/></span><div><h3>Description</h3><label className="sr-only" htmlFor="context-description">Description du contexte</label><textarea id="context-description" maxLength={500} rows={2} value={description} disabled={busy||!state.value} onChange={e=>{setDirty(true);setDescription(e.target.value);setSuccess('');}}/>{dirty&&<button disabled={busy||!state.value}>Enregistrer la description</button>}{success&&<p role="status">{success}</p>}{error&&<p role="alert">{error}</p>}</div></form><div className="product-card"><span className="card-icon"><Icon name="link"/></span><div><h3>Domaine principal</h3><p className="setting-value">{primary?.name??'Non classé'}</p></div></div><div className="product-card"><span className="card-icon"><Icon name="settings"/></span><div><h3>Actions</h3><SpaceActions space={space} state={state}><SpaceEditor openRequest={renameRequest} triggerLabel="Renommer" space={space} api={api} state={state} onChanged={onChanged}/></SpaceActions></div></div></>;
}
