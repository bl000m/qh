import {useEffect,useRef,useState} from 'react';
import {apiMessage} from './api';
import type {QhApi} from './api';
export interface AIDiagnostic {
 id:string;context_id:string;created_at:number;expires_at:number;kind:string;outcome:string;phase?:string;
 attempt_index?:number|null;http_status?:number|null;secret_redacted?:boolean;
 checks:{rule:string;result:string;reason:string|null}[];raw_response:unknown;accounting:unknown;
 metrics?:Record<string,number|null>;warnings?:string[];
}
const metricLabels:Record<string,string>={
 input_tokens:'Tokens d’entrée · usage fournisseur',output_tokens:'Tokens de sortie · usage fournisseur',
 provider_ms:'Appel Mistral · ms',consolidation_ms:'Consolidation totale · ms',
 atomic_items:'Éléments atomiques retournés',passage_references:'Références retournées (occurrences)',
 source_chars:'Source originale · caractères',source_tokens:'Tokens propres à la source · non isolés',source_turns:'Tours sources',
 source_disclosed_chars:'Texte source transmis · caractères',catalogue_passages:'Passages du catalogue',
 catalogue_chars:'Catalogue et étiquettes · caractères JSON normalisés',previous_machine_chars:'État machine précédent · caractères',
 request_message_chars:'Messages transmis, instructions incluses · caractères',request_schema_chars:'Schéma de sortie · caractères JSON normalisés',
 output_json_chars:'JSON retourné · caractères',output_json_bytes:'JSON retourné · octets UTF-8',
 atomic_text_chars:'Textes atomiques · caractères',evidence_json_chars:'Preuves/références · caractères JSON normalisés',
};
const warningLabels:Record<string,string>={
 output_tokens_over_3x_input:'Sortie supérieure à trois fois l’entrée, avec au moins 2 000 tokens de sortie.',
 dense_atomic_items:'Au moins huit éléments et plus d’un élément pour 100 caractères de source.',
 evidence_over_half_output:'Les preuves/références représentent plus de la moitié d’une sortie d’au moins 2 000 caractères.',
 catalogue_over_2x_source:'Métadonnées du catalogue supérieures à deux fois la source, avec au moins 4 000 caractères.',
};
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
 {item.kind==='uum'&&item.metrics&&<section aria-label="Performances UUM privées">
  <h4>Performances UUM</h4>
  <p className="small">Mesures observées ; les tailles JSON normalisées décrivent une sérialisation compacte. Les tokens concernent la requête complète, pas uniquement la source, et ne constituent pas une facture vérifiée. « — » signifie indisponible ; les anciens diagnostics ne sont pas recalculés.</p>
  <dl>{Object.entries(metricLabels).map(([key,label])=><div key={key}><dt>{label}</dt><dd>{item.metrics?.[key]?.toLocaleString('fr-FR')??'—'}</dd></div>)}</dl>
  <p className="small">Seuils indicatifs, sans refus, plafond ou nouvelle tentative automatique. Une sortie longue peut être justifiée.</p>
  {!!item.warnings?.length&&<ul aria-label="Indicateurs de disproportion">{item.warnings.map(code=><li key={code}>{warningLabels[code]??code}</li>)}</ul>}
 </section>}
 {item.secret_redacted&&<p>Une occurrence de la clé a été masquée ; ce JSON n’est donc pas strictement identique.</p>}
 <ul>{item.checks.map((check,index)=><li key={index}>{check.result} · {check.rule}{check.reason?' : '+check.reason:''}</li>)}</ul>
 <p>Les étapes non listées n’ont pas été exécutées ou ne sont pas instrumentées ; aucun contrôle automatique général de vérité.</p>
 <details><summary>Tokens et coût comptabilisés</summary><pre className="json-value">{JSON.stringify(item.accounting,null,2)}</pre></details>
 <details><summary>JSON original Mistral</summary><pre className="json-value">{JSON.stringify(item.raw_response,null,2)}</pre></details>
 <button type="button" className="secondary" disabled={busy} onClick={()=>{void remove(item.id);}}>Supprimer ce diagnostic</button>
 </details>)}
 </section>;
}
