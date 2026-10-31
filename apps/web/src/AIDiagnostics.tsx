import {useEffect,useRef,useState} from 'react';
import {apiMessage} from './api';
import type {QhApi} from './api';
export interface AIDiagnostic {
 id:string;context_id:string;created_at:number;expires_at:number;kind:string;outcome:string;phase?:string;
 attempt_index?:number|null;http_status?:number|null;secret_redacted?:boolean;
 checks:{rule:string;result:string;reason:string|null}[];raw_response:unknown;accounting:unknown;
 metrics?:Record<string,number|null>;warnings?:string[];
 call_phase?:string;legacy_metrics?:boolean;validation_rounds?:{items:number}[];
 operation?:{id:string;calls:{attempt_index:number;phase:string;metrics:Record<string,number|null>}[];totals:Record<string,number|null>};
}
const metricLabels:Record<string,string>={
 input_tokens:'Tokens d’entrée · usage fournisseur',output_tokens:'Tokens de sortie · usage fournisseur',
 provider_ms:'Appel Mistral · ms',consolidation_ms:'Consolidation totale · ms',
 atomic_items:'Éléments atomiques · cette réponse',passage_references:'Références retournées (occurrences)',
 source_chars:'Source originale · caractères',source_tokens:'Tokens propres à la source · non isolés',source_turns:'Tours sources',
 source_disclosed_chars:'Texte source transmis · caractères',catalogue_passages:'Passages du catalogue',
 catalogue_chars:'Catalogue et étiquettes · caractères JSON normalisés',previous_machine_chars:'État machine précédent · caractères',
 request_instruction_chars:'Instructions transmises · caractères',request_data_chars:'Données transmises · caractères',
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
const phaseLabel=(phase?:string)=>phase==='extraction'?'Extraction UUM · source/bloc':phase==='extraction_summary'?'Extraction et synthèse · même appel':phase==='summary'?'Synthèse finale':phase==='recap_review'?'Revue sémantique du résumé':'Appel non classé';
const number=(value?:number|null)=>value?.toLocaleString('fr-FR')??'—';
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
  <h4>{phaseLabel(item.call_phase)}</h4>
  <p>{number(item.metrics.atomic_items)} éléments atomiques dans cette réponse · {number(item.metrics.input_tokens)} tokens d’entrée · {number(item.metrics.request_message_chars)} caractères transmis.</p>
  {item.call_phase==='recap_review'&&<p>Cette revue est une appréciation probabiliste, pas une preuve logique ni une confirmation humaine.</p>}
  {item.call_phase==='summary'&&<p>La synthèse produit un résumé, pas de nouveaux éléments atomiques. Les validations du lot ci-dessous ne comptent pas les éléments de cette réponse.</p>}
  {item.legacy_metrics&&<p className="small">Ancien diagnostic : les compteurs hérités du dernier bloc sont écartés pour la synthèse. Aucun regroupement entre appels n’est déduit ; l’agrégat historique n’était pas enregistré.</p>}
  {!!item.validation_rounds?.length&&<p>Validation des lots : {item.validation_rounds.map((round,index)=>`passage ${index+1} · ${round.items} éléments`).join(' ; ')}. Les passages répétés ne sont pas de nouveaux éléments.</p>}
  {item.operation&&<section aria-label="Consolidation agrégée"><h4>Consolidation agrégée{item.outcome!=='accepted'?' · à ce stade':''}</h4>
   <p>{number(item.operation.totals.calls)} appel(s) observé(s) · {number(item.operation.totals.atomic_items)} éléments extraits · {number(item.operation.totals.blocks)} bloc(s) · {number(item.operation.totals.summaries)} synthèse(s) · {number(item.operation.totals.reviews)} revue(s) sémantique(s) · {number(item.operation.totals.input_tokens)} tokens d’entrée au total.</p>
   <p className="small">HTTP extraction : {number(item.operation.totals.extraction_ms)} ms · HTTP synthèse : {number(item.operation.totals.summary_ms)} ms · HTTP combiné : {number(item.operation.totals.combined_ms)} ms · HTTP revue du résumé : {number(item.operation.totals.recap_review_ms)} ms · Validation locale, contrôles inclus : {number(item.operation.totals.validation_ms)} ms · Publication atomique : {number(item.operation.totals.persistence_ms)} ms.</p>
   <details><summary>Appels de cette opération</summary><table><thead><tr><th>Tentative</th><th>Phase</th><th>Éléments</th><th>Tokens d’entrée</th><th>Caractères transmis</th></tr></thead><tbody>{item.operation.calls.map((call,index)=><tr key={index}><td>{call.attempt_index}</td><td>{phaseLabel(call.phase)}</td><td>{number(call.metrics.atomic_items)}</td><td>{number(call.metrics.input_tokens)}</td><td>{number(call.metrics.request_message_chars)}</td></tr>)}</tbody></table></details>
  </section>}
  <details><summary>Mesures détaillées de cet appel</summary>
  <p className="small">Mesures observées ; les tailles JSON normalisées décrivent une sérialisation compacte. Les tokens concernent la requête complète, pas uniquement la source, et ne constituent pas une facture vérifiée. « — » signifie indisponible ; les fichiers historiques restent inchangés.</p>
  <dl>{Object.entries(metricLabels).map(([key,label])=><div key={key}><dt>{label}</dt><dd>{item.metrics?.[key]?.toLocaleString('fr-FR')??'—'}</dd></div>)}</dl>
  </details>
  <p className="small">Seuils indicatifs, sans refus, plafond ou nouvelle tentative automatique. Une sortie longue peut être justifiée.</p>
  {!!item.warnings?.length&&<ul aria-label="Indicateurs de disproportion">{item.warnings.map(code=><li key={code}>{warningLabels[code]??code}</li>)}</ul>}
 </section>}
 {item.secret_redacted&&<p>Une occurrence de la clé a été masquée ; ce JSON n’est donc pas strictement identique.</p>}
 <details><summary>Contrôles détaillés · {item.checks.filter(c=>c.result==='PASS').length} PASS · {item.checks.filter(c=>c.result!=='PASS').length} autres résultats</summary>
 <ul>{item.checks.map((check,index)=><li key={index}>{check.result} · {check.rule}{check.reason?' : '+check.reason:''}</li>)}</ul></details>
 <p>Les étapes non listées n’ont pas été exécutées ou ne sont pas instrumentées ; aucun contrôle automatique général de vérité.</p>
 <details><summary>Tokens et coût comptabilisés</summary><pre className="json-value">{JSON.stringify(item.accounting,null,2)}</pre></details>
 <details><summary>JSON original Mistral</summary><pre className="json-value">{JSON.stringify(item.raw_response,null,2)}</pre></details>
 <button type="button" className="secondary" disabled={busy} onClick={()=>{void remove(item.id);}}>Supprimer ce diagnostic</button>
 </details>)}
 </section>;
}
