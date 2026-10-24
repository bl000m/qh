import {useEffect,useRef,useState} from 'react';
import {apiMessage} from './api';
import type {QhApi} from './api';
export interface AIDiagnostic {
 id:string;context_id:string;created_at:number;expires_at:number;kind:string;outcome:string;phase?:string;
 attempt_index?:number|null;http_status?:number|null;secret_redacted?:boolean;
 checks:{rule:string;result:string;reason:string|null}[];raw_response:unknown;accounting:unknown;
}
export default function AIDiagnostics({api,scope}:{api:QhApi;scope:string}){
 const [items,setItems]=useState<AIDiagnostic[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{setItems([]);setError('');const timer=window.setInterval(()=>setItems(rows=>rows.filter(r=>r.expires_at>Date.now()/1000)),1000);return()=>clearInterval(timer);},[scope]);
 const active=useRef(true);
 useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 async function load(){setBusy(true);setError('');try{const rows=await api.aiDiagnostics(scope);if(active.current)setItems(rows);}catch(e){setItems([]);setError(apiMessage(e));}finally{setBusy(false);}}
 async function remove(id:string){setBusy(true);try{await api.deleteAIDiagnostic(scope,id);setItems(rows=>rows.filter(r=>r.id!==id));}catch(e){setItems([]);setError(apiMessage(e));}finally{setBusy(false);}}
 return <section aria-label="Diagnostics IA privés" key={scope}><h3>Diagnostics IA privés</h3>
 <p>Réservés à votre compte de développement, dans ce Space. Réponse brute conservée une heure, sans prompt ni en-têtes. Aucun appel Mistral en consultant ces données.</p>
 <button type="button" className="secondary" disabled={busy} onClick={()=>{void load();}}>Charger les diagnostics privés</button>
 {error&&<p role="alert">{error}</p>}
 {items.map(item=><details key={item.id}><summary>{item.kind} · tentative {item.attempt_index??'sans envoi'} · {item.outcome} · HTTP {item.http_status??'—'}</summary>
 <p>Identifiant : {item.id}. Phase : {item.phase??'en cours'}. Expiration : {new Date(item.expires_at*1000).toLocaleString('fr-FR')}.</p>
 <p>HTTP, comptabilité, validation QH et qualité sémantique sont des résultats distincts. Aucun statut ne confirme des faits.</p>
 {item.secret_redacted&&<p>Une occurrence de la clé a été masquée ; ce JSON n’est donc pas strictement identique.</p>}
 <ul>{item.checks.map((check,index)=><li key={index}>{check.result} · {check.rule}{check.reason?' : '+check.reason:''}</li>)}</ul>
 <p>Les étapes non listées n’ont pas été exécutées ou ne sont pas instrumentées ; aucun contrôle automatique général de vérité.</p>
 <details><summary>Tokens et coût comptabilisés</summary><pre className="json-value">{JSON.stringify(item.accounting,null,2)}</pre></details>
 <details><summary>JSON original Mistral</summary><pre className="json-value">{JSON.stringify(item.raw_response,null,2)}</pre></details>
 <button type="button" className="secondary" disabled={busy} onClick={()=>{void remove(item.id);}}>Supprimer ce diagnostic</button>
 </details>)}
 </section>;
}
