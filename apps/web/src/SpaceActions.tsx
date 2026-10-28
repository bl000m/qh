import {useEffect,useId,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import type {ContextSpace} from './api';
import type {useOrganization} from './EnvironmentDomains';
import {Icon} from './Ui';
export function Modal({title,children,onClose,className=''}:{title:string;children:ReactNode;onClose:()=>void;className?:string}){
 const dialog=useRef<HTMLDialogElement>(null),heading=useId();
 useEffect(()=>{const n=dialog.current;const opener=document.activeElement as HTMLElement|null;n?.showModal();return()=>{n?.close();if(opener?.isConnected)opener.focus({preventScroll:true});};},[]);
 return <dialog ref={dialog} className={"space-action-dialog "+className} aria-labelledby={heading} onCancel={e=>{e.preventDefault();onClose();}}><header><h2 id={heading}>{title}</h2><button className="secondary" type="button" onClick={onClose} aria-label="Fermer la fenêtre" autoFocus>×</button></header>{children}</dialog>;
}
function Assignment({space,state,onClose}:{space:ContextSpace;state:ReturnType<typeof useOrganization>;onClose:()=>void}){
 const initial=useRef(state.value!);const [selected,setSelected]=useState(initial.current.memberships[space.id]??[]),[primary,setPrimary]=useState(initial.current.primary_domains[space.id]??'');const [error,setError]=useState('');
 async function save(){setError('');const p={...initial.current.primary_domains};if(selected.length)p[space.id]=primary;else delete p[space.id];try{await state.save({...initial.current,memberships:{...initial.current.memberships,[space.id]:selected},primary_domains:p});onClose();}catch{setError('L’association n’a pas été enregistrée. Recharge l’organisation en cas de conflit, puis réessaie.');}}
 return <Modal title="Assigner à un domaine" onClose={onClose}><form onSubmit={e=>{e.preventDefault();void save();}}><p>{space.name}</p><fieldset disabled={state.busy}><legend>Domaines associés</legend>{initial.current.domains.map(d=><label className="check" key={d.id}><input type="checkbox" checked={selected.includes(d.id)} onChange={e=>{const next=e.target.checked?[...selected,d.id]:selected.filter(id=>id!==d.id);setSelected(next);if(!next.includes(primary))setPrimary(next[0]??'');}}/>{d.name}</label>)}<label>Domaine principal<select value={primary} disabled={!selected.length} onChange={e=>setPrimary(e.target.value)}>{!selected.length&&<option value="">Non classé</option>}{initial.current.domains.filter(d=>selected.includes(d.id)).map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label></fieldset>{error&&<div><p role="alert" className="notice error">{error}</p><button type="button" className="secondary" onClick={()=>{state.reload();onClose();}}>Recharger l’organisation</button></div>}<div className="actions"><button disabled={state.busy||selected.length>0&&!primary}>{state.busy?'Enregistrement…':'Enregistrer les domaines'}</button><button className="secondary" type="button" disabled={state.busy} onClick={onClose}>Annuler</button></div></form></Modal>;
}
export default function SpaceActions({space,state,children,label='Assigner à un domaine',onAssignmentClosed}:{space:ContextSpace;state:ReturnType<typeof useOrganization>;children?:ReactNode;label?:string;onAssignmentClosed?:()=>void}){
 const [action,setAction]=useState<'assign'|null>(null);
 const assignButton=useRef<HTMLButtonElement>(null);const [restoreAssign,setRestoreAssign]=useState(false);
 useEffect(()=>{if(restoreAssign&&action===null&&state.value&&!state.busy){if(onAssignmentClosed)onAssignmentClosed();else assignButton.current?.focus({preventScroll:true});setRestoreAssign(false);}},[restoreAssign,action,state.value,state.busy,onAssignmentClosed]);
 return <><div className="space-context-actions">{children}<button ref={assignButton} className="secondary" aria-label={label==='Gérer'?'Gérer les domaines de ce Space':undefined} disabled={!state.value||state.busy} onClick={()=>setAction('assign')}><Icon name={label==='Gérer'?'settings':'link'}/>{label}</button></div>{action==='assign'&&state.value&&<Assignment space={space} state={state} onClose={()=>{setAction(null);setRestoreAssign(true);}}/>}</>;
}
