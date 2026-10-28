import {useEffect,useRef,useState} from 'react';
import type {RefObject} from 'react';
import Link from './NavLink';
import {domainPath} from './navigation';
import type {QhApi,ContextSpace} from './api';
import {apiMessage} from './api';
import type {Organization} from './environment';
import {Orb} from './Ui';
import Loading from './Loading';
export function useOrganization(api:QhApi,enabled=true){
 const [value,setValue]=useState<Organization|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0);
 useEffect(()=>{if(!enabled){setValue(null);return;}let active=true;setError('');api.organization().then(v=>{if(active)setValue(v);}).catch(e=>{if(active)setError(apiMessage(e));});return()=>{active=false;};},[api,refresh,enabled]);
 async function save(next:Organization){const previous=value;setValue(next);setBusy(true);setError('');try{const saved=await api.organize(next);setValue(saved);return saved;}catch(e){setValue(previous);setError(e instanceof Error&&'status' in e&&e.status===409?'L’organisation a changé. Recharge avant de modifier à nouveau.':apiMessage(e));throw e;}finally{setBusy(false);}}
 return {value,error,busy,save,reload:()=>{setValue(null);setRefresh(n=>n+1);}};
}
export function CarouselArrows({target,name}:{target:RefObject<HTMLUListElement>;name:string}){
 function scroll(direction:number){target.current?.scrollBy({left:direction*320,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
 return <div className="carousel-controls" role="group" aria-label={'Navigation des '+name}><button type="button" className="secondary carousel-arrow" aria-label={name+' précédents'} onClick={()=>scroll(-1)}><span aria-hidden="true">‹</span></button><button type="button" className="secondary carousel-arrow" aria-label={name+' suivants'} onClick={()=>scroll(1)}><span aria-hidden="true">›</span></button></div>;
}
export default function EnvironmentDomains({state}:{state:ReturnType<typeof useOrganization>}){
 const carousel=useRef<HTMLUListElement>(null);const {value,error}=state;
 return <section aria-labelledby="domains-title" className="personal-domains"><div className="section-heading"><h2 id="domains-title">Mes domaines</h2><CarouselArrows target={carousel} name="Domaines"/></div>
 {error&&<div role="alert"><p>{error}</p><button type="button" onClick={state.reload}>Recharger l’organisation</button></div>}
 {!value&&!error&&<Loading label="Chargement de ton organisation…"/>}
 {value&&<ul ref={carousel} className="domain-grid horizontal-carousel" aria-label="Carrousel Mes domaines">{value.domains.map((domain,index)=><li key={domain.id}><Link to={domainPath(domain.id)} className="domain-orb"><Orb tone={index*38}/><span>{domain.name}</span></Link></li>)}</ul>}
 </section>;
}
export function OrganizationEditor({state}:{state:ReturnType<typeof useOrganization>}){
 const [editing,setEditing]=useState(false),[draft,setDraft]=useState<Organization|null>(null),[newName,setNewName]=useState('');
 const {value,error,busy}=state;
 async function submit(){if(!draft)return;try{await state.save(draft);setEditing(false);}catch{/* shown below */}}
 return <section><button type="button" className="secondary" disabled={!value||busy} onClick={()=>{setDraft(structuredClone(value));setEditing(true);}}>Organiser mes domaines</button>{error&&<p role="alert">{error}</p>}
 {editing&&draft&&<form className="organization-editor" aria-label="Organisation des domaines" onSubmit={e=>{e.preventDefault();void submit();}}><p>Modifier ces repères ne change ni le contenu ni les droits des Spaces.</p><nav className="secondary-navigation" aria-label="Voir les Spaces"><Link to="/spaces">Tous les Context Spaces</Link><Link to="/spaces/unclassified">Non classés</Link></nav>
 {draft.domains.map((d,i)=><div className="domain-edit" key={d.id}><label htmlFor={'domain-'+d.id}>Nom du domaine {i+1}</label><input id={'domain-'+d.id} required maxLength={100} value={d.name} disabled={busy} onChange={e=>setDraft({...draft,domains:draft.domains.map(v=>v.id===d.id?{...v,name:e.target.value}:v)})}/><label htmlFor={'domain-description-'+d.id}>Description du domaine {i+1}</label><textarea id={'domain-description-'+d.id} maxLength={500} value={d.description??''} disabled={busy} onChange={e=>setDraft({...draft,domains:draft.domains.map(v=>v.id===d.id?{...v,description:e.target.value}:v)})}/><button type="button" className="secondary" disabled={busy} onClick={()=>setDraft({...draft,domains:draft.domains.filter(v=>v.id!==d.id),memberships:Object.fromEntries(Object.entries(draft.memberships).map(([s,ids])=>[s,ids.filter(id=>id!==d.id)])),primary_domains:Object.fromEntries(Object.entries(draft.memberships).flatMap(([s,ids])=>{const rest=ids.filter(id=>id!==d.id);return rest.length?[[s,draft.primary_domains[s]===d.id?rest[0]:draft.primary_domains[s]]]:[];}))})}>Retirer le domaine {i+1}</button></div>)}
 <label htmlFor="new-domain">Nouveau domaine</label><input id="new-domain" value={newName} maxLength={100} onChange={e=>setNewName(e.target.value)}/><button type="button" disabled={busy||!newName.trim()||draft.domains.length>=50} onClick={()=>{setDraft({...draft,domains:[...draft.domains,{id:crypto.randomUUID(),name:newName}]});setNewName('');}}>Ajouter le domaine</button>
 <div className="actions"><button disabled={busy}>Enregistrer l’organisation</button><button type="button" className="secondary" disabled={busy} onClick={()=>setEditing(false)}>Annuler l’organisation</button></div></form>}
 </section>;
}
export function SpaceMemberships({space,state}:{space:ContextSpace;state:ReturnType<typeof useOrganization>}){
 const {value,busy}=state;if(!value)return null;
 return <details className="space-memberships"><summary>Domaines de ce Space</summary><fieldset disabled={busy}><legend>Organiser {space.name}</legend>{value.domains.map(d=><label key={d.id}><input type="checkbox" checked={(value.memberships[space.id]??[]).includes(d.id)} onChange={e=>{const old=value.memberships[space.id]??[];const assigned=e.target.checked?[...old,d.id]:old.filter(id=>id!==d.id);const primary={...value.primary_domains};if(!assigned.length)delete primary[space.id];else if(!assigned.includes(primary[space.id]))primary[space.id]=assigned[0];void state.save({...value,memberships:{...value.memberships,[space.id]:assigned},primary_domains:primary}).catch(()=>{});}}/>{d.name}</label>)}{(value.memberships[space.id]??[]).length>0&&<label>Domaine principal<select value={value.primary_domains[space.id]} onChange={e=>{void state.save({...value,primary_domains:{...value.primary_domains,[space.id]:e.target.value}}).catch(()=>{});}}>{value.domains.filter(d=>value.memberships[space.id]?.includes(d.id)).map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>}</fieldset></details>;
}
