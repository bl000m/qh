import {useEffect,useState} from 'react';
import type {QhApi,ContextSpace} from './api';
import {apiMessage} from './api';
import type {Organization} from './environment';
import bubble from './brand/qh-bubble.png';
export function useOrganization(api:QhApi){
 const [value,setValue]=useState<Organization|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0);
 useEffect(()=>{let active=true;setError('');api.organization().then(v=>{if(active)setValue(v);}).catch(e=>{if(active)setError(apiMessage(e));});return()=>{active=false;};},[api,refresh]);
 async function save(next:Organization){setBusy(true);setError('');try{const saved=await api.organize(next);setValue(saved);return saved;}catch(e){setError(e instanceof Error&&'status' in e&&e.status===409?'L’organisation a changé. Rechargez avant de modifier à nouveau.':apiMessage(e));throw e;}finally{setBusy(false);}}
 return {value,error,busy,save,reload:()=>{setValue(null);setRefresh(n=>n+1);}};
}
export default function EnvironmentDomains({state,selected,onSelect,onCreate}:{state:ReturnType<typeof useOrganization>;selected:string|null;onSelect:(id:string|null)=>void;onCreate:()=>void}){
 const [editing,setEditing]=useState(false),[draft,setDraft]=useState<Organization|null>(null),[newName,setNewName]=useState('');
 const {value,error,busy}=state;
 async function submit(){if(!draft)return;try{await state.save(draft);setEditing(false);if(selected&&!draft.domains.some(d=>d.id===selected))onSelect(null);}catch{/* error is shown below */}}
 const active=value?.domains.find(d=>d.id===selected);
 return <section aria-labelledby="domains-title" className="personal-domains"><div className="section-heading"><div><h2 id="domains-title">Mes domaines</h2><p className="muted">Des repères personnels pour organiser vos Context Spaces. Un même Space peut apparaître dans plusieurs domaines.</p></div><button type="button" className="secondary" disabled={!value||busy} onClick={()=>{setDraft(structuredClone(value));setEditing(true);}}>Organiser mes domaines</button></div>
 {error&&<div role="alert"><p>{error}</p><button type="button" onClick={state.reload}>Recharger l’organisation</button></div>}
 {!value&&!error&&<p role="status">Chargement de votre organisation…</p>}
 {value&&<><ul className="domain-grid">{value.domains.map(domain=><li key={domain.id}><button type="button" className={'domain-orb'+(selected===domain.id?' selected':'')} aria-pressed={selected===domain.id} onClick={()=>onSelect(selected===domain.id?null:domain.id)}><img src={bubble} alt="" width={400} height={300}/><span>{domain.name}</span></button></li>)}</ul>
 <div className="domain-navigation"><button type="button" className="secondary" onClick={()=>onSelect(null)}>Tous mes Context Spaces</button>{active&&<p role="status">Domaine ouvert : <strong>{active.name}</strong></p>}</div>
 {active&&<p>Les Spaces de ce domaine apparaissent ci-dessous. Pour commencer, <button type="button" className="text-button" onClick={onCreate}>créer un Space dans ce domaine</button> ou associer un Space existant.</p>}
 <details className="profile-preferences"><summary>Mon profil & mes préférences</summary><p>Un repère transversal, distinct des sept domaines. Vous pouvez personnaliser votre organisation ci-dessus. Le profil de compréhension personnel et les préférences partagées ne sont pas encore implémentés.</p></details></>}
 {editing&&draft&&<form className="organization-editor" aria-label="Organisation des domaines" onSubmit={e=>{e.preventDefault();void submit();}}><p>Modifier ces repères ne change ni le contenu ni les droits des Spaces.</p>
 {draft.domains.map((d,i)=><div className="domain-edit" key={d.id}><label htmlFor={'domain-'+d.id}>Nom du domaine {i+1}</label><input id={'domain-'+d.id} required maxLength={100} value={d.name} disabled={busy} onChange={e=>setDraft({...draft,domains:draft.domains.map(v=>v.id===d.id?{...v,name:e.target.value}:v)})}/><button type="button" className="secondary" disabled={busy} onClick={()=>setDraft({...draft,domains:draft.domains.filter(v=>v.id!==d.id),memberships:Object.fromEntries(Object.entries(draft.memberships).map(([s,ids])=>[s,ids.filter(id=>id!==d.id)]))})}>Retirer le domaine {i+1}</button></div>)}
 <label htmlFor="new-domain">Nouveau domaine</label><input id="new-domain" value={newName} maxLength={100} onChange={e=>setNewName(e.target.value)}/><button type="button" disabled={busy||!newName.trim()||draft.domains.length>=50} onClick={()=>{setDraft({...draft,domains:[...draft.domains,{id:crypto.randomUUID(),name:newName}]});setNewName('');}}>Ajouter le domaine</button>
 <div className="actions"><button disabled={busy}>Enregistrer l’organisation</button><button type="button" className="secondary" disabled={busy} onClick={()=>setEditing(false)}>Annuler l’organisation</button></div></form>}
 </section>;
}
export function SpaceMemberships({space,state}:{space:ContextSpace;state:ReturnType<typeof useOrganization>}){
 const {value,busy}=state;if(!value)return null;
 return <details className="space-memberships"><summary>Domaines de ce Space</summary><fieldset disabled={busy}><legend>Organiser {space.name}</legend>{value.domains.map(d=><label key={d.id}><input type="checkbox" checked={(value.memberships[space.id]??[]).includes(d.id)} onChange={e=>{const old=value.memberships[space.id]??[];const assigned=e.target.checked?[...old,d.id]:old.filter(id=>id!==d.id);void state.save({...value,memberships:{...value.memberships,[space.id]:assigned}}).catch(()=>{});}}/>{d.name}</label>)}</fieldset></details>;
}
